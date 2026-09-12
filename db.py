import psycopg
from psycopg.rows import dict_row
from sqlalchemy import create_engine,select,func
from sqlalchemy.orm import sessionmaker
from sqlalchemy.engine import URL
from models import Application,User


def get_connection():
    return psycopg.connect(
        host="localhost",
        port=5432,
        dbname="job_tracker",
        user="postgres",
        password="S@ndy229/",
        row_factory=dict_row
    )
# NEW: SQLAlchemy setup
DATABASE_URL = URL.create(
    drivername="postgresql+psycopg",
    username="postgres",
    password="S@ndy229/",
    host="localhost",
    port=5432,
    database="job_tracker",
)

engine = create_engine(DATABASE_URL)

SessionLocal = sessionmaker(
    bind=engine,
    expire_on_commit=False,
)
def get_applications(user_id,status=None,statuses=None,search=None, limit=None, offset=0,follow_up_before=None,follow_up_after=None):
    with SessionLocal() as session:
        statement = select(Application)
        statement = statement.where(Application.user_id == user_id)

        if status is not None:
            statement = statement.where(
                Application.status == status
            )
        if statuses is not None:
            statement = statement.where(
                Application.status.in_(statuses)
            )
        if search is not None:
            search_term = f"%{search}%"

            statement = statement.where(
               Application.company.ilike(search_term)
                | Application.role.ilike(search_term)
            )
        if follow_up_before is not None:
            statement = statement.where(
                Application.follow_up <= follow_up_before
            )
        if follow_up_after is not None:
            statement = statement.where(
                Application.follow_up >= follow_up_after
            )
        
        statement = statement.order_by(Application.id.desc())
        if offset:
          statement = statement.offset(offset)

        if limit:
          statement = statement.limit(limit)

        result = session.execute(statement)

        applications = result.scalars().all()

        return [
            {
                "id": app.id,
                "company": app.company,
                "role": app.role,
                "source": app.source,
                "status": app.status,
                "job_url": app.job_url,
                "follow_up": app.follow_up,
                "notes": app.notes,
            }
            for app in applications
        ]
def get_application_status_counts():
    with SessionLocal() as session:
        statement = (
            select(Application.status, func.count(Application.id))
            .group_by(Application.status)
        )

        result = session.execute(statement)

        return result.all()
def create_application(user_id,company, role, source, status, job_url, follow_up, notes):
    with SessionLocal() as session:
        try:
            application = Application(
                user_id=user_id,
                company=company,
                role=role,
                source=source,
                status=status,
                job_url=job_url,
                follow_up=follow_up,
                notes=notes,
            )

            session.add(application)
            session.commit()
            session.refresh(application)

            return application

        except Exception:
            session.rollback()
            raise

def update_application(
    user_id,
    application_id,
    company,
    role,
    source,
    status,
    job_url,
    follow_up,
    notes,
):
    with SessionLocal() as session:
        try:
            statement = select(Application).where(
                Application.id == application_id,
                Application.user_id == user_id,
            )

            result = session.execute(statement)

            application = result.scalar_one_or_none()

            if application is None:
                return False
            
            
            application.company = company
            application.role = role
            application.source = source
            application.status = status
            application.job_url = job_url
            application.follow_up = follow_up
            application.notes = notes

            session.commit()

            return True

        except Exception:
            session.rollback()
            raise
def delete_application(application_id,user_id):
    with SessionLocal() as session:
        try:
            statement = select(Application).where(
                Application.id == application_id,
                Application.user_id == user_id,
            )

            result = session.execute(statement)

            application = result.scalar_one_or_none()

            if application is None:
                return False

            session.delete(application)

            session.commit()

            return True

        except Exception:
            session.rollback()
            raise
def get_application(application_id,user_id):
    with SessionLocal() as session:
        statement = select(Application).where(
            Application.id == application_id,
            Application.user_id == user_id,
        )

        result = session.execute(statement)

        return result.scalar_one_or_none()

def create_user(name, email, password_hash):
    with SessionLocal() as session:
        try:
            user = User(
                name=name,
                email=email,
                password_hash=password_hash,
            )

            session.add(user)
            session.commit()
            session.refresh(user)

            return user

        except Exception:
            session.rollback()
            raise


def get_user_by_email(email):
    with SessionLocal() as session:
        statement = select(User).where(User.email == email)

        result = session.execute(statement)

        return result.scalar_one_or_none()


