import json
from botocore.exceptions import ClientError
from .bedrock_runtime import get_bedrock_runtime
from .chat import invoke_model_stream

def answer_with_context(model_id, user_question, retrieved_text, message_history=None, temperature=0.7, top_p=0.9):
    """Uses a chat model to answer a question using retrieved context"""
    bedrock_runtime = get_bedrock_runtime()

    if message_history is None:
        message_history = []

    if 'claude' in model_id.lower():
        if 'claude-3' in model_id.lower() or 'claude-3-5' in model_id.lower():
            message_history.append({
                "role": "user",
                "content": f"Use the following context to answer the question.\n\nContext:\n{retrieved_text}\n\nQuestion:\n{user_question}"
            })
            body = json.dumps({
                "anthropic_version": "bedrock-2023-05-31",
                "max_tokens": 1000,
                "messages": message_history,
                "temperature": temperature,
                "top_p": top_p
            })
        else:
            # Legacy Claude v2 format (no history support)
            prompt = f"""Human: Use the following context to answer the question.

Context:
{retrieved_text}

Question:
{user_question}

Assistant:"""
            body = json.dumps({
                "prompt": prompt,
                "max_tokens_to_sample": 1000,
                "temperature": temperature,
                "top_p": top_p
            })

    # Titan, Llama, Mistral (no history support yet)
    elif 'titan' in model_id.lower() or 'llama' in model_id.lower() or 'mistral' in model_id.lower():
        prompt = f"Context:\n{retrieved_text}\n\nQuestion: {user_question}"
        body = json.dumps({
            "inputText": prompt,
            "textGenerationConfig": {
                "maxTokenCount": 1000,
                "temperature": temperature,
                "top_p": top_p
            }
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
                reply = response_body['content'][0]['text']
                message_history.append({"role": "assistant", "content": reply})
                return reply
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


def answer_with_context_stream(model_id, user_question, retrieved_text, message_history=None, temperature=0.7, top_p=0.9, character_stream=True):
    """Stream a response from Bedrock using the provided retrieved context.

    Yields small text chunks (chars or short chunks) suitable for real-time UI updates.
    """
    if message_history is None:
        message_history = []

    # Build body dict similar to answer_with_context but for streaming
    if 'claude' in model_id.lower():
        if 'claude-3' in model_id.lower() or 'claude-3-5' in model_id.lower():
            temp_messages = message_history + [{
                "role": "user",
                "content": f"Use the following context to answer the question.\n\nContext:\n{retrieved_text}\n\nQuestion:\n{user_question}"
            }]
            body_dict = {
                "anthropic_version": "bedrock-2023-05-31",
                "max_tokens": 1000,
                "messages": temp_messages,
                "temperature": temperature,
                "top_p": top_p
            }
        else:
            prompt = f"Human: Use the following context to answer the question.\n\nContext:\n{retrieved_text}\n\nQuestion:\n{user_question}\n\nAssistant:"
            body_dict = {
                "prompt": prompt,
                "max_tokens_to_sample": 1000,
                "temperature": temperature,
                "top_p": top_p
            }
    elif 'titan' in model_id.lower() or 'llama' in model_id.lower() or 'mistral' in model_id.lower():
        prompt = f"Context:\n{retrieved_text}\n\nQuestion: {user_question}"
        body_dict = {
            "inputText": prompt,
            "textGenerationConfig": {
                "maxTokenCount": 1000,
                "temperature": temperature,
                "top_p": top_p
            }
        }
    else:
        yield f"Model not supported for streaming: {model_id}"
        return

    try:
        for chunk in invoke_model_stream(model_id, body_dict, character_stream=character_stream):
            yield chunk
    except Exception as e:
        print(f"Error streaming answer_with_context: {e}")
        yield f"Error: {str(e)}"