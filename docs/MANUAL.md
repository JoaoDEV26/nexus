# Manual de desenvolvimento do Nexus

Guia prático para João Gabriel aprender programação construindo um projeto full stack no Windows com WSL

Edição de 2 de outubro de 2026 · Versão de estudo 0.1

Este manual parte de um computador sem ambiente de desenvolvimento preparado. Ele acompanha o pacote Nexus-Curso-Completo.zip, que contém os arquivos de uma aplicação de estudo. Você vai instalar as ferramentas, executar a aplicação, entender seus componentes, realizar uma alteração, testar, versionar e publicar o código no GitHub. O capítulo de hospedagem descreve também uma implantação manual com domínio e HTTPS.

O resultado local é uma plataforma de projetos e tarefas com contas, organizações, permissões, comentários, histórico e indicadores. Finalizar o roteiro significa conseguir executar e explicar esse fluxo. Não significa que um sistema comercial foi auditado ou que todos os itens do plano original de SaaS foram implementados.

A implementação foi preparada com assistência de IA. Seu aprendizado estará em ler, executar, investigar, modificar e validar o código. O objetivo é que você consiga explicar uma decisão e demonstrar seu efeito, inclusive quando algo dá errado.

## 1 Como usar este material

Leia uma etapa antes de executar seus comandos. Depois confira o resultado esperado. Todos os arquivos necessários estão no pacote; você não precisa adivinhar trechos omitidos nem criar dependências não mencionadas. O código completo está nos arquivos, enquanto o manual explica como utilizá-lo e estudá-lo. Manter o código nos arquivos também evita erros ao copiar centenas de linhas de um documento Word.

Existem três lugares diferentes para trabalhar: PowerShell do Windows, terminal do Ubuntu e navegador. Nos capítulos de hospedagem haverá um quarto lugar: terminal do servidor remoto. A indicação acima de cada bloco informa o lugar correto. Comandos do Ubuntu também podem ser executados no terminal integrado do VS Code quando a janela estiver conectada ao WSL.

Um bloco com várias linhas contém comandos a executar na ordem. Quando uma linha termina com barra invertida, ela continua na próxima linha. Não copie os delimitadores de bloco nem um símbolo de prompt como $ ou >. Textos como SEU_USUARIO e IP_DO_SERVIDOR são campos que você deve substituir; não são valores prontos.

O roteiro completo foi entregue de uma vez. Você não precisa executá-lo em uma sessão. Anote a última conferência concluída e retome dali. Instalar uma ferramenta, usá-la e explicar sua função vale mais que avançar dez páginas sem compreender o resultado.

### Evidência e limites da entrega

As verificações executadas estão em docs/VALIDATION.md. Testes locais da API utilizaram SQLite porque este ambiente de preparação não dispõe de Docker ou de PostgreSQL executável. O pacote contém testes e um pipeline para PostgreSQL, mas o resultado desse pipeline só existirá depois que você o executar. Instalação no seu Windows, infraestrutura Docker e hospedagem devem ser verificadas no destino.

Não há contas suas conectadas, repositório remoto criado, cobrança contratada ou domínio publicado por esta entrega. Os passos correspondentes são ações que você realizará. Não anuncie testes em PostgreSQL, CI verde ou demo online antes de observar esses resultados.

### Ordem do percurso

| Parte | Resultado esperado |
| --- | --- |
| Ambiente | Ubuntu no WSL, editor e Docker funcionando |
| Execução | Nexus acessível em localhost com dados persistentes |
| Compreensão | Você identifica a função dos arquivos e acompanha uma requisição |
| Alteração | Uma mudança sua, verificada e registrada em Git |
| GitHub | Repositório público com README e CI verificado |
| Operação | Backup restaurado em banco separado |
| Hospedagem | Opcionalmente, aplicação acessível por HTTPS em servidor próprio |

## 2 Entenda o que vamos construir

Imagine a organização fictícia Aurora Studio. João organiza o projeto Portal institucional. Ana recebe a tarefa Criar página inicial, define o andamento e comenta a entrega. João acompanha pendências, prazos e histórico. Outra organização, chamada Horizonte, possui seus próprios dados e não pode acessar a Aurora.

O frontend é a parte visual, executada no navegador. O backend recebe as solicitações e decide o que é permitido. O banco guarda os registros. O Docker inicia os processos em ambientes configurados; o Compose descreve como esses processos se conectam.

| Tecnologia | Função neste projeto |
| --- | --- |
| React e TypeScript | Telas, formulários e tipos de dados da interface |
| Vite | Servidor de desenvolvimento e geração do frontend para publicação |
| FastAPI e Python | Rotas da API e regras de negócio |
| Pydantic | Validação das informações recebidas |
| SQLAlchemy | Consultas e mapeamento de entidades para tabelas |
| Alembic | Histórico de mudanças na estrutura do banco |
| PostgreSQL | Banco utilizado no ambiente Docker |
| Git e GitHub | Histórico local, hospedagem do código e verificações automatizadas |

Uma API é um conjunto de endereços e regras para trocar informações. Quando você salva uma tarefa, o navegador envia uma requisição HTTP com dados em JSON. O backend valida os dados, verifica seu acesso, grava a tarefa e responde. Só então a tela apresenta o resultado.

A primeira versão não inclui pagamentos, anexos, e-mails automáticos, recuperação de senha por e-mail ou projetos privados dentro de uma organização. O cadastro de membros utiliza contas já existentes. Todos os membros ativos consultam todos os projetos da organização.

## 3 Preparar o Windows e instalar o Ubuntu

Objetivo: criar o ambiente Linux em que você trabalhará. Salve os documentos abertos antes de reiniciar o Windows.

No Windows, pressione Windows + R, digite winver e pressione Enter. Anote a edição e a versão. Para a instalação simplificada do WSL, a Microsoft documenta Windows 11 ou Windows 10 a partir da versão 2004, compilação 19041. Isso não substitui os requisitos mais recentes do Docker Desktop. [1]

Abra o Gerenciador de Tarefas com Ctrl + Shift + Esc, entre em Desempenho e CPU e verifique o campo Virtualização. Se estiver desabilitado, a configuração depende do fabricante do computador; consulte o manual do modelo antes de mudar BIOS/UEFI. Em máquina administrada por empresa, a alteração pode depender do administrador.

Onde executar: PowerShell como administrador. Procure PowerShell no menu Iniciar, clique com o botão direito e escolha Executar como administrador.

```powershell
wsl --install -d Ubuntu
```

wsl chama o subsistema Linux; --install pede instalação; -d escolhe a distribuição. Reinicie o computador após a instalação. Abra Ubuntu pelo menu Iniciar e conclua a criação do usuário, por exemplo joao, e da senha. A senha não aparece enquanto você digita; pressione Enter após digitá-la.

