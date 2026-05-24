import webbrowser
import urllib.parse
import urllib.request
import re
from typing import Any, Dict
from hands.skills.base import BaseSkill

class YouTubePlaySkill(BaseSkill):
    name = "youtube_play"
    description = "Opens YouTube in the default browser and plays the first video matching the search query."
    parameters = {
        "query": "The name of the song or video to search for and play."
    }

    def execute(self, **kwargs) -> Dict[str, Any]:
        query = kwargs.get("query")
        if not query:
            return {"success": False, "message": "Missing required parameter 'query'."}

        try:
            encoded_query = urllib.parse.quote(query)
            search_url = f"https://www.youtube.com/results?search_query={encoded_query}"
            
            # Fetch the search results page to find the first video ID
            req = urllib.request.Request(search_url, headers={'User-Agent': 'Mozilla/5.0'})
            html = urllib.request.urlopen(req).read().decode('utf-8')
            
            # Extract the first video ID using regex
            match = re.search(r'"videoId":"([^"]+)"', html)
            if match:
                video_id = match.group(1)
                play_url = f"https://www.youtube.com/watch?v={video_id}"
                webbrowser.open(play_url)
                return {"success": True, "message": f"Playing video for: '{query}' ({play_url})"}
            else:
                # Fallback to just opening the search if no video ID is found
                webbrowser.open(search_url)
                return {"success": True, "message": f"Could not find exact video. Opened search for: '{query}'"}
                
        except Exception as e:
            return {"success": False, "message": f"Failed to open YouTube: {e}"}
