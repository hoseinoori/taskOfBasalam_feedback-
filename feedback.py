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