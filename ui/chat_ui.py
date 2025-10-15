from bedrock_app.model_listing import list_bedrock_models
from bedrock_app.chat import chat_with_bedrock
from bedrock_app.display_utils import display_chat_models

def run_chat_ui():
    print("\n💬 CHAT MODE SELECTED\n")
    chat_models, _ = list_bedrock_models()
    display_chat_models(chat_models, [])

    while True:
        try:
            selection = int(input(f"\nSelect a chat model (1-{len(chat_models)}): "))
            if 1 <= selection <= len(chat_models):
                model = chat_models[selection - 1]
                break
        except ValueError:
            print("Invalid input. Try again.")

    print(f"\n✅ Using model: {model['name']} ({model['id']})")
    print("Type 'exit' to quit.\n")

    message_history = []

    while True:
        user_input = input("You: ").strip()
        if user_input.lower() in ['exit', 'quit']:
            break
        message_history.append({"role": "user", "content": user_input})
        response = chat_with_bedrock(model['id'], user_input, message_history)
        if response:
            message_history.append({"role": "assistant", "content": response})
        print(f"\n🤖 Assistant: {response}\n")
