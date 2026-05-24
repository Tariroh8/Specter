import webbrowser
import urllib.parse
from typing import Any, Dict
from hands.skills.base import BaseSkill

class WebSearchSkill(BaseSkill):
    name = "web_search"
    description = "Opens the default browser and performs a Google search."
    parameters = {
        "query": "The term or phrase to search for."
    }

    def execute(self, **kwargs) -> Dict[str, Any]:
        query = kwargs.get("query")
        if not query:
            return {"success": False, "message": "Missing required parameter 'query'."}

        try:
            encoded_query = urllib.parse.quote(query)
            url = f"https://www.google.com/search?q={encoded_query}"
            webbrowser.open(url)
            return {"success": True, "message": f"Opened web search for: '{query}'"}
        except Exception as e:
            return {"success": False, "message": f"Failed to open web search: {e}"}
