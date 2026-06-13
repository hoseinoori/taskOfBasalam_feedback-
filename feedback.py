from fastapi import FastAPI, Depends, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import create_engine, Column, Integer, String
from sqlalchemy.orm import declarative_base, sessionmaker, Session
from pydantic import BaseModel

engine = create_engine("sqlite:///./feedback.db", connect_args={"check_same_thread": False})

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()

class FeedbackDB(Base):
    __tablename__ = "feedbacks"
    
    id = Column(Integer, primary_key=True, index=True)
    title = Column(String, index=True)
    message = Column(String)
    status = Column(String, default="ثبت شده")

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
def update_feedback_status(feedback_id: int, status_update: FeedbackUpdate, db: Session = Depends(get_db)):
    
    valid_statuses = ["ثبت شده", "در حال بررسی", "رسیدگی شده"]
    if status_update.status not in valid_statuses:
        raise HTTPException(status_code=400, detail="وضعیت نامعتبر است")
    
    db_feedback = db.query(FeedbackDB).filter(FeedbackDB.id == feedback_id)
    if not db_feedback:
        raise HTTPException(status_code=404, detail="فیدبک پیدا نشد")
    
    db_feedback.status = status_update.status
    db.commit()
    db.refresh(db_feedback)
    return db_feedback