"""
    Airflow Plugin to provide a FastAPI application for analyzing task instances.
    Serves HTML, CSS, and JavaScript files for the frontend interface.
"""
import json
from pathlib import Path

import boto3

from airflow.hooks.base import BaseHook  # pylint: disable=no-name-in-module
from airflow.plugins_manager import AirflowPlugin
from fastapi import FastAPI
from fastapi.responses import HTMLResponse, FileResponse, JSONResponse

# pylint: disable=import-error,no-name-in-module
from task_analyzer.prompts import (
    BEDROCK_CONFIG,
    BEDROCK_MODELS,
    PROMPTS,
    build_bedrock_payload
)
from task_analyzer.script_utils import (
    extract_operator_info,
    process_operator_script
)


def fetch_and_add_operator_script(data: dict, conn, logs: str) -> tuple:
    """
    Common function to fetch operator script and add to data dict.
    Returns (script_info, operator_type, params) tuple.
    """
    script_info = None
    operator_type = None
    params = None

    try:
        context_dict = json.loads(data['context']) if isinstance(
            data['context'], str) else data['context']
        operator_type, params = extract_operator_info(context_dict)

        if operator_type and params:
            script_info = process_operator_script(
                operator_type=operator_type,
                params=params,
                logs=logs,
                error_msg=data['error'],
                aws_access_key=conn.login,
                aws_secret_key=conn.password,
                region=conn.extra_dejson.get('region_name', 'us-east-1')
            )

            if script_info:
                data['operator_script'] = script_info['content']
                data['operator_script_location'] = script_info['location']
                data['operator_script_size_kb'] = script_info['size_kb']
                data['operator_script_truncated'] = script_info['was_truncated']
                data['operator_type'] = script_info['type_label']
    except Exception as script_err:  # pylint: disable=broad-except
        print(f"Warning: Could not fetch operator script: {script_err}")

    return script_info, operator_type, params

app = FastAPI()

# Get the directory where this plugin file is located
PLUGIN_DIR = Path(__file__).parent / "task_analyzer"


@app.get("/", response_class=HTMLResponse)
def task_analyzer():
    """Serve the main HTML template"""
    template_path = PLUGIN_DIR / "templates" / "index.html"
    with open(template_path, "r", encoding="utf-8") as f:
        return f.read()


@app.get("/static/css/styles.css")
def get_css():
    """Serve CSS file"""
    css_path = PLUGIN_DIR / "static" / "css" / "styles.css"
    return FileResponse(css_path, media_type="text/css")


@app.get("/static/js/config.js")
def get_config_js():
    """Serve config JavaScript file"""
    config_path = PLUGIN_DIR / "static" / "js" / "config.js"
    return FileResponse(config_path, media_type="application/javascript")


@app.get("/static/js/app.jsx")
def get_js():
    """Serve JavaScript file"""
    js_path = PLUGIN_DIR / "static" / "js" / "app.jsx"
    return FileResponse(js_path, media_type="application/javascript")


@app.get("/static/js/utils.jsx")
def get_utils_js():
    """Serve utilities JavaScript file"""
    js_path = PLUGIN_DIR / "static" / "js" / "utils.jsx"
    return FileResponse(js_path, media_type="application/javascript")


@app.get("/static/js/components.jsx")
def get_components_js():
    """Serve components JavaScript file"""
    js_path = PLUGIN_DIR / "static" / "js" / "components.jsx"
    return FileResponse(js_path, media_type="application/javascript")


@app.get("/static/js/template.jsx")
def get_template_js():
    """Serve template JavaScript file"""
    js_path = PLUGIN_DIR / "static" / "js" / "template.jsx"
    return FileResponse(js_path, media_type="application/javascript")


