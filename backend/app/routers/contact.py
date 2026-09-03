from fastapi import APIRouter, BackgroundTasks
from pydantic import BaseModel
from typing import Optional
from app.services.email_service import send_contact_email

router = APIRouter(prefix="/api/contact", tags=["Contact"])

class ContactFormRequest(BaseModel):
    name: str
    email: str
    subject: str
    tracking_id: Optional[str] = None
    message: str

@router.post("")
def submit_contact_form(data: ContactFormRequest, background_tasks: BackgroundTasks):
    """
    Receive contact form submission from the frontend and dispatch an email to support in the background.
    """
    background_tasks.add_task(send_contact_email, data)
    return {"status": "success", "detail": "Message submitted"}
