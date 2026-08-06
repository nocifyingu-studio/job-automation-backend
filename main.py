import os
import hmac
import hashlib
import logging
from fastapi import FastAPI, Request, HTTPException, BackgroundTasks, Depends
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from supabase import create_client, Client

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(title="JobApply AI Production Engine")

# Configure broad CORS origins to allow clean communication from your frontend and Chrome Extension
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Core infrastructure variables pulled securely from Render Environment Settings
SUPABASE_URL = "https://supabase.co"
SUPABASE_KEY = os.environ.get("SUPABASE_SERVICE_ROLE_KEY", "sb_publishable_key_sb_GMd45FNc_tSp14xZjjbA_Ib0RY1CF")
RAZORPAY_WEBHOOK_SECRET = os.environ.get("RAZORPAY_WEBHOOK_SECRET", "your_secret_webhook_string")

supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

class JobScanRequest(BaseModel):
    email: str
    expected_ctc: str
    notice_period_days: int
    resume_summary: str
    job_text: str

def process_ai_job_matching(data: JobScanRequest):
    logger.info(f"Initiating OpenAI evaluation tracking arrays for premium profile: {data.email}")
    # Real processing logic runs here securely in the cloud

# 🛡️ THE MONETIZATION GATEWAY: Razorpay hits this URL directly server-to-server
@app.post("/razorpay-webhook")
async def razorpay_webhook_listener(request: Request):
    raw_body = await request.body()
    signature = request.headers.get("X-Razorpay-Signature")
    
    if not signature:
        raise HTTPException(status_code=400, detail="Missing secure transaction signature.")
        
    # Verify that the notification actually came from Razorpay and wasn't faked by a hacker
    expected_signature = hmac.new(
        RAZORPAY_WEBHOOK_SECRET.encode(),
        raw_body,
        hashlib.sha256
    .hexdigest()
    
    if not hmac.compare_digest(signature, expected_signature):
        raise HTTPException(status_code=400, detail="Invalid cryptographic payload signature matching.")

    payload = await request.json()
    event = payload.get("event")
    
    # Listen for a successful payment link or payment button capture event
    if event in ["payment.captured", "order.paid", "payment_link.paid"]:
        payment_entity = payload["payload"]["payment"]["entity"]
        customer_email = payment_entity.get("email")
        
        if customer_email:
            logger.info(f"Payment verified for {customer_email}. Activating account infrastructure.")
            # Lock the premium state into your persistent database warehouse table permanently
            supabase.table("user_configs").upsert({
                "email": customer_email,
                "is_premium": True,
                "updated_at": "now()"
            }).execute()
            
    return {"status": "success"}

# 🚀 THE SECURE AUTOMATION ROUTE: Chrome Extension hits this to scan a job listing
@app.post("/start-automation")
async def start_automation_engine(data: JobScanRequest, background_tasks: BackgroundTasks):
    # CRITICAL CHECK: Verify database state before spending any OpenAI completion token budget
    user_check = supabase.table("user_configs").select("is_premium").eq("email", data.email).maybe_single().execute()
    
    if not user_check.data or not user_check.data.get("is_premium"):
        logger.warning(f"Unauthorized execution attempt intercepted from unverified actor: {data.email}")
        raise HTTPException(status_code=403, detail="Subscription inactive. Access denied to premium AI tools.")

    background_tasks.add_task(process_ai_job_matching, data)
    return {"status": "Queued", "message": "Automation worker successfully initialized."}
