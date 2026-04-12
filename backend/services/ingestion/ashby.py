import httpx
from backend.services.ingestion.base import BaseConnector


class AshbyConnector(BaseConnector):
    source_name = "ashby"
    source_type = "ashby"
    
    async def fetch_raw(self) -> list[dict]:
        url = f"{self.base_url}/jobs"
        headers = {"Content-Type": "application/json"}
        body = {
            "query": """
                query {
                    jobs {
                        id
                        title
                        location
                        department
                        team
                        employmentType
                        compensationRange {
                            minAmount
                            maxAmount
                            currency
                        }
                        description
                        offices {
                            id
                            name
                            location
                        }
                        hostedUrl
                        applyUrl
                    }
                }
            """
        }
        
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.post(url, headers=headers, json=body)
            response.raise_for_status()
            data = response.json()
            jobs = data.get("data", {}).get("jobs", [])
            
            normalized = []
            for job in jobs:
                normalized_job = {
                    "id": job.get("id"),
                    "title": job.get("title"),
                    "location": job.get("location"),
                    "employment_type": job.get("employmentType"),
                    "description": job.get("description"),
                    "absolute_url": job.get("hostedUrl"),
                    "application_url": job.get("applyUrl"),
                    "compensation": None,
                }
                if job.get("compensationRange"):
                    normalized_job["compensation"] = {
                        "min_cents": job["compensationRange"].get("minAmount") * 100,
                        "max_cents": job["compensationRange"].get("maxAmount") * 100,
                    }
                normalized.append(normalized_job)
            
            return normalized
