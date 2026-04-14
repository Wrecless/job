from pathlib import Path


def _parse_csv_list(value: str) -> list[str]:
    return [item.strip() for item in value.split(",") if item.strip() and item.strip().lower() != "none"]


def load_portfolio_profile(portfolio_path: str) -> dict:
    text = Path(portfolio_path).read_text(encoding="utf-8")
    lines = [line.strip() for line in text.splitlines() if line.strip()]

    sections: dict[str, list[str]] = {}
    current_section = None

    for line in lines:
        if line.startswith("## "):
            current_section = line[3:].strip().lower()
            sections.setdefault(current_section, [])
            continue
        if line.startswith("- ") and current_section:
            sections[current_section].append(line[2:].strip())

    job_target = sections.get("job target", [])
    target_roles = sections.get("target roles", [])
    core_skills = sections.get("core skills to match", [])
    positioning = sections.get("positioning", [])
    linkedin_headline = sections.get("linkedin headline", [])
    linkedin_about = sections.get("linkedin about", [])
    matching_rules = sections.get("matching rules", [])
    source_filters = sections.get("source filters", [])
    notification_preferences = sections.get("notification preferences", [])
    prepare_everything = sections.get('what "prepare everything" means', [])
    bot_behavior = sections.get("bot behavior", [])
    seniority_preference = sections.get("seniority preference", [])

    source_types_include: list[str] = []
    source_types_exclude: list[str] = []
    source_names_include: list[str] = []
    source_names_exclude: list[str] = []

    for rule in source_filters:
        lowered = rule.lower()
        if lowered.startswith("include source types:"):
            source_types_include = _parse_csv_list(rule.split(":", 1)[1].strip())
        elif lowered.startswith("exclude source types:"):
            source_types_exclude = _parse_csv_list(rule.split(":", 1)[1].strip())
        elif lowered.startswith("include source names:"):
            source_names_include = _parse_csv_list(rule.split(":", 1)[1].strip())
        elif lowered.startswith("exclude source names:"):
            source_names_exclude = _parse_csv_list(rule.split(":", 1)[1].strip())

    salary_floor_gbp = 23837

    seniority = None
    if seniority_preference:
        seniority_text = " ".join(seniority_preference).lower()
        if "entry" in seniority_text or "junior" in seniority_text:
            seniority = "junior"
        elif "intern" in seniority_text or "graduate" in seniority_text:
            seniority = "intern"

    return {
        "source": "portfolio",
        "headline": linkedin_headline[0] if linkedin_headline else (positioning[0] if positioning else "Fully remote jobs only"),
        "target_roles": target_roles,
        "core_skills": core_skills,
        "seniority": seniority,
        "salary_floor": salary_floor_gbp,
        "locations": ["Remote", "United Kingdom", "UK"],
        "remote_preference": "remote",
        "industries_to_avoid": [],
        "keywords_include": ["remote", "fully remote", "distributed", "async"],
        "keywords_exclude": [],
        "preferred_countries": ["UK"],
        "salary_policy": "uk_or_above",
        "source_types_include": source_types_include,
        "source_types_exclude": source_types_exclude,
        "source_names_include": source_names_include,
        "source_names_exclude": source_names_exclude,
        "job_target": job_target,
        "matching_rules": matching_rules,
        "source_filters": source_filters,
        "notification_preferences": notification_preferences,
        "preparation_rules": prepare_everything,
        "bot_behavior": bot_behavior,
        "linkedin_about": linkedin_about,
    }
