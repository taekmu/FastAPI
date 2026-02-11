import uvicorn
import os
from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy import create_engine, Column, Integer
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

# --- 1. Supabase 연결 설정 (환경 변수 사용) ---
# os.getenv는 Render 설정(Environment)에 넣은 DATABASE_URL 값을 자동으로 가져옵니다.
DB_URL = os.getenv("DATABASE_URL")

# 만약 환경 변수가 제대로 설정되지 않았을 때를 대비한 예외 처리
if not DB_URL:
    raise ValueError("DATABASE_URL 환경 변수가 설정되지 않았습니다. Render 설정을 확인하세요.")

# SQLAlchemy 설정
engine = create_engine(DB_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

# --- 2. DB 모델 정의 ---
class Visitor(Base):
    __tablename__ = "visitors"
    id = Column(Integer, primary_key=True, index=True)
    count = Column(Integer, default=0)

app = FastAPI()

# index2.html 파일 경로 설정
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
            # 데이터가 하나도 없을 경우 초기값 생성
            new_visitor = Visitor(count=1)
            db.add(new_visitor)
            db.commit()
            current_count = 1
    except Exception as e:
        print(f"DB Error: {e}")
        current_count = "Error"
    finally:
        db.close()

    # index2.html 파일에 변수 전달
    return templates.TemplateResponse("index2.html", {"request": request, "count": current_count})

if __name__ == "__main__":
    # 포트 번호는 Render의 기본값인 10000을 사용하거나 8000을 사용해도 무방합니다.
    port = int(os.getenv("PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port)