from datetime import datetime
from airflow import DAG
from airflow.providers.standard.operators.bash import BashOperator
from airflow.providers.standard.operators.python import PythonOperator

with DAG(
    dag_id="test_external_scripts",
    start_date=datetime(2024, 1, 1),
    schedule=None,
    catchup=False,
    tags=["test"],
) as dag:

    bash_task = BashOperator(
        task_id="run_bash_script",
        bash_command="/usr/local/airflow/include/scripts/process_data.sh ",
    )

    python_task = PythonOperator(
        task_id="run_python_script",
        python_callable=lambda: exec(
            open("/usr/local/airflow/include/scripts/calculate.py").read()
        ),
    )

    bash_task >> python_task
