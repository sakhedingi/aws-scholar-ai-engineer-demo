from ui.chat_ui import run_chat_ui
from ui.rag_ui import run_rag_ui

def main():
    print("\n🤖 Welcome to Bedrock Assistant")
    print("Choose a mode:")
    print("1. Chat with a model")
    print("2. Document Q&A (RAG)")
    
    while True:
        choice = input("Enter 1 or 2: ").strip()
        if choice == "1":
            run_chat_ui()
            break
        elif choice == "2":
            run_rag_ui()
            break
        else:
            print("Invalid choice. Please enter 1 or 2.")

if __name__ == "__main__":
    main()