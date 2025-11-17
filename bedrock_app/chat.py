import json
from botocore.exceptions import ClientError
from .bedrock_runtime import get_bedrock_runtime

def invoke_model_stream(model_id, body_dict, content_type='application/json', character_stream=True):
    """
    Stream response tokens from Bedrock model.
    Yields text tokens one by one for real-time display.
    
    Args:
        model_id: Bedrock model ID
        body_dict: Request body as dictionary
        content_type: Content type (default: 'application/json')
        character_stream: If True, break larger chunks into character-level streams for smoother UI (default: True)
    
    Yields:
        Text tokens (chars or words) from the model response
    """
    bedrock_runtime = get_bedrock_runtime()
    body = json.dumps(body_dict) if isinstance(body_dict, dict) else body_dict
    
    try:
        response = bedrock_runtime.invoke_model_with_response_stream(
            modelId=model_id,
            body=body,
            contentType=content_type,
            accept='application/json'
        )
        
        # Parse streaming response based on model type
        if 'claude' in model_id.lower():
            # Claude uses event stream format
            for event in response['body']:
                if 'chunk' in event:
                    chunk_data = json.loads(event['chunk']['bytes'].decode('utf-8'))
                    if 'delta' in chunk_data and 'text' in chunk_data['delta']:
                        text = chunk_data['delta']['text']
                        if character_stream:
                            # Stream character by character for smoother UI
                            for char in text:
                                yield char
                        else:
                            yield text
        elif 'titan' in model_id.lower():
            # Titan streaming format
            for event in response['body']:
                if 'chunk' in event:
                    chunk_data = json.loads(event['chunk']['bytes'].decode('utf-8'))
                    if 'outputText' in chunk_data:
                        text = chunk_data['outputText']
                        if character_stream:
                            # Break into smaller chunks for responsive streaming
                            for i in range(0, len(text), 10):  # 10 chars at a time
                                yield text[i:i+10]
                        else:
                            yield text
        elif 'llama' in model_id.lower() or 'mistral' in model_id.lower():
            # Llama/Mistral streaming format
            for event in response['body']:
                if 'chunk' in event:
                    chunk_data = json.loads(event['chunk']['bytes'].decode('utf-8'))
                    if 'generation' in chunk_data:
                        text = chunk_data['generation']
                        if character_stream:
                            for i in range(0, len(text), 10):
                                yield text[i:i+10]
                        else:
                            yield text
                    elif 'outputs' in chunk_data and chunk_data['outputs']:
                        if 'text' in chunk_data['outputs'][0]:
                            text = chunk_data['outputs'][0]['text']
                            if character_stream:
                                for i in range(0, len(text), 10):
                                    yield text[i:i+10]
                            else:
                                yield text
    except Exception as e:
        print(f"Error streaming from model: {e}")
        yield f"Error: {str(e)}"

def chat_with_bedrock(model_id, user_message, message_history=None, temperature=0.7, top_p=0.9):
    bedrock_runtime = get_bedrock_runtime()
    try:
        if message_history is None:
            message_history = []

        if 'claude' in model_id.lower():
            if 'claude-3' in model_id.lower():
                temp_messages = message_history + [{"role": "user", "content": user_message}]
                body = json.dumps({
                    "anthropic_version": "bedrock-2023-05-31",
                    "max_tokens": 1000,
                    "messages": temp_messages,
                    "temperature": temperature,
                    "top_p": top_p
                })
            else:
                body = json.dumps({
                    "prompt": f"\n\nHuman: {user_message}\n\nAssistant:",
                    "max_tokens_to_sample": 1000,
                    "temperature": temperature,
                    "top_p": top_p
                })
        elif 'titan' in model_id.lower():
            body = json.dumps({
                "inputText": user_message,
                "textGenerationConfig": {
                    "maxTokenCount": 1000,
                    "temperature": temperature,
                    "top_p": top_p
                }
            })
        elif 'llama' in model_id.lower() or 'mistral' in model_id.lower():
            body = json.dumps({
                "prompt": f"<s>[INST] {user_message} [/INST]",
                "max_tokens": 1000,
                    "temperature": temperature,
                    "top_p": top_p
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


def chat_stream(model_id, user_message, message_history=None, temperature=0.7, top_p=0.9, character_stream=True):
    """
    Stream a conversational response from Bedrock token-by-token.
    Yields text pieces (chars or small chunks) for real-time UI updates.

    Args:
        model_id: Bedrock model id
        user_message: The user's message string
        message_history: Optional list of prior messages (role/content dicts)
        temperature: Sampling temperature
        top_p: Nucleus sampling parameter
        character_stream: If True, yield character-level pieces for smoother UI

    Yields:
        str tokens from the model streaming endpoint
    """
    try:
        if message_history is None:
            message_history = []

        # Build the body dict similar to chat_with_bedrock but for streaming
        if 'claude' in model_id.lower():
            if 'claude-3' in model_id.lower():
                temp_messages = message_history + [{"role": "user", "content": user_message}]
                body_dict = {
                    "anthropic_version": "bedrock-2023-05-31",
                    "max_tokens": 1000,
                    "messages": temp_messages,
                    "temperature": temperature,
                    "top_p": top_p
                }
            else:
                body_dict = {
                    "prompt": f"\n\nHuman: {user_message}\n\nAssistant:",
                    "max_tokens_to_sample": 1000,
                    "temperature": temperature,
                    "top_p": top_p
                }
        elif 'titan' in model_id.lower():
            body_dict = {
                "inputText": user_message,
                "textGenerationConfig": {
                    "maxTokenCount": 1000,
                    "temperature": temperature,
                    "top_p": top_p
                }
            }
        elif 'llama' in model_id.lower() or 'mistral' in model_id.lower():
            body_dict = {
                "prompt": f"<s>[INST] {user_message} [/INST]",
                "max_tokens": 1000,
                "temperature": temperature,
                "top_p": top_p
            }
        else:
            yield f"Model not supported: {model_id}"
            return

        # Delegate to the generic streaming helper
        for chunk in invoke_model_stream(model_id, body_dict, character_stream=character_stream):
            yield chunk

    except Exception as e:
        print(f"Error in chat_stream: {e}")
        yield f"Error: {str(e)}"