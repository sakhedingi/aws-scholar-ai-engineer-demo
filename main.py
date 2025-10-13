import boto3
import json
import os
import numpy as np
from botocore.exceptions import ClientError
from pdfminer.high_level import extract_text as extract_pdf_text
from docx import Document


# Global vector store for semantic search
vector_store = []

# ─────────────────────────────────────────────────────────────
# MODEL LISTING
# ─────────────────────────────────────────────────────────────

def list_bedrock_models():
    """Lists available chat and embedding models in Amazon Bedrock"""
    bedrock = boto3.client('bedrock', region_name='us-west-2')
    try:
        response = bedrock.list_foundation_models()
        models = response.get('modelSummaries', [])

        print("\n" + "=" * 80)
        print("AVAILABLE MODELS IN AMAZON BEDROCK")
        print("=" * 80 + "\n")

        chat_models = []
        embedding_models = []

        excluded_models = ['anthropic.claude-sonnet-4', 'anthropic.claude-opus-4']

        for model in models:
            model_id = model.get('modelId', 'N/A')
            model_name = model.get('modelName', 'N/A')
            provider = model.get('providerName', 'N/A')
            inference_types = model.get('inferenceTypesSupported', [])

            if any(k in model_id.lower() for k in ['claude', 'llama', 'mistral', 'titan']):
                if any(excluded in model_id.lower() for excluded in excluded_models):
                    continue
                if 'ON_DEMAND' in inference_types or not inference_types:
                    chat_models.append({'id': model_id, 'name': model_name, 'provider': provider})

            if 'embed' in model_id.lower() and 'ON_DEMAND' in inference_types:
                embedding_models.append({'id': model_id, 'name': model_name, 'provider': provider})

        # Display chat models
        if chat_models:
            print("💬 CHAT MODELS AVAILABLE")
            for idx, model in enumerate(chat_models, 1):
                print(f"{idx}. {model['name']}\n   ID: {model['id']}\n   Provider: {model['provider']}\n")

        # Display embedding models
        if embedding_models:
            print("📌 EMBEDDING MODELS AVAILABLE")
            for idx, model in enumerate(embedding_models, 1):
                print(f"{idx}. {model['name']}\n   ID: {model['id']}\n   Provider: {model['provider']}\n")

        return chat_models, embedding_models

    except ClientError as e:
        print(f"Error listing models: {e}")
        return [], []

# ─────────────────────────────────────────────────────────────
# CHAT FUNCTION
# ─────────────────────────────────────────────────────────────

def chat_with_bedrock(model_id, user_message):
    bedrock_runtime = boto3.client('bedrock-runtime', region_name='us-west-2')
    try:
        if 'claude' in model_id.lower():
            if 'claude-3' in model_id.lower():
                body = json.dumps({
                    "anthropic_version": "bedrock-2023-05-31",
                    "max_tokens": 1000,
                    "messages": [{"role": "user", "content": user_message}]
                })
            else:
                body = json.dumps({
                    "prompt": f"\n\nHuman: {user_message}\n\nAssistant:",
                    "max_tokens_to_sample": 1000,
                    "temperature": 0.7,
                    "top_p": 0.9
                })
        elif 'titan' in model_id.lower():
            body = json.dumps({
                "inputText": user_message,
                "textGenerationConfig": {
                    "maxTokenCount": 1000,
                    "temperature": 0.7,
                    "topP": 0.9
                }
            })
        elif 'llama' in model_id.lower() or 'mistral' in model_id.lower():
            body = json.dumps({
                "prompt": f"<s>[INST] {user_message} [/INST]",
                "max_tokens": 1000,
                "temperature": 0.7,
                "top_p": 0.9
            })
        else:
            print(f"Model not supported in this demo: {model_id}")
            return None

        response = bedrock_runtime.invoke_model(
            modelId=model_id,
            body=body,
            contentType='application/json',
            accept='application/json'
        )

        response_body = json.loads(response['body'].read())

        if 'claude' in model_id.lower():
            if 'claude-3' in model_id.lower():
                return response_body['content'][0]['text']
            else:
                return response_body.get('completion', 'No response')
        elif 'titan' in model_id.lower():
            return response_body['results'][0]['outputText']
        elif 'llama' in model_id.lower() or 'mistral' in model_id.lower():
            return response_body.get('generation', response_body.get('outputs', [{}])[0].get('text', 'No response'))

        return str(response_body)

    except ClientError as e:
        print(f"Error invoking model: {e}")
        return None

