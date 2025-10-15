import json
from botocore.exceptions import ClientError
from .bedrock_runtime import get_bedrock_runtime

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