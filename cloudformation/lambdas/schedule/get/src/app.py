import json
import os
import pymysql


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


GET_SCHEDULE_SQL = """
SELECT 
    tm.id       AS match_id,
    tm.winner_team_id,
    t1.id 		as team_1_id,
    t1.name     AS team_1_name,
    t1.logo_url AS team_1_logo,
    t1.tag      AS team_1_tag,
    t2.id 		AS team_2_id,
    t2.name     AS team_2_name,
    t2.logo_url AS team_2_logo,
    t2.tag      AS team_2_tag,
    tm.start_date
FROM tournament_matches tm
JOIN teams t1 ON tm.team_1_id = t1.id
JOIN teams t2 ON tm.team_2_id = t2.id
"""


def lambda_handler(event, context):
    method = event.get("httpMethod")
    if method != "GET":
        return response(405, {"message": "Method Not Allowed"})
    
    connection = None
    try:
        connection = create_connection()
        with connection.cursor() as cursor:
            cursor.execute(GET_SCHEDULE_SQL)
            row = cursor.fetchall()

        if not row:
            return response(
                404, {"message": "No schedule found please set up some matches first."}
            )

        return response(200, {"item": row})

    except Exception as e:
        return response(500, {"message": f"Internal server error: {str(e)}"})

    finally:
        if connection:
            connection.close()
