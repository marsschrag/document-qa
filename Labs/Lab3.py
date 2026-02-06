import streamlit as st
from openai import OpenAI

#title and description
st.title("Lab3 question answering chatbot")

openAI_model = st.sidebar.selectbox("which model?", 
                    ("mini", "regular"))
if openAI_model == "mini":
    model_to_use = "gpt-5-nano"
else:
    model_to_use = "gpt-5-chat-latest"

#create openai client
if 'client' not in st.session_state:
    api_key = st.secrets["OPENAI_API_KEY"]
    st.session_state.client = OpenAI(api_key=api_key)

if "messages" not in st.session_state:
    st.session_state["messages"] = [
        {
            "role": "system", 
            "content": "explain things in a way a 10-year-old would understand. after answering each question, ask 'do you want more info?' and if the user says yes, provide more information and ask again. if the user says no, ask 'how else can I help you?'"
        },
        {
            "role": "assistant", 
            "content": "How can I help you?"
        }
    ]

for msg in st.session_state.messages:
    chat_msg = st.chat_message(msg["role"])
    chat_msg.write(msg["content"])

if prompt := st.chat_input("what is up?"):
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    #last 2 user messages plus assistant's messages
    if len(st.session_state.messages) > 5:
        st.session_state.messages = [st.session_state.messages[0]] + st.session_state.messages[-4:]


    client = st.session_state.client
    stream = client.chat.completions.create(
        model=model_to_use,
        messages = st.session_state.messages,
        stream=True)
    with st.chat_message("assistant"):
        response = st.write_stream(stream)
    st.session_state.messages.append({"role": "assistant", "content": response})