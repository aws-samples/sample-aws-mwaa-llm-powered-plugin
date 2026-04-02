from datetime import datetime
import importlib.util
from airflow import DAG
from airflow.providers.standard.operators.bash import BashOperator
from airflow.providers.standard.operators.python import PythonOperator

SCRIPT_PATH = "/usr/local/airflow/include/scripts/calculate.py"


def run_calculate_script():
    spec = importlib.util.spec_from_file_location("calculate", SCRIPT_PATH)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    module.main()


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
        python_callable=run_calculate_script,
    )

    bash_task >> python_task
