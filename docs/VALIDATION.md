# Verificação desta entrega

Preparação em 2 de outubro de 2026. Os resultados abaixo descrevem o ambiente do assistente, não o computador do usuário.

## Executado

- 13 testes da API aprovados em SQLite, com chaves estrangeiras ativadas.
- Ruff aprovado para o backend.
- TypeScript e build Vite aprovados; dependências registradas no package-lock.json.
- Migration inicial gerada, aplicada em banco SQLite vazio e conferida com alembic check sem diferenças.
- API iniciada via Uvicorn e servidor frontend iniciado via Vite, fora de Docker.
- Arquivos YAML lidos sem erro de sintaxe; scripts de backup conferidos com bash -n.
- Manual Word renderizado e revisado visualmente antes da entrega.

A suíte emitiu um aviso de descontinuação da integração httpx do Starlette TestClient. Não houve falha. Ao atualizar dependências, revisar a recomendação da biblioteca e repetir os testes; não suprimir o aviso sem entender a mudança.

## Não executado neste ambiente

- PostgreSQL real, imagens e rede Docker: runtime indisponível aqui.
- Instalação no Windows/WSL do usuário.
- Execução efetiva do GitHub Actions em um repositório remoto.
- Navegação automatizada ou revisão visual da interface no navegador: não foi possível instalar o binário de navegador neste ambiente. O build não substitui essa revisão.
- Backup/restauração real do PostgreSQL e emissão de certificado HTTPS.
- Hospedagem, testes de carga, revisão completa de segurança e acessibilidade.

## Portões antes de divulgar como funcionando

1. Executar `docker compose -f compose.test.yaml up --build --abort-on-container-exit --exit-code-from tests` e obter todos os testes aprovados em PostgreSQL.
2. Executar o roteiro de uso com duas contas e duas organizações, incluindo os estados de erro e telas em largura de celular.
3. Obter os três jobs verdes no GitHub Actions, inclusive construção e inicialização Docker.
4. Restaurar backup em banco separado conforme o manual.
5. Se publicar uma demo, verificar HTTPS, login, isolamento e persistência no servidor.

## Limites de engenharia conhecidos

Versão para estudo com componentes/rotas concentrados, sem testes automatizados de frontend, sem e-mail de recuperação, sem sincronização de refresh entre abas, sem deploy automático e sem infraestrutura redundante. O bloqueio de linhas não recebeu testes de concorrência em PostgreSQL. Auditar a ordem dos locks e tratamento de deadlocks antes de uso concorrente relevante. Membros/organizações ainda não têm paginação.

Os comandos de testes removem tabelas exclusivamente no banco nexus_test. O banco de teste usa credenciais fictícias e não deve apontar para dados reais. O compose local publica portas somente em 127.0.0.1; a configuração de hospedagem publica apenas as portas do proxy.
