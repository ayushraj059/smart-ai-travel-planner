FROM python:3.11-slim

WORKDIR /app

# libgomp1 is required by PyTorch for OpenMP thread parallelism
RUN apt-get update && \
    apt-get install -y --no-install-recommends gcc libgomp1 && \
    rm -rf /var/lib/apt/lists/*

COPY requirements.txt .

# Install CPU-only PyTorch BEFORE requirements.txt so pip does not pull
# the default CUDA wheel (~3 GB). The CPU wheel is ~220 MB.
RUN pip install --no-cache-dir torch --index-url https://download.pytorch.org/whl/cpu

# Install the rest of the dependencies (sentence-transformers will reuse
# the torch already installed above)
RUN pip install --no-cache-dir -r requirements.txt

# Bake the embedding model into the image so service startup is instant
RUN python -c "from sentence_transformers import SentenceTransformer; SentenceTransformer('all-MiniLM-L6-v2')"

COPY app/ ./app/

EXPOSE 8002
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8002"]
