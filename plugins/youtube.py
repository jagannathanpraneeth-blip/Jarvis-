import urllib.request
import urllib.parse
import re
import webbrowser
from core.logger import get_logger

logger = get_logger("plugin.youtube")

def _play_video(query: str) -> str:
    try:
        logger.info(f"Searching YouTube for: {query}")
        query_string = urllib.parse.urlencode({"search_query": query})
        html_content = urllib.request.urlopen("https://www.youtube.com/results?" + query_string)
        search_results = re.findall(r'/watch\?v=(.{11})', html_content.read().decode())
        
        if search_results:
            video_url = "https://www.youtube.com/watch?v=" + search_results[0]
            # Open in the default visible browser
            webbrowser.open(video_url)
            return f"Successfully found and started playing the video in the browser: {video_url}"
        else:
            return "Failed to find any videos matching the query."
    except Exception as e:
        logger.error(f"YouTube search failed: {e}")
        return f"An error occurred while trying to play the video: {e}"

def register(brain, settings) -> None:
    """Register YouTube tools."""
    brain.register_tool(
        name="play_youtube_video",
        description="Searches YouTube for a specific song, video, or topic, and immediately opens and plays the first result in the user's default visible browser.",
        parameters={
            "type": "object",
            "properties": {
                "query": {"type": "string", "description": "The search query (e.g. 'Iron Man AC/DC Shoot to Thrill')"}
            },
            "required": ["query"]
        },
        handler=_play_video
    )
    logger.info("YouTube plugin registered.")
