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

# =========================
# Auth helpers
# =========================

def get_token_from_event(event) -> str | None:
    headers = event.get("headers") or {}
    auth_header = headers.get("Authorization") or headers.get("authorization")
    if not auth_header:
        return None

    parts = auth_header.split()
    if len(parts) == 2 and parts[0].lower() == "bearer":
        return parts[1]
    # if you sometimes send raw token, just return auth_header
    return auth_header

def get_user_id_from_token(connection, token: str) -> int | None:
    sql = "SELECT id FROM profiles WHERE token = %s"
    with connection.cursor() as cursor:
        cursor.execute(sql, (token,))
        row = cursor.fetchone()
        if not row:
            return None
        return int(row["id"])

# =========================
# Validation helpers
# =========================

def validate_selection_payload(body_json: dict) -> tuple[bool, str | None, list[int] | None]:
    """
    Expecting body:
    {
      "selection_1": <int>,
      "selection_2": <int>,
      "selection_3": <int>,
      "selection_4": <int>,
      "selection_5": <int>
    }
    """
    required_fields = [f"selection_{i}" for i in range(1, 6)]
    try:
        selections = [int(body_json.get(f)) for f in required_fields]
    except (TypeError, ValueError):
        return False, "Selections must be integers", None

    if any(s is None for s in selections):
        return False, "Missing one or more selection fields", None

    if len(set(selections)) != len(selections):
        return False, "Selections must all be different players", None

    return True, None, selections

def validate_budget(connection, selections: list[int]) -> tuple[bool, str | None]:
    """
    Check that:
      1) All players exist
      2) Sum of their costs <= DREAMDRAFT_MAX_BUDGET
    """
    max_budget_sql = f'SELECT value FROM config WHERE name = "dd_max_budget"'

    placeholders = ", ".join(["%s"] * len(selections))
    players_sql = f"SELECT id, cost FROM players WHERE id IN ({placeholders})"

    with connection.cursor() as cursor:
        cursor.execute(max_budget_sql)
        row = cursor.fetchone()
        max_budget = int(row["value"])

        cursor.execute(players_sql, selections)
        rows = cursor.fetchall()

    if len(rows) != len(selections):
        return False, "One or more selected players do not exist"

    total_cost = sum(int(r["cost"]) for r in rows)

    if total_cost > max_budget:
        return False, f"Total cost {total_cost} exceeds budget {max_budget}"

    return True, None

# =========================
# Main handler
# =========================

UPSERT_DREAMDRAFT_SQL = """
INSERT INTO dreamdraft (user_id, selection_1, selection_2, selection_3, selection_4, selection_5)
VALUES (%s, %s, %s, %s, %s, %s)
ON DUPLICATE KEY UPDATE
    selection_1 = VALUES(selection_1),
    selection_2 = VALUES(selection_2),
    selection_3 = VALUES(selection_3),
    selection_4 = VALUES(selection_4),
    selection_5 = VALUES(selection_5);
"""

def lambda_handler(event, context):
    # Only allow PUT (or POST mapped as PUT)
    #method = event.get("httpMethod")
    #if method not in ("PUT", "POST"):
    #    return response(405, {"message": "Method Not Allowed"})

    # Parse token
    token = get_token_from_event(event)
    if not token:
        return response(401, {"message": "Missing or invalid Authorization header"})

    try:
        body_json = json.loads(event.get("body") or "{}")
    except json.JSONDecodeError:
        return response(400, {"message": "Invalid JSON body"})

    ok, err, selections = validate_selection_payload(body_json)
    if not ok:
        return response(400, {"message": err})

    connection = None
    try:
        connection = create_connection()

        user_id = get_user_id_from_token(connection, token)
        if not user_id:
            return response(401, {"message": "Invalid token or user not found"})

        ok, err = validate_budget(connection, selections)
        if not ok:
            return response(400, {"message": err})

        with connection.cursor() as cursor:
            cursor.execute(
                UPSERT_DREAMDRAFT_SQL,
                (user_id, *selections)
            )
            connection.commit()

        return response(200, {
            "message": "DreamDraft selection saved successfully",
            "user_id": user_id,
            "selection": {
                "selection_1": selections[0],
                "selection_2": selections[1],
                "selection_3": selections[2],
                "selection_4": selections[3],
                "selection_5": selections[4],
            }
        })

    except Exception as e:
        # Log `e` with CloudWatch in real code
        return response(500, {"message": f"Internal server error: {str(e)}"})

    finally:
        if connection:
            connection.close()