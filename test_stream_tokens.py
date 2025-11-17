"""
Detailed streaming test to verify token-by-token behavior
"""
import sys
from bedrock_app.chat import invoke_model_stream
from bedrock_app.model_listing import list_bedrock_models

def test_stream_tokens():
    """Test token-level streaming"""
    print("🧪 Testing token-level streaming with invoke_model_stream...\n")
    
    chat_models, _ = list_bedrock_models()
    if not chat_models:
        print("❌ No models available")
        return False
    
    chat_model_id = chat_models[0]['id']
    model_name = chat_models[0]['name']
    print(f"📦 Using model: {model_name}")
    print(f"🔧 Model ID: {chat_model_id}\n")
    
    # Test with a simple question
    question = "What is AI in one sentence?"
    
    if 'claude' in chat_model_id.lower():
        body_dict = {
            "anthropic_version": "bedrock-2023-05-31",
            "max_tokens": 200,
            "messages": [{"role": "user", "content": question}],
            "temperature": 0.7
        }
    elif 'titan' in chat_model_id.lower():
        body_dict = {
            "inputText": question,
            "textGenerationConfig": {
                "maxTokenCount": 200,
                "temperature": 0.7
            }
        }
    else:
        body_dict = {
            "prompt": question,
            "max_tokens": 200,
            "temperature": 0.7
        }
    
    print(f"❓ Question: {question}\n")
    print("📝 Streaming response:")
    print("-" * 60)
    
    try:
        chunk_count = 0
        full_response = ""
        
        for chunk in invoke_model_stream(chat_model_id, body_dict):
            full_response += chunk
            chunk_count += 1
            print(chunk, end="", flush=True)
        
        print("\n" + "-" * 60)
        print(f"\n✅ Streaming completed!")
        print(f"📊 Total chunks received: {chunk_count}")
        print(f"📝 Full response length: {len(full_response)} characters")
        print(f"📈 Avg chunk size: {len(full_response) / max(chunk_count, 1):.1f} chars/chunk")
        return True
        
    except Exception as e:
        print(f"\n❌ Streaming failed: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = test_stream_tokens()
    sys.exit(0 if success else 1)
