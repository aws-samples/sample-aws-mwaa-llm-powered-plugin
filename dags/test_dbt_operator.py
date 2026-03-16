"""
DBT Test DAG - Requires apache-airflow-providers-dbt-cloud to be installed
To install: Add 'apache-airflow-providers-dbt-cloud' to requirements.txt
"""
from datetime import datetime
from airflow import DAG

# Uncomment when DBT provider is installed:
# from airflow.providers.dbt.cloud.operators.dbt import DbtCloudRunJobOperator

with DAG(
    dag_id='test_dbt_operator',
    start_date=datetime(2024, 1, 1),
    schedule=None,
    catchup=False,
    tags=['test', 'dbt']
) as dag:
    
    # Uncomment when DBT provider is installed:
    # dbt_task = DbtCloudRunJobOperator(
    #     task_id='run_dbt_models',
    #     job_id=12345,  # Invalid job ID - will fail
    #     account_id=67890,
    #     conn_id='dbt_cloud_default',
    #     check_interval=10,
    #     timeout=300
    # )
    
    pass
