import requests
from pytube import YouTube
import streamlit as st
import time

# Endpoints
transcript_endpoint = "https://api.assemblyai.com/v2/transcript"
upload_endpoint = 'https://api.assemblyai.com/v2/upload'
CHUNK_SIZE = 5242880

# Function that saves and uploads YouTube link locally
def save_audio(link):
    yt = YouTube(link)
    stream = yt.streams.filter(only_audio=True).first()
    save_location = stream.download()
    print('Saved mp3 to', save_location)
    return save_location

#Function to read local file
def read_file(filename):
    with open(filename, 'rb') as _file:
        while True:
            data = _file.read(CHUNK_SIZE)
            if not data:
                break
            yield data
# Function converting milliseconds
def convertMillis(start_ms):
    seconds = int((start_ms / 1000) % 60)
    minutes = int((start_ms / (1000 * 60)) % 60)
    hours = int((start_ms / (1000 * 60 * 60)) % 24)
    btn_txt = ''
    if hours > 0:
        btn_txt += f'{hours:02d}:{minutes:02d}:{seconds:02d}'
    else:
        btn_txt += f'{minutes:02d}:{seconds:02d}'
    return btn_txt


# a function to upload a given file to AssemblyAI's servers
def upload_file(file, auth_key):
    headers_auth_only = {'authorization': auth_key}
    upload_response = requests.post(
        upload_endpoint,
        headers=headers_auth_only, 
        data=read_file(file)
	)
    return upload_response.json()['upload_url']

# a function that takes a youtube link, downloads the video, uploads it to AssemblyAI's servers and transcribes it
@st.cache_data
def transcribe_from_link(link, auth_key):
	headers_auth_only = {'authorization': auth_key}
    # download the audio of the YouTube video locally
	save_location = save_audio(link)
	# start the transcription of the audio file
	transcript_request = {
		'audio_url': upload_file(save_location, auth_key),
        'speaker_labels': True,
        'entity_detection': True,
        'sentiment_analysis': True

	}
	transcript_response = requests.post(transcript_endpoint, json=transcript_request, headers=headers_auth_only)
	# this is the id of the file that is being transcribed in the AssemblyAI servers
	# we will use this id to access the completed transcription
	transcript_id = transcript_response.json()['id']
	polling_endpoint = transcript_endpoint + "/" + transcript_id
    
	return polling_endpoint, save_location

# return the status of a given transcript 
def get_status(polling_endpoint, auth_key):
    headers_auth_only = {'authorization': auth_key}
    polling_response = requests.get(polling_endpoint, headers=headers_auth_only)
    return polling_response.json()['status']

# repeatedly checks the status of a given transcript until the status is completed or error
def poll(polling_endpoint, auth_key):
    status = get_status(polling_endpoint, auth_key)
    while status not in ["error", "completed"]:
        time.sleep(10)
        status = get_status(polling_endpoint, auth_key)

sent_to_num = {
    "POSITIVE": 1,
    "NEUTRAL": 0,
    "NEGATIVE": -1
}

def flatten(S):
    if S == []:
        return S
    if isinstance(S[0], list):
        return flatten(S[0]) + flatten(S[1:])
    return S[:1] + flatten(S[1:])

# Isolate sentiment for each entity by timestamp near each time the entity is mentioned
def get_sentiment(start, end, entity, sentiment_analysis_results):
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
def get_entities(entities):
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

total = sum(avg_sent_ent.values())
# total_avg_sent = total / len(avg_sent_ent)

# Categorize the overall sentiment
# overall_sentiment_dict = categorize_sentiment({"Overall": total_avg_sent})
# overall_sentiment = overall_sentiment_dict["Overall"]
