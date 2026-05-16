import csv
import json
import re

TECH_TITLES = [
    'developer', 'engineer software', 'software engineer', 'data analyst',
    'data scientist', 'data engineer', 'machine learning', 'ai engineer',
    'backend', 'frontend', 'full stack', 'fullstack', 'devops', 'cloud engineer',
    'cybersecurity', 'cyber security', 'network engineer', 'mobile developer',
    'web developer', 'database', 'nlp', 'computer vision', 'deep learning',
    'react', 'python developer', 'java developer', 'flutter developer',
    'react native', 'android developer', 'ios developer', 'bi developer',
    'business intelligence', 'system analyst', 'it engineer', 'it specialist',
    'مطور برامج', 'مهندس برمجيات', 'محلل بيانات', 'مطور تطبيقات',
    'مهندس شبكات', 'أمن معلومات', 'ذكاء اصطناعي'
]

def is_tech_job(title):
    """Only accept jobs where the TITLE clearly matches tech roles."""
    title_lower = title.lower()
    return any(keyword in title_lower for keyword in TECH_TITLES)

def clean_text(text):
    if not text or str(text).strip() in ('', 'nan'):
        return ""
    text = re.sub(r'\s+', ' ', str(text)).strip()
    text = re.sub(r'<[^>]+>', '', text)
    return text

def is_saudi_job(country, city, location):
    text = f"{country} {city} {location}".lower()
    saudi_keywords = [
        'saudi', 'ksa', 'riyadh', 'jeddah', 'dammam', 'mecca', 'medina',
        'dhahran', 'khobar', 'jubail', 'tabuk', 'abha', 'neom', 'alkhobar',
        'السعودية', 'الرياض', 'جدة', 'الدمام', 'مكة', 'المدينة', 'الخبر'
    ]
    return any(k in text for k in saudi_keywords)

def convert_csv_to_json(csv_path, output_path, max_jobs=40):
    jobs = []
    seen = set()

    with open(csv_path, 'r', encoding='utf-8-sig') as f:
        reader = csv.DictReader(f)

        for row in reader:
            if len(jobs) >= max_jobs:
                break

            title = clean_text(row.get('Title', ''))
            description = clean_text(row.get('Job Description', ''))
            company = clean_text(row.get('Company', ''))
            location = clean_text(row.get('Job Location', ''))
            country = clean_text(row.get('Job Country', ''))
            city = clean_text(row.get('Job City', ''))
            job_url = clean_text(row.get('Job URL', ''))
            tags = clean_text(row.get('Tags', ''))

            # Skip missing fields
            if not title or not description or not company:
                continue

            # Skip short descriptions
            if len(description) < 150:
                continue

            # Must be Saudi
            if not is_saudi_job(country, city, location):
                continue

            # Title must be clearly tech
            if not is_tech_job(title):
                continue

            # No duplicates
            key = f"{title.lower()}_{company.lower()}"
            if key in seen:
                continue
            seen.add(key)

            job = {
                "title": title,
                "company": company,
                "location": location or f"{city}, Saudi Arabia",
                "description": description,
                "source_url": job_url,
                "tags": tags
            }

            jobs.append(job)
            print(f"✓ Added: {title} at {company}")

    with open(output_path, 'w', encoding='utf-8-sig') as f:
        json.dump(jobs, f, ensure_ascii=False, indent=2)

    print(f"\n✅ Done! {len(jobs)} real tech jobs saved to {output_path}")
    return jobs

if __name__ == "__main__":
    csv_path = "jobs_bayt_3.csv"
    output_path = "saudi_tech_jobs_real.json"
    convert_csv_to_json(csv_path, output_path, max_jobs=40)