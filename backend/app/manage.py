"""Criação/recuperação local de conta sem expor senha na linha de comando."""

import getpass
from sqlalchemy import select, update
from .db import SessionLocal
from .models import RefreshSession, User
from .schemas import Register
from .security import passwords


def main():
    email = input("E-mail da conta: ").strip().lower()
    name = input("Nome: ").strip()
    password = getpass.getpass("Nova senha (mínimo 12 caracteres): ")
    if password != getpass.getpass("Repita a senha: "):
        raise SystemExit("Senhas diferentes")
    data = Register(email=email, name=name, password=password)
    with SessionLocal() as db:
        user = db.scalar(select(User).where(User.email == str(data.email).lower()))
        if user:
            if input("Conta existe. Redefinir senha e revogar sessões? Digite SIM: ") != "SIM":
                return
            user.name = data.name
            user.password_hash = passwords.hash(data.password)
            db.execute(update(RefreshSession).where(RefreshSession.user_id == user.id).values(revoked=True))
        else:
            db.add(
                User(
                    email=str(data.email).lower(), name=data.name, password_hash=passwords.hash(data.password)
                )
            )
        db.commit()
    print("Conta salva. Faça login na interface.")


if __name__ == "__main__":
    main()
