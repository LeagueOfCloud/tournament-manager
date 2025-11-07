import base64
import json
import os
import pymysql
from datetime import datetime

INSERT_CONFIG_SQL = """
    INSERT INTO config (name, value)
    VALUES (%s, %s)
"""

def validate_config_data(config_data) -> bool:
    return config_data.get("name", "").strip()

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
    request_id = context.aws_request_id

    config_data = json.loads(event["body"])

    if not validate_config_data(config_data):
        return {
            'statusCode': 400,
            "headers": {
                "Content-Type": "application/json",
                "Access-Control-Allow-Origin": "*"
            },
            'body': json.dumps("Invalid body data")
        }

    name = config_data.get("name")
    value = config_data.get("value")

    connection = None

    try:
        connection = create_connection()

        with connection.cursor() as cursor:
            cursor.execute(
                INSERT_CONFIG_SQL, 
                (name, value)
            )
            connection.commit()

        return {    
            'statusCode': 200,
            'headers': {
                'Content-Type': 'application/json',
                'Access-Control-Allow-Origin': '*'
            },
            "body": json.dumps({
                "message": "Config was created successfully!",
                "config_name": name,
            })
    }

    except Exception as e:
        return {
            "statusCode": 500,
            "headers": {
                "Content-Type": "application/json",
                "Access-Control-Allow-Origin": "*"
            },
            "body": json.dumps(f"Failed to create config, Error: {str(e)}")
        }

    finally:
        if connection:
            connection.close()
