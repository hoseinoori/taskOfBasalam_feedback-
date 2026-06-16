from fastapi import FastAPI, Depends, HTTPException, Response, Cookie
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import create_engine, Column, Integer, String, Boolean
from sqlalchemy.orm import declarative_base, sessionmaker, Session
from pydantic import BaseModel

engine = create_engine(
    "sqlite:///./feedback.db", connect_args={"check_same_thread": False}
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()


class FeedbackDB(Base):
    __tablename__ = "feedbacks"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String, index=True)
    message = Column(String)
    status = Column(String, default="ثبت شده")


class UserDB(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String, unique=True, index=True, nullable=False)
    password = Column(String, nullable=False)
    is_admin = Column(Boolean, default=False)


Base.metadata.create_all(bind=engine)


class FeedbackCreate(BaseModel):
    title: str
    message: str


class FeedbackUpdate(BaseModel):
    status: str


class FeedbackOut(BaseModel):
    id: int
    title: str
    message: str
    status: str

    class Config:
        from_attributes = True


class UserAuth(BaseModel):
    username: str
    password: str
    is_admin: bool = False


app = FastAPI(title="Feedback For Basalam(hoseinoori)")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
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


@app.post("/api/feedbacks/", response_model=FeedbackOut)
def create_feedback(feedback: FeedbackCreate, db: Session = Depends(get_db)):
    new_feedback = FeedbackDB(title=feedback.title, message=feedback.message)
    db.add(new_feedback)
    db.commit()
    db.refresh(new_feedback)
    return new_feedback


@app.get("/api/feedbacks/", response_model=list[FeedbackOut])
def get_feedbacks(db: Session = Depends(get_db)):
    return db.query(FeedbackDB).all()


@app.patch("/api/feedbacks/{feedback_id}/status", response_model=FeedbackOut)
def update_feedback_status(
    feedback_id: int, status_update: FeedbackUpdate, db: Session = Depends(get_db)
):

    valid_statuses = ["ثبت شده", "در حال بررسی", "رسیدگی شده"]
    if status_update.status not in valid_statuses:
        raise HTTPException(status_code=400, detail="وضعیت نامعتبر است")

    db_feedback = db.query(FeedbackDB).filter(FeedbackDB.id == feedback_id).first()
    if not db_feedback:
        raise HTTPException(status_code=404, detail="فیدبک پیدا نشد")

    db_feedback.status = status_update.status
    db.commit()
    db.refresh(db_feedback)
    return db_feedback


@app.post("/api/auth/signup")
def signup(user: UserAuth, db: Session = Depends(get_db)):
    existing_user = db.query(UserDB).filter(UserDB.username == user.username).first()
    if existing_user:
        raise HTTPException(status_code=400, detail="این نام کاربری قبلاً ثبت شده است.")

    new_user = UserDB(
        username=user.username, password=user.password, is_admin=user.is_admin
    )
    db.add(new_user)
    db.commit()
    return {"message": "ثبت‌نام با موفقیت انجام شد."}


@app.post("/api/auth/login")
def login(user: UserAuth, response: Response, db: Session = Depends(get_db)):
    db_user = (
        db.query(UserDB)
        .filter(UserDB.username == user.username, UserDB.password == user.password)
        .first()
    )
    if not db_user:
        raise HTTPException(
            status_code=400, detail="نام کاربری یا رمز عبور اشتباه است."
        )

    role_value = "admin" if db_user.is_admin else "user"
    response.set_cookie(key="user_role", value=role_value, max_age=7200, httponly=False)

    return {"message": "ورود موفقیت‌آمیز بود", "is_admin": db_user.is_admin}


@app.post("/api/auth/logout")
def logout(response: Response):
    response.delete_cookie(key="user_role")
    return {"message": "از حساب خارج شدید"}
