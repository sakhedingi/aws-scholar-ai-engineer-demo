import json
import numpy as np
from botocore.exceptions import ClientError
from .bedrock_runtime import get_bedrock_runtime

def embed_with_bedrock(model_id, input_text):
    bedrock_runtime = get_bedrock_runtime()
    try:
        body = json.dumps({"inputText": input_text})
        response = bedrock_runtime.invoke_model(
            modelId=model_id,
            body=body,
            contentType='application/json',
            accept='application/json'
        )
        response_body = json.loads(response['body'].read())
        return response_body.get('embedding', [])
    except ClientError as e:
        print(f"Error generating embedding: {e}")
        return []

def cosine_similarity(vec1, vec2):
    v1 = np.array(vec1)
    v2 = np.array(vec2)
    return np.dot(v1, v2) / (np.linalg.norm(v1) * np.linalg.norm(v2))