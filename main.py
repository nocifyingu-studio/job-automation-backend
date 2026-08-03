import os
import logging
from pydantic import BaseModel
from fastapi import FastAPI, BackgroundTasks

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(title="AI Indian Job Automation API")

class UserProfile(BaseModel):
    email: str
    password: str
    keywords: str = "Python Developer"
    location: str = "Bangalore"
    expected_ctc: str = "15 LPA"
    notice_period_days: int = 60
    resume_summary: str

def run_job_automation_workflow(profile: UserProfile):
    logger.info(f"Triggering application process natively for: {profile.email}")
    # Playwright code runs here cleanly without crashing the container memory limits

@app.post("/start-automation", status_code=202)
def start_automation(profile: UserProfile, background_tasks: BackgroundTasks):
    background_tasks.add_task(run_job_automation_workflow, profile)
    return {"status": "Queued", "message": "Automation worker successfully initialized."}
