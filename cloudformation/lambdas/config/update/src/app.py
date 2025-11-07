import base64
import json
import os
import pymysql
from datetime import datetime

def validate_config_data(config_data) -> bool:

    updatable_fields = ["name", "value"]
    if not any(field in config_data for field in updatable_fields):
        return False

    if not config_data.get("name", "").strip():
        return False

    if "value" in config_data:
        if config_data.get("value") is not None and not config_data.get("value", "").strip():
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

def build_update_query(config_data):
    update_fields = []
    values = []

    if "value" in config_data:
        update_fields.append("value = %s")
        v = config_data["value"]
        values.append(v.strip() if isinstance(v, str) else None)

    return update_fields, values

def lambda_handler(event, context):
    
    request_id = context.aws_request_id
    
    config_data = json.loads(event["body"])

    if not validate_config_data(config_data):
        return {
            'statusCode': 400,
            'headers': {
                'Content-Type': 'application/json',
                'Access-Control-Allow-Origin': '*'
            },
            'body': json.dumps({"error": "Invalid config data"})
        }
    
    config_name = config_data.get("name").strip()
    connection = None

    try:   
        connection = create_connection()
        
        update_fields, values = build_update_query(config_data)
        
        if not update_fields:
            return {
                'statusCode': 400,
                'headers': {
                    'Content-Type': 'application/json',
                    'Access-Control-Allow-Origin': '*'
                },
                'body': json.dumps({"error": "No valid fields to update"})
            }
        
        values.append(config_name)
        
        update_sql = f"""
            UPDATE config 
            SET {', '.join(update_fields)}
            WHERE name = %s
        """

        with connection.cursor() as cursor:
            rows_affected = cursor.execute(update_sql, values)
            connection.commit()
        
        if rows_affected == 0:
            return {
                'statusCode': 404,
                'headers': {
                    'Content-Type': 'application/json',
                    'Access-Control-Allow-Origin': '*'
                },
                'body': json.dumps({"error": f"Config not found with name: {config_name}"})
            }

        return {    
            'statusCode': 200,
            'headers': {
                'Content-Type': 'application/json',
                'Access-Control-Allow-Origin': '*'
            },
            'body': json.dumps({
                "message": "Config updated successfully",
                "config_name": config_name
            })
        }

    except pymysql.IntegrityError as e:
        error_code = e.args[0]
        error_msg = str(e)
        
        if error_code == 1062:  
            error_response = "A config with this name already exists"
        else:
            error_response = f"Database constraint violation: {error_msg}"
        
        return {
            "statusCode": 400,
            'headers': {
                'Content-Type': 'application/json',
                'Access-Control-Allow-Origin': '*'
            },
            "body": json.dumps({"error": error_response})
        }
    
    except Exception as e:
        return {
            "statusCode": 500,
            'headers': {
                'Content-Type': 'application/json',
                'Access-Control-Allow-Origin': '*'
            },
            "body": json.dumps({"error": f"Failed to update config: {str(e)}"})
        }

    finally:
        if connection:
            connection.close()
