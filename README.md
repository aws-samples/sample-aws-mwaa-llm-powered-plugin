# Task Analyzer Plugin

AI-powered Airflow task failure analyzer for **Apache Airflow 3.x** (FastAPI plugin interface), including Amazon MWAA.

## Table of Contents
- [Quick Start](#quick-start)
- [Features](#features)
- [Supported Operators](#supported-operators)
- [Installation](#installation)
- [Technical Details](#technical-details)
- [Troubleshooting](#troubleshooting)
- [Requirements](#requirements)

---

## Quick Start

1. Place the plugin in your Airflow `plugins/` directory (or package it as `plugins.zip` for Amazon MWAA):
   ```
   plugins/
   ├── task_analyzer_plugin.py
   └── task_analyzer/
   ```
2. Ensure an `aws_default` connection with Bedrock access exists (on Amazon MWAA this maps to the execution role by default).
3. Restart Airflow (or update your MWAA environment).
4. Open: http://localhost:8080/task-analyzer/ (local) or the **Analyze Task** view on a task instance.

---

## Architecture

![Architecture Overview](diagrams/01_architecture_overview.png)

## Features

- 🤖 AI-powered task failure analysis using AWS Bedrock
- 🔍 Root cause identification with detailed explanations
- 💡 Actionable fix recommendations
- 📊 Multiple Claude model support (Sonnet 3.5, 4.5, 4.6, Opus 4.6)
- ⚡ Built on the FastAPI plugin interface (Apache Airflow 3.x)
- 📝 Comprehensive DAG context analysis
- 🔗 Direct integration with the Airflow UI
- 🗺️ **Full support for dynamically mapped tasks**
- ⚙️ **Multi-operator script analysis** - Automatically fetches and analyzes scripts from:
  - AWS Glue jobs (from S3)
  - EMR steps (from S3)
  - Athena queries (inline SQL)
  - Redshift queries (inline SQL)
  - Bash commands (inline)
  - Python callables (function names)
  - DBT models (model names)

---

## Supported Operators

![Multi-Operator Script Analysis](diagrams/02_multi_operator_analysis.png)

The plugin automatically detects and analyzes scripts from various operators:

| Operator | Script Source | What's Analyzed | Button Label |
|----------|--------------|-----------------|--------------|
| **GlueJobOperator** | S3 (fetched via Glue API) | Full Python/Scala script | Show AWS Glue Job |
| **EmrAddStepsOperator** | S3 (from step args) | Full PySpark/Spark script | Show EMR Step |
| **EmrServerlessStartJobOperator** | S3 (from job config) | Full application script | Show EMR Serverless Job |
| **AthenaOperator** | Inline (from query param) | Complete SQL query | Show Athena Query |
| **RedshiftDataOperator** | Inline (from sql param) | Complete SQL query | Show Redshift Query |
| **BashOperator** | Inline (from bash_command) | Full bash command | Show Bash Script |
| **PythonOperator** | Inline (function name only) | Callable name + DAG code | Show Python Code |
| **DbtRunOperator** | Inline (from models/select) | Model names | Show DBT Models |

### How It Works

**1. Automatic Detection**
- Plugin reads task context from the Airflow API
- Identifies operator type from task metadata
- Determines if script analysis would be valuable

**2. Script Fetching**

**External Scripts (Glue, EMR):**
```python
# Fetches from AWS
glue_client.get_job(JobName='MyJob')  # Get S3 location
s3_client.get_object(Bucket=bucket, Key=key)  # Download script
```

**Inline Scripts (Bash, SQL):**
```python
# Extracted from rendered_fields
bash_command = context['rendered_fields']['bash_command']
sql_query = context['rendered_fields']['query']
```

**3. Smart Processing**
- Sanitizes credentials (passwords, tokens, keys)
- Truncates large scripts (max 20KB)
- For join/broadcast errors: extracts relevant code sections
- Adds operator-specific context to the LLM prompt

**4. Enhanced Analysis**

The LLM receives:
```
- Task information (DAG, task ID, state)
- Full execution logs
- DAG source code
- Operator-specific script (with type context)
- Error messages and stack traces
```

### Script Analysis Benefits

**For Code Errors (Syntax, Logic):**
- ⭐⭐⭐⭐⭐ Glue/EMR scripts - See exact error line
- ⭐⭐⭐⭐⭐ SQL queries - Identify syntax/logic issues
- ⭐⭐⭐⭐⭐ Bash commands - Understand command failures

**For Join/Broadcast Failures:**
- ⭐⭐⭐⭐⭐ Glue/EMR - See join conditions, data types
- ⭐⭐⭐⭐⭐ Athena/Redshift - Analyze SQL joins

**For Infrastructure Issues:**
- ⭐⭐ Less valuable (script won't help with memory/timeout)

### Configuration

**Required AWS Permissions:**

For Glue script fetching:
```json
{
  "Effect": "Allow",
  "Action": ["glue:GetJob"],
  "Resource": "arn:aws:glue:*:*:job/*"
}
```

For S3 script fetching:
```json
{
  "Effect": "Allow",
  "Action": ["s3:GetObject"],
  "Resource": "arn:aws:s3:::your-scripts-bucket/*"
}
```

**No configuration needed** - Works automatically for all supported operators!

---

## Installation

### Prerequisites
- Apache Airflow 3.x (including Amazon MWAA 3.x)
- AWS credentials with Bedrock access
- `aws_default` connection configured in Airflow (on Amazon MWAA this resolves to the execution role)

> **Note:** `fastapi` and `boto3` are already installed on Airflow 3.x (`fastapi` is a dependency of `apache-airflow-core`, and `boto3` of `apache-airflow-providers-amazon`), so no extra `requirements.txt` is needed for this plugin.

### Setup Steps

1. **Place plugin files in your Airflow plugins directory**
   ```bash
   # Files should be in: <airflow_home>/plugins/
   task_analyzer_plugin.py
   task_analyzer/
   ```
   For Amazon MWAA, package these into `plugins.zip` (files at the root of the archive) and upload it to your environment's S3 bucket.

2. **Configure AWS connection**
   - Create or reuse the `aws_default` connection in the Airflow UI
   - On Amazon MWAA, leave credentials empty to use the execution role; set region in **Extra** (e.g. `{"region_name": "us-east-1"}`)

3. **(Optional) Configure Bedrock Models**

   The plugin supports the following Claude models with configurable model IDs via Airflow Variables.

   **Default Model IDs (US Region):**

   If no variables are set, these defaults are used:

   | Model | Default Model ID | Variable Name |
   |-------|-----------------|---------------|
   | Claude Sonnet 4.6 | `us.anthropic.claude-sonnet-4-6` | `bedrock_sonnet_4_6_model_id` |
   | Claude Opus 4.6 | `us.anthropic.claude-opus-4-6-v1` | `bedrock_opus_4_6_model_id` |
   | Claude Sonnet 4.5 | `us.anthropic.claude-sonnet-4-5-20250929-v1:0` | `bedrock_sonnet_4_5_model_id` |
   | Claude Sonnet 3.5 | `us.anthropic.claude-3-5-sonnet-20241022-v2:0` | `bedrock_sonnet_3_5_model_id` |
   | Default Model | `claude-3.5-sonnet` | `bedrock_default_model` |

   **How to Override for Different Regions:**

   **Option 1: Via Airflow UI** (Admin → Variables)

   Add variables to override specific models:
   ```
   Key: bedrock_sonnet_4_6_model_id
   Value: eu.anthropic.claude-sonnet-4-6

   Key: bedrock_default_model
   Value: claude-sonnet-4.5
   ```

   **Option 2: Via airflow_settings.yaml** (local development)
   ```yaml
   airflow:
     variables:
       - variable_name: bedrock_sonnet_4_6_model_id
         variable_value: eu.anthropic.claude-sonnet-4-6
       - variable_name: bedrock_opus_4_6_model_id
         variable_value: eu.anthropic.claude-opus-4-6-v1
       - variable_name: bedrock_default_model
         variable_value: claude-sonnet-4.6
   ```

   **Region-Specific Examples:**

   **EU Region:**
   ```
   bedrock_sonnet_4_6_model_id = eu.anthropic.claude-sonnet-4-6
   bedrock_opus_4_6_model_id = eu.anthropic.claude-opus-4-6-v1
   bedrock_sonnet_4_5_model_id = eu.anthropic.claude-sonnet-4-5-20250929-v1:0
   bedrock_sonnet_3_5_model_id = eu.anthropic.claude-3-5-sonnet-20241022-v2:0
   ```

   **Global Inference Profiles:**
   ```
   bedrock_sonnet_4_6_model_id = global.anthropic.claude-sonnet-4-6
   bedrock_opus_4_6_model_id = global.anthropic.claude-opus-4-6-v1
   ```

   **AP Region:**
   ```
   bedrock_sonnet_4_6_model_id = ap.anthropic.claude-sonnet-4-6
   ```

   **Note**: Only set variables for models you want to override. Unset variables use the US region defaults.

4. **Restart Airflow**
   ```bash
   astro dev restart              # Astro CLI
   docker-compose restart         # MWAA Local
   systemctl restart airflow      # Standard Airflow
   ```
   For Amazon MWAA, run `aws mwaa update-environment --name <env> --plugins-s3-path plugins.zip --plugins-s3-object-version <version>`.

5. **Verify installation**
   - Check the Airflow UI for the **Analyze Task** view on a task instance
   - Navigate to http://localhost:8080/task-analyzer/
   - Review logs for any errors

---

## Technical Details

### Mapped Task Support

The plugin **automatically detects and handles both mapped and non-mapped tasks** without any configuration.

#### How It Works

**1. Task Detection**
- Extracts task information from the Airflow UI URL path
- Detects mapped tasks by looking for `/mapped/{index}/` in the URL
- Fetches task instance data from the Airflow API
- Uses the `map_index` field from the API response

**2. Dynamic URL Construction**

**Non-Mapped Tasks:**
```
Task Context: /api/v2/dags/{dagId}/dagRuns/{runId}/taskInstances/{taskId}
Logs:         /api/v2/dags/{dagId}/dagRuns/{runId}/taskInstances/{taskId}/logs/{tryNumber}
```

**Mapped Tasks:**
```
Task Context: /api/v2/dags/{dagId}/dagRuns/{runId}/taskInstances/{taskId}/{mapIndex}
Logs:         /api/v2/dags/{dagId}/dagRuns/{runId}/taskInstances/{taskId}/logs/{tryNumber}?map_index={mapIndex}
```

**3. Key Features**
- ✅ No hardcoded DAG names, task IDs, or map indices
- ✅ Works with ANY DAG and ANY task
- ✅ Automatic detection from URL and API response
- ✅ Handles task retries using the actual `try_number` from context
- ✅ Validates `map_index >= 0` before adding to URLs

**4. Example Usage**

```python
# DAG with dynamic task mapping
@dag()
def my_dag():
    @task
    def process_number(num):
        if num == 2:
            raise ValueError("Intentional failure")
        return num * 2

    # Creates mapped tasks: process_number[0], process_number[1], process_number[2]...
    process_number.expand(num=[0, 1, 2, 3, 4, 5])
```

When `process_number[2]` fails:
- Plugin detects `map_index=2` from URL or API
- Fetches logs: `/taskInstances/process_number/logs/1?map_index=2`
- Displays context for that specific mapped instance
- LLM analyzes the specific failure with full context

**5. Configuration**

All API endpoints are configured in `config.js`:
```javascript
CONFIG.API.ENDPOINTS = {
    TASK_INSTANCE: '/dags/{dagId}/dagRuns/{runId}/taskInstances/{taskId}',
    LOGS: '/dags/{dagId}/dagRuns/{runId}/taskInstances/{taskId}/logs/{tryNumber}',
    DAG_SOURCE: '/dagSources/{dagId}'
}
```

The plugin dynamically modifies these URLs based on whether the task is mapped or not.

### Multi-Operator Script Integration

The plugin **automatically fetches and analyzes scripts from multiple operator types**. See [Supported Operators](#supported-operators) above for the complete list.

#### Smart Detection

**When Scripts ARE Fetched:**
- ✅ Always for inline scripts (Bash, SQL, Python)
- ✅ For external scripts (Glue, EMR) when the error suggests a code issue:
  - Syntax errors, type errors, value errors
  - Join failures, broadcast failures
  - Import errors, key errors

**When Scripts are NOT Fetched:**
- ❌ Infrastructure failures (out of memory, timeout)
- ❌ Permission errors (IAM issues)
- ❌ Resource constraints (DPU limits, network issues)

#### Script Processing

**1. Automatic Detection**
```python
# Works with any supported operator - no changes needed!
run_glue_job = GlueJobOperator(task_id="glue", job_name="MyJob")
run_query = AthenaOperator(task_id="athena", query="SELECT * FROM table")
run_bash = BashOperator(task_id="bash", bash_command="exit 1")
```

**2. Intelligent Fetching**
- **External scripts**: Fetches from S3 via AWS APIs
- **Inline scripts**: Extracts from the task's rendered_fields
- Sanitizes credentials automatically
- Truncates to fit token limits (20KB max)

**3. Operator-Specific Context**

The LLM knows what type of script it's analyzing:
```
## Bash Script
**Operator Type**: Bash Script
**Analysis Context**: This is a Bash Script. Consider operator-specific
best practices, common pitfalls, and error patterns.
```

**4. Enhanced Analysis**

LLM receives complete context:
- DAG source code
- Task execution logs
- Task metadata
- **Operator-specific script with type information**
- Script location (S3 path or "inline")

#### Token Usage

![What the LLM Receives](diagrams/04_llm_context_convergence.png)

**Typical Case:**
- DAG code: ~500 tokens
- Task context: ~1,000 tokens
- Airflow logs: ~10,000 tokens
- Operator script: ~5,000-15,000 tokens
- **Total: ~16,500-26,500 tokens (8-13% of 200K limit)**

**Worst Case:**
- All components at max size
- **Total: ~74,200 tokens (37% of 200K limit)**

**Risk of hitting limit:** <1%

### Plugin Registration (FastAPI)

Airflow 3.x registers the plugin's web component through the `fastapi_apps` attribute, and adds a UI entry through `external_views`:

| Component | Airflow 3.x (FastAPI) |
|-----------|----------------------|
| **Framework** | FastAPI |
| **Plugin Attribute** | `fastapi_apps` |
| **Routes** | `@app.get("/path")` / `@app.post("/path")` |
| **Responses** | `JSONResponse({...})` |
| **File Serving** | `FileResponse()` |
| **Request Body** | `async def func(request: dict)` |
| **UI Integration** | `external_views` |

### File Structure

```
.
├── Dockerfile
├── README.md
├── dags/
├── plugins/
│   ├── task_analyzer_plugin.py       # Airflow 3.x (FastAPI)
│   └── task_analyzer/                # Shared resources
│       ├── __init__.py
│       ├── prompts.py                # Bedrock configuration
│       ├── script_utils.py           # Operator script fetching utilities
│       ├── static/                   # Frontend assets
│       │   ├── css/styles.css
│       │   └── js/
│       │       ├── app.jsx
│       │       ├── components.jsx
│       │       ├── config.js
│       │       ├── template.jsx
│       │       └── utils.jsx
│       └── templates/
│           └── index.html
└──
```

---

## Troubleshooting

### Plugin Not Loading

**Symptom**: Plugin doesn't appear in the Airflow UI

**Solution**:
```bash
# Check plugin location
ls -la plugins/task_analyzer_plugin.py

# Check for import errors
astro dev logs | grep task_analyzer              # Astro CLI
docker logs mwaa-local-runner | grep task_analyzer  # MWAA Local
tail -f /var/log/airflow/webserver.log           # Standard Airflow

# Restart Airflow
astro dev restart
```

### 404 on Plugin Routes

**Symptom**: `/task-analyzer/` returns 404

- Ensure `fastapi_apps` is used with the correct `url_prefix`
- Verify FastAPI is available (it ships with Airflow 3.x)

### Import Errors

**Symptom**: `ModuleNotFoundError: No module named 'task_analyzer'`

**Solution**:
- Ensure `task_analyzer/__init__.py` exists so the folder is importable as a package
- For Amazon MWAA, confirm `task_analyzer_plugin.py` and `task_analyzer/` are at the **root** of `plugins.zip`

### Static Files Not Loading

**Symptom**: CSS/JS files return 404

- Verify `FileResponse` paths are correct
- Ensure `PLUGIN_DIR` is properly set

### AWS Connection Issues

**Symptom**: "AWS connection not found" or Bedrock errors

**Solution**:
1. Create or reuse the `aws_default` connection in the Airflow UI
2. Add AWS credentials with Bedrock access (or rely on the execution role on MWAA)
3. Set the correct region (e.g., us-east-1)
4. Confirm Bedrock model access is enabled for the Claude models in your region
5. Test connection: Navigate to `/task-analyzer/api/test-aws`

---

## Requirements

### Core Requirements
- Apache Airflow 3.x
- Python 3.10+
- AWS account with Bedrock access
- `aws_default` connection in Airflow

### Python Dependencies
- `fastapi` (ships with Airflow 3.x)
- `boto3` (ships with `apache-airflow-providers-amazon`)
- `apache-airflow-providers-amazon`

### AWS Bedrock Models Supported
- Claude Sonnet 4.6
- Claude Opus 4.6
- Claude Sonnet 4.5
- Claude 3.5 Sonnet

---

## Quick Commands Reference

### View Logs
```bash
astro dev logs | grep task_analyzer              # Astro CLI
docker logs mwaa-local-runner | grep task_analyzer  # MWAA Local
tail -f /var/log/airflow/webserver.log           # Standard Airflow
```

### Access Plugin
```bash
open http://localhost:8080/task-analyzer/
```

---

**Supported Environments**: Astro CLI, MWAA Local, Standard Airflow, Amazon MWAA
**Airflow Version**: 3.x
