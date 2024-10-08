import streamlit as st
from llama_index.llms.openai import OpenAI
from llama_index.core import VectorStoreIndex, SimpleDirectoryReader, Settings
from qdrant_client import QdrantClient
import openai
from qdrant_client.http import models
# from llama_index import VectorStoreIndex, StorageContext 
from llama_index.vector_stores.qdrant import QdrantVectorStore
from llama_index.core import VectorStoreIndex, SimpleDirectoryReader
from llama_index.core import StorageContext
# from llama_index.vector_stores import QdrantVectorStore
from llama_index.embeddings.openai import OpenAIEmbedding
from streamlit_pdf_viewer import pdf_viewer
from download_pdfs import download_files_from_blob

st.set_page_config(page_title="Asistent proceduri interne", layout="wide", initial_sidebar_state="auto", menu_items=None)
OPENAI_API_KEY = st.secrets.OPENAI_API_KEY
openai.api_key = st.secrets.OPENAI_API_KEY
QDRANT_URL = st.secrets.QDRANT_URL
QDRANT_API_KEY = st.secrets.QDRANT_API_KEY
connection_string = st.secrets.AZURE_BLOB_STORAGE_CONNECTION_STRING

container_name = "pdfs"
local_download_path = "pdfs"


st.title("Asistent proceduri interne")

if "messages" not in st.session_state.keys():  # Initialize the chat messages history
    st.session_state.messages = [
        {
            "role": "assistant",
            "content": "Intreaba ceva despre procedurile interne ale companiei",
        }
    ]
    
@st.cache_resource(show_spinner=False)
def load_data():
    # reader = SimpleDirectoryReader(input_dir="./data", recursive=True)
    # docs = reader.load_data()
    Settings.llm = OpenAI(
        model="gpt-4o",
        temperature=0.1,
        system_prompt="""Esti un expert contabil angajat finaco si ai ca scop sa ajuti ceilalti angajati sa gaseasca informatii in procedurile interne ale companiei.""",
    )
    # index = VectorStoreIndex.from_documents(docs)

    qdrant_client = QdrantClient(
        url=QDRANT_URL, 
        api_key=QDRANT_API_KEY
    )

    collection_name = "finaco_proceduri_interne_text_only"

    vector_store = QdrantVectorStore(client=qdrant_client, collection_name=collection_name)

    embed_model = OpenAIEmbedding(api_key=OPENAI_API_KEY)

    index = VectorStoreIndex.from_vector_store(vector_store=vector_store, embed_model=embed_model)
    download_files_from_blob(connection_string, container_name, local_download_path)
    
    return index


index = load_data()

col1, col2 = st.columns(spec=[0.3,0.7],gap="medium")

with col1:
    if "chat_engine" not in st.session_state.keys():  # Initialize the chat engine
        llm = OpenAI(
            model="gpt-4o",
            temperature=0.1,
            system_prompt="""Esti un expert contabil angajat finaco si ai ca scop sa ajuti ceilalti angajati sa gaseasca informatii in procedurile interne ale companiei. RASPUNDE DOAR IN ROMANA""",
        )
        st.session_state.chat_engine = index.as_chat_engine(
           verbose=True
        )

    if prompt := st.chat_input(
        "Intreaba ceva despre procedurile interne ale companiei"
    ):  # Prompt for user input and save to chat history
        st.session_state.messages.append({"role": "user", "content": prompt})

    for message in st.session_state.messages:  # Write message history to UI
        with st.chat_message(message["role"]):
            st.write(message["content"])

    # If last message is not from assistant, generate a new response
    if st.session_state.messages[-1]["role"] != "assistant":
        with st.chat_message("assistant"):
            response = st.session_state.chat_engine.chat(prompt)
            source_nodes = response.source_nodes
            if len(source_nodes) == 0:
                st.write("Nu am gasit nicio informatie in procedurile interne ale companiei.")
            else:
                first_node = source_nodes[0]
                print(source_nodes)
                origin_filename = first_node.metadata["origin_filename"]
                st.session_state.last_origin_filename = origin_filename
            st.write(response.response)
            message = {"role": "assistant", "content": response.response}
            # Add response to message history
            st.session_state.messages.append(message)
        
with col2:
    
    if "last_origin_filename" not in st.session_state.keys():
        st.write("Aici va aparea documentul PDF cu procedurile interne ale companiei in functie de intrebarea ta.")
    else:
        src = f"./{local_download_path}/"+st.session_state.last_origin_filename.split(".")[0]+".pdf"
        pdf_viewer(src)
        
        