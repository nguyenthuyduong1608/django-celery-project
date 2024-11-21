from celery import shared_task
import pandas as pd
from .models import TaskStatus, CSVFile
from django.core.files.storage import default_storage
from django.conf import settings
import os

@shared_task(bind=True)
def process_csv_file(self, file_id, operation, column=None, filter_conditions=None):
    try:
        # Retrieve the CSV file from the database
        csv_file = CSVFile.objects.get(id=file_id)
        file_path = csv_file.file.path

        # Check if the file exists
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"CSV file not found at {file_path}")

        # Load the CSV file
        df = pd.read_csv(file_path)

        # Perform the requested operation
        if operation == "dedup":
            df = df.drop_duplicates()
        elif operation == "unique":
            if column:
                df = df[column].drop_duplicates()
            else:
                raise ValueError("Column name is required for 'unique' operation.")
        elif operation == "filter":
            if filter_conditions:
                for col, value in filter_conditions.items():
                    df = df[df[col] == value]
            else:
                raise ValueError("Filter conditions are required for 'filter' operation.")
        else:
            raise ValueError("Invalid operation.")

        # Save the processed CSV file using Django's storage
        # Ensure the directory for processed files exists
        processed_files_dir = os.path.join(settings.MEDIA_ROOT, 'processed_files')
        if not os.path.exists(processed_files_dir):
            os.makedirs(processed_files_dir)

        # Prepare the processed file path
        processed_file_name = f'processed_{file_id}.csv'
        processed_file_path = os.path.join('processed_files', processed_file_name)

        # Save the processed data to a file
        with default_storage.open(processed_file_path, 'w') as f:
            df.to_csv(f, index=False)

        # Save the task status as successful and link the processed file
        task_status = TaskStatus.objects.create(
            task_id=self.request.id,
            status='SUCCESS',
            result_file=processed_file_path  # Store relative file path for Django's FileField
        )

        return task_status.id

    except Exception as e:
        # Handle failure and log the error
        task_status = TaskStatus.objects.create(
            task_id=self.request.id,
            status='FAILURE',
            error_message=str(e)
        )
        return task_status.id