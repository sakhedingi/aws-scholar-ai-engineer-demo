from bedrock_app.optimized_rag import OptimizedRAG

def main():
    rag = OptimizedRAG()
    embed_model_id = None
    # try to pick an embedding model id from model_listing if available
    try:
        from bedrock_app.model_listing import list_bedrock_models
        chat_models, embedding_models = list_bedrock_models()
        if embedding_models:
            embed_model_id = embedding_models[0]['id']
    except Exception:
        pass

    if not embed_model_id:
        embed_model_id = 'amazon.titan-embed-text-v1'

    print('Initializing knowledge base (may use cache)...')
    rag.initialize_knowledge_base('./knowledge_base', embed_model_id)

    question = 'What is retrieval-augmented generation (RAG)?'
    print(f"\nQuery: {question}\n")

    # pick a chat model if available
    chat_model_id = 'anthropic.claude-3-5-sonnet-20241022'
    try:
        from bedrock_app.model_listing import list_bedrock_models
        chat_models, _ = list_bedrock_models()
        if chat_models:
            chat_model_id = chat_models[0]['id']
    except Exception:
        pass

    result = rag.answer_with_optimization(
        model_id=chat_model_id,
        user_question=question,
        embed_model_id=embed_model_id,
        message_history=[],
        temperature=0.2,
        top_p=0.9,
        use_cache=True,
        store_memory=True,
        retrieve_past_contexts=True
    )

    print('\n--- RESPONSE ---')
    print(result.get('response'))
    print('\n--- STATS ---')
    print(result.get('stats'))

if __name__ == '__main__':
    main()
