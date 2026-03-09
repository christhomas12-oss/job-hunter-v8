import os
import re
import smtplib
from datetime import date
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import xml.etree.ElementTree as ET

import pandas as pd
import requests
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

jobs = []

MIN_SALARY = 110000

TITLE_KEYWORDS = [
    "director",
    "assistant director",
    "associate director",
    "international",
    "global",
    "study abroad",
    "student affairs",
    "student success",
    "engagement",
    "partnerships",
    "education abroad",
    "international programs",
    "international student services",
]

def load_resume():
    try:
        with open("resume.txt", "r", encoding="utf-8",errors='replace') as f:
            return f.read().strip()
    except FileNotFoundError:
        return ""

RESUME_TEXT = load_resume()

def estimate_salary_from_text(text):
    """
    Looks for salaries like:
    $120,000
    $120,000 - $140,000
    120000
    """
    if not text:
        return None

    cleaned = text.replace("\n", " ")

    range_match = re.search(r"\$?\s*([0-9]{2,3},?[0-9]{3})\s*[-–to]+\s*\$?\s*([0-9]{2,3},?[0-9]{3})", cleaned, re.IGNORECASE)
    if range_match:
        low = int(range_match.group(1).replace(",", ""))
        high = int(range_match.group(2).replace(",", ""))
        return max(low, high)

    single_matches = re.findall(r"\$?\s*([0-9]{2,3},?[0-9]{3})", cleaned)
    numeric_values = []
    for m in single_matches:
        try:
            value = int(m.replace(",", ""))
            if 40000 <= value <= 500000:
                numeric_values.append(value)
        except ValueError:
            pass

    if numeric_values:
        return max(numeric_values)

    return None

def format_salary_label(salary_value):
    if salary_value is None:
        return "Check posting"
    return f"${salary_value:,.0f}+"

def resume_match_score(resume_text, job_text):
    if not resume_text.strip() or not job_text.strip():
        return 50

    try:
        vectorizer = TfidfVectorizer(stop_words="english")
        tfidf = vectorizer.fit_transform([resume_text, job_text])
        score = cosine_similarity(tfidf[0:1], tfidf[1:2])[0][0]
        return int(score * 100)
    except Exception:
        return 50

def title_bonus(title):
    title_lower = title.lower()
    bonus = 0

    for term in TITLE_KEYWORDS:
        if term in title_lower:
            bonus += 5

    if "director" in title_lower:
        bonus += 10

    return bonus

def final_match_score(title, description):
    base = resume_match_score(RESUME_TEXT, f"{title} {description}")
    bonus = title_bonus(title)
    return min(base + bonus, 99)

def add_job(title, organization, location, salary_text, link, source, description=""):
    estimated_salary = estimate_salary_from_text(f"{title} {description} {salary_text}")

    # Keep jobs with salary >= MIN_SALARY or unknown salary
    if estimated_salary is not None and estimated_salary < MIN_SALARY:
        return

    score = final_match_score(title, description)

    jobs.append({
        "title": title,
        "organization": organization,
        "location": location,
        "salary": format_salary_label(estimated_salary),
        "salary_number": estimated_salary if estimated_salary is not None else "",
        "match_score": score,
        "link": link,
        "source": source,
        "description": description,
        "date_found": str(date.today())
    })

def search_higheredjobs_rss():
    url = "https://www.higheredjobs.com/rss/articleFeed.cfm"

    try:
        response = requests.get(url, timeout=30)
        response.raise_for_status()

        root = ET.fromstring(response.text)

        for item in root.findall(".//item"):
            title = item.findtext("title", default="").strip()
            link = item.findtext("link", default="https://www.higheredjobs.com").strip()
            description = item.findtext("description", default="").strip()

            text = f"{title} {description}".lower()

            if any(k in text for k in TITLE_KEYWORDS):
                add_job(
                    title=title,
                    organization="HigherEdJobs",
                    location="Various",
                    salary_text=description,
                    link=link,
                    source="HigherEdJobs RSS",
                    description=description
                )
    except Exception as e:
        print(f"HigherEdJobs RSS error: {e}")

def add_manual_target_sources():
    add_job(
        title="University of Washington jobs page",
        organization="University of Washington",
        location="Seattle / Hybrid / Remote varies",
        salary_text="Check posting",
        link="https://www.washington.edu/jobs/",
        source="Manual source link",
        description="Official jobs page for the University of Washington."
    )

    add_job(
        title="Washington Community & Technical Colleges jobs page",
        organization="Washington State Board for Community and Technical Colleges",
        location="Washington / Hybrid varies",
        salary_text="Check posting",
        link="https://www.sbctc.edu/about/jobs",
        source="Manual source link",
        description="Official jobs page for Washington community and technical college openings."
    )

def send_email_alerts(df):
    sender = os.getenv("EMAIL_ADDRESS")
    password = os.getenv("EMAIL_APP_PASSWORD")
    recipient = os.getenv("EMAIL_TO")

    if not sender or not password or not recipient:
        print("Email secrets not set. Skipping email.")
        return

    top3 = df.sort_values("match_score", ascending=False).head(3)

    message = MIMEMultipart("alternative")
    message["Subject"] = "Your Top 3 Job Matches Today"
    message["From"] = sender
    message["To"] = recipient

    lines = []
    lines.append("Here are your top 3 job matches today:\n")

    for i, (_, row) in enumerate(top3.iterrows(), start=1):
        lines.append(
            f"{i}. {row['title']}\n"
            f"Organization: {row['organization']}\n"
            f"Location: {row['location']}\n"
            f"Salary: {row['salary']}\n"
            f"Match Score: {row['match_score']}\n"
            f"Link: {row['link']}\n"
        )

    body = "\n".join(lines)
    message.attach(MIMEText(body, "plain"))

    with smtplib.SMTP("smtp.gmail.com", 587) as server:
        server.starttls()
        server.login(sender, password)
        server.sendmail(sender, recipient, message.as_string())

    print("Email sent successfully.")

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
            "salary_number": "",
            "match_score": 0,
            "link": "",
            "source": "",
            "description": "",
            "date_found": str(date.today())
        }])

    df = df.drop_duplicates(subset=["title", "organization", "link"])
    df = df.sort_values("match_score", ascending=False).head(20)

    df.to_csv("jobs.csv", index=False)
    print("Saved jobs.csv successfully")

    if not df.empty and df.iloc[0]["title"] != "No jobs found today":
        send_email_alerts(df)

if __name__ == "__main__":
    main()
