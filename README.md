# CarteiraConsol

CarteiraConsol é uma plataforma full-stack de consolidação e análise de carteiras de investimento construída para ingerir arquivos financeiros imperfeitos do mundo real, normalizá-los em um modelo consistente de portfólio e expor, sobre essa base, tanto uma camada operacional quanto uma camada executiva. O sistema combina backend em FastAPI, workspace em React, pipeline ETL inteligente, controles de revisão, geração de PDF, autenticação, alertas operacionais e padrões de implantação prontos para nuvem em uma arquitetura pensada para operações financeiras reais, não para datasets artificiais.

## Principais Funcionalidades

- Ingestão inteligente de CSV/XLSX com detecção de estrutura e recuperação de arquivos irregulares
- Mapeamento fuzzy de colunas com aliases em português e inglês
- Validação suave com fallback, incluindo inferência de corretora e valores padrão configuráveis
- Trilha de auditoria durável com relatórios persistidos de ingestão
- Review Queue para execuções de baixa confiança ou que exigem atenção operacional
- Fluxo de Approve & Reprocess que atualiza o mesmo relatório de ingestão em vez de duplicar registros
- Dashboard executivo com KPIs ao vivo, alocação, evolução e posições
- Geração server-side de PDF executivo com ReportLab
- Autenticação JWT com rotas protegidas e senhas com hash
- Camada de alertas operacionais com suporte preparado para SNS
- Fundação de ingestão via S3 -> Lambda -> ETL com parsing pronto para SQS
- Ambiente local com Docker Compose, PostgreSQL e MinIO
- CI em GitHub Actions para testes de backend e build do frontend
- Baseline AWS validada com um teste real temporário usando ECS Fargate + S3

## Arquitetura do Sistema

### Backend

O backend é construído sobre FastAPI e organizado em torno de uma camada de serviços. As rotas HTTP permanecem finas e delegam a lógica para serviços responsáveis por orquestração do ETL, persistência de relatórios de ingestão, autenticação, alertas, storage e geração de relatórios.

Responsabilidades centrais do backend:

- autenticação e proteção de API
- intake de upload e orquestração de ETL
- rastreamento do ciclo de vida dos `ingestion_reports`
- endpoints de consulta para dashboard e relatórios
- geração de PDF executivo
- entrypoints compatíveis com S3/Lambda

### Pipeline ETL

O fluxo ETL segue uma sequência clara:

```text
extract -> normalize -> transform -> enrich -> persist
```

Propriedades centrais do pipeline:

- aceita uploads locais e ingestão apoiada em S3
- suporta CSV/XLSX genérico e caminhos específicos por corretora
- normaliza tabulares financeiros ruidosos para um modelo de portfólio consistente
- produz metadados de ingestão que alimentam o sistema de revisão e a trilha de auditoria

### Frontend

O frontend é um workspace em React + Vite com três modos operacionais:

- `Report Builder`
- `Review Queue`
- `Dashboard`

O produto foi desenhado com uma separação deliberada entre:

- camada operacional para ingestão, triagem e correção
- camada executiva para visibilidade patrimonial e entrega de relatórios

### Camada de Dados

O armazenamento relacional principal é PostgreSQL, com versionamento de schema via Alembic.

Áreas principais de persistência:

- tabelas de domínio do portfólio
- `ingestion_reports`
- `accepted_column_mappings`
- usuários e autenticação

Durante a validação temporária em AWS, o backend também foi testado com SQLite efêmero dentro da task do ECS para reduzir custo sem deixar de exercitar o runtime real da aplicação.

## Pipeline ETL em Profundidade

O pipeline foi construído em torno da realidade de que dados financeiros quase nunca chegam limpos.

### Detecção de Estrutura

A camada de smart ingestion inspeciona arquivos CSV e XLSX para inferir:

- delimitador
- linha de cabeçalho
- worksheet mais relevante no Excel
- linhas de preâmbulo ou ruído que podem ser ignoradas

Isso permite lidar com arquivos em que o cabeçalho não está na primeira linha ou em que a estrutura exportada varia entre instituições.

### Resolução de Aliases e Mapeamento Fuzzy

Campos canônicos como cliente, corretora, ticker, quantidade, preço médio, valor total e data de referência são mapeados a partir de colunas heterogêneas usando:

- aliases explícitos
- normalização textual de rótulos
- comparação fuzzy com RapidFuzz

Isso cobre variações em português e inglês, além de diferenças de nomenclatura entre corretoras e custodians.

### Lógica de Fallback

Uma estrutura financeira consistente continua sendo importante, mas falhar cedo demais gera falsos erros operacionais. Por isso, o pipeline suporta comportamento de fallback quando o dado ainda é recuperável.

