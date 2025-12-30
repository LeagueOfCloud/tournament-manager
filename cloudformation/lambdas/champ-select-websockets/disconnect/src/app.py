import json
import os
import boto3
from boto3.dynamodb.conditions import Attr
from typing import Any, Dict

ddb_client = boto3.client("dynamodb")


def lambda_handler(event: Dict[str, Any], context: Any) -> Dict[str, int]:
    try:
        connection_id = event["requestContext"]["connectionId"]
        
        lobby = get_lobby(
            os.environ["TABLE_NAME"],
            connection_id
        )

        if not lobby:
            return { "statusCode": 400, "body": "No Lobby found" }

        blue_captain = lobby.get("blueCaptain", {}).get("S")
        red_captain = lobby.get("redCaptain", {}).get("S")
        spectators = json.loads(lobby.get("spectators", {}).get("S", "[]"))

        if blue_captain == connection_id:
            lobby["blueCaptain"] = {"S":""}
        elif red_captain == connection_id:
            lobby["redCaptain"] = {"S": ""}
        else:
            spectators.remove(connection_id)
            lobby["spectators"] = {"S": json.dumps(spectators)}

        put_item(
            table_name=os.environ["TABLE_NAME"],
            item=lobby
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

def get_lobby(table_name: str, connection_id: str) -> Dict[str, Any]:
    response = ddb_client.scan(
        TableName=table_name,
        FilterExpression=(
            "contains(#spectators, :connection_id) "
            "OR #blueCaptain = :connection_id "
            "OR #redCaptain = :connection_id"
        ),
        ExpressionAttributeNames={
            "#spectators": "spectators",
            "#blueCaptain": "blueCaptain",
            "#redCaptain": "redCaptain"
        },
        ExpressionAttributeValues={
            ":connection_id": {"S": connection_id}
        }
    )

    items = response.get("Items", [])
    if items:
        return items[0]

    return {}