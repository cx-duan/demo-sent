import streamlit as st
import pandas as pd
import json
import plotly.express as px
import plotly.graph_objects as go
import numpy as np

# Streamlit command to run: python3 -m streamlit run sentiment-entity-overview.py 

#JSON file read. Can be replaced with upload
with open('response.json', 'r') as transcript_json:
    transcript_data = json.load(transcript_json)

# Results for entities and sentiment returned from JSON file read
sentiment_analysis_results = transcript_data['sentiment_analysis_results']
entities = transcript_data['entities']

# Dictionary to translate sentiment values to -1, 0 , 1 to calculate sentiment later
sent_to_num = {
    "POSITIVE": 1,
    "NEUTRAL": 0,
    "NEGATIVE": -1
}

# Flatten function to remove redundant zeros
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
        # Add JSON keyvalue to list if sentiment is between the start and end time specified 
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
    sent_list = ''
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
real_sent_ent = {}
for i in sent_ent:
    flat = flatten(sent_ent[i])
    s = sum(flat)
    l = len(flat)
    if l > 0:
        avg = s / l
        real_sent_ent[i] = avg
# Add the sentiment value to the dictionary based on if the average sentiment value is >0, <0, =0
sent_and_label = {}
sentences = []
for i in real_sent_ent:
    sentiment = "neutral"

    if real_sent_ent[i] < 0:
        sentiment = "negative"
        if real_sent_ent[i] < -0.5:
            sentiment = "very negative"
    elif real_sent_ent[i] > 0:
        sentiment = "positive"
        if real_sent_ent[i] < 0.5:
            sentiment = "very positive"
    
    sent_and_label[i] = {
        "sentiment_value": real_sent_ent[i],
        "sentiment": sentiment
    }
    sentences.append("%s has a %s sentiment" % (i, sentiment))

#Streamlit Frontend
#App description
st.title('Sentiment analysis overview')
# st.subheader('Demo Day')

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

#set 2 columns
col1, col2 = st.columns(2)

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

#list sentiment list as bullet points
with col2:
    for i in sentences:
        st.markdown("- " + i)



### Print Sentiment Summary (%) and respective sentiment texts ###

# print('\n===| Sentiment Summary |===\n')
# print(f'Positive Sentiment Total: {round((positive_sum / total_sum) * 100, 2)}%')
# print(f'Neutral Sentiment Total: {round((neutral_sum / total_sum) * 100, 2)}%')
# print(f'Negative Sentiment Total: {round((negative_sum / total_sum) * 100, 2)}%')


# postive_sentiment =(sen_df[sen_df['sentiment']== 'POSITIVE'])
# neutral_sentiment =(sen_df[sen_df['sentiment']== 'NEUTRAL'])
# negative_sentiment =(sen_df[sen_df['sentiment']== 'NEGATIVE'])

# print('\n===| Positive Sentiment Text + Confidence |===\n')

# # print(postive_sentiment['text'])
# print(postive_sentiment[['text', 'confidence']])

# print('\n===| Negative Sentiment Text + Confidence |===\n')

# # print(negative_sentiment['text'])
# print(negative_sentiment[['text', 'confidence']])

## Display sentiment score

# pos_sentiment = grouped[grouped['sentiment']=='POSITIVE']['count']
# neg_sentiment = grouped[grouped['sentiment']=='NEGATIVE']['count']
# neu_sentiment = grouped[grouped['sentiment']=='NEUTRAL']['count']

# pos_perc = round(pos_sentiment.iloc[0]*100/data_total_count)
# neg_perc = round(neg_sentiment.iloc[0]*100/data_total_count)
# neu_perc = round(neu_sentiment.iloc[0]*100/data_total_count)

# sentiment_score = pos_perc + neu_perc - neg_perc
# print (pos_perc , neg_perc, neu_perc)

