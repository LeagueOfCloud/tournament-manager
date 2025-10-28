import json
import os
import pymysql

UPDATE_ACCOUNT_SQL = """
    UPDATE riot_accounts SET is_primary = %s WHERE id = %s
"""


def validate_account_data(account_data) -> bool:
    try:
        int(account_data.get("account_id", ""))
        
        if not isinstance(account_data.get("is_primary"), bool):
            raise TypeError
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

    print(f"{request_id} Reveived account_data: {str(account_data)}")

    if not validate_account_data(account_data):
        print(f"{request_id} Invalid account_data for request_id")
        return {
            "statusCode": 400,
        }

    account_id = account_data.get("account_id")
    is_primary = account_data.get("is_primary")

    connection = None

    try:

        print(f"{request_id} Connecting to db")

        connection = create_connection()

        with connection.cursor() as cursor:
            cursor.execute(
                UPDATE_ACCOUNT_SQL, ("true" if is_primary else "false", account_id)
            )
            connection.commit()

        print(f"{request_id} Riot Account Updated")

        return {
            "statusCode": 200,
            "headers": {
                "Content-Type": "application/json",
                "Access-Control-Allow-Origin": "*",
            },
            "body": json.dumps(f"Riot Account Updated"),
        }

    except Exception as e:
        print(f"{request_id} Failed to update riot account, Error: {str(e)}")
        return {
            "statusCode": 500,
            "body": json.dumps(f"Failed to update riot account, Error: {str(e)}"),
        }

    finally:
        if connection:
            connection.close()