Exemplo:

- se `broker` estiver ausente, o sistema tenta inferi-lo a partir de:
  - `custodian`
  - `institution`
  - `corretora`
  - `advisorcode`
  - pistas do nome do arquivo, como `XP` ou `BTG`
- se ainda assim a corretora não puder ser inferida, o sistema pode aplicar `UNKNOWN` quando o modo de validação suave estiver ativo

### Modo de Validação Suave

O pipeline distingue entre:

- falhas técnicas ou de dado realmente irrecuperáveis
- ingestões recuperáveis, mas de baixa confiança

Quando o dado ainda é utilizável, mas a confiança não é suficiente, a execução não é bloqueada. Em vez disso, ela prossegue com:

- `review_required = true`
- motivos estruturados de revisão
- persistência do relatório de ingestão para acompanhamento operacional

### Ciclo de Vida do Ingestion Report

Cada execução real de ingestão cria ou atualiza um relatório que registra:

- filename
- detected type
- parser utilizado
- referência do arquivo bruto
- referência do arquivo processado
- colunas detectadas
- mappings aplicados
- nível de confiança
- status e motivos de revisão
- linhas processadas e puladas
- timestamps
- metadados de reprocessamento

Isso torna o fluxo ETL auditável e sustenta o ciclo de revisão sem acoplar o produto inteiro a uma aprovação manual.

## Sistema de Revisão

O sistema de revisão é a camada de controle que impede que uma ingestão de baixa confiança seja tratada como sucesso silencioso ou como erro técnico fatal.

### Semântica de Status

O CarteiraConsol diferencia explicitamente:

- `success`
  - os dados foram processados com sucesso e nenhuma ação humana adicional é necessária
- `review_required`
  - os dados foram processados o suficiente para persistência, mas exigem revisão operacional
- `technical error`
  - o arquivo não pôde ser processado com segurança e a execução falhou

Essa distinção é central para o produto, porque arquivos revisáveis precisam permanecer operáveis, enquanto falhas técnicas precisam continuar claramente identificadas como falhas.

### Review Queue

A Review Queue expõe relatórios de ingestão que exigem atenção humana. O operador pode inspecionar:

- metadados do arquivo
- estrutura detectada
- mapeamentos de coluna
- score de confiança
- motivos da revisão
- parser utilizado
- resultado do processamento

### Approve & Reprocess

O fluxo de revisão suporta:

1. aprovar um relatório
2. reprocessar a fonte original
3. atualizar o mesmo relatório de ingestão em vez de criar um novo
4. incrementar metadados de reprocessamento para auditoria

Isso fecha o loop operacional de aprendizagem sem sacrificar rastreabilidade.

### Aprendizado via Accepted Mappings

Mappings aprovados são persistidos em `accepted_column_mappings`, de modo que novas ingestões possam reutilizar layouts conhecidos antes de recorrer novamente ao fuzzy matching. Isso cria aprendizado operacional incremental sem introduzir uma camada pesada de machine learning.

## Dashboard e Relatórios

A camada executiva transforma posições processadas em algo apresentável para clientes, liderança e áreas analíticas.

### Dashboard

O dashboard ao vivo consome APIs reais do backend e exibe:

- valor total consolidado da carteira
- total de clientes
- total de ativos
- total de contas
- alocação por classe de ativo
- alocação por cliente
- top ativos por valor
- evolução da carteira ao longo do tempo
- tabela de principais posições

A interface foi intencionalmente refinada para se comportar como um produto fintech premium, e não como um painel administrativo genérico.

### PDF Executivo

O CarteiraConsol inclui geração server-side de PDF para relatórios de portfólio voltados a cliente ou diretoria.

A primeira versão inclui:

- cabeçalho executivo e timestamp de geração
- resumo de KPIs
- alocação por classe de ativo
- top ativos por valor
- evolução da carteira
- tabela de principais posições
- notas operacionais quando relevantes

O PDF é gerado a partir de dados processados reais no backend, e não por exportação frágil da interface do navegador.

## Autenticação e Segurança

A plataforma já possui uma primeira camada segura de autenticação, adequada para uso além do ambiente local.

Decisões de segurança:

- autenticação via JWT
- hash de senha com Passlib e bcrypt
- rotas de negócio protegidas
- apenas health check e login públicos
- restauração de sessão no frontend via `/auth/me`
- inclusão automática do bearer token nas chamadas da API
- logout e limpeza de sessão inválida no frontend

Capacidades protegidas incluem:

- upload
- ingestion reports
- endpoints de dados do portfólio
- dashboard
- geração de PDF

