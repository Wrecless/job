import pytest

from backend.services.ingestion.base import BaseConnector


class DummyConnector(BaseConnector):
    source_name = "greenhouse"
    source_type = "greenhouse"

    async def fetch_raw(self) -> list[dict]:
        return []


def test_greenhouse_normalize_flattens_location_and_uses_company_name():
    connector = DummyConnector("https://boards.greenhouse.io/gitlab")

    normalized = connector.normalize(
        {
            "id": 123,
            "company_name": "GitLab",
            "title": "Backend Engineer",
            "location": {"name": "Remote, India"},
            "content": "<p>Example</p>",
            "absolute_url": "https://example.com/jobs/123",
        }
    )

    assert normalized["company"] == "GitLab"
    assert normalized["location"] == "Remote, India"
    assert normalized["source_url"] == "https://example.com/jobs/123"
    assert normalized["application_url"] == "https://example.com/jobs/123"
