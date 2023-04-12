import streamlit as st
import pandas as pd
import json
import plotly.express as px
import plotly.graph_objects as go
import numpy as np
import util
from configure import auth_key
import requests
from urllib.request import urlopen
from bs4 import BeautifulSoup
from time import sleep


transcript_endpoint = "https://api.assemblyai.com/v2/transcript"
upload_endpoint = 'https://api.assemblyai.com/v2/upload'

headers_auth_only = {'authorization': auth_key}
headers = {
   "authorization": auth_key,
   "content-type": "application/json"
}

#JSON file read. Can be replaced with upload
with open('response.json', 'r') as transcript_json:
    transcript_data = json.load(transcript_json)

# Results for entities and sentiment returned from JSON file read
sentiment_analysis_results = transcript_data['sentiment_analysis_results']
transcript = transcript_data['text']

entities = transcript_data['entities']

# Dictionary to translate sentiment values to -1, 0 , 1 to calculate sentiment later
sent_to_num = {
    "POSITIVE": 1,
    "NEUTRAL": 0,
    "NEGATIVE": -1
}

# Flatten function to remove redundant zeros and help collect average for each entity
def flatten(S):
    if S == []:
        return S
    if isinstance(S[0], list):
        return flatten(S[0]) + flatten(S[1:])
    return S[:1] + flatten(S[1:])

# Isolate sentiment for each entity by timestamp near each time the entity is mentioned
def get_sentiment(start, end, entity):
    sent = []
    ent_arr = []
    for sentiment in sentiment_analysis_results:
        # Add JSON key-value to list if sentiment is between the start and end time specified 
        if int(sentiment['start']) >= start and int(sentiment['end'] <= end):
            sent.append(sentiment)
        # Extract the sentitment from the key value. Matching two conditions
    for s in sent:
        #Sent_to_num function to convert sentiment to a number
        ent_arr.append(sent_to_num[s['sentiment']])
        # Return formatted entity with respective sentiment value 
    return entity.capitalize(), ent_arr

#Loop to define start and end times. 2000ms buffer. Add 
sent_ent = {}
for ent in entities:
    start = 0
    end = int(ent['end'] + 2000)
    if int(ent['start'] - 2000 >= 0):
        start = int(ent['start'] - 2000)
# List to dictionary. Append sentiment values for each key
    sent = get_sentiment(start, end, ent['text'])
    if sent[0] in sent_ent:
        sent_ent[sent[0]].append(sent[1])
    else:
        sent_ent[sent[0]] = [sent[1]]

# Flatten result and average each value for each key
avg_sent_ent = {}
for i in sent_ent:
    flat = flatten(sent_ent[i])
    s = sum(flat)
    l = len(flat)
    if l > 0:
        avg = s / l
        avg_sent_ent[i] = avg
def categorize_sentiment(avg_sent_ent):
    result = {}
    for i in avg_sent_ent:
        sentiment = "neutral"
        if avg_sent_ent[i] < 0:
            sentiment = "negative"
            if avg_sent_ent[i] < -0.5:
                sentiment = "very negative"
        elif avg_sent_ent[i] > 0:
            sentiment = "positive"
            if avg_sent_ent[i] < 0.5:
                sentiment = "very positive"
        result[i] = sentiment
    return result

# Add the sentiment value to the dictionary based on if the average sentiment value is >0, <0, =0
sent_and_label = {}
sentences = []
for i in avg_sent_ent:
    sentiment_dict = categorize_sentiment({i: avg_sent_ent[i]})
    sentiment = sentiment_dict[i]
    
    sent_and_label[i] = {
        "sentiment_value": avg_sent_ent[i],
        "sentiment": sentiment
    }
    sentences.append("%s has a %s sentiment" % (i, sentiment))
print(sentences)

total = sum(avg_sent_ent.values())
total_avg_sent = total / len(avg_sent_ent)

# Categorize the overall sentiment
overall_sentiment_dict = categorize_sentiment({"Overall": total_avg_sent})
overall_sentiment = overall_sentiment_dict["Overall"]

# Print the overall sentiment
print("The overall sentiment is %s with an average sentiment value of %.2f" % (overall_sentiment, total_avg_sent))


#Streamlit Frontend
#App description
st.title('Sentiment analysis overview')
st.caption("This is a Sentiment Analysis on your chosen audio file using AssemblyAI's API")	

# Display transcript
print('creating transcript')
st.sidebar.header('Transcript of the earnings call')
st.sidebar.markdown(transcript)

#convert json to dataframe
sen_df = pd.DataFrame(sentiment_analysis_results)

#sum sentiment to run calculations
positive_sum = (sen_df['sentiment'] == 'POSITIVE').sum()
neutral_sum = (sen_df['sentiment'] == 'NEUTRAL').sum()
negative_sum = (sen_df['sentiment'] == 'NEGATIVE').sum()
total_sum = positive_sum + neutral_sum + negative_sum

#number of sentences
data_total_count = sen_df.shape[0]
st.markdown("### Number of sentences: " + str(data_total_count))

#count and group sentiment by count
grouped = pd.DataFrame(sen_df['sentiment'].value_counts()).reset_index()
grouped.columns = ['sentiment','count']

#set 3 columns
col1, col2, col3 = st.columns(3)

#pie graph
fig = px.pie(grouped, values='count', names='sentiment',color='sentiment', color_discrete_map={"NEGATIVE":"#D96098","NEUTRAL":"#5584AC","POSITIVE":"#95D1CC"}, title='<span style="font-size: 34px;">Pie Chart') 

fig.update_layout(
    legend_title_text='Legend - Sentiment',
    showlegend=True,
    autosize=False,
    width=400,
    height=500,
    
    legend=dict(
    yanchor="top",
    y=0.99,
    xanchor="right",
    x=0.01
    )
)
col1.plotly_chart(fig)

pos_perc = grouped[grouped['sentiment']=='POSITIVE']['count'].iloc[0]*100/sen_df.shape[0]
neg_perc = grouped[grouped['sentiment']=='NEGATIVE']['count'].iloc[0]*100/sen_df.shape[0]
neu_perc = grouped[grouped['sentiment']=='NEUTRAL']['count'].iloc[0]*100/sen_df.shape[0]

sentiment_score = neu_perc+pos_perc-neg_perc

fig = go.Figure()

fig.add_trace(go.Indicator(
    mode = "delta",
    value = sentiment_score,
    domain = {'row': 1, 'column': 1}))

fig.update_layout(
	template = {'data' : {'indicator': [{
        'title': {'text': "Sentiment score"},
        'mode' : "number+delta+gauge",
        'delta' : {'reference': 50}}]
                         }},
    autosize=False,
    width=400,
    height=500,
    margin=dict(
        l=20,
        r=50,
        b=50,
        pad=4
    )
)

col3.plotly_chart(fig)

## Display negative sentence locations
fig = px.scatter(sentiment_analysis_results, y='sentiment', color='sentiment', size='confidence', hover_data=['text'], color_discrete_map={"NEGATIVE":"firebrick","NEUTRAL":"navajowhite","POSITIVE":"darkgreen"})


fig.update_layout(
	showlegend=False,
    autosize=False,
    width=800,
    height=300,
    margin=dict(
        l=50,
        r=50,
        b=50,
        t=50,
        pad=4
    )
)

st.plotly_chart(fig)

#list sentiment list as bullet points
with st.expander("Entity Sentiment List",True):
    for i in sentences:
        st.write("- " + i)


