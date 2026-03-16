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


@app.get("/message", response_class=HTMLResponse)
def hello_sushant():
    return """
    <!DOCTYPE html>
    <html>
    <head>
        <title>Hello Sushant</title>
    </head>
    <body>
        <h1 id="greeting">Hello Sushant!</h1>
        <script>
            document.getElementById('greeting').style.color = 'blue';
        </script>
    </body>
    </html>
    """


class HelloWorldPlugin(AirflowPlugin):
    name = "Custom"
    fastapi_apps = [
        {
            "app": app,
            "url_prefix": "/hello-world",
            "name": "Hello World",
        }
    ]
    external_views = [
        {
            "name": "Hello Admin",
            "href": "/hello-world/message",
            "destination": "nav",
            "category": "admin"
        }
    ]