Onde executar: PowerShell, depois de reiniciar.

```powershell
wsl --update
wsl --list --verbose
wsl --version
```

Resultado esperado: Ubuntu listado com VERSION igual a 2. A versão do programa WSL, exibida pelo último comando, é uma informação diferente da coluna VERSION. Se Ubuntu aparecer usando versão 1, execute wsl --set-version Ubuntu 2 e confira novamente. Se o nome listado for diferente, utilize o nome mostrado na lista. [1]

Onde executar: terminal Ubuntu.

```bash
sudo apt update
sudo apt upgrade -y
sudo apt install -y git curl unzip python3 ca-certificates
```

sudo executa a ação com privilégio administrativo no Linux. apt update atualiza o catálogo de pacotes; apt upgrade atualiza os pacotes instalados; apt install instala as ferramentas. A senha solicitada é a do Ubuntu. O indicador -y aceita as confirmações do gerenciador.

Conferência: execute os comandos abaixo no Ubuntu. Eles devem mostrar o diretório atual, seu usuário e as versões instaladas.

```bash
pwd
whoami
git --version
python3 --version
```

## 4 Instalar o editor e o Docker

Objetivo: editar os arquivos pelo Windows e executar os serviços integrados ao Ubuntu.

No navegador do Windows, acesse https://code.visualstudio.com/ e instale o Visual Studio Code para Windows. Se oferecida pelo instalador, mantenha a opção de adicionar ao PATH. Abra o editor, pressione Ctrl + Shift + X e instale a extensão WSL publicada pela Microsoft. O editor deve ser instalado no Windows; a extensão conecta a janela ao Linux. [2]

No navegador do Windows, abra https://docs.docker.com/desktop/setup/install/windows-install/ e baixe Docker Desktop para a arquitetura do computador. A maioria dos computadores Intel/AMD usa x86_64; confira em Configurações do Windows, Sistema, Sobre. A página oficial lista requisitos atuais, incluindo 8 GB de RAM e virtualização habilitada. Instalar WSL com sucesso não garante compatibilidade com a versão atual do Docker. [3]

Execute o instalador e escolha o backend WSL 2 quando houver essa opção. Abra Docker Desktop e espere o mecanismo iniciar. Em Settings, General, confira Use the WSL 2 based engine. Em Resources, WSL Integration, habilite Ubuntu e aplique as alterações. Use containers Linux. Os nomes exatos dos menus podem mudar entre versões. [4]

Neste percurso, o Docker Engine vem do Docker Desktop. Não execute instruções de instalação de outro Docker Engine dentro do Ubuntu do WSL. O capítulo de servidor Linux é um cenário separado.

Onde executar: Ubuntu.

```bash
docker version
docker compose version
docker run --rm hello-world
```

Resultado esperado: informações de Client e Server, versão do Compose e mensagem de sucesso do hello-world. O container de demonstração é removido ao terminar por causa de --rm.

Se aparecer Cannot connect to the Docker daemon, abra Docker Desktop e confira a integração com Ubuntu. Se docker não for encontrado, feche e reabra Ubuntu após habilitar a integração. Não tente corrigir isso com chmod 777 no socket.

Onde executar: Ubuntu.

```bash
mkdir -p ~/projetos
cd ~/projetos
code .
```

mkdir cria a pasta, -p aceita pais ausentes, ~ representa sua pasta pessoal, cd muda de diretório e code . abre o diretório atual. O VS Code deverá mostrar uma conexão WSL com Ubuntu no canto inferior esquerdo. Se code não existir, reinicie o terminal e confira a extensão e a instalação do editor.

## 5 Colocar os arquivos no lugar certo

Objetivo: trabalhar com o projeto dentro do sistema de arquivos Linux. Isso facilita a integração das ferramentas. [2]

Baixe Nexus-Curso-Completo.zip pelo link da conversa e use Extrair Tudo no Windows. A extração contém uma pasta nexus. Esse pacote é completo; não é necessário misturá-lo com o ZIP da Fase 1.

Onde executar: Ubuntu.

```bash
mkdir -p ~/projetos
cd ~/projetos
explorer.exe .
```

O último comando abre o Explorador de Arquivos do Windows exatamente na pasta Linux atual. Copie a pasta nexus extraída para essa janela. Se já existir uma pasta nexus, não substitua arquivos sem conferir o conteúdo; renomeie a pasta anterior para manter seu trabalho.

Onde executar: Ubuntu.

```bash
cd ~/projetos/nexus
ls
code .
```

Resultado esperado: README.md, backend, frontend, docs, scripts e compose.yaml diretamente nessa pasta. Se houver apenas outra pasta nexus, você está um nível acima. Abra a pasta correta antes de continuar.

No VS Code conectado ao WSL, use Terminal, Novo Terminal. Execute pwd. O resultado deve terminar em /projetos/nexus. A partir deste ponto, quando o manual disser raiz do projeto, refere-se a essa pasta.

| Arquivo ou pasta | O que você encontrará |
| --- | --- |
| backend/app | Código Python da API |
| backend/alembic | Migrations do banco |
| backend/tests | Testes automatizados |
| frontend/src | Interface React e estilos |
| compose.yaml | Ambiente local |
| compose.test.yaml | Ambiente de testes isolado |
| compose.prod.yaml | Configuração de hospedagem |
| .github/workflows/ci.yml | Verificações do GitHub Actions |
| docs | Manual, arquitetura e registro de validação |

## 6 Os primeiros conceitos de programação

Você pode executar a aplicação antes de dominar todas as linguagens. Para estudar o código, comece pelos conceitos abaixo e localize um exemplo de cada um.

Uma variável dá nome a um valor. Uma função recebe informações, executa instruções e pode devolver um resultado. Uma condição escolhe um caminho. Uma lista reúne elementos; um dicionário relaciona chaves e valores. Um módulo é um arquivo Python que pode ser importado por outros arquivos.

Exemplo didático em Python, para leitura:

```python
status = "TODO"

def pode_concluir(pendentes):
    return pendentes == 0

if pode_concluir(0):
    status = "COMPLETED"
```

O sinal = atribui um valor; == compara valores. A indentação define os blocos de Python. Quatro espaços é o padrão usado no projeto. Não apague a indentação ao editar funções.

Em TypeScript, uma função de componente retorna a descrição da interface. O estado guarda dados que podem mudar e provocar uma atualização da tela. O tipo define o formato esperado; não substitui a validação no servidor.

Exemplo didático em TypeScript, para leitura:

```typescript
type Task = { title: string; status: string };
const tarefa: Task = { title: "Estudar API", status: "TODO" };
```

