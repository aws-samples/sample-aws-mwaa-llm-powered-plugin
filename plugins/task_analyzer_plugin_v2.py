"""
    Airflow Plugin for Task Analyzer - Airflow 2.x Compatible Version
    Uses Flask Blueprint instead of FastAPI for compatibility with Airflow 2.x
"""
import json
from pathlib import Path

import boto3

from airflow.hooks.base import BaseHook
from airflow.plugins_manager import AirflowPlugin
from flask import Blueprint, send_from_directory, jsonify, request
from flask_appbuilder import expose, BaseView as AppBuilderBaseView

# pylint: disable=import-error,no-name-in-module
from task_analyzer.prompts import (
    BEDROCK_CONFIG,
    BEDROCK_MODELS,
    PROMPTS,
    build_bedrock_payload
)

# Get the directory where this plugin file is located
PLUGIN_DIR = Path(__file__).parent / "task_analyzer"

# Create Flask Blueprint
task_analyzer_bp = Blueprint(
    "task_analyzer",
    __name__,
    template_folder=str(PLUGIN_DIR / "templates"),
    static_folder=str(PLUGIN_DIR / "static"),
    static_url_path="/task-analyzer/static"
)


@task_analyzer_bp.route("/", methods=["GET"])
def task_analyzer():
    """Serve the main HTML template with optional pre-filled parameters"""
    # Get query parameters for pre-filling the form
    dag_id = request.args.get('dag_id', '')
    task_id = request.args.get('task_id', '')
    run_id = request.args.get('run_id', '')
    
    template_path = PLUGIN_DIR / "templates" / "index.html"
    with open(template_path, "r", encoding="utf-8") as file:
        html_content = file.read()
        # Inject parameters into the HTML if provided
        if dag_id or task_id or run_id:
            params_script = f"""
            <script>
                window.PREFILL_PARAMS = {{
                    dagId: '{dag_id}',
                    taskId: '{task_id}',
                    runId: '{run_id}'
                }};
            </script>
            """
            html_content = html_content.replace('</head>', f'{params_script}</head>')
        return html_content


@task_analyzer_bp.route("/static/css/styles.css", methods=["GET"])
def get_css():
    """Serve CSS file"""
    return send_from_directory(
        PLUGIN_DIR / "static" / "css",
        "styles.css",
        mimetype="text/css"
    )


@task_analyzer_bp.route("/static/js/config.js", methods=["GET"])
def get_config_js():
    """Serve config JavaScript file"""
    return send_from_directory(
        PLUGIN_DIR / "static" / "js",
        "config.js",
        mimetype="application/javascript"
    )


@task_analyzer_bp.route("/static/js/app.jsx", methods=["GET"])
def get_js():
    """Serve JavaScript file"""
    return send_from_directory(
        PLUGIN_DIR / "static" / "js",
        "app.jsx",
        mimetype="application/javascript"
    )


@task_analyzer_bp.route("/static/js/utils.jsx", methods=["GET"])
def get_utils_js():
    """Serve utilities JavaScript file"""
    return send_from_directory(
        PLUGIN_DIR / "static" / "js",
        "utils.jsx",
        mimetype="application/javascript"
    )


@task_analyzer_bp.route("/static/js/components.jsx", methods=["GET"])
def get_components_js():
    """Serve components JavaScript file"""
    return send_from_directory(
        PLUGIN_DIR / "static" / "js",
        "components.jsx",
        mimetype="application/javascript"
    )


@task_analyzer_bp.route("/static/js/template.jsx", methods=["GET"])
def get_template_js():
    """Serve template JavaScript file"""
    return send_from_directory(
        PLUGIN_DIR / "static" / "js",
        "template.jsx",
        mimetype="application/javascript"
    )


@task_analyzer_bp.route("/api/test-aws", methods=["GET"])
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

        return jsonify({
            'success': True,
            'bucket': bucket_name,
            'objects': objects,
            'count': len(objects)
        })
    except Exception as err:  # pylint: disable=broad-except
        return jsonify({
            'success': False,
            'error': str(err),
            'error_type': type(err).__name__
        }), 500


@task_analyzer_bp.route("/api/models", methods=["GET"])
def get_models():
    """Get available Bedrock models"""
    models = [{
        "key": key,
        "name": config["name"]
    } for key, config in BEDROCK_MODELS.items()]
    return jsonify({
        "models": models,
        "default": BEDROCK_CONFIG['default_model']
    })


@task_analyzer_bp.route("/api/analyze-task", methods=["POST"])
def analyze_task():  # pylint: disable=too-many-locals
    """Analyze task failure using Bedrock"""
    try:
        request_data = request.get_json()

        conn = BaseHook.get_connection('aws_default')
        bedrock_client = boto3.client(
            'bedrock-runtime',
            aws_access_key_id=conn.login,
            aws_secret_access_key=conn.password,
            region_name=conn.extra_dejson.get('region_name', 'us-east-1')
        )

        dag_code = request_data.get('dag_code') or 'Not provided'
        logs = request_data.get('logs') or 'Not provided'

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
            'dag_id': request_data.get('dag_id'),
            'task_id': request_data.get('task_id'),
            'run_id': request_data.get('run_id'),
            'state': request_data.get('state'),
            'error': request_data.get('error') or 'No error message available',
            'context': request_data.get('context') or 'Not provided',
            'dag_code': dag_code,
            'logs': logs
        }

        model_key = request_data.get('model') or BEDROCK_CONFIG['default_model']
        model_name = BEDROCK_MODELS[model_key]['name']

        prompt_content = PROMPTS['task_analysis'](data)['content']
        bedrock_payload = build_bedrock_payload(
            'task_analysis', model_key, data
        )

        response = bedrock_client.invoke_model(
            modelId=bedrock_payload['model_id'],
            body=json.dumps(bedrock_payload['payload'])
        )

        result = json.loads(response['body'].read())
        analysis = result['content'][0]['text']

        return jsonify({
            'success': True,
            'analysis': analysis,
            'model_used': model_name,
            'model_key': model_key,
            'prompt': prompt_content,
            'metrics': {'code_lines': code_lines, 'log_size_kb': log_size_kb}
        })
    except Exception as err:  # pylint: disable=broad-except
        return jsonify({
            'success': False,
            'error': str(err),
            'error_type': type(err).__name__
        }), 500


class TaskAnalyzerView(AppBuilderBaseView):
    """AppBuilder view for Task Analyzer"""
    default_view = "index"
    route_base = "/task-analyzer"

    @expose("/")
    def index(self):
        """Render the task analyzer page"""
        template_path = PLUGIN_DIR / "templates" / "index.html"
        with open(template_path, "r", encoding="utf-8") as file:
            return file.read()


class TaskAnalyzerPluginV2(AirflowPlugin):  # pylint: disable=too-few-public-methods
    """Airflow Plugin for Task Analyzer - Airflow 2.x Compatible"""
    name = "task_analyzer_plugin_v2"
    flask_blueprints = [task_analyzer_bp]
    appbuilder_views = [
        {
            "name": "Analyze Task",
            "category": "Browse",
            "view": TaskAnalyzerView()
        }
    ]
