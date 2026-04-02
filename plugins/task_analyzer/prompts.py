"""Bedrock prompts configuration for Task Analyzer"""
from airflow.models import Variable

def get_model_id(var_name, default_value):
    """Get model ID from Airflow Variable or use default"""
    try:
        return Variable.get(var_name, default_var=default_value)
    except Exception:  # pylint: disable=broad-except
        return default_value

# Model IDs - can be overridden via Airflow Variables:
# - bedrock_sonnet_4_6_model_id
# - bedrock_opus_4_6_model_id
# - bedrock_sonnet_4_5_model_id
# - bedrock_sonnet_3_5_model_id
BEDROCK_MODELS = {
    'claude-sonnet-4.6': {
        'model_id': get_model_id(
            'bedrock_sonnet_4_6_model_id',
            'us.anthropic.claude-sonnet-4-6'
        ),
        'name': 'Claude Sonnet 4.6',
        'max_tokens': 8192
    },
    'claude-opus-4.6': {
        'model_id': get_model_id(
            'bedrock_opus_4_6_model_id',
            'us.anthropic.claude-opus-4-6-v1'
        ),
        'name': 'Claude Opus 4.6',
        'max_tokens': 8192
    },
    'claude-sonnet-4.5': {
        'model_id': get_model_id(
            'bedrock_sonnet_4_5_model_id',
            'us.anthropic.claude-sonnet-4-5-20250929-v1:0'
        ),
        'name': 'Claude Sonnet 4.5',
        'max_tokens': 8192
    },
    'claude-3.5-sonnet': {
        'model_id': get_model_id(
            'bedrock_sonnet_3_5_model_id',
            'us.anthropic.claude-3-5-sonnet-20241022-v2:0'
        ),
        'name': 'Claude Sonnet 3.5',
        'max_tokens': 8192
    }
}

BEDROCK_CONFIG = {
    'anthropic_version': 'bedrock-2023-05-31',
    'default_model': get_model_id('bedrock_default_model', 'claude-3.5-sonnet'),
    'guardrail_id': get_model_id('bedrock_guardrail_id', ''),
    'guardrail_version': get_model_id('bedrock_guardrail_version', 'DRAFT'),
}

PROMPTS = {
    'task_analysis': lambda data: {
        'role': 'user',
        'content': f"""
You are an expert Apache Airflow engineer specializing in debugging and root cause analysis.
Analyze the following failed Airflow task and provide a comprehensive diagnostic report.

## Task Information
- **DAG ID**: {data.get('dag_id', 'N/A')}
- **Task ID**: {data.get('task_id', 'N/A')}
- **Run ID**: {data.get('run_id', 'N/A')}
- **State**: {data.get('state', 'N/A')}
- **Error Message**: {data.get('error', 'No error message available')}

## Task Context
```json
{data.get('context', 'Not provided')}
```

## DAG Source Code
```python
{data.get('dag_code', 'Not provided')}
```

## Task Execution Logs
```
{data.get('logs', 'Not provided')}
```

{f'''## {data.get('operator_type', 'Operator')} Script
**Operator Type**: {data.get('operator_type', 'Unknown')}
**Script Location**: {data.get('operator_script_location', 'N/A')}
**Script Size**: {data.get('operator_script_size_kb', 0)} KB
{"**Note**: Script was truncated to fit token limits" if data.get('operator_script_truncated') else ""}

```
{data.get('operator_script', 'Not available')}
```

**Analysis Context**: This is a {data.get('operator_type', 'data processing')} script. Consider operator-specific best practices, common pitfalls, and error patterns when analyzing the failure.
''' if data.get('operator_script') else ''}

## Analysis Requirements

Provide a detailed analysis with the following sections:

### 🔍 ROOT CAUSE
Provide a clear explanation of what caused the failure, including:
- The specific error and why it occurred
- The failure category (Configuration Error, Dependency Issue, Resource Problem, Code Bug, External Service Failure, etc.)
- The exact location where the error occurred (file, line number, component)

### ✅ RESOLUTION
Provide step-by-step instructions to fix this specific failure:
- Immediate actions to resolve the issue
- Specific code changes needed (with examples)
- Configuration changes required
- Estimated fix time and severity level

### 📋 ADDITIONAL DETAILS
Provide supplementary information:
- Preventive measures to avoid this issue in the future
- Code improvements and best practices
- Monitoring recommendations and alerts to add
- Related issues that might need attention

## Guidelines
- Focus on actionable insights, not generic advice
- Reference specific log lines, error messages, or code snippets
- Prioritize the most likely root cause based on evidence
- Consider Airflow best practices and common pitfalls
- If logs are truncated, note what additional information would help
- Provide code examples for fixes when applicable
- For Glue jobs: Reference specific lines in the Glue script when available
"""
    }
}


def build_bedrock_payload(prompt_key, model_key=None, data=None):
    """Build Bedrock API payload from prompt configuration"""
    prompt_template = PROMPTS.get(prompt_key)
    if not prompt_template:
        raise ValueError(f"Prompt '{prompt_key}' not found")

    # Get prompt content
    if callable(prompt_template):
        if not data:
            raise ValueError(f"Prompt '{prompt_key}' requires data parameter")
        prompt = prompt_template(data)
    else:
        prompt = prompt_template

    # Get model configuration
    model_key = model_key or BEDROCK_CONFIG['default_model']
    model_config = BEDROCK_MODELS.get(model_key)
    if not model_config:
        raise ValueError(f"Model '{model_key}' not found")

    result = {
        'model_id': model_config['model_id'],
        'payload': {
            'anthropic_version': BEDROCK_CONFIG['anthropic_version'],
            'max_tokens': model_config['max_tokens'],
            'messages': [prompt]
        }
    }

    if BEDROCK_CONFIG['guardrail_id']:
        result['guardrail_id'] = BEDROCK_CONFIG['guardrail_id']
        result['guardrail_version'] = BEDROCK_CONFIG['guardrail_version']

    return result
