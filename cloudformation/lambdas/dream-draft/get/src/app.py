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
        cursorclass=pymysql.cursors.DictCursor
    )

def response(status_code, body):
    return {
        "statusCode": status_code,
        "headers": {
            "Content-Type": "application/json",
            "Access-Control-Allow-Origin": "*"
        },
        "body": json.dumps(body)
    }

GET_DREAMDRAFT_SQL = """
SELECT
    d.user_id,

    p1.id   AS selection_1_id,
    p1.name AS selection_1_name,
    p1.cost AS selection_1_cost,

    p2.id   AS selection_2_id,
    p2.name AS selection_2_name,
    p2.cost AS selection_2_cost,

    p3.id   AS selection_3_id,
    p3.name AS selection_3_name,
    p3.cost AS selection_3_cost,

    p4.id   AS selection_4_id,
    p4.name AS selection_4_name,
    p4.cost AS selection_4_cost,

    p5.id   AS selection_5_id,
    p5.name AS selection_5_name,
    p5.cost AS selection_5_cost

FROM dreamdraft d
JOIN players p1 ON d.selection_1 = p1.id
JOIN players p2 ON d.selection_2 = p2.id
JOIN players p3 ON d.selection_3 = p3.id
JOIN players p4 ON d.selection_4 = p4.id
JOIN players p5 ON d.selection_5 = p5.id
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
            return response(404, {"message": "DreamDraft selection not found for this profile"})

        selection = [
            {
                "slot": 1,
                "player_id": row["selection_1_id"],
                "name": row["selection_1_name"],
                "cost": row["selection_1_cost"],
            },
            {
                "slot": 2,
                "player_id": row["selection_2_id"],
                "name": row["selection_2_name"],
                "cost": row["selection_2_cost"],
            },
            {
                "slot": 3,
                "player_id": row["selection_3_id"],
                "name": row["selection_3_name"],
                "cost": row["selection_3_cost"],
            },
            {
                "slot": 4,
                "player_id": row["selection_4_id"],
                "name": row["selection_4_name"],
                "cost": row["selection_4_cost"],
            },
            {
                "slot": 5,
                "player_id": row["selection_5_id"],
                "name": row["selection_5_name"],
                "cost": row["selection_5_cost"],
            },
        ]

        return response(200, {
            "user_id": row["user_id"],
            "selection": selection
        })

    except Exception as e:
        return response(500, {"message": f"Internal server error: {str(e)}"})

    finally:
        if connection:
            connection.close()