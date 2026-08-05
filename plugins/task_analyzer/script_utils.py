"""
Utility functions for fetching scripts from various AWS/Data operators
"""
import os
import re
from typing import Optional, Dict, Tuple

import boto3


def _get_allowed_base_dirs() -> list:
    """Return the list of directories the plugin is allowed to read from."""
    from pathlib import Path  # pylint: disable=import-outside-toplevel
    base_dirs: list = []
    try:
        from airflow.configuration import conf  # pylint: disable=import-outside-toplevel
        dags_folder = conf.get('core', 'dags_folder', fallback=None)
        if dags_folder:
            base_dirs.append(Path(dags_folder).resolve())
    except Exception:  # pylint: disable=broad-except
        pass
    airflow_home = os.environ.get('AIRFLOW_HOME')
    if airflow_home:
        base_dirs.append(Path(airflow_home).resolve())
    base_dirs.append(Path('/usr/local/airflow').resolve())
    return base_dirs


def read_whitelisted_file(filename: str) -> Optional[str]:
    """Safely read a user-referenced script file.

    Prevents path traversal (CWE-22) by resolving the canonical path and
    verifying it resides within an allowed base directory before reading.

    Returns the file contents, or None if the path is not allowed, not found,
    or cannot be read.
    """
    if not filename or not isinstance(filename, str):
        return None

    from pathlib import Path  # pylint: disable=import-outside-toplevel

    # gitlab-advanced-sast-exclude
    resolved_path = Path(filename).resolve()

    # Validate the resolved path is within an allowed directory.
    allowed = False
    for base_dir in _get_allowed_base_dirs():
        if resolved_path.is_relative_to(base_dir):
            allowed = True
            break

    if not allowed:
        raise ValueError("Invalid file path")

    return resolved_path.read_text(encoding='utf-8')  # gitlab-advanced-sast-exclude


# Error patterns that benefit from seeing code
CODE_RELEVANT_ERRORS = [
    'SyntaxError',
    'NameError',
    'AttributeError',
    'TypeError',
    'ValueError',
    'ImportError',
    'KeyError',
    'join',
    'broadcast',
    'ambiguous',
    'cartesian',
    'data type mismatch',
    'SQL',
    'query',
    'compilation',
]

# Token limits
MAX_TOKENS = {
    'script': 20000,  # ~20KB
    'logs': 50000,    # ~50KB
}


def should_fetch_script(logs: str, error_msg: str, operator_type: str = None) -> bool:
    """Determine if fetching script would be valuable based on error type"""
    # Always fetch for inline scripts (bash, python, sql)
    if operator_type in ['bash', 'python', 'athena', 'redshift', 'dbt']:
        return True

    # For external scripts (glue, emr), check error patterns
    combined_text = f"{logs} {error_msg}".lower()
    return any(pattern.lower() in combined_text for pattern in CODE_RELEVANT_ERRORS)


def extract_operator_info(context: Dict) -> Tuple[Optional[str], Optional[Dict]]:
    """
    Extract operator type and relevant parameters from task context

    Returns:
        Tuple of (operator_type, params_dict)
    """
    if not context:
        return None, None

    operator = context.get('operator')
    if not operator:
        return None, None

    print(f"DEBUG: Operator detected: {operator}")

    # Map operator class names to types (check for substring match)
    operator_map = {
        'GlueJobOperator': 'glue',
        'EmrAddStepsOperator': 'emr',
        'EmrServerlessStartJobOperator': 'emr_serverless',
        'AthenaOperator': 'athena',
        'DbtRunOperator': 'dbt',
        'RedshiftDataOperator': 'redshift',
        'BashOperator': 'bash',
        'PythonOperator': 'python',
    }

    operator_type = None
    for op_class, op_type in operator_map.items():
        if op_class in operator:
            operator_type = op_type
            break

    if not operator_type:
        print(f"DEBUG: Operator type not recognized: {operator}")
        return None, None

    print(f"DEBUG: Operator type identified as: {operator_type}")

    # Extract relevant parameters
    rendered = context.get('rendered_fields', {})
    params = context.get('params', {})

    combined_params = {**rendered, **params}
    # Add task reference for Python operator
    combined_params['_task_context'] = {
        'dag_id': context.get('dag_id'),
        'task_id': context.get('task_id'),
        'run_id': context.get('run_id')
    }
    print(f"DEBUG: Extracted params: {list(combined_params.keys())}")
    print(f"DEBUG: Task context: dag_id={context.get('dag_id')}, task_id={context.get('task_id')}")

    return operator_type, combined_params


