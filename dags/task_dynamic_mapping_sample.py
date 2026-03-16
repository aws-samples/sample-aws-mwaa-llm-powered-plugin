"""
DAG to test Task Analyzer plugin with dynamic task mapping and induced failures.
"""
from datetime import datetime
import random
from airflow import DAG
from airflow.decorators import task

with DAG(
    dag_id="sample_task_dynamic_mapping",
    start_date=datetime(2024, 1, 1),
    schedule=None,
    catchup=False,
    tags=["test", "task_analyzer", "dynamic"],
) as dag:

    @task
    def generate_numbers():
        """Generate random count of numbers to process"""
        count = random.randint(3, 7)
        return list(range(count))

    @task
    def process_number(number: int):
        """Process a number - fails if number is 2 or 5"""
        print(f"Processing number: {number}")

        # Induce failure for specific numbers
        if number == 2:
            raise ValueError(f"Number {number} is not allowed (even prime)")
        if number == 5:
            raise RuntimeError(f"Number {number} causes processing error")

        # Success case
        result = number * 10
        print(f"Successfully processed {number} -> {result}")
        return result

    @task
    def summarize(results):
        """Summarize all results"""
        total = sum(results)
        print(f"Total of all results: {total}")
        return total

    # Dynamic task mapping
    numbers = generate_numbers()
    processed = process_number.expand(number=numbers)
    summary = summarize(processed)
