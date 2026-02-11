import os
import uvicorn
import google.generativeai as genai
from fastapi import FastAPI, Request, Form
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy import create_engine, Column, Integer, String
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

# --- 1. 설정 (DB & AI) ---
DB_URL = os.getenv("DATABASE_URL")
AI_KEY = os.getenv("GEMINI_API_KEY")

# Gemini AI 설정
genai.configure(api_key=AI_KEY)
model = genai.GenerativeModel('gemini-1.5-flash')

engine = create_engine(DB_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

class Visitor(Base):
    __tablename__ = "visitors"
    id = Column(Integer, primary_key=True, index=True)
    count = Column(Integer, default=0)

app = FastAPI()
templates = Jinja2Templates(directory=".")

@app.get("/", response_class=HTMLResponse)
async def read_index(request: Request):
    db = SessionLocal()
    visitor = db.query(Visitor).first()
    if not visitor:
        visitor = Visitor(count=0)
        db.add(visitor)
    visitor.count += 1
    db.commit()
    current_count = visitor.count
    db.close()
    
    # 처음 접속했을 때는 AI 메시지가 없으므로 빈 값을 보냅니다.
    return templates.TemplateResponse("index2.html", {"request": request, "count": current_count, "ai_msg": ""})

@app.post("/ask", response_class=HTMLResponse)
async def ask_ai(request: Request, user_input: str = Form(...)):
    # 1. DB에서 현재 카운트 가져오기
    db = SessionLocal()
    visitor = db.query(Visitor).first()
    current_count = visitor.count if visitor else 0
    db.close()

    # 2. Gemini AI에게 메시지 부탁하기
    prompt = f"사용자가 이렇게 말했어: '{user_input}'. 이 사람에게 아주 다정하고 짧은 응원 메시지를 한 줄로 해줘."
    response = model.generate_content(prompt)
    ai_msg = response.text

    return templates.TemplateResponse("index2.html", {
        "request": request, 
        "count": current_count, 
        "ai_msg": ai_msg,
        "user_text": user_input
    })

if __name__ == "__main__":
    port = int(os.getenv("PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port)