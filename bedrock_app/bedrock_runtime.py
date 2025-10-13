import boto3

def get_bedrock_runtime(region="us-west-2"):
    return boto3.client("bedrock-runtime", region_name=region)