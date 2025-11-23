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

def lambda_handler(event, context):
    request_id = context.aws_request_id
    
    pickems_id = event["pathParameters"]["id"]

    connection = None
    try:
        connection = create_connection()
        with connection.cursor() as cursor:
            cursor.execute("SELECT * FROM pickems WHERE user_id = %s", (pickems_id,))
            result = cursor.fetchone()

        if not result:
            return {
                'statusCode': 404,
                'headers': {
                    'Content-Type': 'application/json',
                    'Access-Control-Allow-Origin': '*'
                },
                'body': json.dumps({"error": f"pickems not found with id: {pickems_id}"})
            }

        return {
            'statusCode': 200,
            'headers': {
                'Content-Type': 'application/json',
                'Access-Control-Allow-Origin': '*'
            },
            'body': json.dumps({
                "message": "Pickems retrieved successfully",
                "data": result
            })
        }

    except Exception as e:
        return {
            'statusCode': 500,
            'headers': {
                'Content-Type': 'application/json',
                'Access-Control-Allow-Origin': '*'
            },
            'body': json.dumps({"error": str(e)})
        }
    finally:
        if connection:
            connection.close()