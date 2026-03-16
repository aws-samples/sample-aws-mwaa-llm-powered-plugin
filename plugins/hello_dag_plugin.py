from airflow.plugins_manager import AirflowPlugin
from fastapi import FastAPI
from fastapi.responses import HTMLResponse

app = FastAPI()

@app.get("/", response_class=HTMLResponse)
def hello_world():
    return """
    <!DOCTYPE html>
    <html>
    <head><title>Hello World</title></head>
    <body>
        <h1>Hello World!</h1>
        <p>This is a custom plugin message displayed in Airflow UI.</p>
    </body>
    </html>
    """

@app.get("/test", response_class=HTMLResponse)
def hello_sushant():
    return """
    <!DOCTYPE html>
    <html>
    <head><title>Hello Sushant</title></head>
    <body>
        <script>
            const h1 = document.createElement('h1');
            h1.textContent = 'Hello Sushant!';
            h1.style.color = 'red';
            document.body.appendChild(h1);
        </script>
    </body>
    </html>
    """


class HelloDagPlugin(AirflowPlugin):
    name = "hello_dag_plugin"
    fastapi_apps = [
        {
            "app": app,
            "url_prefix": "/hello-dag",
            "name": "Hello DAG",
        }
    ]
    external_views = [
        {
            "name": "Hello",
            "href": "/hello-dag/test",
            "url_route": "hello_dag_view",
            "destination": "dag_run",
        }
    ]
