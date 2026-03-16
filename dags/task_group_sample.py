"""
DAG to test Task Analyzer plugin with a failing task inside a task group.
"""
from datetime import datetime
from airflow import DAG
from airflow.operators.bash import BashOperator
from airflow.utils.task_group import TaskGroup

with DAG(
    dag_id="sample_task_group_dag",
    start_date=datetime(2024, 1, 1),
    schedule=None,
    catchup=False,
    tags=["test", "task_analyzer"],
) as dag:

    start = BashOperator(
        task_id="start",
        bash_command="echo 'Starting test DAG'",
    )

    with TaskGroup("processing_group") as processing:

        success_task = BashOperator(
            task_id="success_task",
            bash_command="echo 'This task will succeed'",
        )

        failing_task = BashOperator(
            task_id="failing_task",
            bash_command="exit 1",  # This will fail
        )

        another_task = BashOperator(
            task_id="another_task",
            bash_command="echo 'This task depends on success_task'",
        )

        success_task >> another_task  # pylint: disable=pointless-statement

    end = BashOperator(
        task_id="end",
        bash_command="echo 'DAG completed'",
    )

    start >> processing >> end  # pylint: disable=pointless-statement
