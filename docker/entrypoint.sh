#!/usr/bin/env bash
# Entrypoint: aplica migrations, coleta estáticos, executa CMD.
set -euo pipefail

echo "▶ Aplicando migrations..."
python manage.py migrate --noinput

echo "▶ Coletando estáticos..."
python manage.py collectstatic --noinput --clear

echo "▶ Iniciando: $*"
exec "$@"
