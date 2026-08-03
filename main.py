import os
import time
import json
import logging
from pydantic import BaseModel, Field
from fastapi import FastAPI, BackgroundTasks
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from openai import OpenAI

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)

app = FastAPI(title="AI Indian Job Automation API")
openai_client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

NAUKRI_LOGIN_URL = "https://naukri.com"
MAX_DAILY_APPLICATIONS = 50

class UserProfile(BaseModel):
    email: str
    password: str
    keywords: str = "Python Developer, Data Analyst"
    location: str = "Bangalore"
    expected_ctc: str = "15 LPA"
    notice_period_days: int = 60
    resume_summary: str

class JobMatchEvaluation(BaseModel):
    match_score: float
    is_good_fit: bool
    justification: str

class FormScreeningAnswers(BaseModel):
    answers: dict[str, str]

def evaluate_job_match(job_description: str, profile: UserProfile) -> JobMatchEvaluation:
    try:
        prompt = f"Evaluate job fit for {profile.expected_ctc}, {profile.location}, notice period {profile.notice_period_days} days.\nProfile:\n{profile.resume_summary}\n\nJob:\n{job_description}"
        completion = openai_client.beta.chat.completions.parse(
            model="gpt-4o-mini",
            messages=[{"role": "user", "content": prompt}],
            response_format=JobMatchEvaluation,
        )
        return completion.choices.message.parsed
    except Exception as e:
        logger.error(f"AI Matcher Error: {e}")
        return JobMatchEvaluation(match_score=0.0, is_good_fit=False, justification="Error")

def generate_screening_answers(questions: list[str], profile: UserProfile) -> FormScreeningAnswers:
    try:
        prompt = f"Answer questions: {json.dumps(questions)} based on target CTC {profile.expected_ctc}, {profile.notice_period_days} days notice."
        completion = openai_client.beta.chat.completions.parse(
            model="gpt-4o-mini",
            messages=[{"role": "user", "content": prompt}],
            response_format=FormScreeningAnswers,
        )
        return completion.choices.message.parsed
    except Exception as e:
        return FormScreeningAnswers(answers={q: "Negotiable" for q in questions})

def run_job_automation_workflow(profile: UserProfile):
    options = Options()
    options.add_argument('--headless')
    options.add_argument('--no-sandbox')
    options.add_argument('--disable-dev-shm-usage')
    options.add_argument('user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36')
    
    driver = webdriver.Chrome(options=options)
    wait = WebDriverWait(driver, 15)
    applied_count = 0
    
    try:
        driver.get(NAUKRI_LOGIN_URL)
        wait.until(EC.presence_of_element_located((By.XPATH, '//input[@placeholder="Enter your active Email ID / Username"]'))).send_keys(profile.email)
        driver.find_element(By.XPATH, '//input[@placeholder="Enter your password"]').send_keys(profile.password)
        driver.find_element(By.XPATH, '//button[@type="submit"]').click()
        time.sleep(5)
        
        search_query = f"{profile.keywords.replace(',', ' ').replace(' ', '-')}-jobs-in-{profile.location.lower()}"
        driver.get(f"https://naukri.com{search_query}")
        time.sleep(4)
        
        job_tuples = driver.find_elements(By.XPATH, '//div[contains(@class, "srp-job-tuple")]')
        for job in job_tuples:
            if applied_count >= MAX_DAILY_APPLICATIONS: break
            try:
                evaluation = evaluate_job_match(job.text, profile)
                if evaluation.is_good_fit:
                    job.find_element(By.XPATH, './/a[contains(@class, "title")]').click()
                    time.sleep(3)
                    driver.switch_to.window(driver.window_handles[-1])
                    wait.until(EC.element_to_be_clickable((By.XPATH, '//button[contains(text(), "Apply")]'))).click()
                    applied_count += 1
                    driver.close()
                    driver.switch_to.window(driver.window_handles[0])
            except Exception:
                continue
    finally:
        driver.quit()

@app.post("/start-automation", status_code=202)
def start_automation(profile: UserProfile, background_tasks: BackgroundTasks):
    background_tasks.add_task(run_job_automation_workflow, profile)
    return {"status": "Queued"}
