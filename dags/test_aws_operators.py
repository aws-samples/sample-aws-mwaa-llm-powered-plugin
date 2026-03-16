from datetime import datetime
from airflow import DAG
from airflow.providers.amazon.aws.operators.athena import AthenaOperator
from airflow.providers.amazon.aws.operators.redshift_data import RedshiftDataOperator
from airflow.providers.amazon.aws.operators.emr import EmrAddStepsOperator, EmrServerlessStartJobOperator

with DAG(
    dag_id="test_aws_sql_operators",
    start_date=datetime(2024, 1, 1),
    schedule=None,
    catchup=False,
    tags=["test", "aws"],
) as dag:

    # Athena task - will fail if database doesn't exist or has SQL error
    athena_task = AthenaOperator(
        task_id="run_athena_query",
        query="""
        SELECT 
            customer_id,
            customer_name,
            COUNT(*) as order_count,
            SUM(amount) as total_amount,
            invalid_column  -- Intentional error: column doesn't exist
        FROM customers
        WHERE order_date > DATE '2024-01-01'
        GROUP BY customer_id, customer_name
        HAVING COUNT(*) > 5
        ORDER BY total_amount DESC
        LIMIT 100
        """,
        database="test_db",
        output_location="s3://your-bucket/athena-results/",
        aws_conn_id="aws_default",
    )

    # Redshift task - will fail if cluster doesn't exist or has SQL error
    redshift_task = RedshiftDataOperator(
        task_id="run_redshift_query",
        sql="""
        CREATE TEMP TABLE sales_summary AS
        SELECT 
            product_id,
            product_name,
            SUM(quantity) as total_qty,
            SUM(amount) / 0 as avg_amount,  -- Intentional error: division by zero
            COUNT(DISTINCT customer_id) as unique_customers
        FROM sales s
        JOIN products p ON s.product_id = p.id
        WHERE sale_date >= CURRENT_DATE - 30
        GROUP BY product_id, product_name;
        """,
        database="analytics",
        cluster_identifier="test-cluster",
        db_user="admin",
        aws_conn_id="aws_default",
    )

    # EMR task - will fail with invalid cluster ID
    emr_task = EmrAddStepsOperator(
        task_id="run_emr_step",
        job_flow_id="j-INVALIDCLUSTER",
        aws_conn_id="aws_default",
        steps=[
            {
                "Name": "Process Sales Data",
                "ActionOnFailure": "CONTINUE",
                "HadoopJarStep": {
                    "Jar": "command-runner.jar",
                    "Args": [
                        "spark-submit",
                        "--deploy-mode",
                        "cluster",
                        "--master",
                        "yarn",
                        "--conf",
                        "spark.sql.shuffle.partitions=200",
                        "s3://bms-test-cfn/mwaa-blog/process_sales.py",
                        "--input",
                        "s3://my-bucket/raw-data/sales/",
                        "--output",
                        "s3://my-bucket/processed-data/sales/",
                        "--date",
                        "2024-01-01",
                    ],
                },
            }
        ],
    )

    # EMR Serverless task - will fail with invalid application ID
    emr_serverless_task = EmrServerlessStartJobOperator(
        task_id="run_emr_serverless_job",
        application_id="00000000000000000",
        execution_role_arn="arn:aws:iam::123456789012:role/EMRServerlessRole",
        job_driver={
            "sparkSubmit": {
                "entryPoint": "s3://bms-test-cfn/mwaa-blog/process_sales.py",
                "entryPointArguments": [
                    "--input", "s3://my-bucket/raw-data/sales/",
                    "--output", "s3://my-bucket/processed-data/sales/",
                    "--date", "2024-01-01"
                ],
                "sparkSubmitParameters": "--conf spark.executor.cores=2 --conf spark.executor.memory=4g"
            }
        },
        configuration_overrides={
            "monitoringConfiguration": {
                "s3MonitoringConfiguration": {
                    "logUri": "s3://my-bucket/emr-serverless-logs/"
                }
            }
        },
        aws_conn_id="aws_default"
    )

    emr_serverless_task >> emr_task >> athena_task >> redshift_task
