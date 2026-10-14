#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")/.."
file="${1:?Informe o arquivo de backup}"
shift
# Cria OUTRO banco, sem apagar o banco da aplicação. Falha se o nome já existe.
docker compose "$@" exec -T db sh -c 'createdb -U "$POSTGRES_USER" nexus_restore_check'
docker compose "$@" exec -T db sh -c 'pg_restore -U "$POSTGRES_USER" -d nexus_restore_check --exit-on-error' < "$file"
docker compose "$@" exec -T db sh -c 'psql -U "$POSTGRES_USER" -d nexus_restore_check -c "SELECT count(*) FROM tasks;"'
echo "Restauração concluída em nexus_restore_check. O banco original foi preservado."
