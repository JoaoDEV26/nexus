#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")/.."
mkdir -p backups
umask 077
file="backups/nexus-$(date +%Y%m%d-%H%M%S).dump"
docker compose "$@" exec -T db sh -c 'pg_dump -U "$POSTGRES_USER" -d "$POSTGRES_DB" -Fc' > "$file"
if [ ! -s "$file" ]; then
  echo "Backup vazio; verifique o banco." >&2
  exit 1
fi
echo "Backup criado: $file"
