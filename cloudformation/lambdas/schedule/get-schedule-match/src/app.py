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
        "body": json.dumps(body),
    }


GET_SCHEDULE_SQL = """
SELECT 
    tm.id AS match_id,
    tm.start_date,
    t1.name AS team_1_name,
    t1.logo_url AS team_1_logo,
    t1.tag AS team_1_tag,
    JSON_ARRAYAGG(JSON_OBJECT(
        'name', p1.name,
        'avatar_url', p1.avatar_url,
        'team_role', p1.team_role
    )) AS team_1_players,
    t2.name AS team_2_name,
    t2.logo_url AS team_2_logo,
    t2.tag AS team_2_tag,
    JSON_ARRAYAGG(JSON_OBJECT(
        'name', p2.name,
        'avatar_url', p2.avatar_url,
        'team_role', p2.team_role
    )) AS team_2_players
FROM tournament_matches tm
JOIN teams t1 ON tm.team_1_id = t1.id
JOIN teams t2 ON tm.team_2_id = t2.id
LEFT JOIN players p1 ON p1.team_id = t1.id
LEFT JOIN players p2 ON p2.team_id = t2.id
WHERE tm.id = %s
"""


def lambda_handler(event, context):
    method = event.get("httpMethod")
    if method != "GET":
        return response(405, {"message": "Method Not Allowed"})
    
    path_params = event.get("pathParameters") or {}
    match_id_raw = path_params.get("match_id")
    if not match_id_raw:
        return response(400, {"message": "Missing match_id path parameter"})

    try:
        match_id = int(match_id_raw)
    except ValueError:
        return response(400, {"message": "match_id must be an integer"})
    
    connection = None
    try:
        connection = create_connection()
        with connection.cursor() as cursor:
            cursor.execute(GET_SCHEDULE_SQL, match_id)
            row = cursor.fetchone()

        if not row:
            return response(
                404, {"message": "No match found with the provided match id"}
            )

        return response(200, {"schedule": row})

    except Exception as e:
        return response(500, {"message": f"Internal server error: {str(e)}"})

    finally:
        if connection:
            connection.close()