## Sistema de Alertas

A camada de alertas foi implementada como uma preocupação operacional separada do núcleo do ETL.

### O que Dispara Alertas

Os gatilhos atuais são:

- falhas técnicas de ingestão
- ingestões concluídas com `review_required = true`

### Princípios de Design

- alertas não são bloqueantes
- o sucesso do ETL nunca depende da entrega da notificação
- providers são configuráveis
- existe caminho preparado para SNS em AWS
- o desenvolvimento local continua funcional com alertas desligados

Com isso, o sistema ganha prontidão operacional sem transformar entrega de notificação em dependência crítica.

## Arquitetura AWS e Validação Real

O CarteiraConsol foi desenhado para suportar uma topologia de ingestão cloud-native, preservando ao mesmo tempo um runtime separado para a API autenticada.

### Arquitetura Recomendada

```text
Frontend estático
    ->
FastAPI backend (ECS Fargate)
    ->
PostgreSQL (RDS em produção)

Arquivos brutos
    ->
S3
    ->
SQS
    ->
Lambda de ingestão
    ->
Pipeline ETL
    ->
PostgreSQL + ingestion reports
```

### Por que Essa Arquitetura Foi Escolhida

- Lambda é um bom encaixe para ingestão orientada a evento
- SQS adiciona buffer, retry controlado e caminho natural para DLQ
- FastAPI continua sendo uma escolha melhor para autenticação, upload HTTP, dashboard, review queue e geração de PDF
- por isso, o runtime da API fica separado do runtime serverless de ingestão

### Validação AWS Real

O repositório foi validado com um teste real e temporário em AWS.

Serviços usados na verificação:

- ECS Fargate para o backend FastAPI
- S3 para storage de arquivos brutos
- IAM roles para execução do ECS e acesso ao bucket
- CloudWatch Logs para observabilidade de runtime

Escolha de custo para o teste:

- SQLite foi usado dentro da task efêmera do ECS em vez de provisionar RDS, porque o objetivo era validar o runtime real do produto com o menor footprint possível

O que foi validado com sucesso:

- backend acessível publicamente
- login autenticado
- acesso a rota protegida
- upload funcional
- persistência do arquivo bruto em S3
- leitura de dados do portfólio após ingestão
- geração de PDF

Importante:

- esse foi um teste real de implantação, não apenas um desenho arquitetural
- o ambiente foi destruído depois da validação para evitar custo contínuo

Para a trilha de implantação em AWS, consulte:

- [docs/aws-deployment.md](C:/Users/vitor/OneDrive/Documentos/Playground/docs/aws-deployment.md)
- [template.yaml](C:/Users/vitor/OneDrive/Documentos/Playground/template.yaml)
- [deploy/ecs-task-definition.sample.json](C:/Users/vitor/OneDrive/Documentos/Playground/deploy/ecs-task-definition.sample.json)
- [.env.aws.example](C:/Users/vitor/OneDrive/Documentos/Playground/.env.aws.example)

## Desenvolvimento Local

### Pré-requisitos

- Python 3.13
- Node.js 20+
- Docker Desktop

### Ambiente do Backend

Crie um arquivo de ambiente local:

```powershell
Copy-Item .env.example .env
```

Instale as dependências do backend:

```powershell
python -m pip install -r requirements.txt
```

Aplique as migrações:

```powershell
alembic upgrade head
```

Crie o primeiro admin:

```powershell
python scripts/create_admin.py --email admin@carteira.local --full-name "Admin Local"
```

Suba o backend:

```powershell
uvicorn app.main:app --reload
```

### Stack Docker Compose

O repositório também inclui uma stack local cloud-like com PostgreSQL e MinIO:

```powershell
docker compose --env-file .env.docker up --build -d
docker compose --env-file .env.docker ps
```

Essa stack valida:

- FastAPI em containers
- conectividade com PostgreSQL
- storage bruto S3-compatible via MinIO
- bootstrap automático do bucket
- upload e ETL em ambiente containerizado

Para parar e remover volumes:

```powershell
docker compose --env-file .env.docker down -v
```

### Frontend

```powershell
cd frontend
npm install
npm run dev
```

O frontend fica disponível em:

- `http://127.0.0.1:5173`

## Testes

O projeto possui uma superfície relevante de testes automatizados.

Áreas cobertas incluem:

- normalização ETL e recuperação de schema
- smart ingestion e fuzzy mapping
- comportamento de API
- autenticação
- ingestion reports e lógica de review
- endpoint de PDF
- parsing e invocação de eventos Lambda
- alertas operacionais

Para rodar a suíte backend:

```powershell
python -m pytest
```

