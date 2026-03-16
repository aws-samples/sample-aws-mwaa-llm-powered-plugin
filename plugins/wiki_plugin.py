# plugins/wiki_plugin.py
from __future__ import annotations
from airflow.plugins_manager import AirflowPlugin

class WikiPlugin(AirflowPlugin):
    name = "Wiki"
    external_views = [
        {
            "name": "📖 Wiki Search",
            "href": "https://en.wikipedia.org/wiki/Main_Page",
            "url_route": "wikipedia_search",
            "destination": "dag"
        }
    ]
