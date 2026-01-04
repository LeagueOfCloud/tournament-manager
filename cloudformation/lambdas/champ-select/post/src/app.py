import json
import os
import uuid
import boto3
from typing import Any, Dict
from datetime import datetime, timedelta


ddb_client = boto3.client("dynamodb")


def lambda_handler(event, context):

    lobby_guid = str(uuid.uuid4())

    lobby_id = f"LOBBY#{lobby_guid}"

    item = {
        "lobbyId": {"S": lobby_id},
        "redCaptain": {"S": ""},
        "blueCaptain": {"S": ""},
        "spectators": {"S": "[]"},
        "state": {"S": "WAITING"},
        "bans": {"S": "[]"},
        "redTeamChampions": {"S": "[]"},
        "blueTeamChampions": {"S": "[]"},
        "TTL": {"N": str(round((datetime.now() + timedelta(days=1)).timestamp()))},
    }

    put_item(table_name=os.environ["TABLE_NAME"], item=item)

    return response(200, {"lobbyId": lobby_guid})


def put_item(table_name: str, item: Dict[str, Any]) -> None:

    ddb_client.put_item(TableName=table_name, Item=item)


def response(status_code, body):
    return {
        "statusCode": status_code,
        "headers": {
            "Content-Type": "application/json",
            "Access-Control-Allow-Origin": "*",
        },
        "body": json.dumps(body, default=str),
    }