HTML descreve a estrutura; CSS define aparência e organização visual; JavaScript/TypeScript controla comportamento. JSON transporta dados, como {"status":"DONE"}. SQL consulta o banco. Não é necessário aprender tudo de uma vez: cada capítulo liga o conceito a um arquivo existente.

Exercício de leitura: abra backend/app/schemas.py, procure TaskStatus e identifique o campo status. Abra frontend/src/api.ts e encontre o tipo Task. Os dois lados descrevem dados relacionados, mas o backend continua sendo a autoridade sobre o que aceita.

## 7 Preparar as configurações locais

Objetivo: criar senhas e configurações específicas da sua instalação sem publicá-las no GitHub.

Onde executar: Ubuntu, na raiz do projeto.

```bash
python3 scripts/setup_env.py
```

Resultado esperado: mensagem informando criação de .env. O script lê .env.example, gera valores aleatórios para a senha do banco e JWT_SECRET e cria .env com permissão restrita. Se o arquivo já existir, o script o preserva e encerra; isso evita trocar a senha de um banco existente por acidente.

O ponto inicial em .env é parte do nome. No VS Code, o arquivo pode aparecer normalmente. Seu conteúdo não deve ser copiado para mensagens, capturas ou commits. O arquivo .env.example contém apenas um modelo sem segredos reais.

| Variável | Significado |
| --- | --- |
| POSTGRES_DB | Nome do banco |
| POSTGRES_USER | Usuário do banco |
| POSTGRES_PASSWORD | Senha gerada para o banco |
| JWT_SECRET | Chave usada para assinar e verificar tokens |
| APP_ORIGIN | Endereço exato da interface autorizada |
| COOKIE_SECURE | Exige HTTPS no cookie quando true |
| ALLOW_REGISTRATION | Permite cadastro pela interface quando true |

Para desenvolvimento, mantenha APP_ORIGIN=http://localhost:5173, COOKIE_SECURE=false e ALLOW_REGISTRATION=true. O cookie local precisa funcionar em HTTP. A configuração de hospedagem força HTTPS e desativa cadastro público.

Onde executar: Ubuntu, na raiz.

```bash
docker compose config --quiet
```

Resultado esperado: terminar sem mensagem de erro. --quiet evita imprimir a configuração expandida, que pode conter segredos. Não altere a senha do PostgreSQL no .env depois de criar o volume esperando que o usuário do banco mude automaticamente; essa configuração inicializa um banco novo.

## 8 Construir e iniciar o Nexus

Objetivo: subir banco, aplicar o schema e iniciar API e interface. Execute os comandos nesta ordem, na raiz do projeto.

Onde executar: Ubuntu.

```bash
docker compose build
docker compose up -d db
docker compose run --rm api alembic upgrade head
docker compose up -d api web
docker compose ps
```

build constrói as imagens. A primeira execução baixa dependências e demora mais. up -d db inicia o banco em segundo plano. run --rm api executa uma tarefa temporária no ambiente da API e remove esse container ao terminar. alembic upgrade head aplica as migrations até a versão mais recente. Finalmente, api e web são iniciados.

O arquivo requirements.txt fixa as versões Python usadas na preparação. package-lock.json fixa a árvore de dependências do frontend e npm ci a reproduz. As tags de imagens Docker utilizadas não estão fixadas por digest; builds posteriores podem receber correções dessas imagens. Reexecute verificações após atualizações.

Onde conferir: navegador do Windows.

```text
http://localhost:5173
http://localhost:8000/health/ready
http://localhost:8000/api/docs
```

O primeiro endereço deve mostrar o login. O segundo deve responder {"status":"ok"}. O terceiro apresenta a documentação interativa da API. Use localhost de forma consistente; alternar para 127.0.0.1 muda a origem e pode causar rejeição no login.

Onde executar: Ubuntu, se um serviço não iniciar.

```bash
docker compose logs --tail=80 api
docker compose logs --tail=80 web
docker compose logs --tail=80 db
```

Leia o final do erro antes de repetir comandos. Não apague volumes como tentativa genérica de correção. Caso veja que uma tabela não existe, confira se a migration terminou sem erro.

### Parar e retomar

```bash
docker compose stop
docker compose start
```

stop pausa os serviços sem remover containers ou dados. start retoma containers existentes. Depois de mudanças em dependências, use docker compose up -d --build. Se os containers foram removidos com down, recrie com up -d.

O volume postgres_data conserva registros fora do ciclo de vida do container. docker compose down -v apaga esse volume: não é um comando de rotina e não deve ser usado para preservar trabalho.

## 9 Usar o fluxo completo pela primeira vez

Objetivo: observar a aplicação antes de alterar código. Todas as pessoas e organizações deste exercício são fictícias. Escolha senhas próprias com pelo menos 12 caracteres.

1. Abra http://localhost:5173 e escolha Criar conta. Cadastre João de Estudo com e-mail joao@example.com. Esse endereço é apenas identificador neste exercício; o sistema não envia e-mail.
2. Crie a organização Aurora Studio. Seu vínculo será Owner, apresentado como Proprietário.
3. Em Projetos, crie Portal institucional e descreva a entrega. O status inicial será Ativo.
4. Clique em Sair. Cadastre Ana de Estudo, com ana@example.com. Depois saia dessa conta e entre novamente como João.
5. Em Membros, adicione ana@example.com como Membro. A conta precisa existir antes de ser adicionada.
6. Em Tarefas, crie Criar página inicial, selecione Portal institucional, atribua a Ana e escolha prioridade Alta. Use o dia anterior ao dia da execução como prazo para observar o indicador de atraso.
7. Saia e entre como Ana. Abra Tarefas e mova a tarefa para Em andamento. Em Detalhes, adicione um comentário. Depois marque Concluída.
8. Volte à conta João. Confira Visão geral e Histórico. O atraso deve desaparecer e a conclusão deve aparecer se o período incluir a data atual.
9. Em Projetos, edite o projeto e marque Concluído. Para voltar a alterar as tarefas, reabra o projeto como Ativo.
10. Crie outra organização pela conta João. Ela deve começar sem os projetos da Aurora. Alterne a organização no menu e confira a separação.

Conferência: você consegue explicar quem criou o projeto, quem recebeu a tarefa, qual mudança ocorreu e por que o dashboard se alterou. Trocar de organização não deve misturar tarefas ou indicadores.

Exercício de permissão: na conta Ana, confira que não aparecem formulários administrativos de projetos e tarefas. A API também bloqueia ações indevidas; a ausência de um botão, sozinha, não seria proteção suficiente.

## 10 Acompanhar uma requisição do começo ao fim

