"""A simple Airflow DAG that prints "Hello World" and includes a task that intentionally fails.
"""
from datetime import datetime, timedelta
from airflow import DAG
from airflow.operators.bash import BashOperator

# Default arguments for the DAG
default_args = {
    "owner": "airflow",
    "depends_on_past": False,
    "start_date": datetime(2024, 1, 1),
    "email_on_failure": False,
    "email_on_retry": False,
    "retries": 1,
    "retry_delay": timedelta(seconds=10),
}

# Define the DAG
dag = DAG(
    "hello_world_test",
    default_args=default_args,
    description="A simple Hello World DAG using BashOperator",
    schedule=timedelta(days=1),
    catchup=False,
    tags=["example", "bash"],
)

# Create the bash task
hello_task = BashOperator(
    task_id="print_hello_world",
    bash_command='echo "Hello World from Airflow!"',
    dag=dag,
)

# Create a failing task
fail_task = BashOperator(
    task_id="intentional_failure",
    bash_command='exit 1',
    dag=dag,
)

hello_task >> fail_task  # pylint: disable=pointless-statement
