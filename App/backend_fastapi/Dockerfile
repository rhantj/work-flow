FROM python:3.12-slim
WORKDIR /app

# requirements 먼저 복사해서 설치 → 코드만 바뀌었을 땐 pip install을 다시 안 하고 캐시를 씀
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY app app

EXPOSE 8000
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