Objetivo: entender o caminho do botão Salvar tarefa até o banco.

Abra frontend/src/App.tsx e procure function Tasks. O formulário coleta título, descrição, prioridade, responsável e prazo. Ao enviar, a função save monta um objeto e chama api. Abra frontend/src/api.ts e veja fetch: ele faz a requisição HTTP, envia JSON e inclui o token quando existe.

No ambiente local, Vite encaminha /api para a API usando a configuração em vite.config.ts. Isso permite que a interface use o mesmo endereço de origem. Em hospedagem, Nginx faz esse encaminhamento.

Abra backend/app/main.py e procure create_task. O parâmetro data usa o contrato TaskCreate de schemas.py. FastAPI transforma o JSON em dados validados. current_user identifica a conta; member verifica vínculo com a organização; permit verifica o papel. O serviço ainda confere o responsável e o projeto.

A rota cria um objeto Task, chama flush para obter o ID, adiciona Activity e confirma com commit. Se algo falhar antes do commit, a sessão faz rollback. Por isso a tarefa e seu evento não devem ficar pela metade.

A resposta retorna ao navegador. O frontend invalida as consultas do TanStack Query para buscar os dados atualizados. Essa biblioteca controla cache e carregamento das consultas; ela não decide permissões.

Onde observar: navegador, F12, aba Network ou Rede. Salve uma tarefa e selecione a requisição POST correspondente. Confira endereço, método, status e JSON. Não compartilhe o cabeçalho Authorization: ele contém um token de acesso.

| Código HTTP | O que significa neste projeto |
| --- | --- |
| 200 | Leitura ou alteração concluída |
| 201 | Registro criado |
| 204 | Ação concluída sem corpo de resposta |
| 401 | Sessão ausente, inválida ou expirada |
| 403 | Usuário identificado, mas sem permissão para a ação |
| 404 | Recurso não encontrado ou fora da organização autorizada |
| 409 | Conflito de regra ou de integridade |
| 422 | Campos inválidos |

## 11 Entender o banco e as migrations

Objetivo: distinguir dados, modelos e evolução de schema.

backend/app/models.py descreve as tabelas. User é a conta. Organization é o espaço de trabalho. Membership liga conta e organização e guarda o papel. Project organiza entregas. Task guarda a unidade de trabalho. Comment armazena comentários. Activity registra alterações. RefreshSession controla sessões renováveis.

Uma chave primária identifica um registro. Uma chave estrangeira exige que um registro referenciado exista. Uma restrição única impede duplicação. Uma transação reúne operações que devem ser confirmadas ou revertidas juntas.

A tarefa tem organization_id e project_id. A chave estrangeira composta exige que esse par exista em Project. Assim, mesmo um erro na aplicação não deveria criar uma tarefa da Aurora ligada a um projeto da Horizonte. Ainda é necessário limitar as consultas: uma FK não impede alguém de ler uma tabela inteira.

Alembic guarda uma sequência de alterações do banco. A migration inicial cria as tabelas e restrições explicitamente. Não edite uma migration já aplicada para fazer uma mudança nova; crie outra migration e revise seu conteúdo.

Onde executar: Ubuntu, com a aplicação iniciada.

```bash
docker compose exec api alembic current
docker compose exec api alembic history
docker compose exec api alembic check
```

current mostra a revisão aplicada, history mostra a sequência e check verifica diferenças detectáveis entre os modelos e o schema. O resultado esperado de check, sem mudanças, é não encontrar operações novas.

Onde executar: Ubuntu, para observar o banco sem alterá-lo.

```bash
docker compose exec db psql -U nexus -d nexus
```

Agora você está no console SQL, não no Bash. Execute:

```sql
SELECT name FROM organizations;
SELECT title, status, priority FROM tasks;
```

Para sair do psql, digite \q e pressione Enter. Não faça alterações manuais para contornar uma regra da API. Este exercício é de leitura.

## 12 Entender autenticação e sessões

Objetivo: compreender o que acontece entre login e logout sem tratar segurança como uma palavra no README.

Autenticação responde quem está acessando. Autorização responde o que essa pessoa pode fazer. São verificações diferentes. No Nexus, estar autenticado não permite ler qualquer organização.

A senha não é armazenada como texto: pwdlib produz um hash Argon2. No login, a biblioteca verifica a senha apresentada contra o hash. Hash não é uma senha criptografada que o aplicativo precisa descriptografar. O exemplo oficial de FastAPI também demonstra uso de bibliotecas de hashing e JWT. [5]

O access token é um JWT com expiração de 15 minutos. A interface o mantém em memória. O refresh token é opaco, aleatório, e fica em cookie HttpOnly. A API armazena somente seu hash. HttpOnly impede leitura direta do cookie por JavaScript; não elimina todos os riscos de uma aplicação web.

Cada renovação revoga o refresh anterior e emite outro. Reutilizar um token antigo revoga a família da sessão. Cada chamada autenticada consulta também a sessão persistida, permitindo que logout revogue acesso imediatamente nesta implementação.

A validação de Origin nas rotas de sessão exige o endereço configurado em APP_ORIGIN. Em produção, HTTPS e COOKIE_SECURE=true protegem o transporte do cookie. O navegador cuida do cabeçalho Origin nas requisições do frontend.

Limite conhecido: duas abas renovando ao mesmo tempo podem parecer reutilização de refresh e encerrar a sessão. A renovação é serializada dentro de uma aba, mas não entre abas. Esse é um exercício de evolução, não um comportamento que devemos esconder.

### Recuperação administrativa da conta

Nesta versão não há e-mail de recuperação. Para criar uma conta ou redefinir a senha em uma instalação que você administra:

```bash
docker compose exec api python -m app.manage
```

O comando pede e-mail, nome e senha sem colocá-la na linha de comando. Para conta existente, exige confirmação e revoga suas sessões. Esta ferramenta só deve ser usada pelo administrador da instalação.

## 13 Entender papéis e regras de negócio

Objetivo: prever uma permissão antes de testar a interface.

| Ação | Owner | Admin | Manager | Member |
| --- | --- | --- | --- | --- |
| Ler projetos e tarefas da organização | Sim | Sim | Sim | Sim |
| Criar e editar projetos e tarefas | Sim | Sim | Sim | Não |
| Alterar status de qualquer tarefa | Sim | Sim | Sim | Só as próprias |
| Comentar em tarefa ativa | Sim | Sim | Sim | Sim |
| Administrar membros e gestores | Sim | Sim | Não | Não |
| Administrar Admins | Sim | Não | Não | Não |
| Alterar nome da organização | Sim | Sim | Não | Não |

