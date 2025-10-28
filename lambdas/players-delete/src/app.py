import json
import os
import pymysql

DELETE_PLAYER_SQL = """
    DELETE FROM players
    WHERE id = %s
"""

def validate_player_data(player_data) -> bool:
    try:
        int(player_data.get("player_id", ""))
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
        cursorclass=pymysql.cursors.DictCursor
    )

def lambda_handler(event, context):

    request_id = context.aws_request_id

    player_data = json.loads(event["body"])

    print(f"{request_id} Reveived player_data: {str(player_data)}")

    if not validate_player_data(player_data):
        print(f"{request_id} Invalid player_data")
        return {
            'statusCode': 400,
        }
    
    player_id = player_data.get("player_id")
    
    connection = None

    try:

        print(f"{request_id} Connecting to db")

        connection = create_connection()

        print(f"{request_id} Connection established, deleting player...")

        with connection.cursor() as cursor:
            cursor.execute(
                DELETE_PLAYER_SQL, 
                (player_id)
            )
            connection.commit()
            if cursor.rowcount == 0:
                return {
                    'statusCode': 400,
                    'headers': {
                        'Content-Type': 'application/json',
                        'Access-Control-Allow-Origin': '*'
                    },
                    'body': json.dumps({"error": f"No player with id: {player_id}"})
                }
            delete_id = cursor.lastrowid
            
        
        print(f"{request_id} Player deleted. Deleted player id: {player_id}")

        return {    
            'statusCode': 200,
            'headers': {
                'Content-Type': 'application/json',
                'Access-Control-Allow-Origin': '*'
            },
            "body": json.dumps(f"Player deleted: {delete_id}")
    }

    except Exception as e:
        print(f"{request_id} Failed to delete player, Error: {str(e)}")
        return {
            "statusCode": 500,
            "body": json.dumps(f"Failed to delete player, Error: {str(e)}")
        }

    finally:
        if connection:
            connection.close()
