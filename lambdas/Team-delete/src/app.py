import json
import os
import pymysql

DELETE_TEAM_SQL = """
    DELETE FROM teams
    WHERE id = %s
"""

def validate_team_data(team_data) -> bool:
    try:
        int(team_data.get("team_id", ""))
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

    team_data = json.loads(event["body"])

    if not validate_team_data(team_data):
        
        return {
            'statusCode': 400,
            "headers": {
                "Content-Type": "application/json",
                "Access-Control-Allow-Origin": "*"
            },
        }
    
    team_id = team_data.get("team_id")    
    connection = None

    try:
        connection = create_connection()

        with connection.cursor() as cursor:
            cursor.execute(
                DELETE_TEAM_SQL, 
                (team_id)
            )
            connection.commit()
            if cursor.rowcount == 0:
                return {
                    'statusCode': 400,
                    'headers': {
                        'Content-Type': 'application/json',
                        'Access-Control-Allow-Origin': '*'
                    },
                    'body': json.dumps({"error": f"No Team with id: {team_id}"})
                }
            delete_id = cursor.lastrowid

        return {    
            'statusCode': 200,
            'headers': {
                'Content-Type': 'application/json',
                'Access-Control-Allow-Origin': '*'
            },
            "body": json.dumps(f"Team deleted: {delete_id}")
    }

    except Exception as e:
        return {
            "statusCode": 500,
            "headers": {
                "Content-Type": "application/json",
                "Access-Control-Allow-Origin": "*"
            },
            "body": json.dumps(f"Failed to delete Team, Error: {str(e)}")
        }

    finally:
        if connection:
            connection.close()
