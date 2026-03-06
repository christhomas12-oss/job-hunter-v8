import pandas as pd
import requests
import xml.etree.ElementTree as ET
from datetime import date

jobs = []

def add_job(title, organization, location, salary, link, match_score, source):
    jobs.append({
        "title": title,
        "organization": organization,
        "location": location,
        "salary": salary,
        "match_score": match_score,
        "link": link,
        "source": source,
        "date_found": str(date.today())
    })

def score_title(title):
    t = title.lower()
    score = 50

    preferred_terms = [
        "director",
        "assistant director",
        "associate director",
        "international",
        "global",
        "study abroad",
        "student success",
        "engagement",
        "partnerships"
    ]

    for term in preferred_terms:
        if term in t:
            score += 8

    if "director" in t:
        score += 10

    return min(score, 99)

def search_higheredjobs_rss():
    url = "https://www.higheredjobs.com/rss/articleFeed.cfm"

    try:
        response = requests.get(url, timeout=30)
        response.raise_for_status()

        root = ET.fromstring(response.text)

        for item in root.findall(".//item"):
            title = item.findtext("title", default="").strip()
            link = item.findtext("link", default="https://www.higheredjobs.com").strip()

            title_lower = title.lower()

            keywords = [
                "director",
                "assistant director",
                "associate director",
                "international",
                "global",
                "study abroad",
                "student affairs",
                "student success",
                "engagement"
            ]

            if any(k in title_lower for k in keywords):
                add_job(
                    title=title,
                    organization="HigherEdJobs",
                    location="Various",
                    salary="Check posting",
                    link=link,
                    match_score=score_title(title),
                    source="HigherEdJobs RSS"
                )
    except Exception as e:
        print(f"HigherEdJobs RSS error: {e}")

def add_manual_target_sources():
    add_job(
        title="University of Washington jobs page",
        organization="University of Washington",
        location="Seattle / Hybrid / Remote varies",
        salary="Check posting",
        link="https://www.washington.edu/jobs/",
        match_score=82,
        source="Manual source link"
    )

    add_job(
        title="Washington Community & Technical Colleges jobs page",
        organization="Washington State Board for Community and Technical Colleges",
        location="Washington / Hybrid varies",
        salary="Check posting",
        link="https://www.sbctc.edu/about/jobs",
        match_score=80,
        source="Manual source link"
    )

def main():
    search_higheredjobs_rss()
    add_manual_target_sources()

    df = pd.DataFrame(jobs)

    if df.empty:
        df = pd.DataFrame([{
            "title": "No jobs found today",
            "organization": "",
            "location": "",
            "salary": "",
            "match_score": 0,
            "link": "",
            "source": "",
            "date_found": str(date.today())
        }])

    df = df.drop_duplicates(subset=["title", "organization", "link"])
    df = df.sort_values("match_score", ascending=False)

    df.to_csv("jobs.csv", index=False)
    print("Saved jobs.csv successfully")

if __name__ == "__main__":
    main()
