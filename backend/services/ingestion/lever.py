import httpx
from backend.services.ingestion.base import BaseConnector


class LeverConnector(BaseConnector):
    source_name = "lever"
    source_type = "lever"
    
    async def fetch_raw(self) -> list[dict]:
        url = f"{self.base_url}/postings"
        headers = {}
        if self.api_key:
            headers["Authorization"] = f"Bearer {self.api_key}"
        
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.get(url, headers=headers)
            response.raise_for_status()
            data = response.json()
            return data if isinstance(data, list) else data.get("data", [])
