# Operacao e ambiente de desenvolvimento

## Objetivo

Padronizar subida local de backend, banco, cache, storage e web para desenvolvimento seguro.

## Stack de runtime local

- PostgreSQL + PostGIS
- Redis
- MinIO (S3-compatible)
- FastAPI (server-core)
- Next.js (web-intelligence-console)
- Nginx + observabilidade (quando via compose)

## Arquivos de referencia

- [infra/docker/docker-compose.yml](/c:/Users/msrov/OneDrive/Área%20de%20Trabalho/FARO/infra/docker/docker-compose.yml)
- [server-core/alembic.ini](/c:/Users/msrov/OneDrive/Área%20de%20Trabalho/FARO/server-core/alembic.ini)
- [server-core/alembic/versions/0001_initial_schema.py](/c:/Users/msrov/OneDrive/Área%20de%20Trabalho/FARO/server-core/alembic/versions/0001_initial_schema.py)
- [server-core/alembic/versions/0002_operational_indexes.py](/c:/Users/msrov/OneDrive/Área%20de%20Trabalho/FARO/server-core/alembic/versions/0002_operational_indexes.py)

## Subida do backend

```bash
cd server-core
python -m venv venv
venv\Scripts\activate
pip install -r requirements.txt
python -m alembic -c alembic.ini upgrade head
uvicorn app.main:app --reload --port 8000
```

## Subida do web

```bash
cd web-intelligence-console
npm install
npm run dev
```

## Subida da infra por compose

```bash
cd infra/docker
docker-compose up -d
```

## Validacoes minimas recomendadas

### Web

```bash
cd web-intelligence-console
npm run type-check
```

### Backend

```bash
cd server-core
python -m compileall app
```

## Android (status atual)

O modulo `mobile-agent-field` ainda precisa de wrapper versionado para build reproduzivel no repo:

- `gradlew`
- `gradlew.bat`
- `gradle/wrapper/gradle-wrapper.jar`
- `gradle/wrapper/gradle-wrapper.properties`

Ate essa etapa, a compilacao local depende de ambiente externo com Android Studio/Gradle instalado.

## Notas operacionais

- integracao estadual permanece em fallback dev (`sem conexao`) ate entrega do adapter real
- migration `0002` e aditiva e focada em indices geoespaciais + analiticos