@app.get("/api/test-aws")
def test_aws():
    """Test AWS connection by listing S3 bucket contents"""
    try:
        conn = BaseHook.get_connection('aws_default')
        s3_client = boto3.client(
            's3',
            aws_access_key_id=conn.login,
            aws_secret_access_key=conn.password,
            region_name=conn.extra_dejson.get('region_name', 'us-east-1')
        )

        bucket_name = 'cdk-bms-test-common-bucket-189468857953'
        response = s3_client.list_objects_v2(Bucket=bucket_name, MaxKeys=10)

        objects = []
        if 'Contents' in response:
            for obj in response['Contents']:
                objects.append({
                    'key': obj['Key'],
                    'size': obj['Size'],
                    'last_modified': obj['LastModified'].isoformat()
                })

        return JSONResponse({
            'success': True,
            'bucket': bucket_name,
            'objects': objects,
            'count': len(objects)
        })
    except Exception as e:  # pylint: disable=broad-except
        return JSONResponse(
            status_code=500,
            content={'success': False, 'error': str(e), 'error_type': type(e).__name__}
        )


@app.get("/api/models")
def get_models():
    """Get available Bedrock models"""
    models = [{"key": key, "name": config["name"]} for key, config in BEDROCK_MODELS.items()]
    return JSONResponse({"models": models, "default": BEDROCK_CONFIG['default_model']})


@app.post("/api/analyze-task")
async def analyze_task(request: dict):  # pylint: disable=too-many-locals
    """Analyze task failure using Bedrock"""
    try:
        conn = BaseHook.get_connection('aws_default')
        bedrock_client = boto3.client(
            'bedrock-runtime',
            aws_access_key_id=conn.login,
            aws_secret_access_key=conn.password,
            region_name=conn.extra_dejson.get('region_name', 'us-east-1')
        )

        dag_code = request.get('dag_code') or 'Not provided'
        logs = request.get('logs') or 'Not provided'

        # Handle both string and list types
        if isinstance(dag_code, str):
            code_lines = (
                len(dag_code.split('\n')) if dag_code != 'Not provided' else 0
            )
        else:
            code_lines = 0

        if isinstance(logs, str):
            log_size_kb = (
                round(len(logs.encode('utf-8')) / 1024, 2)
                if logs != 'Not provided' else 0
            )
        else:
            log_size_kb = 0

        data = {
            'dag_id': request.get('dag_id'),
            'task_id': request.get('task_id'),
            'run_id': request.get('run_id'),
            'state': request.get('state'),
            'error': request.get('error') or 'No error message available',
            'context': request.get('context') or 'Not provided',
            'dag_code': dag_code,
            'logs': logs
        }

        # Try to fetch operator script if applicable
        script_info, operator_type, params = fetch_and_add_operator_script(
            data, conn, logs
        )

        model_key = request.get('model') or BEDROCK_CONFIG['default_model']
        model_name = BEDROCK_MODELS[model_key]['name']

        prompt_content = PROMPTS['task_analysis'](data)['content']
        # pylint: disable=too-many-function-args
        bedrock_payload = build_bedrock_payload(
            'task_analysis', model_key, data
        )

        response = bedrock_client.invoke_model(
            modelId=bedrock_payload['model_id'],
            body=json.dumps(bedrock_payload['payload'])
        )

        result = json.loads(response['body'].read())
        analysis = result['content'][0]['text']

        response_data = {
            'success': True,
            'analysis': analysis,
            'model_used': model_name,
            'model_key': model_key,
            'prompt': prompt_content,
            'metrics': {
                'code_lines': code_lines,
                'log_size_kb': log_size_kb
            }
        }

        # Add operator script metrics if available
        if script_info:
            response_data['metrics']['operator_script_kb'] = script_info['size_kb']
            response_data['metrics']['operator_script_truncated'] = script_info['was_truncated']
            response_data['operator_type'] = script_info['type_label']
            response_data['operator_name'] = params.get('job_name') or params.get('query_execution_id') or operator_type

        return JSONResponse(response_data)
    except Exception as e:  # pylint: disable=broad-except
        return JSONResponse(
            status_code=500,
            content={'success': False, 'error': str(e), 'error_type': type(e).__name__}
        )


class TaskAnalyzerPlugin(AirflowPlugin):  # pylint: disable=too-few-public-methods
    """Airflow Plugin for Task Analyzer
    """
    name = "task_analyzer_plugin"
    fastapi_apps = [
        {
            "app": app,
            "url_prefix": "/task-analyzer",
            "name": "Task Analyzer",
        }
    ]
    external_views = [
        {
            "name": "Analyze Task",
            "href": "/task-analyzer/",
            "url_route": "task_analyzer_view",
            "destination": "task_instance",
        }
    ]
