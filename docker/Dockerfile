# syntax=docker/dockerfile:1.7
# ════════════════════════════════════════════════════════════
# LUPA — Dockerfile multi-stage
# ════════════════════════════════════════════════════════════

# ────────── Stage: builder ──────────
FROM python:3.12-slim AS builder

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    libpq-dev \
    libpango-1.0-0 libpangoft2-1.0-0 \
    libcairo2 libffi-dev \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /build

COPY requirements/base.in requirements/prod.in /build/requirements/
RUN pip install --upgrade pip pip-tools \
    && pip-compile --quiet --output-file=/build/requirements/prod.txt /build/requirements/prod.in

RUN pip install --prefix=/install -r /build/requirements/prod.txt

# ────────── Stage: tailwind (builda o CSS) ──────────
# Tailwind standalone CLI (binário, sem Node). Escaneia templates+js pra gerar
# só as classes usadas — substitui o CDN que carregava ~3MB de JS no browser.
FROM debian:bookworm-slim AS tailwind

RUN apt-get update && apt-get install -y --no-install-recommends \
    curl ca-certificates \
    && rm -rf /var/lib/apt/lists/* \
    && curl -sSL -o /usr/local/bin/tailwindcss \
       https://github.com/tailwindlabs/tailwindcss/releases/download/v3.4.17/tailwindcss-linux-x64 \
    && chmod +x /usr/local/bin/tailwindcss

WORKDIR /tw
# Só o necessário pros content paths do tailwind.config.js
COPY tailwind.config.js ./
COPY static/css/input.css ./static/css/input.css
COPY templates ./templates
COPY apps ./apps
COPY static/js ./static/js
RUN tailwindcss -c tailwind.config.js -i static/css/input.css -o /tw/tailwind.css --minify

# ────────── Stage: runtime ──────────
FROM python:3.12-slim AS runtime

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    DJANGO_SETTINGS_MODULE=config.settings.prod \
    PATH="/usr/local/bin:$PATH"

RUN apt-get update && apt-get install -y --no-install-recommends \
    libpq5 \
    libpango-1.0-0 libpangoft2-1.0-0 \
    libcairo2 \
    fonts-liberation \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Usuário non-root
RUN groupadd --system lupa && useradd --system --gid lupa --create-home lupa

WORKDIR /app

COPY --from=builder /install /usr/local
COPY --chown=lupa:lupa . /app
# CSS buildado pelo stage tailwind (gitignored, então vem só daqui)
COPY --from=tailwind --chown=lupa:lupa /tw/tailwind.css /app/static/css/tailwind.css

# Diretórios pra estáticos e media. Pré-criados com chown lupa:lupa pra que
# volumes Docker nomeados herdem essas permissões quando montados vazios.
RUN mkdir -p /app/staticfiles /app/media && chown -R lupa:lupa /app/staticfiles /app/media

USER lupa

EXPOSE 8000

HEALTHCHECK --interval=30s --timeout=5s --start-period=20s --retries=3 \
    CMD curl -fsS http://127.0.0.1:8000/healthz || exit 1

ENTRYPOINT ["/app/docker/entrypoint.sh"]
# Workers sync (Django sync + HTMX). UvicornWorker exigiria uvicorn[standard]
# completo (click, httptools, etc) que o pip-compile não vinha resolvendo.
CMD ["gunicorn", "config.wsgi:application", \
     "--bind", "0.0.0.0:8000", \
     "--workers", "3", \
     "--worker-class", "sync", \
     "--timeout", "60", \
     "--access-logfile", "-", \
     "--error-logfile", "-"]
