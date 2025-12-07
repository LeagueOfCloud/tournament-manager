import json
import os
import pymysql

GET_LEADERBOARD_PICKEMS_SQL = """
SET @limit := 10;
SET @offset := ?;

SELECT
    p.id,
    p.name,
    p.discord_id,
    p.avatar_url,
    p.pickems_score,
    p.dd_score,
    ROW_NUMBER() OVER (ORDER BY p.pickems_score DESC, p.id ASC) AS rank
FROM profiles AS p
ORDER BY {} DESC, p.id ASC
LIMIT @limit OFFSET @offset
"""

GET_TOTAL_PAGES_SQL = "SELECT CEIL(COUNT(*) / 10) AS total_pages FROM profiles"


def response(status_code, body):
    return {
        "statusCode": status_code,
        "headers": {
            "Content-Type": "application/json",
            "Access-Control-Allow-Origin": "*",
        },
        "body": json.dumps(body),
    }


def create_connection() -> pymysql.Connection:
    return pymysql.connect(
        host=os.environ["DB_HOST"],
        port=int(os.environ["DB_PORT"]),
        user=os.environ["DB_USER"],
        password=os.environ["DB_PASSWORD"],
        database=os.environ["DB_NAME"],
        cursorclass=pymysql.cursors.DictCursor,
    )


def lambda_handler(event, context):
    path_params = event.get("pathParameters") or {}
    leaderboard_type = path_params.get("board")

    if leaderboard_type not in ["pickems", "dream-draft"]:
        return response(404, {"message": "Requested leaderboard could not be found"})

    qparams = event.get("queryStringParameters") or {}
    page = qparams.get("page", 1)

    match leaderboard_type:
        case "pickems":
            score_column = "pickems_score"
        case "dream-draft":
            score_column = "dd_score"
        case _:
            return response(400, {"message": "Invalid leaderboard type"})

    try:
        connection = create_connection()

        with connection.cursor() as cur:
            cur.execute(
                GET_LEADERBOARD_PICKEMS_SQL.format(score_column), ((page - 1) * 10)
            )
            rows = cur.fetchall()
            cur.execute(GET_TOTAL_PAGES_SQL)
            total_pages = cur.fetchone()["total_pages"]

        return response(200, {"items": rows, "pages": total_pages, "page": page})

    except Exception as e:
        return response(500, {"message": f"{e}"})
