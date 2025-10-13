from bedrock_app.model_listing import list_bedrock_models
from bedrock_app.semantic_search import build_vector_store_from_folder, semantic_search_local
from bedrock_app.rag import answer_with_context
from bedrock_app.display_utils import display_models

def run_rag_ui():
    print("\n📚 DOCUMENT Q&A MODE SELECTED\n")
    chat_models, embedding_models = list_bedrock_models()
    display_models(chat_models, embedding_models)

    # Select chat model
    while True:
        try:
            selection = int(input(f"\nSelect a chat model (1-{len(chat_models)}): "))
            if 1 <= selection <= len(chat_models):
                chat_model = chat_models[selection - 1]
                break
        except ValueError:
            print("Invalid input. Try again.")

    # Select embedding model
    embed_model = embedding_models[0]
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
        answer = answer_with_context(chat_model['id'], query, context, message_history)

        print(f"\n🤖 Answer: {answer}\n")
