#!/usr/bin/env bash
# ════════════════════════════════════════════════════════════
# Backup do banco — roda no cron diário (03h).
# ════════════════════════════════════════════════════════════
#
# Configurar no crontab do VPS (como `paulo`):
#   0 3 * * * /opt/lupa/scripts/backup.sh >> /var/log/lupa-backup.log 2>&1
#
set -euo pipefail

BACKUP_DIR="${BACKUP_DIR:-/var/backups/lupa}"
RETENTION_DAYS="${RETENTION_DAYS:-14}"
DB_NAME="${DB_NAME:-lupa_v2}"
DB_USER="${DB_USER:-lupa_app}"

mkdir -p "$BACKUP_DIR"

STAMP=$(date +%F_%H%M)
OUT="$BACKUP_DIR/lupa_${STAMP}.sql.gz"

echo "▶ Iniciando dump → $OUT"
docker compose -f /opt/lupa/docker/docker-compose.prod.yml \
    exec -T db pg_dump -U "$DB_USER" -Fc "$DB_NAME" | gzip > "$OUT"

echo "▶ Removendo backups mais antigos que $RETENTION_DAYS dias"
find "$BACKUP_DIR" -name "lupa_*.sql.gz" -mtime "+$RETENTION_DAYS" -delete

echo "✓ Backup concluído: $OUT ($(du -h "$OUT" | cut -f1))"

# TODO: upload pra bucket S3-compatible (R2) quando configurado.
# Exemplo (descomentar quando S3 estiver pronto):
# aws s3 cp "$OUT" s3://lupa-backups/ --endpoint-url=$AWS_ENDPOINT_URL
