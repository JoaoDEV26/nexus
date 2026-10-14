"""Execute uma vez. Não sobrescreve configurações existentes."""
from pathlib import Path
import secrets
path=Path(".env")
if path.exists(): raise SystemExit(".env já existe; mantido sem alterações.")
value=Path(".env.example").read_text()
value=value.replace("POSTGRES_PASSWORD=SUBSTITUIR", "POSTGRES_PASSWORD="+secrets.token_hex(24))
value=value.replace("JWT_SECRET=SUBSTITUIR", "JWT_SECRET="+secrets.token_hex(32))
path.write_text(value)
path.chmod(0o600)
print(".env criado com valores aleatórios. Não publique este arquivo.")