Para validar o build de produção do frontend:

```powershell
cd frontend
npm run build
```

O CI em GitHub Actions executa testes do backend e build do frontend em `push` e `pull_request`.

## Principais Decisões Técnicas

### ReportLab em vez de HTML para PDF

A primeira versão do PDF usa ReportLab em vez de uma abordagem HTML-to-PDF porque:

- evita dependências gráficas no sistema operacional
- roda com mais previsibilidade em Docker e ECS
- mantém a trilha server-side de geração de relatório mais simples para um deployment enxuto

### Validação Suave em vez de Validação Totalmente Rígida

Arquivos reais de investimento frequentemente chegam incompletos, mas ainda úteis. A validação suave reduz falsos negativos, preserva valor operacional e desloca a ambiguidade para um fluxo explícito de revisão em vez de bloquear o produto inteiro.

### Review Queue em vez de Bloquear Ingestão

A review queue cria alavancagem operacional. Ela permite que o sistema continue funcionando enquanto preserva visibilidade sobre incerteza e baixa confiança. Para o problema que o CarteiraConsol resolve, isso é mais realista do que transformar toda ambiguidade em erro fatal.

### SQLite no Teste Temporário em AWS

A validação AWS priorizou prova real de execução com o menor custo possível. SQLite dentro de uma task efêmera do ECS foi suficiente para validar:

- autenticação
- migrações
- upload
- ETL
- storage bruto em S3
- comportamento de rotas protegidas
- geração de PDF

sem deixar uma instância de RDS ligada desnecessariamente.

### Separação entre Parsing de Evento e Execução ETL

O parsing de evento Lambda foi mantido separado da execução do ETL para que o mesmo serviço de ingestão consiga suportar:

- uploads diretos via API
- processamento direto por S3
- eventos S3 disparados por Lambda
- eventos SQS contendo eventos S3

Isso mantém a arquitetura adaptável sem duplicar lógica de ingestão.

## Lições Aprendidas e Insights de Engenharia

- Ingestão financeira do mundo real é, em grande parte, um problema de qualidade de dados, não apenas um problema de upload de arquivo.
- Validação excessivamente rígida gera falsos erros e corrói confiança; validação suave com semântica de revisão explícita é um desenho operacional mais robusto.
- Consistência de estado importa tanto quanto correção de processamento. O produto só parece confiável quando backend, relatórios persistidos, payloads de API e UI estão alinhados.
- Estados operacionais de revisão e estados de erro técnico precisam permanecer separados. Misturá-los gera ações erradas, UX confusa e leitura incorreta do sistema.
- Resiliência de frontend é crítica em produtos de dados. Payloads parciais, refresh atrasado e resultados não fatais de ETL não podem derrubar a tela.
- Paridade entre ambiente local e cloud precisa ser intencional. Docker + MinIO foi uma ponte valiosa antes da validação em AWS real.
- Prontidão para deploy não é só questão de código. Também envolve estratégia de secrets, ordem de startup, migrações, bootstrap, observabilidade e teardown responsável.

## Próximos Passos

- Infraestrutura AWS completa com CDK ou uma camada SAM mais abrangente
- RDS PostgreSQL como backing store padrão em produção
- Ativação completa do pipeline S3 -> SQS -> Lambda em ambiente implantado
- Estratégia de DLQ e observabilidade operacional mais rica
- Canais adicionais de alerta, como WhatsApp ou Slack
- Ferramentas mais avançadas de revisão humana com correção de campo
- Suporte multi-tenant com fronteiras mais fortes de autorização
- Cobertura mais profunda de parsers específicos por instituição
- Otimizações para analytics histórico em maior escala

## Destaques do Repositório

- Backend e ETL: [app](C:/Users/vitor/OneDrive/Documentos/Playground/app)
- Workspace frontend: [frontend](C:/Users/vitor/OneDrive/Documentos/Playground/frontend)
- Migrações de banco: [alembic](C:/Users/vitor/OneDrive/Documentos/Playground/alembic)
- Guia de deploy AWS: [docs/aws-deployment.md](C:/Users/vitor/OneDrive/Documentos/Playground/docs/aws-deployment.md)
- Baseline de ingestão AWS: [template.yaml](C:/Users/vitor/OneDrive/Documentos/Playground/template.yaml)
- Exemplo de task definition ECS: [deploy/ecs-task-definition.sample.json](C:/Users/vitor/OneDrive/Documentos/Playground/deploy/ecs-task-definition.sample.json)

## Autoria

Desenvolvido por Vitória Martins como projeto de engenharia de produto com foco em arquitetura backend, confiabilidade de ETL, desenho operacional e entrega executiva de dados.
