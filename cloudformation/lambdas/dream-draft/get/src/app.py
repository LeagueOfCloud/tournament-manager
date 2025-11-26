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
    d.selection_1,
    d.selection_2,
    d.selection_3,
    d.selection_4,
    d.selection_5
FROM dreamdraft d
WHERE d.user_id = %s
"""

# Optional: If you want to also return player names/costs, you can do a JOIN:
# SELECT d.user_id, d.selection_1, ..., p1.name AS selection_1_name, ...
# and so on. For now we just return IDs.

def lambda_handler(event, context):
    #method = event.get("httpMethod")
    #if method != "GET":
    #    return response(405, {"message": "Method Not Allowed"})

    profile_id_raw = event["pathParameters"]["id"]
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

        return response(200, {
            "user_id": row["user_id"],
            "selection": {
                "selection_1": row["selection_1"],
                "selection_2": row["selection_2"],
                "selection_3": row["selection_3"],
                "selection_4": row["selection_4"],
                "selection_5": row["selection_5"],
            }
        })

    except Exception as e:
        return response(500, {"message": f"Internal server error: {str(e)}"})

    finally:
        if connection:
            connection.close()