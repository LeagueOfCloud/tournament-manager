import json
import os
import pymysql

DELETE_CONFIG_SQL = """
    DELETE FROM config
    WHERE name = %s
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
            }
        }
    
    config_name = config_data.get("name")    
    connection = None

    try:
        connection = create_connection()

        with connection.cursor() as cursor:
            cursor.execute(
                DELETE_CONFIG_SQL,
                (config_name)
            )
            connection.commit()
            if cursor.rowcount == 0:
                return {
                    'statusCode': 400,
                    'headers': {
                        'Content-Type': 'application/json',
                        'Access-Control-Allow-Origin': '*'
                    },
                    'body': json.dumps({"error": f"No config with name: {config_name}"})
                }

        return {    
            'statusCode': 200,
            'headers': {
                'Content-Type': 'application/json',
                'Access-Control-Allow-Origin': '*'
            },
            "body": json.dumps(f"Config deleted: {config_name}")
    }

    except Exception as e:
        return {
            "statusCode": 500,
            "headers": {
                "Content-Type": "application/json",
                "Access-Control-Allow-Origin": "*"
            },
            "body": json.dumps(f"Failed to delete config, Error: {str(e)}")
        }

    finally:
        if connection:
            connection.close()
