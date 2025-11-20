import json
import os
import re
import pymysql

ROUTES = {
    # Route config (resource -> table/columns/pk)
    "players": {"table": "players", "columns": "id, name, discord_id, avatar_url, team_id, team_role"},
    "teams": {"table": "teams", "columns": "id, name, logo_url, banner_url, tag"},
    "riot-accounts": {"table": "riot_accounts", "columns": "id, account_name, account_puuid, player_id, is_primary"},
    "profiles": {"table": "profiles", "columns": "id, name, discord_id, avatar_url, type"},
    "config": {"table": "config", "columns": "name, value"},
}

# Helper functions
def _safe_int(value, *, allow_none=False):
    if value is None:
        return None if allow_none else 0
    try:
        return int(value)
    except Exception:
        return None if allow_none else 0

def _extract_path(event) -> str:
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
    path_params = event.get("pathParameters") or {}
    id_from_params = path_params.get("id")

    path = _extract_path(event)
    segs = _split_path_segments(path)

    resource = segs[0] if segs else None

    # Allow both styles: /resource and /resource/{id}
    id_from_path = segs[1] if len(segs) > 1 else None

    record_id = id_from_params if id_from_params is not None else id_from_path
    return resource, record_id

def _response(status: int, body) -> dict:
    return {
        "statusCode": status,
        "headers": {
            "Content-Type": "application/json",
            "Access-Control-Allow-Origin": "*"
        },
        "body": json.dumps(body, default=str)
    }

def create_connection() -> pymysql.Connection:
    return pymysql.connect(
        host=os.environ["DB_HOST"],
        port=int(os.environ["DB_PORT"]),
        user=os.environ["DB_USER"],
        password=os.environ["DB_PASSWORD"],
        database=os.environ["DB_NAME"],
        cursorclass=pymysql.cursors.DictCursor
    )

def lambda_handler(event, context):
    request_id = getattr(context, "aws_request_id", "no-request-id")

    try:
        resource, record_id = _resolve_route_and_id(event)
        qparams = event.get("queryStringParameters") or {}

        print(f"{request_id} Incoming path: { _extract_path(event) } | resource={resource} id={record_id}")

        if resource == "settings":
            conn = create_connection()

            with conn.cursor() as cur:
                list_sql = "SELECT * FROM config"
                cur.execute(list_sql)
                rows = cur.fetchall()
                formatted_rows = {row["name"]: row["value"] for row in rows if row["name"] in ["maintenance", "pickem_unlocked", "dd_unlocked", "tournament_name"]}
                return _response(200, formatted_rows)

        # Validate resource
        if resource not in ROUTES:
            print(f"{request_id} Unknown resource: {resource}")
            return _response(404, {"message": "Resource not found"})

        cfg = ROUTES[resource]
        table = cfg["table"]
        columns = cfg["columns"]

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
                # LIST (/resource)
                if not record_id:
                    if table == "config":
                        list_sql = (
                            f"SELECT {columns} FROM {table} "
                        )
                        cur.execute(list_sql)
                        rows = cur.fetchall()
                        formatted_rows = {row["name"]: row["value"] for row in rows}

                        return _response(200, formatted_rows)
                    
                    else:
                        list_sql = (
                            f"SELECT {columns} FROM {table} "
                            f"ORDER BY id DESC LIMIT %s OFFSET %s"
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

                # DETAIL (/resource/{id})
                try:
                    record_id_val = int(str(record_id).strip())
                except Exception:
                    print(f"{request_id} Invalid id for {resource}: {record_id}")
                    return _response(400, {"message": "Invalid id"})
        
                detail_sql = f"SELECT {columns} FROM {table} WHERE id = %s"
                print(f"{request_id} DETAIL {table}.id={record_id_val}")
                cur.execute(detail_sql, (record_id_val,))
                row = cur.fetchone()

                if not row:
                    print(f"{request_id} Not found {table}.id={record_id_val}")
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
