import streamlit as st
import os
from dotenv import load_dotenv
from langchain_chroma import Chroma
from langchain_ollama import OllamaEmbeddings
from helpers.chain_handler import setup_chain, setup_agent
from langchain_core.messages import AIMessage, HumanMessage
from langchain_ollama import ChatOllama
from helpers.tools import tools


# Load environment variables
load_dotenv()

# ---- Streamlit UI ---- #
st.set_page_config(layout="wide")
st.title("📚 My Local Chatbot")

st.sidebar.header("Settings")
MODEL_PROVIDER = "ollama"  # Default model provider
MODEL = st.sidebar.selectbox("Choose Ollama Model", ["llama3.2","deepseek-r1:1.5b"], index=0)
MAX_HISTORY = st.sidebar.number_input("Max History", 1, 10, 2)
CONTEXT_SIZE = st.sidebar.number_input("Context Size", 1024, 16384, 8192, step=1024)
CHAIN_TYPE='stuff'  # Default chain type, can be extended later

# ---- Session State Setup ---- #
if "chat_history" not in st.session_state:
    st.session_state.chat_history = []

# ---- LangChain Components ---- #

embeddings = OllamaEmbeddings(
    model="mxbai-embed-large"
)

# Initialize Chroma vector store
vectorstore = Chroma(persist_directory="/Users/raksingh/personal/github/my-ollama-rag-app/db/chroma_db", embedding_function=embeddings)
retriever = vectorstore.as_retriever(search_type="similarity")
qa = setup_agent(MODEL_PROVIDER, MODEL)

# ---- Display Chat History ---- #
for message in st.session_state.chat_history:
    if isinstance(message, AIMessage):
        with st.chat_message("AI"):
            st.markdown(message.content)
    elif isinstance(message, HumanMessage):
        with st.chat_message("Human"):
            st.markdown(message.content)

# ---- Trim Chat Memory ---- #
def trim_memory():
    while len(st.session_state.chat_history) > MAX_HISTORY * 2:
        st.session_state.chat_history.pop(0)  # Remove oldest messages

# ---- Handle User Input ---- #
# conversation
            
if query := st.chat_input("Say something"):
    st.session_state.chat_history.append(HumanMessage(content=query))
    
    with st.chat_message("Human"):
        st.markdown(query)
        trim_memory()

    with st.chat_message("AI"):
        response_container = st.empty()
        # Retrieve relevant documents & run QA
        print(query)
        retrieved_docs = retriever.invoke(query)
        print(retrieved_docs)
        result = (
            "No relevant documents found." if not retrieved_docs
            else 
                # qa.invoke({"user_question": query}).get("result", "No response generated.")
                qa.invoke({"input": query, "history": st.session_state.chat_history, "context": retrieved_docs, "tools": tools, "intermediate_steps": []})
        )
        print(type(result))
        # st.markdown(full_response['answer'])
        # Display the full response
        response_container.markdown(result)
        # st.session_state.chat_history.append({"role": "AI", "content": full_response})
        st.session_state.chat_history.append(AIMessage(result))
        trim_memory()