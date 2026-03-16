"""
DAG to test Task Analyzer plugin with AWS Glue job failure
"""
from airflow.decorators import dag
from airflow.providers.amazon.aws.operators.glue import GlueJobOperator
from pendulum import datetime


@dag(
    start_date=datetime(2025, 1, 1),
    schedule=None,  # Manual trigger only
    catchup=False,
    tags=["test", "glue", "failure"],
    doc_md=__doc__,
)
def test_glue_job_failure():
    """Test DAG to trigger Glue job with intentional syntax error"""
    
    run_glue_job = GlueJobOperator(
        task_id="run_glue_job_with_error",
        job_name="SimpleETLJob-SyntaxError",
        aws_conn_id="aws_default",
        region_name="us-east-1",
        wait_for_completion=True,
        verbose=True,
    )
    
    run_glue_job


test_glue_job_failure()
