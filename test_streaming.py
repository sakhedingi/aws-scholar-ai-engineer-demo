"""
Quick test script to verify streaming functionality
"""
import sys
from bedrock_app.optimized_rag import OptimizedRAG
from bedrock_app.model_listing import list_bedrock_models

def test_streaming():
    """Test streaming response generation"""
    print("🧪 Testing streaming functionality...\n")
    
    # Get models
    chat_models, embedding_models = list_bedrock_models()
    
    if not chat_models or not embedding_models:
        print("❌ No models available")
        return False
    
    chat_model_id = chat_models[0]['id']
    embed_model_id = embedding_models[0]['id']
    
    print(f"📦 Using chat model: {chat_models[0]['name']}")
    print(f"📦 Using embedding model: {embedding_models[0]['name']}\n")
    
    # Initialize RAG
    rag = OptimizedRAG()
    try:
        rag.initialize_knowledge_base("./knowledge_base", embed_model_id)
    except Exception as e:
        print(f"⚠️  KB initialization failed: {e}")
    
    # Test streaming
    print("🚀 Starting streaming response test...\n")
    print("Response tokens (streaming):")
    print("-" * 50)
    
    try:
        token_count = 0
        full_response = ""
        
        for token, stats in rag.answer_with_optimization_stream(
            model_id=chat_model_id,
            user_question="What is retrieval-augmented generation?",
            embed_model_id=embed_model_id,
            use_cache=False,  # Disable cache for clean test
            store_memory=False,  # Disable memory for clean test
            retrieve_past_contexts=False
        ):
            full_response += token
            token_count += 1
            print(token, end="", flush=True)
            
            # Show stats every 50 tokens
            if token_count % 50 == 0:
                print(f" [{token_count} tokens]", flush=True)
        
        print("\n" + "-" * 50)
        print(f"\n✅ Streaming test completed!")
        print(f"📊 Total tokens: {token_count}")
        print(f"📝 Response length: {len(full_response)} characters")
        return True
        
    except Exception as e:
        print(f"\n❌ Streaming test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = test_streaming()
    sys.exit(0 if success else 1)
