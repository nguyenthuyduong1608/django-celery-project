from django.conf import settings
from django.shortcuts import render
from django.http import JsonResponse
from .models import CSVFile, TaskStatus
from .tasks import process_csv_file
from django.core.files.storage import default_storage
import uuid
import pandas as pd  # Import pandas for CSV processing
import json  # Import json for request parsing
from django.views.decorators.csrf import csrf_exempt
import os
from rest_framework.permissions import IsAuthenticated
from rest_framework.decorators import api_view, permission_classes

# CSV Upload API
@csrf_exempt
@api_view(['POST'])
@permission_classes([IsAuthenticated])
def upload_csv(request):
    if request.method == "POST" and request.FILES.get("file"):
        file = request.FILES["file"]
        if file.name.endswith('.csv'):
            file_id = str(uuid.uuid4())
            file_path = f"csv_files/{file_id}.csv"

            # Ensure the directory exists
            file_dir = os.path.dirname(file_path)
            if not os.path.exists(file_dir):
                os.makedirs(file_dir)  # Create the directory if it doesn't exist

            with default_storage.open(file_path, 'wb') as f:
                for chunk in file.chunks():
                    f.write(chunk)

            # Save file record
            csv_file = CSVFile.objects.create(file=file_path)
            return JsonResponse({
                "message": "File uploaded successfully",
                "file_id": str(csv_file.id)
            })
        else:
            return JsonResponse({"error": "Invalid file format. Only CSV files are allowed."}, status=400)
    return JsonResponse({"error": "No file uploaded."}, status=400)

# CSV Operation API
@csrf_exempt
@api_view(['POST'])
@permission_classes([IsAuthenticated])
def perform_operation(request):
    if request.method == "POST":
        try:
            data = json.loads(request.body)  # Correct way to parse JSON in Django
            file_id = data.get("file_id")
            operation = data.get("operation")
            column = data.get("column", None)
            filter_conditions = data.get("filter_conditions", None)

            if file_id and operation:
                task = process_csv_file.apply_async(args=[file_id, operation, column, filter_conditions])
                return JsonResponse({
                    "message": "Operation started",
                    "task_id": task.id
                })
            else:
                return JsonResponse({"error": "Invalid operation or file not found."}, status=400)
        except json.JSONDecodeError:
            return JsonResponse({"error": "Invalid JSON data."}, status=400)
    return JsonResponse({"error": "Invalid request."}, status=400)

# Task Status API
@api_view(['GET'])
@permission_classes([IsAuthenticated])
def task_status(request):
    task_id = request.GET.get('task_id')
    if not task_id:
        return JsonResponse({"error": "Task ID is required."}, status=400)

    task_status = TaskStatus.objects.filter(task_id=task_id).first()
    if not task_status:
        return JsonResponse({"error": "Task not found."}, status=404)

    # Get the 'n' parameter, defaulting to 100 if not provided
    n = request.GET.get('n', 100)

    try:
        n = int(n)
        if n <= 0:
            return JsonResponse({"error": "'n' must be a positive integer."}, status=400)
    except ValueError:
        return JsonResponse({"error": "'n' must be an integer."}, status=400)

    response_data = {
        "task_id": task_id,
        "status": task_status.status,
    }

    if task_status.status == "SUCCESS":
        try:
            # Using pandas to read CSV from the result file
            result_file_path = os.path.join(settings.MEDIA_ROOT, task_status.result_file.name)
            if not os.path.exists(result_file_path):
                return JsonResponse({"error": "Processed file not found."}, status=404)

            # Read the CSV file and limit the number of records
            df = pd.read_csv(result_file_path)
            result_data = df.head(n).to_dict(orient="records")
            
            response_data["result"] = {
                "data": result_data,
                "file_link": task_status.result_file.url
            }
        except Exception as e:
            response_data["error"] = f"Error reading result file: {str(e)}"
    elif task_status.status == "FAILURE":
        response_data["error"] = task_status.error_message

    return JsonResponse(response_data)