# ─────────────────────────────────────────────────────────────
# EMBEDDING + SEARCH
# ─────────────────────────────────────────────────────────────

def embed_with_bedrock(model_id, input_text):
    bedrock_runtime = boto3.client('bedrock-runtime', region_name='us-west-2')
    try:
        body = json.dumps({"inputText": input_text})
        response = bedrock_runtime.invoke_model(
            modelId=model_id,
            body=body,
            contentType='application/json',
            accept='application/json'
        )
        response_body = json.loads(response['body'].read())
        return response_body.get('embedding', [])
    except ClientError as e:
        print(f"Error generating embedding: {e}")
        return []

def cosine_similarity(vec1, vec2):
    v1 = np.array(vec1)
    v2 = np.array(vec2)
    return np.dot(v1, v2) / (np.linalg.norm(v1) * np.linalg.norm(v2))

def load_documents_from_folder(folder_path):
    """Reads .txt, .pdf, and .docx files from a folder"""
    documents = []

    for filename in os.listdir(folder_path):
        full_path = os.path.join(folder_path, filename)

        if filename.endswith(".txt"):
            with open(full_path, "r", encoding="utf-8") as f:
                content = f.read()

        elif filename.endswith(".pdf"):
            try:
                content = extract_pdf_text(full_path)
            except Exception as e:
                print(f"❌ Failed to read PDF: {filename} — {e}")
                continue

        elif filename.endswith(".docx"):
            try:
                doc = Document(full_path)
                content = "\n".join([para.text for para in doc.paragraphs])
            except Exception as e:
                print(f"❌ Failed to read DOCX: {filename} — {e}")
                continue

        else:
            continue  # Skip unsupported formats

        documents.append({
            "filename": filename,
            "content": content
        })

    return documents

def build_vector_store_from_folder(folder_path, embed_model_id):
    docs = load_documents_from_folder(folder_path)
    store = []
    for doc in docs:
        embedding = embed_with_bedrock(embed_model_id, doc["content"])
        if embedding:
            store.append({
                "filename": doc["filename"],
                "content": doc["content"],
                "embedding": embedding
            })
            print(f"✅ Embedded: {doc['filename']}")
        else:
            print(f"❌ Failed to embed: {doc['filename']}")
    return store

def semantic_search_local(query_text, embed_model_id, store, top_k=3):
    query_embedding = embed_with_bedrock(embed_model_id, query_text)
    if not query_embedding:
        print("Failed to generate embedding for query.")
        return []
    scored = []
    for entry in store:
        score = cosine_similarity(query_embedding, entry["embedding"])
        scored.append((entry["filename"], score, entry["content"]))  # Full content
    scored.sort(key=lambda x: x[1], reverse=True)
    return scored[:top_k]

# ─────────────────────────────────────────────────────────────
# RAG
# ─────────────────────────────────────────────────────────────

