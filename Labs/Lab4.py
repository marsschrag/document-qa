import streamlit as st
from openai import OpenAI
import sys

__import__('pysqlite3')
sys.modules['sqlite3'] = sys.modules.pop('pysqlite3')

import chromadb
from pathlib import Path
from PyPDF2 import PdfReader



#create chromadb client
chroma_client = chromadb.PersistentClient(path='./ChromaDB_for_Lab')
collection = chroma_client.get_or_create_collection('Lab4Collection')

openAI_model = st.sidebar.selectbox("which model?", 
                    ("mini", "regular"))
if openAI_model == "mini":
    model_to_use = "gpt-5-nano"
else:
    model_to_use = "gpt-5-chat-latest"

#create openai client
if 'openai_client' not in st.session_state:
    api_key = st.secrets["OPENAI_API_KEY"]
    st.session_state.openai_client = OpenAI(api_key=api_key)

def add_to_collection(collection, text, file_name):
    #create embedding
    client = st.session_state.openai_client
    response = client.embeddings.create(
        input=text,
        model='text-embedding-3-small'
    )
    #get embedding
    embedding = response.data[0].embedding
    
    #add embedding and doc to chromadb
    collection.add(
        documents=[text],
        ids=file_name,
        embeddings=[embedding]
    )

def extract_text_from_pdf(pdf_path):
    try:
        reader = PdfReader(pdf_path)
        text = ""
        for page in reader.pages:
            text += page.extract_text()
        return text
    except Exception as e:
        st.error(f"Error reading {pdf_path}: {e}")
        return None


def load_pdfs_to_collection(folder_path, collection):
    folder = Path(folder_path)
    pdf_files = list(folder.glob("*.pdf"))
    
    if not pdf_files:
        st.warning(f"No PDF files found in {folder_path}")
        return False
    
    progress_bar = st.progress(0)
    status_text = st.empty()
    
    for idx, pdf_file in enumerate(pdf_files):
        status_text.text(f"Processing {pdf_file.name}...")
        
        # Extract text from PDF
        text = extract_text_from_pdf(pdf_file)
        
        if text:
            # Add to collection
            add_to_collection(collection, text, pdf_file.name)
            st.success(f"✓ Added {pdf_file.name}")
        
        # Update progress
        progress_bar.progress((idx + 1) / len(pdf_files))
    
    status_text.text("All PDFs processed!")
    return True
    
def create_vectordb():
    #create chromadb client
    chroma_client = chromadb.PersistentClient(path='./ChromaDB_for_Lab')
    collection = chroma_client.get_or_create_collection('Lab4Collection')
    
    #only load PDFs if collection is empty
    if collection.count() == 0:
        st.info("Loading PDFs into ChromaDB...")
        loaded = load_pdfs_to_collection('./Lab-04-Data/', collection)
        if loaded:
            st.success(f"Successfully loaded {collection.count()} documents into ChromaDB!")
    else:
        st.info(f"ChromaDB already contains {collection.count()} documents")
    
    return collection

def search_vectordb(collection, query, top_k=3):
    client = st.session_state.openai_client
    
    #create embedding for the query
    response = client.embeddings.create(
        input=query,
        model='text-embedding-3-small'
    )
    query_embedding = response.data[0].embedding
    
    #query chromadb
    results = collection.query(
        query_embeddings=[query_embedding],
        n_results=top_k
    )
    
    return results

if collection.count() == 0:
    loaded = load_pdfs_to_collection('./Lab-04-Data/', collection)

#title and description
st.title("Lab4: Chatbot Using RAG")


#for testing
topic = st.sidebar.text_input('Topic', placeholder='type your topic here')
if topic:
    client = st.session_state.openai_client
    response = client.embeddings.create(
        input=topic,
        model='text-embedding-3-small')
    query_embedding = response.data[0].embedding
    results = collection.query(
        query_embeddings=[query_embedding],
        n_results=3
    )
    st.subheader(f"results for {topic}")
    for i in range(len(results['documents'][0])):
        doc = results['documents'][0][1]
        doc_id = results['ids'][0][1]
        st.write(f"**{1+1}. {doc_id}")
else:
    st.info("enter a topic in the sidebar to search the collection.")
#end testing
    


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