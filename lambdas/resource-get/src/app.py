import json
import os
import re
import pymysql

# ---------- DB connection ----------
def create_connection() -> pymysql.Connection:
    return pymysql.connect(
        host=os.environ["DB_HOST"],
        port=int(os.environ["DB_PORT"]),
        user=os.environ["DB_USER"],
        password=os.environ["DB_PASSWORD"],
        database=os.environ["DB_NAME"],
        cursorclass=pymysql.cursors.DictCursor
    )

def _response(status: int, body) -> dict:
    return {
        "statusCode": status,
        "headers": {
            "Content-Type": "application/json",
            "Access-Control-Allow-Origin": "*"
        },
        "body": json.dumps(body, default=str)
    }

# ---------- Route config (resource -> table/columns/pk) ----------
# Only allow explicit resources for safety
ROUTES = {
    "players": {
        "table": "players",
        "columns": "id, name, avatar_url, discord_id, team_id, team_role",
        "pk": "id",
        "pk_is_int": True,
    },
    "teams": {
        "table": "teams",
        "columns": "id, team_name, created_at",
        "pk": "id",
        "pk_is_int": True,
    },
    "riot-accounts": {
        "table": "riot_accounts",
        # Avoid exposing PUUID publicly unless you must
        "columns": "id, account_name, player_id, is_primary",
        "pk": "id",
        "pk_is_int": True,
    },
    "profiles": {
        "table": "profiles",
        "columns": "id, player_id, bio, created_at",
        "pk": "id",
        "pk_is_int": True,
    },
}

# ---------- Helpers ----------
def _safe_int(value, *, allow_none=False):
    if value is None:
        return None if allow_none else 0
    try:
        return int(value)
    except Exception:
        return None if allow_none else 0

def _extract_path(event) -> str:
    """
    Return the raw path as seen by API Gateway.
    Supports REST and HTTP API v2.
    """
    # REST API
    if "path" in event and isinstance(event["path"], str):
        return event["path"]
    # HTTP API v2
    rc = event.get("requestContext") or {}
    http = rc.get("http") or {}
    if "path" in http:
        return http["path"]
    if "rawPath" in event:
        return event["rawPath"]
    # Fallback
    return "/"

def _split_path_segments(path: str):
    # "/teams/5" -> ["teams","5"]
    return [seg for seg in (path or "").split("/") if seg]

def _resolve_route_and_id(event):
    """
    Determine resource key (e.g., 'teams') and id (if present).
    Priority:
      1) Use event.pathParameters.id if present (API Gateway mapping)
      2) Parse from path segments: /{resource}/{id}?
    """
    path_params = event.get("pathParameters") or {}
    id_from_params = path_params.get("id")

    path = _extract_path(event)
    segs = _split_path_segments(path)

    resource = segs[0] if segs else None

    # Allow both styles: /resource and /resource/{id}
    id_from_path = segs[1] if len(segs) > 1 else None

    record_id = id_from_params if id_from_params is not None else id_from_path
    return resource, record_id

# ---------- Main handler ----------
def lambda_handler(event, context):
    request_id = getattr(context, "aws_request_id", "no-request-id")

    try:
        resource, record_id = _resolve_route_and_id(event)
        qparams = event.get("queryStringParameters") or {}

        print(f"{request_id} Incoming path: { _extract_path(event) } | resource={resource} id={record_id}")

        # Validate resource
        if resource not in ROUTES:
            print(f"{request_id} Unknown resource: {resource}")
            return _response(404, {"message": "Resource not found"})

        cfg = ROUTES[resource]
        table = cfg["table"]
        columns = cfg["columns"]
        pk = cfg["pk"]
        pk_is_int = cfg["pk_is_int"]

        # Pagination for list
        limit = _safe_int(qparams.get("limit"), allow_none=True)
        offset = _safe_int(qparams.get("offset"), allow_none=True)
        limit = 100 if (limit is None or limit < 0) else min(limit, 1000)
        offset = 0 if (offset is None or offset < 0) else offset

        conn = None
        try:
            print(f"{request_id} Connecting to DB")
            conn = create_connection()
            print(f"{request_id} DB connected")

            with conn.cursor() as cur:
                # -------- LIST (/resource) --------
                if record_id is None or str(record_id).strip() == "":
                    list_sql = (
                        f"SELECT {columns} FROM {table} "
                        f"ORDER BY {pk} DESC LIMIT %s OFFSET %s"
                    )
                    print(f"{request_id} LIST {table} limit={limit} offset={offset}")
                    cur.execute(list_sql, (limit, offset))
                    rows = cur.fetchall()

                    count_sql = f"SELECT COUNT(*) AS total FROM {table}"
                    cur.execute(count_sql)
                    total = cur.fetchone()["total"]

                    return _response(200, {
                        "items": rows,
                        "count": len(rows),
                        "total": total,
                        "limit": limit,
                        "offset": offset
                    })

                # -------- DETAIL (/resource/{id}) --------
                if pk_is_int:
                    try:
                        record_id_val = int(str(record_id).strip())
                    except Exception:
                        print(f"{request_id} Invalid id for {resource}: {record_id}")
                        return _response(400, {"message": "Invalid id"})
                else:
                    record_id_val = str(record_id).strip()

                detail_sql = f"SELECT {columns} FROM {table} WHERE {pk} = %s"
                print(f"{request_id} DETAIL {table}.{pk}={record_id_val}")
                cur.execute(detail_sql, (record_id_val,))
                row = cur.fetchone()

                if not row:
                    print(f"{request_id} Not found {table}.{pk}={record_id_val}")
                    return _response(404, {"message": f"{resource} record not found"})

                return _response(200, row)

        finally:
            if conn:
                conn.close()
                print(f"{request_id} DB connection closed")

    except pymysql.err.OperationalError as e:
        print(f"{request_id} DB connection error: {str(e)}")
        return _response(500, {"message": "Database connection error"})
    except Exception as e:
        print(f"{request_id} Unhandled error: {str(e)}")
        return _response(500, {"message": "Internal server error"})
