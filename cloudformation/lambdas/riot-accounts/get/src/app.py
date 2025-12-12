import pymysql
import os
import json

SELECT_ACCOUNTS_SQL = """
    SELECT
        acc.id,
        acc.account_name,
        acc.account_puuid,
        acc.player_id,
        acc.is_primary,
        p.name as player_name,
        (
            SELECT COUNT(*)
            FROM processed_match_data pmd
            WHERE pmd.account_puuid = acc.account_puuid
        ) as processed_matches
    FROM riot_accounts acc
    JOIN players p on p.id = acc.player_id
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
    conn = create_connection()

    with conn.cursor() as cur:
        cur.execute(SELECT_ACCOUNTS_SQL)
        rows = cur.fetchall()

        return {
            "statusCode": 200,
            "headers": {
                "Content-Type": "application/json",
                "Access-Control-Allow-Origin": "*",
            },
            "body": json.dumps({"items": rows, "count": len(rows)}),
        }
