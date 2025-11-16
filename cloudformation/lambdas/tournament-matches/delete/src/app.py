import json
import os
import pymysql

DELETE_TOURNAMENT_MATCH_SQL = """
    DELETE FROM tournament_matches WHERE id = %s
"""

def validate_match_data(match_data) -> bool:
    try:
        int(match_data.get("id", ""))
    except (ValueError, TypeError):
        return False

    return True

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
    request_id = context.aws_request_id
    match_data = json.loads(event["body"])

    if not validate_match_data(match_data):
        
        return {
            "statusCode": 400,
            "headers": {
                "Content-Type": "application/json",
                "Access-Control-Allow-Origin": "*"
            },
        }

    match_id = int(match_data.get("id"))
    connection = None

    try:
        connection = create_connection()

        with connection.cursor() as cursor:
            cursor.execute(
                DELETE_TOURNAMENT_MATCH_SQL, (match_id)
            )
            connection.commit()

        return {
            "statusCode": 200,
            "headers": {
                "Content-Type": "application/json",
                "Access-Control-Allow-Origin": "*",
            },
            "body": json.dumps(f"Tournament Match Deleted"),
        }

    except Exception as e:
        return {
            "statusCode": 500,
            "headers": {
                "Content-Type": "application/json",
                "Access-Control-Allow-Origin": "*"
            },
            "body": json.dumps(f"Failed to delete tournament match, Error: {str(e)}"),
        }

    finally:
        if connection:
            connection.close()