def answer_with_context(model_id, user_question, retrieved_text):
    """Uses a chat model to answer a question using retrieved context"""
    bedrock_runtime = boto3.client('bedrock-runtime', region_name='us-west-2')

    if 'claude' in model_id.lower():
        if 'claude-3' in model_id.lower() or 'claude-3-5' in model_id.lower():
            body = json.dumps({
                "anthropic_version": "bedrock-2023-05-31",
                "max_tokens": 1000,
                "messages": [
                    {
                        "role": "user",
                        "content": f"Use the following context to answer the question.\n\nContext:\n{retrieved_text}\n\nQuestion:\n{user_question}"
                    }
                ]
            })
        else:
            # Legacy Claude v2 format
            prompt = f"""
    Human: Use the following context to answer the question.

    Context:
    {retrieved_text}

    Question:
    {user_question}

    Assistant:"""
            body = json.dumps({
                "prompt": prompt,
                "max_tokens_to_sample": 1000,
                "temperature": 0.7,
                "top_p": 0.9
            })

    elif 'titan' in model_id.lower():
        prompt = f"Context:\n{retrieved_text}\n\nQuestion: {user_question}"
        body = json.dumps({
            "inputText": prompt,
            "textGenerationConfig": {
                "maxTokenCount": 1000,
                "temperature": 0.7,
                "topP": 0.9
            }
        })

    elif 'llama' in model_id.lower() or 'mistral' in model_id.lower():
        prompt = f"<s>[INST] Use this context to answer: {user_question}\n\n{retrieved_text} [/INST]"
        body = json.dumps({
            "prompt": prompt,
            "max_tokens": 1000,
            "temperature": 0.7,
            "top_p": 0.9
        })

    else:
        print(f"Model not supported for context-based answering: {model_id}")
        return None

    try:
        response = bedrock_runtime.invoke_model(
            modelId=model_id,
            body=body,
            contentType='application/json',
            accept='application/json'
        )
        response_body = json.loads(response['body'].read())

        if 'claude' in model_id.lower():
                if 'claude-3' in model_id.lower() or 'claude-3-5' in model_id.lower():
                    return response_body['content'][0]['text']
                else:
                    return response_body.get('completion', 'No response')
        elif 'titan' in model_id.lower():
            return response_body['results'][0]['outputText']
        elif 'llama' in model_id.lower() or 'mistral' in model_id.lower():
            return response_body.get('generation', response_body.get('outputs', [{}])[0].get('text', 'No response'))

        return str(response_body)

    except ClientError as e:
        print(f"Error answering with context: {e}")
        return None

# ─────────────────────────────────────────────────────────────
# MAIN
# ─────────────────────────────────────────────────────────────

def main():
    print("\n🤖 AMAZON BEDROCK CONVERSATION + EMBEDDING DEMO 🤖\n")

    chat_models, embedding_models = list_bedrock_models()
    if not chat_models:
        print("No available chat models found.")
        return

    # Select chat model
    print("=" * 80)
    while True:
        try:
            selection = int(input(f"\nSelect a chat model (1-{len(chat_models)}): "))
            if 1 <= selection <= len(chat_models):
                selected_model = chat_models[selection - 1]
                break
            else:
                print(f"Please select a number between 1 and {len(chat_models)}")
        except ValueError:
            print("Please enter a valid number")

    print(f"\n✅ Selected chat model: {selected_model['name']}")
    print(f"   ID: {selected_model['id']}\n")

    # Chat loop
    print("=" * 80)
    print("CONVERSATION (type 'exit' or 'quit' to end)")
    print("=" * 80 + "\n")
    while True:
        user_input = input("You: ")
        if user_input.lower() in ['exit', 'quit']:
            break
        if not user_input.strip():
            continue
        print("\n🤖 Assistant: ", end="", flush=True)
        response = chat_with_bedrock(selected_model['id'], user_input)
        print(response if response else "Could not get a response.")
        print()

    # Knowledge base embedding + search
   
    kb_folder = "./knowledge_base"
    if embedding_models:
        embed_model = embedding_models[0]
        print(f"Selected model: {embed_model}")
        print(f"\n📚 Building knowledge base from: {kb_folder}")
        vector_store = build_vector_store_from_folder(kb_folder, embed_model['id'])

        # Step 6: Search the knowledge base
        while True:
            query = input("\n🔍 Enter a question to search your knowledge base (or 'done'): ").strip()
            if query.lower() == 'done':
                break
            results = semantic_search_local(query, embed_model['id'], vector_store)
            if not results:
                print("No relevant documents found.\n")
                continue

            # Combine top results into one context block
            context = "\n\n".join([r[2] for r in results])
            answer = answer_with_context(selected_model['id'], query, context)

            print("\n🤖 Answer:")
            print(answer if answer else "Could not generate an answer.\n")

if __name__ == "__main__":
    main()            