import os
import uvicorn
from google import genai  # 최신 구글 AI 라이브러리
from fastapi import FastAPI, Request, Form
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy import create_engine, Column, Integer
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

# --- 1. 설정 (DB & AI) ---
DB_URL = os.getenv("DATABASE_URL")
AI_KEY = os.getenv("GEMINI_API_KEY")

# 최신 Gemini AI 클라이언트 설정
if AI_KEY:
    client = genai.Client(api_key=AI_KEY)
else:
    client = None

# DB 연결 설정
engine = create_engine(DB_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

# DB 모델 정의
class Visitor(Base):
    __tablename__ = "visitors"
    id = Column(Integer, primary_key=True, index=True)
    count = Column(Integer, default=0)

app = FastAPI()
templates = Jinja2Templates(directory=".")

# --- 2. 메인 화면 (GET) ---
@app.get("/", response_class=HTMLResponse)
async def read_index(request: Request):
    db = SessionLocal()
    try:
        visitor = db.query(Visitor).first()
        if not visitor:
            visitor = Visitor(count=0)
            db.add(visitor)
            db.commit()
            db.refresh(visitor)
        
        # 방문 횟수 증가
        visitor.count += 1
        db.commit()
        current_count = visitor.count
    except Exception as e:
        print(f"DB Error: {e}")
        current_count = "Error"
    finally:
        db.close()
    
    return templates.TemplateResponse("index2.html", {
        "request": request, 
        "count": current_count, 
        "ai_msg": "",
        "user_text": ""
    })

# --- 3. AI 응원 요청 (POST) ---
@app.post("/ask", response_class=HTMLResponse)
async def ask_ai(request: Request, user_input: str = Form(...)):
    # DB에서 현재 카운트 가져오기
    db = SessionLocal()
    visitor = db.query(Visitor).first()
    current_count = visitor.count if visitor else 0
    db.close()

    # Gemini AI에게 응원 메시지 요청
    ai_msg = "AI 키가 설정되지 않았습니다."
    if client:
        try:
            response = client.models.generate_content(
                model="gemini-3-flash-preview",
                contents=f"사용자가 이렇게 말했어: '{user_input}'. 이 사람에게 아주 다정하고 짧은 응원 메시지를 한 줄로 해줘."
                "1. 사용자가 사용한 언어를 감지해줘"
                "2. 그 언어에 맞춰서 아주 다정하고 짧은 응원 메시지를 한 줄로 해줘"
                "3. 만약 언어를 알 수 없다면 한국어로 대답해줘"
            )
            ai_msg = response.text
        except Exception as e:
            ai_msg = f"AI 호출 중 오류가 발생했습니다: {e}"

    return templates.TemplateResponse("index2.html", {
        "request": request, 
        "count": current_count, 
        "ai_msg": ai_msg,
        "user_text": user_input
    })

if __name__ == "__main__":
    # Render 환경에 맞는 포트 설정
    port = int(os.getenv("PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port)