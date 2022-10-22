from datetime import date
import streamlit as st
from streamlit.components.v1 import iframe
import streamlit.components.v1 as components
import os
import numpy as np
from io import BytesIO
#import whisper
import assembly

import os
import openai
openai.api_key = os.getenv("OPENAI_API_KEY")


words=['Soccer', 'Badminton', 'University']


parent_dir = os.path.dirname(os.path.abspath(__file__))
# Custom REACT-based component for recording client audio in browser
build_dir = os.path.join(parent_dir, "st_audiorec/frontend/build")
# specify directory and initialize st_audiorec object functionality
st_audiorec = components.declare_component("st_audiorec", path=build_dir)

st.set_page_config(layout="centered", page_icon="🎓", page_title="Hitorigoto")

def next_word():
    st.session_state["answering"]=True
    st.session_state["current_word_index"]+=1



if "answering" not in st.session_state:
    st.session_state["answering"] = True
if "audio_data" not in st.session_state:
    st.session_state["audio_data"] = {}

if "current_word_index" not in st.session_state:
    st.session_state["current_word_index"] = 0
if "answer" not in st.session_state:
    st.session_state["answer"] = ""
if "transcript" not in st.session_state:
    st.session_state["transcript"] = ""
if "correction" not in st.session_state:
    st.session_state["correction"] = ""
if "native" not in st.session_state:
    st.session_state["native"] = ""


st.sidebar.title(words[st.session_state["current_word_index"]])
st.sidebar.button('次の単語', on_click=next_word)

st.title("独り言エクササイズ")

val = st_audiorec()

answer = st.empty()
if st.session_state["answering"]:
    answer.info('AIの回答：')
elif st.session_state["answer"] == words[st.session_state["current_word_index"]]:
    answer.success('AIの回答：'+st.session_state["answer"])
else:
    answer.error('AIの回答：'+st.session_state["answer"])


col1, col2, col3 = st.columns(3)

with col1:
   transcript=st.empty()
   with transcript.expander("あなたの英語", not st.session_state["answering"]):
        st.write(st.session_state["transcript"])

with col2:
   correction=st.empty()
   with correction.expander("添削", not st.session_state["answering"]):
        st.write(st.session_state["correction"])

with col3:
   native=st.empty()
   with native.expander("お手本", not st.session_state["answering"]):
        st.write(st.session_state["native"])

if isinstance(val, dict) and  val != st.session_state['audio_data'] and st.session_state["answering"]==True:  # retrieve audio data
    st.session_state["answering"] = False
    st.session_state['audio_data']=val

    with st.spinner('ロード中。。'):
        ind, vall = zip(*val['arr'].items())
        ind = np.array(ind, dtype=int)  # convert to np array
        vall = np.array(vall)             # convert to np array
        sorted_ints = vall[ind]
        stream = BytesIO(b"".join([int(v).to_bytes(1, "big") for v in sorted_ints]))
        wav_bytes = stream.read()

        # wav_bytes contains audio data in format to be further processed
        # display audio data as received on the Python side
        with open('myfile.wav', mode='bx') as f:
            f.write(wav_bytes)

        # model = whisper.load_model("tiny")
        # result = model.transcribe("myfile.wav")['text']
        result = assembly.transcribe("myfile.wav")
        print(result)
        os.remove("myfile.wav")

        st.session_state['transcript']=result
        with transcript.expander("あなたの英語", True):
            st.write(st.session_state['transcript'])

    response = openai.Completion.create(
      model="text-davinci-002",
      prompt="Guess what the words is.\n\n" + result + "\n\nWord:",
      temperature=0,
      max_tokens=40,
      top_p=1,
      frequency_penalty=0,
      presence_penalty=0
    )
    print(response)
    st.session_state['answer'] = response['choices'][0]['text'].strip()
    if st.session_state["answer"] == words[st.session_state["current_word_index"]]:
        st.balloons()
        answer.success('AIの回答：'+st.session_state["answer"])
    else:
        answer.error('AIの回答：'+st.session_state["answer"])

    response = openai.Completion.create(
      model="text-davinci-002",
      prompt="Correct English grammar\n\n" + result + "\n",
      temperature=0,
      max_tokens=40,
      top_p=1,
      frequency_penalty=0,
      presence_penalty=0
    )
    st.session_state['correction'] = response['choices'][0]['text']
    with correction.expander("添削", True):
         st.write(st.session_state['correction'])

    response = openai.Completion.create(
      model="text-davinci-002",
      prompt="Completely rewrite the paragraph about '"+words[st.session_state["current_word_index"]]+"' into natural and easy English without using the word '"+words[st.session_state["current_word_index"]]+"'.\n\n" + result + "\n",
      temperature=0.7,
      max_tokens=40,
      top_p=1,
      frequency_penalty=0.3,
      presence_penalty=0.3
    )
    st.session_state['native'] = response['choices'][0]['text']
    with native.expander("お手本", True):
         st.write(st.session_state['native'])
