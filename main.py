import secrets
from fastapi import FastAPI, HTTPException , Depends
from email_parser import clean_email_body
from llm_parser import extract_job_details

from db import (
    create_application,
    delete_application,
    get_application,
    get_applications,
    update_application,
    create_user,
    get_user_by_email,
    get_application_status_counts,
    create_raw_email,
    get_user_by_inbound_email,
    process_email_application,

)
from schemas import (
    ApplicationCreate,
    ApplicationResponse,
    ApplicationUpdate,
    UserCreate,
    UserLogin
)
from security import hash_password,verify_password, create_access_token, get_current_user_id
from dotenv import load_dotenv

load_dotenv()
import os
import resend

resend.api_key = os.getenv("RESEND_API_KEY")


def send_welcome_email(to_email: str, name: str):
    resend.Emails.send({
        "from": "onboarding@resend.dev",
        "to": to_email,
        "subject": "Welcome to TrackDesk 🎉",
        "html": f"""
            <h2>Welcome to TrackDesk, {name}!</h2>
            <p>Your account was created successfully.</p>
            <p>Happy job hunting! 🚀</p>
        """,
    })

app = FastAPI()


@app.get("/")
def root():
    return {"message": "Job Tracker API is running"}


@app.post("/applications", response_model=ApplicationResponse)
def create_application_endpoint(
    application: ApplicationCreate,
    current_user_id: int = Depends(get_current_user_id),
):
    new_application = create_application(
        user_id=current_user_id,
        company=application.company,
        role=application.role,
        source=application.source,
        status=application.status,
        job_url=application.job_url,
        follow_up=application.follow_up,
        notes=application.notes,
    )

    return new_application


@app.get("/applications", response_model=list[ApplicationResponse])
def list_applications(current_user_id: int = Depends(get_current_user_id,)
):
    return get_applications(current_user_id)

@app.get("/applications/status-counts")
def get_status_counts(
    current_user_id: int = Depends(get_current_user_id),
):
    return get_application_status_counts(current_user_id)
@app.get(
    "/applications/{application_id}",
    response_model=ApplicationResponse,
)
def get_application_endpoint(
    application_id: int,
    current_user_id: int = Depends(get_current_user_id),
):
    application = get_application(application_id, current_user_id)
    if application is None:
        raise HTTPException(
            status_code=404,
            detail="Application not found",
        )

    return application


@app.put(
    "/applications/{application_id}",
    response_model=ApplicationResponse,
)
def update_application_endpoint(
    application_id: int,
    application: ApplicationUpdate,
    current_user_id: int = Depends(get_current_user_id),

):
    updated = update_application(
        user_id=current_user_id,
        application_id=application_id,
        company=application.company,
        role=application.role,
        source=application.source,
        status=application.status,
        job_url=application.job_url,
        follow_up=application.follow_up,
        notes=application.notes,
    )

    if not updated:
        raise HTTPException(
            status_code=404,
            detail="Application not found",
        )

    return get_application(application_id,current_user_id)


@app.delete("/applications/{application_id}")
def delete_application_endpoint(
    application_id: int,
    current_user_id: int = Depends(get_current_user_id),
):
    deleted = delete_application(
        application_id=application_id,
        user_id=current_user_id,
    )

    if not deleted:
        raise HTTPException(
            status_code=404,
            detail="Application not found",
        )

    return {"message": "Application deleted successfully"}

@app.post("/users")
def register_user(user: UserCreate):
    existing_user = get_user_by_email(user.email)

    if existing_user is not None:
        raise HTTPException(
            status_code=409,
            detail="Email already registered",
        )

    password_hash = hash_password(user.password)
    inbound_email = f"u_{secrets.token_urlsafe(8)}@inbound.trackdesk.local"

    new_user = create_user(
        name=user.name,
        email=user.email,
        password_hash=password_hash,
        inbound_email=inbound_email,
    )

    return {
        "id": new_user.id,
        "name": new_user.name,
        "email": new_user.email,
    }


@app.post("/login")
def login_user(user: UserLogin):
    existing_user = get_user_by_email(user.email)

    if existing_user is None:
        raise HTTPException(
            status_code=401,
            detail="Invalid email or password",
        )

    if not verify_password(
        user.password,
        existing_user.password_hash,
    ):
        raise HTTPException(
            status_code=401,
            detail="Invalid email or password",
        )

    access_token = create_access_token(existing_user.id)

    return {
        "access_token": access_token,
        "token_type": "bearer",
    }
@app.get("/me")
def get_me(
    current_user_id: int = Depends(get_current_user_id),
):
    return {
        "user_id": current_user_id
    }

@app.post("/webhooks/email")
def receive_email(event: dict):
    email_id = event["data"]["email_id"]
    to_email = event["data"]["to"][0]

    user = get_user_by_inbound_email(to_email)

    if user is None:
        raise HTTPException(
            status_code=400,
            detail="Unknown TrackDesk inbound email address",
        )

    received_email = resend.Emails.Receiving.get(email_id)

    from_email = received_email["from"]
    subject = received_email.get("subject")
    body = received_email.get("text") or received_email.get("html") or ""
    message_id = received_email.get("message_id")

    new_email = create_raw_email(
        user_id=user.id,
        from_email=from_email,
        to_email=to_email,
        subject=subject,
        body=body,
        message_id=message_id,
    )

    cleaned_text = clean_email_body(body)

    extraction = extract_job_details(cleaned_text)

    if extraction.confidence < 0.7:
        return {
            "message": "Email stored but confidence was too low",
            "email_id": new_email.id,
            "confidence": extraction.confidence,
        }

    application_result = process_email_application(
        user_id=user.id,
        company=extraction.company,
        role=extraction.role,
        status=extraction.status,
    )

    return {
        "message": "Email processed successfully",
        "email_id": new_email.id,
        "application": application_result,
    }