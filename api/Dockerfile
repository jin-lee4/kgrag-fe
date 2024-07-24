FROM langchain/langchain

WORKDIR /app

RUN apt-get update && apt-get install -y \
    build-essential \
    curl \
    software-properties-common \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .

RUN pip install --upgrade -r requirements.txt

COPY src/api.py .
COPY src/upload.py .
COPY src/embedding.py .
COPY src/pdf.py .
COPY src/database.py .

HEALTHCHECK CMD curl --fail http://localhost:8504

ENTRYPOINT [ "uvicorn", "api:app", "--host", "0.0.0.0", "--port", "8504" ]
