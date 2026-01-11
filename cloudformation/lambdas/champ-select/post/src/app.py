import json
import os
import uuid
import boto3
import pymysql
from typing import Any, Dict
from datetime import datetime, timedelta

ddb_client = boto3.client("dynamodb")

SELECT_BANNEDCHAMP_SQL = """
    SELECT value FROM config WHERE name = "banned_champions"
"""


def create_connection() -> pymysql.Connection:
    return pymysql.connect(
        host=os.environ["DB_HOST"],
        port=int(os.environ["DB_PORT"]),
        user=os.environ["DB_USER"],
        password=os.environ["DB_PASSWORD"],
        database=os.environ["DB_NAME"],
        cursorclass=pymysql.cursors.DictCursor,
    )


def lambda_handler(event, context):

    lobby_guid = str(uuid.uuid4())

    lobby_id = f"LOBBY#{lobby_guid}"

    try:
        connection = create_connection()
        row = None
        with connection.cursor() as cursor:
            cursor.execute(SELECT_BANNEDCHAMP_SQL)
            row = cursor.fetchone()

        item = {
            "lobbyId": {"S": lobby_id},
            "redCaptain": {"S": ""},
            "blueCaptain": {"S": ""},
            "spectators": {"S": "[]"},
            "state": {"S": "Waiting"},
            "preBans": {"S": row["value"] if row else "[]"},
            "blueTeamBans": {"S": "[]"},
            "redTeamBans": {"S": "[]"},
            "redTeamChampions": {"S": "[]"},
            "blueTeamChampions": {"S": "[]"},
            "TTL": {"N": str(round((datetime.now() + timedelta(days=1)).timestamp()))},
        }

        put_item(table_name=os.environ["TABLE_NAME"], item=item)

        return response(200, {"lobbyId": lobby_guid})

    except Exception as e:
        print(f"Error creating lobby: {e}")
        return response(500, {"error": "Internal server error"})


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
