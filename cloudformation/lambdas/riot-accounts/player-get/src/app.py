import pymysql
import json
import os

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
    player_id = event.get("pathParameters", {}).get("player_id")

    if not player_id:
        return {
            "statusCode": 400,
            "headers": {
                "Content-Type": "application/json",
                "Access-Control-Allow-Origin": "*",
            },
            "body": json.dumps({"message": "Invalid player ID"}),
        }

    connection = None

    try:
        connection = create_connection()

        with connection.cursor() as cursor:
            cursor.execute(
                "SELECT (id, account_name, account_puuid, player_id, is_primary) FROM riot_accounts WHERE player_id = %s",
                (player_id)
            )

            accounts = cursor.fetchall()

        return {
            "statusCode": 200,
            "headers": {
                "Content-Type": "application/json",
                "Access-Control-Allow-Origin": "*",
            },
            "body": json.dumps(accounts),
        }

    except Exception as e:
        return {
            "statusCode": 400,
            "headers": {
                "Content-Type": "application/json",
                "Access-Control-Allow-Origin": "*",
            },
            "body": json.dumps({"message": f"{e}"}),
        }
