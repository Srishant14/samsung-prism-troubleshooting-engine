import requests
from typing import Optional, Dict
from config import SERPAPI_API_KEY


def search_official_support(query: str, domain: str) -> Optional[Dict]:
    """
    Searches Samsung official support via SerpApi.
    Returns a link to official Samsung support page — does NOT generate steps.

    The LLM must NOT generate troubleshooting advice.
    Only verified KB records may provide troubleshooting steps.
    SERP results are used as a helpful link, not as a source of steps.
    """
    if not SERPAPI_API_KEY:
        return None

    try:
        # Call SerpApi
        search_query = f"site:samsung.com/in/support {domain} {query}"
        params = {
            "q": search_query,
            "api_key": SERPAPI_API_KEY,
            "engine": "google"
        }

        response = requests.get("https://serpapi.com/search", params=params)
        response.raise_for_status()
        data = response.json()

        organic_results = data.get("organic_results", [])
        if not organic_results:
            return None

        # Return just the link — no LLM-generated steps
        top_result = organic_results[0]
        title = top_result.get("title", f"Samsung Support: {domain.capitalize()}")
        link = top_result.get("link", "https://www.samsung.com/in/support/")

        return {
            "title": title,
            "link": link,
            "source": "Samsung Official Support",
            "source_type": "web_search"
        }

    except Exception as e:
        print(f"SerpApi fallback failed: {e}")
        return None
