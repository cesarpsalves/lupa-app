#!/usr/bin/env bash
# Deploy do LUPA no VPS. Segue o padrão dos /opt/update-*.sh dos outros
# ~30 projetos hospedados via Traefik no mesmo host.
#
# Instalação no VPS:
#   sudo ln -sf /opt/lupa/scripts/deploy-vps.sh /opt/update-lupa.sh
#   sudo chmod +x /opt/update-lupa.sh
#
# Uso:
#   sudo /opt/update-lupa.sh                  # pull + up
#   sudo LUPA_TAG=<sha> /opt/update-lupa.sh   # deploy de tag específica
#
# Pré-requisitos no VPS:
#   /opt/.env.lupa            — secrets de produção (root:root, chmod 600)
#   /opt/lupa/                — clone do repo (este script vive aqui)
#   network traefik-public    — criada pelo /opt/traefik
#   docker login ghcr.io      — se imagem for privada
set -euo pipefail

APP_DIR="/opt/lupa"
ENV_FILE="/opt/.env.lupa"
COMPOSE_FILE="$APP_DIR/docker/docker-compose.prod.yml"
PROJECT_NAME="lupa"
BRANCH="main"

ts() { date +'%Y-%m-%d %H:%M:%S'; }

echo "[$(ts)] ▶ Deploy LUPA — APP_DIR=$APP_DIR BRANCH=$BRANCH"

# ── Pré-condições ────────────────────────────────────────────
[[ -f "$ENV_FILE" ]]      || { echo "ERRO: $ENV_FILE não existe" >&2; exit 1; }
[[ -d "$APP_DIR/.git" ]]  || { echo "ERRO: $APP_DIR não é repo git (clone primeiro)" >&2; exit 1; }

# Network do Traefik (idempotente)
docker network inspect traefik-public >/dev/null 2>&1 || {
    echo "▶ Criando network traefik-public"
    docker network create traefik-public
}

# Config dinâmica do Traefik (file provider — labels Docker são ignoradas
# nesse VPS). Idempotente: só copia se o arquivo no repo for diferente.
TRAEFIK_DYNAMIC="/opt/traefik/dynamic/lupa.yml"
TRAEFIK_SOURCE="$APP_DIR/deploy/traefik-lupa.yml"
if [[ -f "$TRAEFIK_SOURCE" ]]; then
    if ! cmp -s "$TRAEFIK_SOURCE" "$TRAEFIK_DYNAMIC" 2>/dev/null; then
        echo "▶ Atualizando $TRAEFIK_DYNAMIC"
        cp "$TRAEFIK_SOURCE" "$TRAEFIK_DYNAMIC"
        # Traefik recarrega automaticamente (watch: true)
    fi
fi

# ── Atualizar código ─────────────────────────────────────────
cd "$APP_DIR"
echo "▶ Atualizando $APP_DIR"
git fetch origin
git reset --hard "origin/$BRANCH"
COMMIT_SHA="$(git rev-parse --short HEAD)"
echo "  → commit $COMMIT_SHA"

# Tag da imagem: usa LUPA_TAG do env se passado, senão 'latest'
export LUPA_TAG="${LUPA_TAG:-latest}"
echo "  → LUPA_TAG=$LUPA_TAG"

# ── Pull da imagem do GHCR ───────────────────────────────────
echo "▶ Pull imagem ghcr.io/cesarpsalves/lupa:$LUPA_TAG"
docker compose -p "$PROJECT_NAME" -f "$COMPOSE_FILE" --env-file "$ENV_FILE" pull web

# ── Subir stack ──────────────────────────────────────────────
echo "▶ Subindo stack (db + redis + web)"
docker compose -p "$PROJECT_NAME" -f "$COMPOSE_FILE" --env-file "$ENV_FILE" \
    up -d --remove-orphans

# ── Healthcheck ──────────────────────────────────────────────
echo "▶ Aguardando web ficar healthy..."
for i in {1..30}; do
    status=$(docker inspect --format '{{.State.Health.Status}}' lupa-web 2>/dev/null || echo "starting")
    if [[ "$status" == "healthy" ]]; then
        echo "  ✓ web healthy"
        break
    fi
    [[ $i -eq 30 ]] && { echo "ERRO: web não ficou healthy em 60s" >&2; docker logs --tail 50 lupa-web; exit 1; }
    sleep 2
done

# ── Smoke test interno ──────────────────────────────────────
echo "▶ Smoke test interno (rede do compose)"
docker compose -p "$PROJECT_NAME" -f "$COMPOSE_FILE" --env-file "$ENV_FILE" \
    exec -T web curl -fsS http://127.0.0.1:8000/healthz >/dev/null
echo "  ✓ /healthz responde 200"

# ── Limpeza ──────────────────────────────────────────────────
echo "▶ Limpando imagens antigas"
docker image prune -f >/dev/null 2>&1 || true

echo "[$(ts)] ✓ Deploy concluído (commit $COMMIT_SHA)"
docker compose -p "$PROJECT_NAME" -f "$COMPOSE_FILE" --env-file "$ENV_FILE" ps
