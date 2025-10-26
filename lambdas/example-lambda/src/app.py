import json
import os
import requests
from datetime import datetime

def lambda_handler(event, context):
    call_url = os.environ["CALL_URL"]
    
    res = requests.get(call_url)
    
    return {
        'statusCode': 200,
        'headers': {
            'Content-Type': 'application/json',
            'Access-Control-Allow-Origin': '*'
        },
        'body': json.dumps(f"GET of {call_url} returned status code {res.status_code}", indent=2)
    }
