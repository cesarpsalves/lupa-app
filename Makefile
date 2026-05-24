# ════════════════════════════════════════════════════════════
# LUPA — Makefile
# Comandos comuns do dia a dia. `make help` lista tudo.
# ════════════════════════════════════════════════════════════

.DEFAULT_GOAL := help
SHELL := /bin/bash
PYTHON := python3
VENV := .venv
BIN := $(VENV)/bin
MANAGE := $(BIN)/python manage.py

# ────────── Cores ──────────
CYAN := \033[36m
BOLD := \033[1m
RESET := \033[0m

.PHONY: help
help:  ## Lista todos os comandos
	@awk 'BEGIN {FS = ":.*?## "; printf "\n${BOLD}LUPA — comandos${RESET}\n\n"} \
		/^[a-zA-Z_-]+:.*?## / { printf "  ${CYAN}%-20s${RESET} %s\n", $$1, $$2 }' $(MAKEFILE_LIST)
	@echo

# ────────── Setup ──────────
.PHONY: install
install:  ## Cria venv e instala deps (dev)
	$(PYTHON) -m venv $(VENV)
	$(BIN)/pip install --upgrade pip pip-tools
	$(BIN)/pip-sync requirements/dev.txt
	$(BIN)/pre-commit install

.PHONY: lock
lock:  ## Atualiza requirements/*.txt a partir dos *.in
	$(BIN)/pip-compile requirements/base.in -o requirements/base.txt
	$(BIN)/pip-compile requirements/dev.in  -o requirements/dev.txt
	$(BIN)/pip-compile requirements/prod.in -o requirements/prod.txt

# ────────── Banco ──────────
.PHONY: migrate
migrate:  ## Aplica migrations
	$(MANAGE) migrate

.PHONY: makemigrations
makemigrations:  ## Gera migrations
	$(MANAGE) makemigrations

.PHONY: superuser
superuser:  ## Cria superusuário
	$(MANAGE) createsuperuser

.PHONY: shell
shell:  ## Shell Django (com ipython se disponível)
	$(MANAGE) shell_plus 2>/dev/null || $(MANAGE) shell

.PHONY: dbshell
dbshell:  ## Shell do Postgres
	$(MANAGE) dbshell

# ────────── Run ──────────
.PHONY: run
run:  ## Roda servidor de desenvolvimento
	$(MANAGE) runserver 0.0.0.0:8000

.PHONY: runprod
runprod:  ## Roda Gunicorn (modo produção local)
	$(BIN)/gunicorn config.wsgi:application -c docker/gunicorn.conf.py

# ────────── Qualidade ──────────
.PHONY: lint
lint:  ## Roda ruff (lint)
	$(BIN)/ruff check apps config tests

.PHONY: fmt
fmt:  ## Formata código
	$(BIN)/ruff format apps config tests
	$(BIN)/ruff check --fix apps config tests

.PHONY: type
type:  ## Roda mypy
	$(BIN)/mypy apps config

.PHONY: audit
audit:  ## Audita dependências (CVE)
	$(BIN)/pip-audit -r requirements/prod.txt

.PHONY: security
security:  ## Roda bandit
	$(BIN)/bandit -c pyproject.toml -r apps config

.PHONY: check
check: lint type audit security  ## Roda todos os checks de qualidade

# ────────── Testes ──────────
.PHONY: test
test:  ## Roda testes
	$(BIN)/pytest

.PHONY: testcov
testcov:  ## Testes com coverage
	$(BIN)/pytest --cov --cov-report=term-missing --cov-report=html

.PHONY: testfast
testfast:  ## Testes excluindo `slow`
	$(BIN)/pytest -m "not slow"

# ────────── Docker ──────────
.PHONY: up
up:  ## Sobe stack local (compose)
	docker compose -f docker/docker-compose.yml up -d

.PHONY: down
down:  ## Derruba stack local
	docker compose -f docker/docker-compose.yml down

.PHONY: logs
logs:  ## Tail dos logs
	docker compose -f docker/docker-compose.yml logs -f --tail=100

.PHONY: build
build:  ## Builda imagem Docker
	docker compose -f docker/docker-compose.yml build

# ────────── Limpeza ──────────
.PHONY: clean
clean:  ## Limpa caches
	find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name ".pytest_cache" -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name ".mypy_cache" -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name ".ruff_cache" -exec rm -rf {} + 2>/dev/null || true
	rm -rf htmlcov .coverage coverage.xml

.PHONY: nuke
nuke: clean  ## Limpa tudo incluindo venv
	rm -rf $(VENV)
