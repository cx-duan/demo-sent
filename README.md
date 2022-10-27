# Demo - Sentiment Analysis for each Entity

## Description:
This demo was put together to showcase possible applications of AssemblyAI's API. Processing the JSON file returned after processing audio, a user can display a dashboard showing sentiment analysis for each entity identified in the audio file. The website displays a pie-chart of a sentiment analysis overview (positive, negative, neutral) distributions as well as a high-level list of entities and correlating sentiment.

File contains:
- Sentiment overview for call (Pie Chart)    
- Sentiment of an Entity (List)
- Number of sentences 

Streamlit App:
https://cx-duan-demo-sent-sentiment-entity-overview-dqspnq.streamlitapp.com/

<img width="1138" alt="image" src="https://user-images.githubusercontent.com/57568318/198199829-48215e8c-0085-46af-ba6c-0232d931aec0.png">


## To Run:

To run Python file:
python3 -m streamlit run sentiment-entity-overview.py 

To run app via StreamLit:
python3 -m streamlit run sentiment-entity-overview.py 


## Import Libraries
pip3 install streamlit
pip3 install pandas
pip3 install numpy
pip3 install plotly

#Need to add ability to upload own file.


