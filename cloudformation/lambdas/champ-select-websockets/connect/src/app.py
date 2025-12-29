import os
import boto3
from typing import Any, Dict

ddb_client = boto3.client("dynamodb")

def lambda_handler(event, context):
    try:
        connection_id = event["requestContext"]["connectionId"]

        item = {
            "connectionId": {"S": connection_id},
        }

        put_item(
            table_name=os.environ["TABLE_NAME"],
            item=item
        )

    except Exception as e:
        error_type = type(e).__name__ 
        error_message = str(e) 
        print(f"Error occurred: {error_type}: {error_message}") 
        return { "statusCode": 500, "body": f"{error_type}: {error_message}" }
    
    return {"statusCode": 200}


def put_item(table_name: str, item: Dict[str, Any]) -> None:
    ddb_client.put_item(
        TableName=table_name,
        Item=item
    )