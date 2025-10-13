from botocore.exceptions import ClientError
from .bedrock_client import get_bedrock_client

EXCLUDED_MODELS = ['anthropic.claude-sonnet-4', 'anthropic.claude-opus-4']

def list_bedrock_models():
    """Lists available chat and embedding models in Amazon Bedrock"""
    bedrock = get_bedrock_client()
    try:
        response = bedrock.list_foundation_models()
        models = response.get('modelSummaries', [])

        chat_models = []
        embedding_models = []

        for model in models:
            model_id = model.get('modelId', 'N/A')
            model_name = model.get('modelName', 'N/A')
            provider = model.get('providerName', 'N/A')
            inference_types = model.get('inferenceTypesSupported', [])

            if any(k in model_id.lower() for k in ['claude', 'llama', 'mistral', 'titan']):
                if any(excluded in model_id.lower() for excluded in EXCLUDED_MODELS):
                    continue
                if 'ON_DEMAND' in inference_types or not inference_types:
                    chat_models.append({'id': model_id, 'name': model_name, 'provider': provider})

            if 'embed' in model_id.lower() and 'ON_DEMAND' in inference_types:
                embedding_models.append({'id': model_id, 'name': model_name, 'provider': provider})

        return chat_models, embedding_models

    except ClientError as e:
        print(f"Error listing models: {e}")
        return [], []