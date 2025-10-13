def display_models(chat_models, embedding_models):
    print("\n" + "=" * 80)
    print("AVAILABLE MODELS IN AMAZON BEDROCK")
    print("=" * 80 + "\n")

    if chat_models:
        print("💬 CHAT MODELS AVAILABLE")
        for idx, model in enumerate(chat_models, 1):
            print(f"{idx}. {model['name']}\n   ID: {model['id']}\n   Provider: {model['provider']}\n")

    # if embedding_models:
    #     print("📌 EMBEDDING MODELS AVAILABLE")
    #     for idx, model in enumerate(embedding_models, 1):
    #         print(f"{idx}. {model['name']}\n   ID: {model['id']}\n   Provider: {model['provider']}\n")