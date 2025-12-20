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
    (
        SELECT JSON_ARRAYAGG(
            JSON_OBJECT(
                'name', p.name,
                'avatar_url', p.avatar_url,
                'team_role', p.team_role
            )
        )
        FROM players p
        WHERE p.team_id = t1.id
    ) AS team_1_players,
    t2.name AS team_2_name,
    t2.logo_url AS team_2_logo,
    t2.tag AS team_2_tag,
    (
        SELECT JSON_ARRAYAGG(
            JSON_OBJECT(
                'name', p.name,
                'avatar_url', p.avatar_url,
                'team_role', p.team_role
            )
        )
        FROM players p
        WHERE p.team_id = t2.id
    ) AS team_2_players
FROM tournament_matches tm
JOIN teams t1 ON tm.team_1_id = t1.id
JOIN teams t2 ON tm.team_2_id = t2.id
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

        row["start_date"] = str(row["start_date"])

        if row.get("team_1_players"):
            row["team_1_players"] = json.loads(row["team_1_players"])
        if row.get("team_2_players"):
            row["team_2_players"] = json.loads(row["team_2_players"])

        return response(200, {"item": row})

    except Exception as e:
        return response(500, {"message": f"Internal server error: {str(e)}"})

    finally:
        if connection:
            connection.close()
