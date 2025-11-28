import pymysql
import os
import json

SELECT_PLAYERS_SQL = """
    SELECT
        p.*,
        t.name AS team_name,
        t.logo_url as team_logo_url,
        t.banner_url as team_banner_url,
        t.tag as team_tag
    FROM players p
    JOIN teams t ON p.team_id = t.id
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
        cur.execute(SELECT_PLAYERS_SQL)
        rows = cur.fetchall()

        return {
            "statusCode": 200,
            "headers": {
                "Content-Type": "application/json",
                "Access-Control-Allow-Origin": "*",
            },
            "body": json.dumps({"items": rows, "count": len(rows)}),
        }