O Owner é protegido contra remoção/rebaixamento no MVP. Não implementamos transferência de propriedade. Admin não administra outro Admin nem se promove. O papel pertence ao vínculo, não à conta global: João pode ser Owner na Aurora e Member na Horizonte.

Mover status tem uma rota separada de editar detalhes. Um Member pode enviar apenas status para sua tarefa. Se tentar adicionar priority ao JSON dessa rota, o schema recusa o campo extra. Essa separação reduz mudanças indevidas de campos administrativos.

Quando um membro é removido, seu vínculo fica inativo. Tarefas abertas atribuídas a ele ficam sem responsável, com eventos correspondentes. Autoria e histórico permanecem. Concluir um projeto exige concluir ou arquivar suas tarefas pendentes. Arquivar não é apagar.

Exercício: abra services.py, leia member, permit e scoped. Explique em uma frase o motivo de existir cada função. Depois localize onde create_task chama essas funções. Se você consegue seguir esse caminho, já está relacionando regra de negócio com implementação.

## 14 Entender e alterar a interface

Objetivo: localizar estrutura visual, comportamento e comunicação com a API.

frontend/src/main.tsx inicializa React, React Router e o cliente de consultas. App.tsx contém login, estrutura da aplicação e páginas. api.ts centraliza fetch e renovação. style.css controla cores, espaçamento e adaptação de layout. A versão didática concentra componentes; separar páginas em arquivos menores é uma próxima refatoração útil.

useState guarda estado local, como o filtro de status. useQuery carrega dados identificados por uma chave; o ID da organização faz parte das chaves para evitar mistura de cache. useEffect executa integração com recursos externos, como a restauração da sessão ao abrir a página.

O formulário usa preventDefault para impedir a navegação padrão do navegador. A função useAction controla erro e estado de envio. Botões são desabilitados durante determinadas operações; a regra continua protegida na API.

TypeScript ajuda a detectar erros de formato durante o build. Ele não valida automaticamente dados maliciosos enviados diretamente à API. Por isso existem schemas Python, restrições no banco e testes.

Primeira mudança visual: no VS Code, abra App.tsx e procure o texto Trabalho organizado. Altere a frase para Organização que vira entrega. Salve com Ctrl + S. A página de login deve atualizar pelo servidor de desenvolvimento. Saia da conta para observar a tela, caso necessário.

Agora execute:

```bash
docker compose exec web npm run build
```

Resultado esperado: compilação TypeScript e build do Vite sem erros. O build é diferente do servidor de desenvolvimento: ele prepara os arquivos que serão servidos na hospedagem.

Exercício de acessibilidade: percorra o formulário de login apenas com Tab, Shift + Tab e Enter. Confira se o foco aparece, os campos têm rótulos e o botão pode ser acionado. Reduza a janela para a largura de um celular e confira navegação e formulários.

## 15 Executar os testes certos

Objetivo: verificar regras e isolamento em banco separado, sem apagar os dados da sua aplicação.

Onde executar: Ubuntu, na raiz do projeto.

```bash
docker compose exec api ruff check .
docker compose exec web npm run build
docker compose -f compose.test.yaml up --build \
  --abort-on-container-exit --exit-code-from tests
```

Ruff procura problemas estáticos de Python. O build verifica TypeScript e gera a interface. O terceiro comando inicia PostgreSQL exclusivo de testes, aplica a migration, verifica diferenças de schema e executa pytest. --exit-code-from tests faz o resultado refletir a saída do serviço de testes.

Resultado esperado: testes aprovados e código de saída zero. Na preparação inicial foram executados 13 testes em SQLite; a suíte pode crescer à medida que você trabalhar. O arquivo VALIDATION.md registra a contagem entregue. Não considere o portfólio validado em PostgreSQL antes de obter esse resultado no seu ambiente ou no CI.

Ao terminar:

```bash
docker compose -f compose.test.yaml down
```

O compose de teste tem nome, serviço e banco próprios. Ele usa memória temporária para os dados do PostgreSQL. Nunca aponte TEST_DATABASE_URL para o banco da aplicação: os testes criam e removem tabelas. Existe uma verificação do nome nexus_test como proteção adicional.

Abra backend/tests/test_api.py. Uma fixture prepara o ambiente de cada teste. assert declara o resultado esperado. Os cenários verificam hash de senha, sessão, ciclo de projeto, permissões, remoção de membro, isolamento, filtros e integridade. Um teste simula falha no histórico e confere que a tarefa não permaneceu gravada.

Se um teste falhar, leia o nome do teste, o assert e a resposta recebida. Não altere a expectativa apenas para obter verde. Primeiro decida se a regra mudou intencionalmente ou se a implementação está incorreta.

## 16 Fazer sua primeira alteração de backend

Objetivo: implementar uma mudança pequena, executar seu teste e compreender por que funciona.

Vamos adicionar uma rota que informa a versão da aplicação. Isso não altera o banco. Abra backend/app/main.py e acrescente ao final:

```python
@app.get("/api/v1/version")
def version():
    return {"name": "Nexus", "version": app.version}
```

O decorator @app.get registra uma rota GET. def declara a função. O dicionário retornado vira JSON. Salve o arquivo; o servidor local usa --reload e deve recarregar.

Abra http://localhost:8000/api/v1/version no navegador. Resultado esperado: name igual a Nexus e version igual a 0.1.0.

Agora abra backend/tests/test_api.py e acrescente:

```python
def test_version_endpoint(client):
    response = client.get("/api/v1/version")
    assert response.status_code == 200
    assert response.json() == {
        "name": "Nexus",
        "version": "0.1.0",
    }
```

Execute novamente a suíte PostgreSQL do capítulo anterior. A contagem deverá aumentar em um. Essa alteração não vem aplicada na base entregue: é seu primeiro exercício de implementação, com código e resultado esperados completos.

Perguntas para registrar no caderno: por que GET? Por que não precisamos de migration? Onde a versão original está definida? O teste faz uma chamada HTTP ou apenas chama a função Python diretamente? O cliente de testes simula a chamada à aplicação sem precisar de um servidor de rede externo.

## 17 Criar o histórico local com Git

Objetivo: registrar o estado inicial e uma mudança real sua. Git funciona localmente; GitHub é o serviço remoto que usaremos depois.

Onde executar: Ubuntu, na raiz. Substitua nome e e-mail pelos seus. O e-mail passa a constar nos commits; você pode usar o endereço noreply fornecido nas configurações de e-mail do GitHub.

```bash
git config --global user.name "João Gabriel"
git config --global user.email "SEU_EMAIL_DE_COMMIT"
git config --global init.defaultBranch main
git init
git status
```

Antes de adicionar arquivos, confirme que .env está ignorado:

```bash
git check-ignore .env
```

Resultado esperado: .env. O .gitignore entregue também exclui node_modules, caches, builds, bancos locais e backups. Git ignore não retira automaticamente um segredo que já foi commitado.

Se ainda não fez o exercício do capítulo 16, registre a base primeiro. Se já fez, o primeiro commit pode registrar a base com o exercício; não invente uma cronologia anterior.

```bash
git add .
git diff --cached --stat
git diff --cached --name-only
git commit -m "chore: adiciona base de estudo do Nexus"
```

git add seleciona mudanças para o próximo commit. diff --cached mostra o que foi selecionado. commit registra um ponto do histórico. Confira os nomes dos arquivos antes de confirmar; .env e backups não devem aparecer.

Para uma próxima mudança, use uma branch:

```bash
git switch -c feat/version-endpoint
```

Faça o exercício da rota de versão, execute as verificações e registre:

```bash
git add backend/app/main.py backend/tests/test_api.py
git diff --cached
git commit -m "feat: adiciona consulta da versão da API"
```

Se o exercício já estiver no primeiro commit, escolha outra mudança real para essa branch. Não recrie commits apenas para aparentar experiência. O importante é saber explicar o que mudou e como você verificou.

## 18 Autenticar e publicar no GitHub

Objetivo: enviar o repositório local para um repositório remoto vazio.

No navegador, entre em https://github.com/ ou crie sua conta. Verifique o e-mail e configure autenticação em duas etapas. Em Settings, Emails, copie o e-mail noreply se quiser utilizá-lo nos commits e ajuste a configuração do Git antes dos próximos commits.

Vamos usar uma chave SSH exclusiva. Onde executar: Ubuntu.

```bash
mkdir -p ~/.ssh
ls ~/.ssh
ssh-keygen -t ed25519 -C "SEU_EMAIL_DE_COMMIT" \
  -f ~/.ssh/id_ed25519_nexus
```

Se id_ed25519_nexus já existir, não sobrescreva; utilize a chave existente ou escolha outro nome e ajuste os comandos seguintes. Quando solicitado, defina uma frase secreta. A chave privada é id_ed25519_nexus; a pública termina em .pub. Apenas a pública será cadastrada no GitHub. [6]

```bash
eval "$(ssh-agent -s)"
ssh-add ~/.ssh/id_ed25519_nexus
cat ~/.ssh/id_ed25519_nexus.pub
```

Em novas sessões do Ubuntu, repita eval e ssh-add antes de usar essa chave, pois o agente pode não estar ativo. Copie a linha pública completa. No GitHub, abra Settings, SSH and GPG keys, New SSH key. Informe um título como Nexus WSL, escolha Authentication Key e cole a chave pública. Confirme.

```bash
ssh -T git@github.com
```

Na primeira conexão, compare a impressão digital mostrada com a página oficial indicada nas fontes antes de aceitar. A resposta esperada informa autenticação bem-sucedida e avisa que GitHub não fornece shell. Essa mensagem pode acompanhar código de saída 1; não significa que a autenticação falhou. [7]

No GitHub, clique em New repository. Nome sugerido: nexus. Escolha Public quando estiver pronto para divulgação. Não marque criação de README, .gitignore ou licença nessa etapa, pois o histórico já existe localmente. Crie o repositório vazio. A escolha de licença pode ser feita depois, conscientemente. [8]

Onde executar: Ubuntu, na raiz. Substitua SEU_USUARIO pelo identificador da sua conta.

```bash
git remote add origin git@github.com:SEU_USUARIO/nexus.git
git push -u origin main
```

-u associa a branch local à remota. Se origin já existir, confira git remote -v antes de alterar; não remova configurações às cegas. Se o remoto não estiver vazio, não use --force como atalho: escolha um repositório vazio ou integre o histórico de forma consciente.

Se você criou uma branch com o exercício:

```bash
git push -u origin feat/version-endpoint
```

No GitHub, abra a sugestão de Compare and pull request. Explique a alteração e a verificação. Aguarde o CI. Com os testes aprovados e o diff conferido, faça o merge e atualize a cópia local:

```bash
git switch main
git pull --ff-only
```

## 19 Conferir o GitHub Actions e preparar o portfólio

Objetivo: obter evidência reproduzível de qualidade e apresentar o projeto com precisão.

Abra a aba Actions do repositório. O arquivo .github/workflows/ci.yml dispara verificações em push para main e em pull requests. Um job roda backend com PostgreSQL; outro compila frontend; o terceiro constrói e inicia containers. As credenciais do banco nesse arquivo são exclusivas de um serviço temporário de testes, não segredos de produção. [9]

Se um job estiver vermelho, abra-o e localize a primeira etapa que falhou. Corrija o problema em uma branch, execute o teste correspondente localmente e envie o commit. O histórico dessa correção é parte legítima do trabalho.

Este pipeline é CI, integração contínua. A hospedagem do capítulo seguinte é manual. Não descreva a entrega como deploy contínuo automático. Também não confunda um build TypeScript aprovado com testes completos de interface.

No README, acrescente uma captura real depois de executar o aplicativo. Use dados fictícios e esconda tokens ou informações pessoais. Crie docs/images, salve a imagem como dashboard.png e inclua:

```markdown
![Dashboard do Nexus](docs/images/dashboard.png)
```

Na página do repositório, edite About: adicione uma descrição curta e topics como python, fastapi, react, typescript e postgresql. Só adicione URL de demo depois que estiver acessível e verificada. Fixe o repositório no seu perfil quando o fluxo principal e o CI estiverem funcionando.

Para criar uma versão identificável após validar:

```bash
git tag -a v0.1.0 -m "Primeira versão de estudo validada"
git push origin v0.1.0
```

No GitHub, abra Releases, Draft a new release, selecione a tag e descreva funcionalidades e limites conhecidos. Esse rótulo não deve prometer uso comercial ou validação inexistente.

## 20 Backup e restauração sem apagar o original

Objetivo: comprovar que os dados podem ser recuperados.

Onde executar: Ubuntu, na raiz, com o banco iniciado.

```bash
bash scripts/backup.sh
```

O script usa pg_dump no formato custom e cria um arquivo em backups. O nome inclui data e hora. A pasta é ignorada pelo Git. Faça uma cópia em outro local protegido se os dados tiverem valor; um backup no mesmo disco não protege contra perda do computador.

Para testar, substitua o nome abaixo pelo arquivo realmente criado:

```bash
bash scripts/verify_backup.sh backups/NOME_DO_ARQUIVO.dump
```

O script cria nexus_restore_check, restaura o backup nesse banco separado e consulta a quantidade de tarefas. Ele não substitui o banco nexus. Se nexus_restore_check já existir, o script falha sem apagá-lo.