def fetch_glue_script(
    job_name: str,
    aws_access_key: str,
    aws_secret_key: str,
    region: str = 'us-east-1'
) -> Tuple[Optional[str], Optional[str]]:
    """Fetch Glue job script from S3"""
    try:
        glue_client = boto3.client(
            'glue',
            aws_access_key_id=aws_access_key,
            aws_secret_access_key=aws_secret_key,
            region_name=region
        )

        response = glue_client.get_job(JobName=job_name)
        script_location = response.get('Job', {}).get('Command', {}).get('ScriptLocation')

        if not script_location or not script_location.startswith('s3://'):
            return None, script_location

        s3_path = script_location[5:]
        bucket, key = s3_path.split('/', 1)

        s3_client = boto3.client(
            's3',
            aws_access_key_id=aws_access_key,
            aws_secret_access_key=aws_secret_key,
            region_name=region
        )

        obj = s3_client.get_object(Bucket=bucket, Key=key)
        script_content = obj['Body'].read().decode('utf-8')

        return script_content, script_location

    except Exception as e:  # pylint: disable=broad-except
        print(f"Error fetching Glue script: {e}")
        return None, None


def fetch_emr_script(
    step_config: Dict,
    aws_access_key: str,
    aws_secret_key: str,
    region: str = 'us-east-1'
) -> Tuple[Optional[str], Optional[str]]:
    """Fetch EMR step script from S3"""
    try:
        # Extract script location from step config
        # Args can be at top level or inside HadoopJarStep
        hadoop_jar_step = step_config.get('HadoopJarStep', {})
        args = step_config.get('Args', []) or hadoop_jar_step.get('Args', [])
        
        print(f"DEBUG: EMR args: {args}")
        script_location = None

        for arg in args:
            if isinstance(arg, str) and arg.startswith('s3://') and (arg.endswith('.py') or arg.endswith('.jar') or arg.endswith('.scala')):
                script_location = arg
                break

        if not script_location:
            print(f"DEBUG: No S3 script location found in EMR args")
            return None, None

        print(f"DEBUG: Found EMR script location: {script_location}")
        s3_path = script_location[5:]
        bucket, key = s3_path.split('/', 1)

        s3_client = boto3.client(
            's3',
            aws_access_key_id=aws_access_key,
            aws_secret_access_key=aws_secret_key,
            region_name=region
        )

        obj = s3_client.get_object(Bucket=bucket, Key=key)
        script_content = obj['Body'].read().decode('utf-8')
        
        print(f"DEBUG: Successfully fetched EMR script, size: {len(script_content)}")
        return script_content, script_location

    except Exception as e:  # pylint: disable=broad-except
        print(f"DEBUG: Error fetching EMR script: {e}")
        return None, None


def fetch_emr_serverless_script(
    job_driver: Dict,
    aws_access_key: str,
    aws_secret_key: str,
    region: str = 'us-east-1'
) -> Tuple[Optional[str], Optional[str]]:
    """Fetch EMR Serverless job script from S3"""
    try:
        # EMR Serverless structure: job_driver -> sparkSubmit -> entryPoint
        spark_submit = job_driver.get('sparkSubmit', {})
        entry_point = spark_submit.get('entryPoint', '')
        
        print(f"DEBUG: EMR Serverless entry_point: {entry_point}")
        
        if not entry_point or not entry_point.startswith('s3://'):
            return None, None
        
        if not (entry_point.endswith('.py') or entry_point.endswith('.jar') or entry_point.endswith('.scala')):
            return None, None
        
        print(f"DEBUG: Found EMR Serverless script location: {entry_point}")
        s3_path = entry_point[5:]
        bucket, key = s3_path.split('/', 1)

        s3_client = boto3.client(
            's3',
            aws_access_key_id=aws_access_key,
            aws_secret_access_key=aws_secret_key,
            region_name=region
        )

        obj = s3_client.get_object(Bucket=bucket, Key=key)
        script_content = obj['Body'].read().decode('utf-8')
        
        print(f"DEBUG: Successfully fetched EMR Serverless script, size: {len(script_content)}")
        return script_content, entry_point

    except Exception as e:  # pylint: disable=broad-except
        print(f"DEBUG: Error fetching EMR Serverless script: {e}")
        return None, None


