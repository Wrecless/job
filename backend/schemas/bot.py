from pydantic import BaseModel


class BotRunResponse(BaseModel):
    sources_checked: int
    sources_skipped: int
    sources_failed: int
    jobs_created: int
    jobs_updated: int
    jobs_scored: int
