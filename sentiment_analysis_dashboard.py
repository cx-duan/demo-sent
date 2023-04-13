import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import util
import requests
from PIL import Image
from pytube import YouTube

# Streamlit command to run: python3 -m streamlit run sentiment_analysis_dashboard.py

#Import AAI logo
image = Image.open('AAI Logo.png')

#Streamlit Frontend
#Initiate App with config, AAI logo and title
st.image(image, caption='Entity Sentiment Analysis demo')
st.title('AssemblyAI - Sentiment Analysis Dashboard')
st.caption("This is a Sentiment Analysis on the entities of your chosen audio file using AssemblyAI's API")

auth_key = st.text_input("Enter your AssemblyAI API key", type="password")
headers = {'authorization': auth_key}
while not auth_key:
    st.warning("Please enter your API key.")
    st.stop()

# Get YouTube link from user
video_url = st.text_input(label= "Paste YouTube URL here (Sample URL Provided)",value="https://www.youtube.com/watch?v=hF4kap6WvOk")
# Alternate URL
# video_url = st.text_input(label= "Paste YouTube URL here (Sample URL Provided)",value="https://www.youtube.com/watch?v=SsUNBUe9hPE")
# Set progress bar
youtube_progress_bar = st.progress(0, text="Transcription in progress")

# Set title to YouTube video using metadata
video_title=(f'{YouTube(video_url).title}')
st.subheader(video_title)
st.video(video_url)

polling_endpoint, file = util.transcribe_from_link(video_url, auth_key)
# Update progress bar
youtube_progress_bar.progress(40, text="Uploading to AssemblyAI endpoint")
print('Uploaded')

# Changes status to 'submitted'
st.session_state['status'] = 'submitted'

# Repeatedly poll the transcript until it is completed
util.poll(polling_endpoint, auth_key)

# Get status
st.session_state['status']  = util.get_status(polling_endpoint, auth_key)
# Status complete, return transcript
if st.session_state['status'] =='completed':
    polling_response = requests.get(polling_endpoint, headers=headers)
    full_transcript = polling_response.json()
# Return Sentiment, Entity Keys    
    transcript = polling_response.json()['text']
    sentiment_analysis_results = polling_response.json()['sentiment_analysis_results']
    entities = polling_response.json()['entities']

# Display transcript
print('Transcript completed')
youtube_progress_bar.progress(100, text="Completed transcript")
st.sidebar.title("Transcript")
st.sidebar.header(video_title)
st.sidebar.markdown(transcript)

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
sentences = util.entity_sentiment_analysis(entities, sentiment_analysis_results)
with st.expander("Entity Sentiment List",True):
    for i in sentences:
        st.write("- " + i)