def extract_inline_script(operator_type: str, params: Dict) -> Tuple[Optional[str], str]:
    """Extract inline scripts from operator parameters"""

    if operator_type == 'athena':
        query = params.get('query') or params.get('sql')
        if query:
            return query, 'inline_athena_query'

    elif operator_type == 'redshift':
        sql = params.get('sql')
        print(f"DEBUG: Redshift params keys: {list(params.keys())}")
        print(f"DEBUG: Redshift sql value: {sql}")
        if sql:
            return sql, 'inline_redshift_query'

    elif operator_type == 'bash':
        bash_command = params.get('bash_command')
        if bash_command:
            # Check if it's a file path (ends with .sh or contains a path)
            bash_cmd_stripped = bash_command.strip()
            if bash_cmd_stripped.endswith('.sh') or '/' in bash_cmd_stripped:
                # Read the referenced script only if it resolves inside an
                # allowed directory (prevents path traversal). Falls back to the
                # inline command when the path is not whitelisted or unreadable.
                try:
                    script_content = read_whitelisted_file(bash_cmd_stripped)
                except (ValueError, FileNotFoundError, PermissionError, IOError):
                    script_content = None
                if script_content is not None:
                    return script_content, f'bash_script_{os.path.basename(bash_cmd_stripped)}'
                return bash_command, 'inline_bash_command'
            else:
                # It's an inline command
                return bash_command, 'inline_bash_command'

    elif operator_type == 'python':
        # Python callable - extract from DAG code
        task_context = params.get('_task_context', {})
        dag_id = task_context.get('dag_id')
        task_id = task_context.get('task_id')
        
        print(f"DEBUG: Python operator - dag_id: {dag_id}, task_id: {task_id}")
        
        # Try to import the DAG and get the task
        if dag_id and task_id:
            try:
                from airflow.models import DagBag
                dagbag = DagBag()
                dag = dagbag.get_dag(dag_id)
                
                if dag:
                    task = dag.get_task(task_id)
                    if task and hasattr(task, 'python_callable'):
                        import inspect
                        python_callable = task.python_callable
                        func_name = getattr(python_callable, '__name__', 'unknown')
                        print(f"DEBUG: Found python_callable: {func_name}")
                        
                        try:
                            source = inspect.getsource(python_callable)
                            print(f"DEBUG: Extracted source, length: {len(source)}")
                            
                            # Check if it's a lambda with exec() and file path
                            if 'exec(' in source and 'open(' in source:
                                # Bounded quantifier + capped input length to avoid
                                # catastrophic backtracking (ReDoS) on tainted source.
                                match = re.search(
                                    r"open\(['\"]([^'\"]{1,4096})['\"]",
                                    source[:100000]
                                )
                                if match:
                                    file_path = match.group(1)
                                    print(f"DEBUG: Found file path in lambda: {file_path}")
                                    # Read only if the path is inside an allowed
                                    # directory (prevents path traversal).
                                    try:
                                        file_content = read_whitelisted_file(file_path)
                                    except (ValueError, FileNotFoundError, PermissionError, IOError):
                                        file_content = None
                                    if file_content is not None:
                                        return file_content, f'python_script_{os.path.basename(file_path)}'
                            
                            return source, f'python_function_{func_name}'
                        except (TypeError, OSError) as e:
                            print(f"DEBUG: Could not get source: {e}")
                            op_args = params.get('op_args', [])
                            op_kwargs = params.get('op_kwargs', {})
                            return f"# Python Function: {func_name}\n# Args: {op_args}\n# Kwargs: {op_kwargs}", f'python_callable_{func_name}'
            except Exception as e:  # pylint: disable=broad-except
                print(f"DEBUG: Error loading DAG: {e}")
        
        print(f"DEBUG: No python_callable found")
        return None, None

    elif operator_type in ['emr', 'emr_serverless']:
        # EMR steps or EMR Serverless job_driver - show configuration as fallback
        steps = params.get('steps') or params.get('step_config')
        job_driver = params.get('job_driver')
        
        if steps:
            import json
            step_info = json.dumps(steps, indent=2)
            return f"# EMR Step Configuration\n\n{step_info}", 'emr_step_config'
        elif job_driver:
            import json
            job_info = json.dumps(job_driver, indent=2)
            return f"# EMR Serverless Job Configuration\n\n{job_info}", 'emr_serverless_config'

    elif operator_type == 'dbt':
        # DBT models/commands
        models = params.get('models')
        select = params.get('select')
        if models or select:
            return f"DBT models: {models or select}", 'dbt_models'

    return None, None


