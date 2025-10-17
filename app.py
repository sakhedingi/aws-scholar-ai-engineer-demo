import streamlit as st
from bedrock_app.model_listing import list_bedrock_models
from bedrock_app.chat import chat_with_bedrock
from bedrock_app.semantic_search import build_vector_store_from_folder, semantic_search_local
from bedrock_app.rag import answer_with_context
import time
import random
import os

os.makedirs("./temp_docs", exist_ok=True)

def retry_bedrock_call(func, *args, retries=5, base_delay=1, max_delay=15):
    for attempt in range(1, retries + 1):
        try:
            return func(*args)
        except Exception as e:
            err = str(e)
            if "Throttling" in err or "Rate exceeded" in err:
                # Exponential backoff + jitter (recommended by AWS)
                sleep_time = min(base_delay * (2 ** (attempt - 1)), max_delay)
                sleep_time += random.uniform(0, 0.5)
                print(f"⏳ Throttled by Bedrock. Waiting {sleep_time:.2f}s (attempt {attempt}/{retries})...")
                time.sleep(sleep_time)
            else:
                print(f"Unexpected error: {e}")
                time.sleep(1)
    return "Bedrock API throttled. Please try again later."

st.set_page_config(page_title="Sakhe AI Assistant", layout="wide")

st.sidebar.title("🧠 Sakhe AI Assistant")
mode = st.sidebar.radio("Choose a mode", ["Chat", "Document Q&A (RAG)"])

chat_models, embedding_models = list_bedrock_models()
chat_model_names = [m['name'] for m in chat_models]
selected_chat_name = st.sidebar.selectbox("Select Chat Model", chat_model_names)
selected_chat_model = next(m for m in chat_models if m['name'] == selected_chat_name)

st.sidebar.markdown("### 🔧 Model Parameters")
temperature = st.sidebar.slider("Temperature", min_value=0.0, max_value=1.0, value=0.7, step=0.05)
top_p = st.sidebar.slider("Top-p (nucleus sampling)", min_value=0.0, max_value=1.0, value=0.9, step=0.05)

if mode == "Document Q&A (RAG)":
    embed_model = embedding_models[0]
    st.sidebar.markdown(f"**Embedding Model:** {embed_model['name']}")
    kb_folder = "./knowledge_base"
    st.sidebar.markdown(f"**Knowledge Base:** `{kb_folder}`")
    st.session_state.vector_store = build_vector_store_from_folder(kb_folder, embed_model['id'])

st.title("🤖 Sakhe AI Assistant")

# Initialize history if not present
if "mode_histories" not in st.session_state:
    st.session_state.mode_histories = {
        "Chat": [],
        "Document Q&A (RAG)": []
    }

if "last_greeted_mode" not in st.session_state:
    st.session_state.last_greeted_mode = None

# Mode-specific greeting logic
if "greeting_shown" not in st.session_state:
    st.session_state.greeting_shown = {"Chat": False, "Document Q&A (RAG)": False}

if not st.session_state.greeting_shown[mode]:
    greeting = (
        "👋 Hello! I'm ready to chat. How can I help you?"
        if mode == "Chat"
        else "📚 Ready to answer questions from your knowledge base. Ask me anything based on your documents!"
    )
    st.session_state.mode_histories[mode].append({"role": "assistant", "content": greeting})
    st.session_state.greeting_shown[mode] = True

# Create a placeholder container to suppress default rendering
chat_container = st.container()

# Capture user input
user_input = st.chat_input("Ask a question...")

if mode == "Chat":
    uploaded_file = st.sidebar.file_uploader("Upload a document for Q&A", type=["pdf", "txt", "docx"])
    if uploaded_file:
        # st.sidebar.success(f"Uploaded: {uploaded_file.name}")
        # Save uploaded file temporarily
        temp_path = f"./temp_docs/{uploaded_file.name}"
        with open(temp_path, "wb") as f:
            f.write(uploaded_file.getbuffer())
        # Build vector store from uploaded document
        embed_model = embedding_models[0]
        st.session_state.temp_vector_store = build_vector_store_from_folder("./temp_docs", embed_model['id'])

# Only generate response if there's new input
if user_input:
    current_history = st.session_state.mode_histories[mode]
    # Temporarily extend history for context
    temp_history = current_history + [{"role": "user", "content": user_input}]

    if mode == "Chat":
        if uploaded_file:

            results = semantic_search_local(user_input, embed_model['id'], st.session_state.temp_vector_store)
            if results:
                context = "\n\n".join([r[2] for r in results])
                response = retry_bedrock_call(answer_with_context, selected_chat_model['id'], user_input, context, temp_history)
                if response is None or response == "Bedrock API throttled. Please try again later.":
                    response = "I couldn't generate a response right now. Please try again shortly or rephrase your question."
            else:
                response = "No relevant documents found."
        else:
            response = retry_bedrock_call(chat_with_bedrock, selected_chat_model['id'], user_input, temp_history)
            time.sleep(1.5)
    else:
        results = semantic_search_local(user_input, embed_model['id'], st.session_state.vector_store)
        if results:
            context = "\n\n".join([r[2] for r in results])
            response = retry_bedrock_call(answer_with_context, selected_chat_model['id'], user_input, context, temp_history)
            if response is None or response == "Bedrock API throttled. Please try again later.":
                response = "I couldn't generate a response right now. Please try again shortly or rephrase your question."
        else:
            response = "No relevant documents found."

    # Append both messages to history
    current_history.append({"role": "user", "content": user_input})
    current_history.append({"role": "assistant", "content": response})

# Render full history
with chat_container:
    for msg in st.session_state.mode_histories[mode]:
        with st.chat_message(msg["role"]):
            st.markdown(msg["content"])