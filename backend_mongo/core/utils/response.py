from django.http import JsonResponse
from bson import ObjectId
import datetime

def convert_mongo_types(data):
    if isinstance(data, list):
        return [convert_mongo_types(item) for item in data]
    elif isinstance(data, dict):
        return {k: convert_mongo_types(v) for k, v in data.items()}
    elif isinstance(data, ObjectId):
        return str(data)
    elif isinstance(data, datetime.datetime):
        return data.isoformat()
    else:
        return data

def api_response(data=None, message="Success", status=200):
    formatted_data = convert_mongo_types(data)
    return JsonResponse({
        "message": message,
        "status": status,
        "data": formatted_data
    }, status=status, safe=False)