def sanitize_script(script: str) -> str:
    """Remove sensitive information from script"""
    patterns = [
        (r'password\s*=\s*["\'][^"\']+["\']', 'password="<REDACTED>"'),
        (r'secret\s*=\s*["\'][^"\']+["\']', 'secret="<REDACTED>"'),
        (r'token\s*=\s*["\'][^"\']+["\']', 'token="<REDACTED>"'),
        (r'api_key\s*=\s*["\'][^"\']+["\']', 'api_key="<REDACTED>"'),
        (r'aws_access_key_id\s*=\s*["\'][^"\']+["\']', 'aws_access_key_id="<REDACTED>"'),
        (r'aws_secret_access_key\s*=\s*["\'][^"\']+["\']', 'aws_secret_access_key="<REDACTED>"'),
    ]

    sanitized = script
    for pattern, replacement in patterns:
        sanitized = re.sub(pattern, replacement, sanitized, flags=re.IGNORECASE)

    return sanitized


def truncate_script(script: str, max_tokens: int = MAX_TOKENS['script']) -> Tuple[str, bool]:
    """Intelligently truncate script"""
    if len(script) <= max_tokens:
        return script, False

    # Keep beginning and end
    keep_start = int(max_tokens * 0.3)
    keep_end = int(max_tokens * 0.7)

    truncated = (
        script[:keep_start] +
        '\n\n# ... [TRUNCATED FOR TOKEN LIMIT] ...\n\n' +
        script[-keep_end:]
    )

    return truncated, True


def process_operator_script(
    operator_type: str,
    params: Dict,
    logs: str,
    error_msg: str,
    *,  # Force keyword-only arguments after this
    aws_access_key: str,
    aws_secret_key: str,
    region: str = 'us-east-1'
) -> Optional[Dict]:
    """
    Main function to fetch and process operator scripts

    Returns:
        Dict with script info or None
    """
    # Check if we should fetch
    if not should_fetch_script(logs, error_msg, operator_type):
        print(f"DEBUG: Skipping script fetch for {operator_type} - not relevant")
        return None

    print(f"DEBUG: Attempting to fetch script for {operator_type}")

    script = None
    location = None

    # Try to fetch script based on operator type
    if operator_type == 'glue':
        job_name = params.get('job_name')
        if job_name:
            script, location = fetch_glue_script(job_name, aws_access_key, aws_secret_key, region)

    elif operator_type in ['emr', 'emr_serverless']:
        steps = params.get('steps') or params.get('step_config')
        job_driver = params.get('job_driver')
        
        print(f"DEBUG: EMR params keys: {list(params.keys())}")
        print(f"DEBUG: EMR steps value: {steps}")
        print(f"DEBUG: EMR job_driver value: {job_driver}")
        
        if steps and isinstance(steps, list) and len(steps) > 0:
            script, location = fetch_emr_script(steps[0], aws_access_key, aws_secret_key, region)
        elif job_driver:
            # EMR Serverless uses job_driver
            script, location = fetch_emr_serverless_script(job_driver, aws_access_key, aws_secret_key, region)

    # If no external script, try inline
    if not script:
        print(f"DEBUG: Trying inline script extraction for {operator_type}")
        script, location = extract_inline_script(operator_type, params)
        print(f"DEBUG: Inline script extracted: {bool(script)}, location: {location}")

    if not script:
        print(f"DEBUG: No script found for {operator_type}")
        return None

    print(f"DEBUG: Script found, size: {len(script)} bytes")

    # Sanitize and truncate
    script = sanitize_script(script)
    truncated_script, was_truncated = truncate_script(script)

    # Determine script type label
    type_labels = {
        'glue': 'AWS Glue Job',
        'emr': 'EMR Script',
        'emr_serverless': 'EMR Serverless Script',
        'athena': 'Athena Query',
        'redshift': 'Redshift Query',
        'bash': 'Bash Script',
        'python': 'Python Code',
        'dbt': 'DBT Models'
    }

    return {
        'content': truncated_script,
        'location': location,
        'operator_type': operator_type,
        'type_label': type_labels.get(operator_type, 'Script'),
        'original_size': len(script),
        'truncated_size': len(truncated_script),
        'was_truncated': was_truncated,
        'size_kb': round(len(truncated_script) / 1024, 2)
    }
