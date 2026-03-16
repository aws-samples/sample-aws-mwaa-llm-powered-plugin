from datetime import datetime
from airflow import DAG
from airflow.providers.standard.operators.bash import BashOperator
from airflow.providers.standard.operators.python import PythonOperator

def add_numbers():
    """Add two numbers - intentionally fails"""
    a = 10
    b = 20
    result = a + b
    # Intentional error - undefined variable
    print(f"Result: {result}")
    print(f"Final: {undefined_variable}")  # This will fail

with DAG(
    dag_id='test_analyzer',
    start_date=datetime(2024, 1, 1),
    schedule=None,
    catchup=False,
    tags=['test']
) as dag:

    success_task = BashOperator(
        task_id='success_bash',
        bash_command='echo "Starting process..." && echo "Processing data..." && echo "Complete!"'
    )

    fail_task = PythonOperator(
        task_id='fail_python',
        python_callable=add_numbers
    )

    success_task >> fail_task
