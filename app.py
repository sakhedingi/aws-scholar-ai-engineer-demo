import streamlit as st
from bedrock_app.model_listing import list_bedrock_models
from bedrock_app.chat import chat_with_bedrock
from bedrock_app.semantic_search import build_vector_store_from_folder, semantic_search_local
from bedrock_app.rag import answer_with_context

st.set_page_config(page_title="Sakhe's AI Assistant", layout="wide")

st.sidebar.title("🧠 Sakhe's AI Assistant")
mode = st.sidebar.radio("Choose a mode", ["Chat", "Document Q&A (RAG)"])

chat_models, embedding_models = list_bedrock_models()
chat_model_names = [m['name'] for m in chat_models]
selected_chat_name = st.sidebar.selectbox("Select Chat Model", chat_model_names)
selected_chat_model = next(m for m in chat_models if m['name'] == selected_chat_name)

st.sidebar.markdown("### 🔧 Model Parameters")
temperature = st.sidebar.slider("Temperature", min_value=0.0, max_value=1.0, value=0.7, step=0.05)
top_p = st.sidebar.slider("Top-p (nucleus sampling)", min_value=0.0, max_value=1.0, value=0.9, step=0.05)

if "greeting_shown" not in st.session_state:
    st.session_state.greeting_shown = False

if mode == "Document Q&A (RAG)":
    embed_model = embedding_models[0]
    st.sidebar.markdown(f"**Embedding Model:** {embed_model['name']}")
    kb_folder = "./knowledge_base"
    st.sidebar.markdown(f"**Knowledge Base:** `{kb_folder}`")
    st.session_state.vector_store = build_vector_store_from_folder(kb_folder, embed_model['id'])

st.title("🤖 Sakhe's Assistant")

# Initialize history if not present
if "history" not in st.session_state:
    st.session_state.history = []

if mode == "Chat" and not st.session_state.greeting_shown:
    st.session_state.history.append({
    "role": "assistant",
    "content": "👋 Hello! I'm ready to chat. Ask me anything."
})
st.session_state.greeting_shown = True

# Create a placeholder container to suppress default rendering
chat_container = st.container()

# Capture user input
user_input = st.chat_input("Ask a question...")

# Only generate response if there's new input
if user_input:
    # Temporarily extend history for context
    temp_history = st.session_state.history + [{"role": "user", "content": user_input}]

    if mode == "Chat":
        response = chat_with_bedrock(selected_chat_model['id'], user_input, temp_history)
    else:
        results = semantic_search_local(user_input, embed_model['id'], st.session_state.vector_store)
        if results:
            context = "\n\n".join([r[2] for r in results])
            response = answer_with_context(selected_chat_model['id'], user_input, context, temp_history)
        else:
            response = "No relevant documents found."

    # Append both messages to history
    st.session_state.history.append({"role": "user", "content": user_input})
    st.session_state.history.append({"role": "assistant", "content": response})

# Render full history
with chat_container:
    for msg in st.session_state.history:
        with st.chat_message(msg["role"]):
            st.markdown(msg["content"])