Confira alguns registros da cópia:

```bash
docker compose exec db psql -U nexus -d nexus_restore_check
```

Dentro do psql:

```sql
SELECT name FROM organizations;
SELECT title, status FROM tasks;
```

Saia com \q. Somente depois de conferir que se trata da cópia descartável, você pode remover esse banco de conferência:

```bash
docker compose exec db dropdb -U nexus nexus_restore_check
```

O comando acima apaga apenas o banco de conferência nomeado. Não substitua o nome por nexus. Para uma recuperação real, mantenha o banco atual preservado, restaure uma cópia, confira os registros e planeje a troca da aplicação para a cópia validada. A operação depende do incidente e não deve ser automatizada como tentativa genérica de reparo.

## 21 Hospedar com domínio e HTTPS

Objetivo: disponibilizar uma instalação de demonstração administrada por você. Esta etapa exige servidor Linux, domínio, contas e possível custo. Nada foi contratado ou publicado pelo assistente. Você pode concluir o aprendizado local e o GitHub antes de realizá-la.

O caminho descrito usa uma VPS Ubuntu 24.04, Docker Compose, Nginx e Caddy. O provedor é de sua escolha; telas de contratação variam. No painel, crie um servidor Ubuntu 24.04 com IP público, chave SSH e recursos suficientes para construir frontend e executar banco/API. Como ponto de partida de planejamento, considere 2 vCPU e 4 GB de RAM; monitore o uso e ajuste. Isso é uma hipótese de capacidade, não garantia ou orçamento pesquisado.

Configure no firewall do provedor: SSH na porta 22 restrito ao seu IP; HTTP 80 e HTTPS 443 para visitantes. Não exponha 5432, 8000 ou 5173. No DNS do domínio, crie um registro A para nexus.seudominio.com apontando ao IPv4 do servidor. Só adicione AAAA se IPv6 estiver realmente configurado.

Onde executar: Ubuntu local, para entrar no servidor. Use o usuário e a chave informados na criação da VPS.

```bash
ssh -i CAMINHO_DA_CHAVE USUARIO_DO_SERVIDOR@IP_DO_SERVIDOR
```

A partir daqui, confira hostname e pwd antes de executar comandos: você está no servidor, não no WSL. Os próximos passos pressupõem servidor novo Ubuntu 24.04 e usuário com sudo. Se houver aplicações ou Docker existentes, confira a instalação antes de modificá-la.

### Instalar Docker Engine no servidor

Onde executar: servidor Ubuntu. O procedimento usa o repositório oficial Docker. [10]

```bash
sudo apt update
sudo apt install -y ca-certificates curl git python3
sudo install -m 0755 -d /etc/apt/keyrings
sudo curl -fsSL https://download.docker.com/linux/ubuntu/gpg \
  -o /etc/apt/keyrings/docker.asc
sudo chmod a+r /etc/apt/keyrings/docker.asc
```

O bloco seguinte configura o repositório para Ubuntu 24.04, cujo codinome é noble. Confirme a versão com cat /etc/os-release antes de usar esse valor.

```bash
printf '%s\n' \
  'Types: deb' \
  'URIs: https://download.docker.com/linux/ubuntu' \
  'Suites: noble' \
  'Components: stable' \
  "Architectures: $(dpkg --print-architecture)" \
  'Signed-By: /etc/apt/keyrings/docker.asc' \
  | sudo tee /etc/apt/sources.list.d/docker.sources
sudo apt update
sudo apt install -y docker-ce docker-ce-cli containerd.io \
  docker-buildx-plugin docker-compose-plugin
sudo docker run --rm hello-world
```

Usaremos sudo docker no servidor. Isso evita adicionar o usuário ao grupo docker sem explicar que esse grupo oferece acesso administrativo ao host. No WSL, continue usando Docker Desktop como nos capítulos iniciais.

### Preparar a instalação

Onde executar: servidor. O exemplo pressupõe repositório público; substitua SEU_USUARIO.

```bash
mkdir -p ~/apps
cd ~/apps
git clone https://github.com/SEU_USUARIO/nexus.git
cd nexus
python3 scripts/setup_env.py
nano .env
```

No editor nano, acrescente uma linha DOMAIN=nexus.seudominio.com usando seu domínio real, sem https e sem barra final. Salve com Ctrl + O, Enter, e saia com Ctrl + X. A configuração de produção define origem HTTPS, cookie seguro e cadastro público desativado, independentemente das opções locais do .env.

Crie uma função temporária para reduzir erros nos comandos:

```bash
dc() { sudo docker compose -f compose.prod.yaml "$@"; }
dc config --quiet
dc build
dc up -d db
dc run --rm api alembic upgrade head
dc up -d api web caddy
dc ps
```

Essa função existe apenas na sessão atual de terminal. Ao reconectar, execute sua definição novamente dentro da pasta nexus.

O Caddy recebe o domínio pelo Caddyfile e tenta obter/renovar certificado HTTPS automaticamente. Isso depende de DNS correto e acesso às portas necessárias. [11]

```bash
dc logs --tail=80 caddy
dc exec api python -m app.manage
```

O último comando cria sua conta administrativamente. O cadastro público está desativado. Para cadastrar outros participantes de uma demonstração, repita a ferramenta e depois adicione as contas à organização pela interface. O botão de cadastro continua presente, mas a API retorna cadastro público desativado; ajustar essa apresentação é uma melhoria conhecida.

Onde conferir: navegador externo, em https://nexus.seudominio.com. Faça login, crie uma organização e conclua a jornada principal. Confirme HTTPS, persistência após reiniciar serviços e negação de acesso entre organizações. Não use credenciais de produção na demonstração.

### Atualizar com cuidado

Antes de atualizar, faça backup. No servidor, na pasta do projeto:

```bash
sudo bash scripts/backup.sh -f compose.prod.yaml
git pull --ff-only
dc build
dc run --rm api alembic upgrade head
dc up -d api web caddy
```

Revise migrations antes de aplicá-las a dados importantes. Alterar a imagem de PostgreSQL para outra versão principal exige um plano de migração do banco; não é apenas trocar a tag. Não habilite cadastro irrestrito sem desenvolver proteção contra abuso, verificação/recuperação de contas e limites de uso adequados.

Este desenho é uma demonstração em servidor único. Não possui alta disponibilidade, monitoramento externo ou deploy automático. Essas são evoluções posteriores, não recursos já entregues.

## 22 Resolver problemas frequentes

