import os
import json
import requests
import boto3
import pymysql
import traceback

TWITCH_STREAMS_URL = "https://api.twitch.tv/helix/streams"
GET_CHANNEL_NAME_SQL = 'SELECT value FROM config WHERE name = "twitch_channel"'

secrets_client = boto3.client("secretsmanager")


def get_access_token(secret_arn: str) -> str:
    response = secrets_client.get_secret_value(SecretId=secret_arn)
    secret_string = response["SecretString"]
    secret_data = json.loads(secret_string)
    return secret_data["access_token"]


def create_connection() -> pymysql.Connection:
    return pymysql.connect(
        host=os.environ["DB_HOST"],
        port=int(os.environ["DB_PORT"]),
        user=os.environ["DB_USER"],
        password=os.environ["DB_PASSWORD"],
        database=os.environ["DB_NAME"],
        cursorclass=pymysql.cursors.DictCursor,
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


def lambda_handler(event, context):
    client_id = os.environ.get("TWITCH_CLIENT_ID")
    secret_arn = os.environ.get("TWITCH_APP_SECRET_ARN")

    try:
        connection = create_connection()

        with connection.cursor() as cursor:
            cursor.execute(GET_CHANNEL_NAME_SQL)
            result = cursor.fetchone()

        if not result or not result["value"]:
            return response(400, "twitch_channel is not defined in the database")

        channel_login = result["value"]

        if not client_id or not secret_arn or not channel_login:
            return response(500, "Misconfiguration error")

        access_token = get_access_token(secret_arn)

        headers = {"Client-Id": client_id, "Authorization": f"Bearer {access_token}"}

        params = {"user_login": channel_login}

        res = requests.get(
            TWITCH_STREAMS_URL, headers=headers, params=params, timeout=10
        )
        res.raise_for_status()

        data = res.json().get("data", [])

        is_live = len(data) > 0

        return response(200, {"is_live": is_live})

    except:
        traceback.print_exc()

        return response(500, {"message": "There was an error fetching the status"})

    finally:
        if connection:
            connection.close()
