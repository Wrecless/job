import httpx
from urllib.parse import urlparse

from backend.services.ingestion.base import BaseConnector


class GreenhouseConnector(BaseConnector):
    source_name = "greenhouse"
    source_type = "greenhouse"
    
    async def fetch_raw(self) -> list[dict]:
        board_slug = self._board_slug()
        url = f"https://boards-api.greenhouse.io/v1/boards/{board_slug}/jobs?content=true"
        headers = {}
        if self.api_key:
            headers["Authorization"] = f"Bearer {self.api_key}"
        
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.get(url, headers=headers)
            response.raise_for_status()
            data = response.json()
            return data.get("jobs", [])

    def _board_slug(self) -> str:
        parsed = urlparse(self.base_url)
        parts = [part for part in parsed.path.split("/") if part]

        if "boards" in parts:
            index = parts.index("boards")
            if index + 1 < len(parts):
                return parts[index + 1]

        if parts:
            return parts[-1]

        return parsed.path.strip("/") or self.base_url.rsplit("/", 1)[-1]
