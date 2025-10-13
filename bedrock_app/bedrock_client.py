import boto3

def get_bedrock_client(region="us-west-2"):
    return boto3.client("bedrock", region_name=region)