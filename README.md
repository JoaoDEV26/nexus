# Nexus

Plataforma de estudo para gestão de projetos e tarefas por organização.

React · TypeScript · FastAPI · PostgreSQL · Docker

## Estado da entrega

Código da versão de estudo implementado. Consulte `docs/VALIDATION.md` para distinguir verificações executadas das pendentes. Nenhuma demo pública nem execução de GitHub Actions é presumida.

## Funcionalidades

Cadastro local e login; sessões renováveis; organizações; quatro papéis; projetos; tarefas; responsáveis; prioridades; prazos; filtros; paginação de tarefas/projetos/eventos; comentários; histórico; dashboard.

## Requisitos

Windows com WSL 2, Ubuntu, Docker Desktop integrado ao Ubuntu, Git e VS Code. O manual acompanha o pacote e começa pela instalação. No caminho Docker, não é necessário instalar Node, PostgreSQL ou bibliotecas Python diretamente no Windows.

## Executar

No Ubuntu, na pasta que contém este README:

```bash
python3 scripts/setup_env.py
docker compose build
docker compose up -d db
docker compose run --rm api alembic upgrade head
docker compose up -d api web
```

Interface: http://localhost:5173

API interativa: http://localhost:8000/api/docs

Crie uma conta pela interface. Senha com pelo menos 12 caracteres. Use dados fictícios. Abra sempre localhost, sem alternar com 127.0.0.1, pois a origem é validada.

## Verificar

```bash
docker compose exec api ruff check .
docker compose exec web npm run build
docker compose -f compose.test.yaml up --build --abort-on-container-exit --exit-code-from tests
docker compose -f compose.test.yaml down
```

O compose de testes possui banco separado e descartável. Não altere TEST_DATABASE_URL para apontar ao banco da aplicação.

## Parar e retomar

```bash
docker compose stop
docker compose start
```

`docker compose down` remove containers e rede; os dados permanecem no volume. `docker compose down -v` também apaga o volume e não faz parte da rotina.

## Documentação

- [Arquitetura e limites](docs/ARCHITECTURE.md)
- [Validação](docs/VALIDATION.md)
- [Manual completo em texto](docs/MANUAL.md)

O CI definido em `.github/workflows/ci.yml` verifica backend com PostgreSQL, build do frontend e inicialização em Docker. O resultado deve ser consultado na aba Actions após publicar o repositório.

## Autoria e aprendizado

Base preparada com assistência de IA para estudo de João Gabriel. Evolua o código, registre suas próprias mudanças e demonstre as decisões que consegue explicar. Não atribua a este projeto experiência profissional ou uso real ainda não comprovados.

Licença de distribuição ainda não escolhida pelo autor. Não há credenciais de demonstração fixas no código da aplicação.