| Sintoma | Conferência e próximo passo |
| --- | --- |
| WSL não inicia | Confira virtualização, reinicialização e wsl --update |
| docker não encontrado no Ubuntu | Abra Docker Desktop e habilite integração WSL para Ubuntu |
| Cannot connect to daemon | Aguarde o mecanismo Docker iniciar; reabra o terminal |
| code não encontrado | Confira VS Code no Windows, extensão WSL e PATH; reinicie terminal |
| .env já existe | O script protegeu a configuração; continue usando o arquivo existente |
| Porta já utilizada | Identifique a aplicação concorrente antes de alterar portas |
| Origem não permitida | Use localhost:5173 e confira APP_ORIGIN; recrie api após alterar .env |
| Tabela não existe | Execute alembic upgrade head e leia a saída |
| Senha de PostgreSQL rejeitada | Confira a senha original do volume; editar .env não altera usuário existente |
| Conta não encontrada ao adicionar membro | Cadastre a conta primeiro e confira o e-mail exato |
| Não é possível concluir projeto | Termine ou arquive tarefas pendentes |
| Sessão encerra com várias abas | Limite conhecido de renovação concorrente; use uma aba e faça login |
| Permission denied publickey no GitHub | Confira ssh-add, chave pública cadastrada e conta correta |
| Push rejeitado | Confira remoto/branch; não use --force para contornar sem entender |
| Frontend não reflete nova dependência | Execute npm ci dentro do serviço web e reinicie-o |
| Certificado HTTPS não emitido | Confira DNS A/AAAA, portas 80/443 e logs do Caddy |

Para atualizar dependências do frontend após mudar package.json e package-lock.json:

```bash
docker compose exec web npm ci
docker compose restart web
```

Para investigar o projeto, reúna o comando executado, o diretório atual, o serviço envolvido e a mensagem completa. Remova senhas e tokens antes de compartilhar. Alterar várias configurações ao mesmo tempo dificulta descobrir a causa.

## 23 Concluir o projeto e explicar suas decisões

Marque os itens somente depois de executar a conferência correspondente.

- WSL 2, Ubuntu e Docker funcionam no seu computador.
- O editor está conectado ao WSL e os arquivos ficam na pasta Linux.
- O Nexus inicia seguindo o README e conserva dados ao reiniciar.
- Você concluiu a jornada com Owner e Member.
- O isolamento entre organizações foi verificado.
- A suíte foi executada em PostgreSQL sem falhas.
- O build do frontend e Ruff passaram.
- Você fez pelo menos uma alteração e explicou o teste.
- .env, tokens, senhas e backups não estão no repositório.
- O repositório está publicado e o resultado do Actions foi conferido.
- O README contém uma captura real e descreve limites com precisão.
- Um backup foi restaurado em banco separado.
- Se houve hospedagem, HTTPS, acesso e persistência foram verificados no destino.

Perguntas para uma entrevista: onde você impede leitura entre organizações? Por que papel fica em Membership? O que acontece se a auditoria falha? Por que Docker não torna a API um conjunto de microsserviços? Como uma migration difere de um modelo? Qual risco existe ao renovar sessão em duas abas? O que seu CI verifica e o que ainda não verifica?

Uma resposta forte aponta o arquivo, explica a regra, mostra um teste e reconhece um limite. Você não precisa apresentar o projeto como maior do que ele é.

Ao chegar a esse ponto, atualize o LinkedIn com as competências realmente praticadas. Cite o projeto como pessoal/de estudo. Se o CI PostgreSQL foi aprovado, você pode descrever esse teste; se a demo não existe, não a anuncie. A reformulação completa do LinkedIn é uma entrega posterior, apoiada nessa evidência.

## 24 Glossário de consulta

| Termo | Significado prático |
| --- | --- |
| Terminal | Interface para executar comandos |
| Diretório raiz do projeto | Pasta com README e compose.yaml |
| Dependência | Biblioteca ou ferramenta utilizada pelo código |
| Imagem Docker | Modelo usado para iniciar containers |
| Container | Processo executado a partir de uma imagem |
| Volume | Armazenamento persistente gerenciado pelo Docker |
| Endpoint | Método e endereço de uma operação da API |
| Schema Pydantic | Contrato que valida dados de entrada |
| Schema do banco | Estrutura de tabelas e restrições |
| Migration | Alteração versionada da estrutura do banco |
| Commit | Registro de um conjunto de alterações no Git |
| Branch | Linha de trabalho no histórico |
| Pull request | Proposta de alteração revisável no GitHub |
| CI | Verificações automáticas integradas ao trabalho com código |
| Deploy | Instalação de uma versão em um ambiente de execução |
| RBAC | Permissões baseadas em papéis |
| Tenant | Organização cujos dados precisam permanecer isolados |
| Hash de senha | Representação usada para verificar senha sem guardar o texto original |
| Rollback | Reversão de uma transação não confirmada |

## 25 Fontes oficiais e próximos estudos

Documentação consultada na preparação em 2 de outubro de 2026. Telas, requisitos e versões podem mudar; confira a página oficial quando uma etapa não coincidir com seu ambiente.

[1] Microsoft Learn. Instalar WSL e comandos básicos. https://learn.microsoft.com/pt-br/windows/wsl/install

[2] Visual Studio Code. Desenvolvimento no WSL. https://code.visualstudio.com/docs/remote/wsl

[3] Docker. Instalação do Docker Desktop no Windows. https://docs.docker.com/desktop/setup/install/windows-install/

[4] Docker. Integração WSL 2. https://docs.docker.com/desktop/features/wsl/

[5] FastAPI. Senhas e JWT. https://fastapi.tiangolo.com/tutorial/security/oauth2-jwt/

[6] GitHub. Gerar chave SSH. https://docs.github.com/en/authentication/connecting-to-github-with-ssh/generating-a-new-ssh-key-and-adding-it-to-the-ssh-agent

[7] GitHub. Impressões digitais SSH. https://docs.github.com/en/authentication/keeping-your-account-and-data-secure/githubs-ssh-key-fingerprints

[8] GitHub. Publicar código local. https://docs.github.com/en/migrations/importing-source-code/using-the-command-line-to-import-source-code/adding-locally-hosted-code-to-github

[9] GitHub. Serviços PostgreSQL no Actions. https://docs.github.com/actions/guides/creating-postgresql-service-containers

[10] Docker. Instalar Engine no Ubuntu. https://docs.docker.com/engine/install/ubuntu/

[11] Caddy. HTTPS automático. https://caddyserver.com/docs/automatic-https

Estude depois: separar rotas por domínio, reduzir tamanho de componentes, testes automatizados de interface, sincronização de sessões entre abas, paginação de membros, convites e recuperação por e-mail, observabilidade e proteção contra abuso. Faça uma melhoria de cada vez e registre a evidência de funcionamento.
