import json
import os
import re
import pymysql

TABLE_NAME   = "players"
#COLUMNS_LIST = "id, name, avatar_url, discord_id, team_id, team_role"
PRIMARY_KEY  = "id"

# SQL injection prevention regex
_VALID_IDENT = re.compile(r"^[A-Za-z_][A-Za-z0-9_]*$")

def _assert_ident(name: str, value: str):
    if not _VALID_IDENT.match(value or ""):
        raise ValueError(f"Invalid {name}: {value}")

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

def lambda_handler(event, context):
    request_id = getattr(context, "aws_request_id", "no-request-id")
    path_params = (event.get("pathParameters") or {})
    qparams = (event.get("queryStringParameters") or {})

    table_name = os.environ["TABLE_NAME"]
    pk = os.environ.get("PRIMARY_KEY", "id")

    # Prevent SQL injection through env misconfig
    try:
        _assert_ident("TABLE_NAME", table_name)
        _assert_ident("PRIMARY_KEY", pk)
    except ValueError as ve:
        print(f"{request_id} Invalid configuration: {ve}")
        return _response(500, {"message": "Server configuration error"})

    record_id = path_params.get("id")

    # Parse pagination (list endpoint)
    def _as_int(val, default):
        try:
            if val is None:
                return default
            v = int(val)
            return v if v >= 0 else default
        except Exception:
            return default

    limit = _as_int(qparams.get("limit"), 100)
    offset = _as_int(qparams.get("offset"), 0)
    if limit > 1000:  # hard cap
        limit = 1000

    connection = None

    try:
        print(f"{request_id} Connecting to DB")
        connection = create_connection()
        print(f"{request_id} Connection established")

        with connection.cursor() as cursor:
            if record_id is None:
                # LIST /players
                list_sql = (
                    f"SELECT * FROM {table_name} "
                    f"ORDER BY {pk} DESC "
                    f"LIMIT %s OFFSET %s"
                )
                print(f"{request_id} Executing LIST on {table_name} (limit={limit}, offset={offset})")
                cursor.execute(list_sql, (limit, offset))
                rows = cursor.fetchall()

                # Also return total count for pagination (optional)
                count_sql = f"SELECT COUNT(*) AS total FROM {table_name}"
                cursor.execute(count_sql)
                total = cursor.fetchone()["total"]

                return _response(200, {"items": rows, "count": len(rows), "total": total, "limit": limit, "offset": offset})

            # DETAIL /players/{id}
            # is id int or varchar? if varchar -> remove this
            try:
                record_id_cast = int(record_id)
            except Exception:
                print(f"{request_id} Invalid id '{record_id}' (must be integer)")
                return _response(400, {"message": "Invalid id"})

            detail_sql = f"SELECT * FROM {table_name} WHERE {pk} = %s"
            print(f"{request_id} Executing DETAIL on {table_name} by {pk}={record_id_cast}")
            cursor.execute(detail_sql, (record_id_cast,))
            row = cursor.fetchone()

            if not row:
                print(f"{request_id} Not found: {table_name}.{pk}={record_id_cast}")
                return _response(404, {"message": f"{table_name} record not found"})

            return _response(200, row)

    except pymysql.err.OperationalError as e:
        print(f"{request_id} DB connection error: {str(e)}")
        return _response(500, {"message": "Database connection error"})
    except Exception as e:
        print(f"{request_id} Unhandled error: {str(e)}")
        return _response(500, {"message": "Internal server error"})
    finally:
        if connection:
            connection.close()
            print(f"{request_id} DB connection closed")