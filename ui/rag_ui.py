from bedrock_app.model_listing import list_bedrock_models
from bedrock_app.semantic_search import build_vector_store_from_folder, semantic_search_local
from bedrock_app.rag import answer_with_context
from bedrock_app.display_utils import display_chat_models, display_embed_models
import time

def retry_bedrock_call(func, *args, retries=3, delay=1):
    for attempt in range(retries):
        try:
            return func(*args)
        except Exception as e:
            print(f"Retry {attempt + 1}/{retries} after error: {e}")
            time.sleep(delay * (2 ** attempt))
    return "⚠️ Bedrock API throttled. Please try again later."

def run_rag_ui():
    print("\n📚 DOCUMENT Q&A MODE SELECTED\n")
    chat_models, embedding_models = list_bedrock_models()
    display_chat_models(chat_models)

    # Select chat model
    while True:
        try:
            selection = int(input(f"\nSelect a chat model (1-{len(chat_models)}): "))
            if 1 <= selection <= len(chat_models):
                chat_model = chat_models[selection - 1]
                break
        except ValueError:
            print("Invalid input. Try again.")

    display_embed_models(embedding_models)
    # Select embedding model
    while True:
        try:
            selection = int(input(f"\nSelect an embedding model (1-{len(embedding_models)}): "))
            if 1 <= selection <= len(embedding_models):
                embed_model = embedding_models[selection - 1]
                break
        except ValueError:
            print("Invalid input. Try again.")
    print(f"\n📌 Using embedding model: {embed_model['name']} ({embed_model['id']})")

    kb_folder = "./knowledge_base"
    print(f"\n📂 Loading documents from: {kb_folder}")
    vector_store = build_vector_store_from_folder(kb_folder, embed_model['id'])

    message_history = []

    while True:
        query = input("\n🔍 Ask a question (or type 'done'): ").strip()
        if query.lower() == 'done':
            break

        results = semantic_search_local(query, embed_model['id'], vector_store)
        
        if not results:
            print("No relevant documents found.\n")
            continue

        context = "\n\n".join([r[2] for r in results])

        answer = retry_bedrock_call(answer_with_context, chat_model['id'], query, context, message_history)

        if answer is None:
            answer = "⚠️ I couldn't generate a response. Please try again or rephrase your question."

        print(f"\n🤖 Answer: {answer}\n")
