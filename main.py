from fastapi import FastAPI, Depends
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from sqlalchemy.orm import Session
from database import SessionLocal, Booking
import rag
import os
from dotenv import load_dotenv
from twilio.rest import Client

load_dotenv()

TWILIO_ACCOUNT_SID = os.getenv("TWILIO_ACCOUNT_SID")
TWILIO_AUTH_TOKEN = os.getenv("TWILIO_AUTH_TOKEN")
TWILIO_PHONE_NUMBER = os.getenv("TWILIO_PHONE_NUMBER")

app = FastAPI(title="Academic Portal API")

# Setup CORS for React frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], # Allow all for dev
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

class ChatRequest(BaseModel):
    message: str

class BookingRequest(BaseModel):
    name: str
    phone: str
    course: str
    college: str

@app.get("/")
def read_root():
    return {"status": "Backend is running"}

@app.post("/api/chat")
def chat(request: ChatRequest):
    response_text = rag.generate_response(request.message)
    return {"reply": response_text}

@app.post("/api/book")
def book_admission(request: BookingRequest, db: Session = Depends(get_db)):
    # Save to SQLite
    db_booking = Booking(
        name=request.name,
        phone=request.phone,
        course=request.course,
        college=request.college
    )
    db.add(db_booking)
    db.commit()
    db.refresh(db_booking)
    
    # Twilio Real SMS Integration
    sms_status = "Mock SMS logged (missing keys)"
    if TWILIO_ACCOUNT_SID and TWILIO_AUTH_TOKEN and TWILIO_PHONE_NUMBER:
        try:
            client = Client(TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN)
            message = client.messages.create(
                body=f"Hi {request.name}, your inquiry for {request.course} at {request.college} is confirmed. We will contact you soon.",
                from_=TWILIO_PHONE_NUMBER,
                to=request.phone
            )
            print(f"[TWILIO] SMS sent successfully. SID: {message.sid}")
            sms_status = "Real SMS confirmation sent"
        except Exception as e:
            print(f"[TWILIO ERROR] Failed to send SMS: {e}")
            sms_status = f"Failed to send SMS check console"
    else:
        # Fallback Mock
        print(f"[SMS MOCK] Missing Twilio keys in .env. Would have sent SMS to {request.phone}: 'Hi {request.name}, your inquiry for {request.course} at {request.college} is confirmed.'")
    
    return {"message": f"Booking successful! {sms_status}.", "booking_id": db_booking.id}
