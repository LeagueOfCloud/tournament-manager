import json
import os
import pymysql

DELETE_ACCOUNT_SQL = """
    DELETE FROM riot_accounts WHERE id = %s
"""


def validate_account_data(account_data) -> bool:
    try:
        int(account_data.get("account_id", ""))
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
    account_data = json.loads(event["body"])

    if not validate_account_data(account_data):
        
        return {
            "statusCode": 400,
            "headers": {
                "Content-Type": "application/json",
                "Access-Control-Allow-Origin": "*"
            },
        }

    account_id = account_data.get("account_id")
    connection = None

    try:
        connection = create_connection()

        with connection.cursor() as cursor:
            cursor.execute(
                DELETE_ACCOUNT_SQL, (account_id)
            )
            connection.commit()

        return {
            "statusCode": 200,
            "headers": {
                "Content-Type": "application/json",
                "Access-Control-Allow-Origin": "*",
            },
            "body": json.dumps(f"Riot Account Deleted"),
        }

    except Exception as e:
        return {
            "statusCode": 500,
            "headers": {
                "Content-Type": "application/json",
                "Access-Control-Allow-Origin": "*"
            },
            "body": json.dumps(f"Failed to delete riot account, Error: {str(e)}"),
        }

    finally:
        if connection:
            connection.close()
