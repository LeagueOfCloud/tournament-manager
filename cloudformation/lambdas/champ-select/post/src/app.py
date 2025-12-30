import json
import os
import uuid
import boto3


ddb_client = boto3.client("dynamodb")

def lambda_handler(event, context):

    lobby_id = f"LOBBY#{str(uuid.uuid4())}"

    item = {
        "LobbyId": lobby_id,
        "Red_Captain": "",
        "Blue_Captain": "",
        "Spectators": [""]
    }

    put_item(
        table_name=os.environ["TABLE_NAME"],
        item=item
    )

    return response(200, {"lobbyId": lobby_id})
    
def put_item(table_name: str, item: Dict[str, Any]) -> None:

    ddb_client.put_item(
        TableName=table_name,
        Item=item
    )

def response(status_code, body):
    return {
        "statusCode": status_code,
        "headers": {
            "Content-Type": "application/json",
            "Access-Control-Allow-Origin": "*",
        },
        "body": json.dumps(body, default=str),
    }
