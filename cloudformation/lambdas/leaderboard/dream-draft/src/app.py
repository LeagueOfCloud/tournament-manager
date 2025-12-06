import json
import os
import pymysql

GET_LEADERBOARD_PICKEMS_SQL = """
SELECT
    name,
    discord_id,
    avatar_url
FROM profiles
ORDER BY dd_score DESC
"""


def response(status_code, body):
    return {
        "statusCode": status_code,
        "headers": {
            "Content-Type": "application/json",
            "Access-Control-Allow-Origin": "*",
        },
        "body": json.dumps(body),
    }


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
    try:
        connection = create_connection()

        with connection.cursor() as cur:
            cur.execute(GET_LEADERBOARD_PICKEMS_SQL)
            rows = cur.fetchall()

        return response(200, rows)

    except Exception as e:
        return response(500, {"message": f"{e}"})
