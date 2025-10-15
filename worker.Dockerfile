# ---------------- Base Image ----------------
ARG PYTHON_VERSION=3.13.3
FROM python:${PYTHON_VERSION}-slim

# ---------------- Env Settings ----------------
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
ENV PATH=/usr/local/bin:$PATH
ENV HOME=/home/appuser

WORKDIR /app

# ---------------- System Dependencies ----------------
RUN apt-get update && apt-get install -y --no-install-recommends \
    openjdk-17-jre-headless \
    wget \
    unzip \
    curl \
    git \
    && rm -rf /var/lib/apt/lists/*

# ---------------- Create App User ----------------
ARG UID=10001
RUN adduser \
    --disabled-password \
    --gecos "" \
    --home "/home/appuser" \
    --shell "/bin/bash" \
    --uid "${UID}" \
    appuser

# ---------------- Create Cache in /opt (shared location) ----------------
RUN mkdir -p /opt/cache/whisper /opt/cache/language_tool_python

# ---------------- Download LanguageTool to /opt ----------------
RUN wget -q https://languagetool.org/download/LanguageTool-6.6.zip -O /tmp/lt.zip && \
    unzip -q /tmp/lt.zip -d /tmp/languagetool && \
    mv /tmp/languagetool/LanguageTool-6.6/* /opt/cache/language_tool_python/ && \
    rm -rf /tmp/languagetool /tmp/lt.zip

# ---------------- Set Permissions ----------------
RUN chown -R appuser:appuser /opt/cache && \
    chmod -R 755 /opt/cache

# ---------------- Environment Variables ----------------
ENV LT_DISABLE_DOWNLOAD=1
ENV LANGUAGE_TOOL_HOME=/opt/cache/language_tool_python
ENV WHISPER_CACHE_DIR=/opt/cache/whisper

# ---------------- Install Python Dependencies ----------------
COPY pyproject.toml uv.lock* ./
RUN pip install --no-cache-dir .

# ---------------- Copy Source ----------------
COPY src/ ./src

# ---------------- Permissions ----------------
RUN chown -R appuser:appuser /app

# ---------------- Define Volume ----------------
VOLUME ["/opt/cache"]

# ---------------- Switch to App User ----------------
USER appuser

# ---------------- Start Celery Worker ----------------
CMD ["celery", "-A", "src.background.celery_app.celery_app", "worker", "--loglevel=info"]
