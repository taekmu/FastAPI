import uvicorn
import os
from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy import create_engine, Column, Integer
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

# --- 1. Supabase 연결 설정 ---
DB_URL = "postgresql://postgres.ttjxuxyxsexavaidmqvc:yongsacocori2@aws-1-ap-south-1.pooler.supabase.com:6543/postgres"


engine = create_engine(DB_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

# --- 2. DB 모델 정의 ---
class Visitor(Base):
    __tablename__ = "visitors"
    id = Column(Integer, primary_key=True, index=True)
    count = Column(Integer, default=0)

app = FastAPI()

# index2.html 파일이 들어있는 폴더를 지정합니다 (보통 현재 폴더면 ".")
templates = Jinja2Templates(directory=".")

@app.get("/", response_class=HTMLResponse)
async def read_index(request: Request):
    db = SessionLocal()
    try:
        # DB에서 카운트 조회 및 업데이트
        visitor = db.query(Visitor).first()
        if visitor:
            visitor.count += 1
            db.commit()
            current_count = visitor.count
        else:
            current_count = 0
    except Exception as e:
        print(f"DB Error: {e}")
        current_count = "Error"
    finally:
        db.close()

    # index2.html 파일에 current_count 변수를 넘겨줍니다.
    return templates.TemplateResponse("index2.html", {"request": request, "count": current_count})

if __name__ == "__main__":
    #uvicorn.run(app, host="127.0.0.1", port=8000)
    uvicorn.run(app, host="0.0.0.0", port=8000)