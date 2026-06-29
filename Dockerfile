# ForgeLoop web app — the browser control plane (catalog, runs, approvals) with
# real browser execution. One image, deployable anywhere; open it in any browser.
#
#   docker build -t forgeloop .
#   docker run -p 8055:8055 forgeloop      # then open http://localhost:8055/
#
FROM python:3.12-slim

ENV PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    DASHBOARD_HOST=0.0.0.0 \
    DASHBOARD_PORT=8055

WORKDIR /app

# Playwright + Chromium (and its OS deps) for live/agentic runs. The core web app,
# catalog, dashboard, and simulate runs work without it; live runs need it.
COPY integration/requirements.txt /app/integration/requirements.txt
RUN pip install -r /app/integration/requirements.txt \
    && python -m playwright install --with-deps chromium

COPY . /app

EXPOSE 8055
CMD ["python", "-m", "integration.server"]
