FROM python:3.11-slim

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
ENV DEBIAN_FRONTEND=noninteractive

RUN apt-get update && apt-get install -y --no-install-recommends \
curl \
build-essential \
&& apt-get clean \
&& rm -rf /var/lib/apt/lists/*

RUN curl https://sh.rustup.rs -sSf | sh -s -- -y
ENV PATH="/root/.cargo/bin:${PATH}"
ENV CARGO_HOME=/opt/cargo_cache
RUN mkdir -p $CARGO_HOME

WORKDIR /app

COPY requirements.txt .
RUN pip install --upgrade pip && \
pip install --only-binary :all: -r requirements.txt 2>/dev/null || \
pip install -r requirements.txt

COPY . .

RUN mkdir -p /app/data /app/logs
VOLUME ["/app/data", "/app/logs"]

EXPOSE 8000

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]