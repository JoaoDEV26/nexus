# Arquitetura da versão de estudo

Monorepo com React/TypeScript, API FastAPI e PostgreSQL. A API é um monólito; não há microsserviços.

- `models.py`: entidades, índices e chaves estrangeiras compostas.
- `schemas.py`: contratos de entrada, tamanhos e campos permitidos.
- `services.py`: autorização e regras reutilizadas.
- `main.py`: rotas e transações. Está concentrado para permitir acompanhar o fluxo inicial; separar roteadores por domínio é exercício futuro.
- `security.py`: Argon2, JWT, sessão persistida, renovação e origem.
- `alembic/versions/`: schema histórico explícito, independente de alterações futuras nos models.
- `frontend/src/api.ts`: transporte e renovação serializada dentro de uma aba.
- `frontend/src/App.tsx`: páginas e formulários. A divisão em arquivos por página é uma próxima refatoração.

O banco é compartilhado por organizações. Cada rota valida um vínculo ativo; consultas filtram organization_id. FKs compostas impedem tarefas ligadas a projetos/responsáveis de outra organização. Isso não equivale a RLS: ainda exige cuidado em todas as consultas novas.

Membro pode ver os projetos da organização, comentar e mover somente suas tarefas. Gestor cria e edita projetos/tarefas. Admin administra membros comuns e gestores. Owner também administra Admins. Owner não pode ser removido. Membros são desativados; registros não são apagados.

Projeto só conclui sem tarefas pendentes não arquivadas. Tarefas de projeto fechado não são alteradas. Reabrir tarefa limpa completed_at. Eventos são gravados na mesma transação da alteração, mas não são um log imutável contra administradores do banco.

Datas de prazo usam America/Sao_Paulo; timestamps usam UTC. Dashboard conta tarefas atualmente concluídas no intervalo, não produtividade individual nem total histórico de transições.

## Decisões em relação ao plano inicial

Esta entrega é uma versão de estudo implementada. Mantém o núcleo do produto. Autoria de projeto é obtida no evento de criação, em vez de uma coluna no projeto. Arquivamento de tarefa usa booleano. Todas as rotas reais estão em `/api/docs`; o esboço da Fase 1 não é um contrato já implementado. Membros e organizações são listados sem paginação, adequado à escala didática e uma limitação a corrigir antes de crescimento.

JWT tem 15 minutos; refresh tem sete dias, rotativo, hash no banco. Cada requisição também verifica a sessão no banco, permitindo revogação imediata. Reuso de refresh revoga a família. Duas abas renovando ao mesmo tempo podem encerrar a sessão por detecção de reuso; não há sincronização entre abas nesta versão.

Produção usa Nginx para arquivos e proxy, Caddy para HTTPS e cadastro público desativado. Recuperação de senha é administrativa via CLI; não há e-mail nem verificação de endereço. Limite de login no Nginx atrás do Caddy é conservador e agregado pelo IP do proxy. Antes de disponibilizar a muitos usuários, configurar cadeia de proxies confiáveis e rate limiting por origem real/conta.

Anexos, clientes, equipes internas, notificações, faturamento, convites por e-mail e deploy automático não foram implementados. CI valida; publicação é manual. Não chamar isso de CI/CD completo nem de SaaS pronto para venda.
