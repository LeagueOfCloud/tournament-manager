import pymysql
import json
import os
import traceback
from datetime import datetime

SELECT_MATCHES_SQL = """
SELECT
    m.*,
    t1.name as team_1_name,
    t2.name as team_2_name,
    t3.name as winner_team_name
FROM tournament_matches m
JOIN teams t1 ON t1.id = m.team_1_id
JOIN teams t2 ON t2.id = m.team_2_id
LEFT JOIN teams t3 ON t3.id = m.winner_team_id
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


def response(status_code, body):
    return {
        "statusCode": status_code,
        "headers": {
            "Content-Type": "application/json",
            "Access-Control-Allow-Origin": "*",
        },
        "body": json.dumps(body),
    }


def format_date(dt: datetime):
    return int(dt.timestamp() * 1000)


def lambda_handler(event, context):
    try:
        connection = create_connection()

        with connection.cursor() as cur:
            cur.execute(SELECT_MATCHES_SQL)
            rows = cur.fetchall()

        formatted_rows = [
            {
                **row,
                "start_date": format_date(row["start_date"]),
                "end_date": format_date(row["end_date"]) if row["end_date"] else None,
            }
            for row in rows
        ]

        return response(200, {"items": formatted_rows, "total": len(formatted_rows)})
    except Exception as e:
        traceback.print_exc()
        return response(500, {"error": f"{e}"})
