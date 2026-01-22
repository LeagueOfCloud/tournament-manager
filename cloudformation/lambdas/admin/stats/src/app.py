import json
import os
import pymysql
import traceback


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


GET_STATS_SQL = """
SELECT
    (SELECT COUNT(*) FROM profiles) AS total_profiles,
    (SELECT COUNT(*) FROM players) AS total_players,
    (SELECT COUNT(*) FROM teams) AS total_teams,
    (SELECT COUNT(*) FROM riot_accounts) AS total_riot_accounts,
    (SELECT COUNT(*) FROM dreamdraft) AS dreamdraft_done,
    (SELECT COUNT(DISTINCT user_id) FROM pickems) AS pickems_done,
    (SELECT COUNT(*) FROM match_history) AS matches_processed,
    (SELECT COUNT(*) FROM processed_match_data) AS processed_match_data
"""


def lambda_handler(event, context):
    method = event.get("httpMethod")
    if method != "GET":
        return response(405, {"message": "Method Not Allowed"})

    connection = None
    try:
        connection = create_connection()
        with connection.cursor() as cursor:
            cursor.execute(GET_STATS_SQL)
            row = cursor.fetchone()

        if not row:
            return response(404, {"message": "No data could be fetched."})

        return response(200, row)

    except Exception as e:
        traceback.print_exc()
        return response(500, {"message": f"Internal server error: {str(e)}"})

    finally:
        if connection:
            connection.close()
