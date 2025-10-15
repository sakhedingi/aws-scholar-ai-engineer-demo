import boto3

def get_bedrock_client(region="us-east-1"):
    return boto3.client("bedrock", region_name=region)