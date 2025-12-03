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


GET_DREAMDRAFT_SQL = """
SELECT
    d.user_id,

    p1.id   AS selection_1_id,
    p1.name AS selection_1_name,
    p1.avatar_url AS selection_1_avatar_url,
    p1.cost AS selection_1_cost,
    t1.tag AS team_1_tag,

    p2.id   AS selection_2_id,
    p2.name AS selection_2_name,
    p2.avatar_url AS selection_2_avatar_url,
    p2.cost AS selection_2_cost,
    t2.tag AS team_2_tag,

    p3.id   AS selection_3_id,
    p3.name AS selection_3_name,
    p3.avatar_url AS selection_3_avatar_url,
    p3.cost AS selection_3_cost,
    t3.tag AS team_3_tag,

    p4.id   AS selection_4_id,
    p4.name AS selection_4_name,
    p4.avatar_url AS selection_4_avatar_url,
    p4.cost AS selection_4_cost,
    t4.tag AS team_4_tag,

    p5.id   AS selection_5_id,
    p5.name AS selection_5_name,
    p5.avatar_url AS selection_5_avatar_url,
    p5.cost AS selection_5_cost
    t5.tag AS team_5_tag

FROM dreamdraft d
JOIN players p1 ON d.selection_1 = p1.id
JOIN teams t1 ON p1.team_id = t1.id
JOIN players p2 ON d.selection_2 = p2.id
JOIN teams t2 ON p2.team_id = t2.id
JOIN players p3 ON d.selection_3 = p3.id
JOIN teams t3 ON p3.team_id = t3.id
JOIN players p4 ON d.selection_4 = p4.id
JOIN teams t4 ON p4.team_id = t4.id
JOIN players p5 ON d.selection_5 = p5.id
JOIN teams t5 ON p5.team_id = t5.id
WHERE d.user_id = %s
"""

# Optional: If you want to also return player names/costs, you can do a JOIN:
# SELECT d.user_id, d.selection_1, ..., p1.name AS selection_1_name, ...
# and so on. For now we just return IDs.


def lambda_handler(event, context):
    method = event.get("httpMethod")
    if method != "GET":
        return response(405, {"message": "Method Not Allowed"})

    path_params = event.get("pathParameters") or {}
    profile_id_raw = path_params.get("profile_id")
    if not profile_id_raw:
        return response(400, {"message": "Missing profile_id path parameter"})

    try:
        profile_id = int(profile_id_raw)
    except ValueError:
        return response(400, {"message": "profile_id must be an integer"})

    connection = None
    try:
        connection = create_connection()
        with connection.cursor() as cursor:
            cursor.execute(GET_DREAMDRAFT_SQL, (profile_id,))
            row = cursor.fetchone()

        if not row:
            return response(
                404, {"message": "DreamDraft selection not found for this profile"}
            )

        selection = [
            {
                "player_id": row[f"selection_{i}_id"],
                "name": row[f"selection_{i}_name"],
                "cost": row[f"selection_{i}_cost"],
                "tag": row[f"selection_{i}_tag"],
                "avatar_url": row[f"selection_{i}_avatar_url"],
            }
            for i in range(1, 6)  # 1 to 5
        ]

        return response(200, {"user_id": row["user_id"], "selection": selection})

    except Exception as e:
        return response(500, {"message": f"Internal server error: {str(e)}"})

    finally:
        if connection:
            connection.close()
