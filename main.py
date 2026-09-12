
from fastapi import FastAPI, HTTPException , Depends

from db import (
    create_application,
    delete_application,
    get_application,
    get_applications,
    update_application,
    create_user,
    get_user_by_email,
)
from schemas import (
    ApplicationCreate,
    ApplicationResponse,
    ApplicationUpdate,
    UserCreate,
    UserLogin
)
from security import hash_password,verify_password, create_access_token, get_current_user_id

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

    new_user = create_user(
        name=user.name,
        email=user.email,
        password_hash=password_hash,
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

