# F.A.R.O. - Ferramenta de Análise de Rotas e Observações

## Visão Geral

F.A.R.O. é uma plataforma de inteligência policial completa com ciclo fechado de feedback entre campo e inteligência, projetada para análise de rotas e observações de veículos suspeitos em tempo real.

## Arquitetura

### Stack Tecnológico
- **Backend**: FastAPI 0.115.0 + SQLAlchemy 2.0.36 (async)
- **Database**: PostgreSQL 16 + PostGIS 3.4 + TimescaleDB + Citus
- **Cache/Queue**: Redis 7 (3 bancos separados)
- **Storage**: MinIO (S3-compatible) com fallback local
- **Mobile**: Android nativo (Kotlin/Java) com Jetpack Compose
- **Web**: Next.js 15 + React 18 + TypeScript
- **ML/OCR**: PyTorch 2.5.0 + YOLO 8.3.0 + EasyOCR 1.7.1

### Componentes Principais
1. **Server Core** (porta 8000) - Backend monolítico modular
2. **Mobile Agent Field** - APK Android para captura em campo
3. **Web Intelligence Console** (porta 3000) - Dashboard de inteligência
4. **Analytics Dashboard** (porta 9002) - Monitoramento em tempo real
5. **Infraestrutura** - Docker Compose com 12 serviços

## Funcionalidades Implementadas

### ✅ Frontend Features (Completas)

#### Alta Prioridade
- **Mobile UI Requirements** - Interface otimizada para abordagens policiais com uso de uma mão
- **Alert Acknowledge Button** - Botão de reconhecimento de alertas no console web
- **Mobile Feedback Section** - Seção de feedback de campo nos detalhes de observações
- **Export Functions** - Funcionalidades de exportação em PDF, DOCX, XLSX

#### Média Prioridade
- **Suspicion Reports Module** - Módulo completo com 12 endpoints para gestão de suspeitas
- **Agents Management Module** - Gestão completa de agentes com 4 endpoints
- **Haptic Feedback & Visual Alerts** - Feedback tátil e alertas visuais no app mobile
- **One-Handed Mobile UI** - Interface mobile otimizada para uso policial

#### Baixa Prioridade
- **Devices Management Module** - Monitoramento completo de dispositivos
- **Monitoring Dashboard** - Dashboard de saúde do sistema em tempo real
- **WebSocket Integration** - Atualizações em tempo real com reconexão automática

### 🚀 Algoritmos de Detecção Autônoma

7 algoritmos principais integrados com validação de campo:
1. **WATCHLIST** - Matches em watchlist
2. **IMPOSSIBLE TRAVEL** - Viagens impossíveis
3. **ROUTE ANOMALY** - Anomalias em regiões
4. **SENSITIVE ZONE RECURRENCE** - Recorrência em zonas sensíveis
5. **CONVOY** - Detecção de comboio
6. **ROAMING** - Movimento repetitivo
7. **INTERCEPT** - Algoritmo combinatório

### 📊 Capacidades Espaciais Avançadas

- **PostGIS Implementation**: Extensões PostGIS, TimescaleDB, Citus habilitadas
- **Tipos Geométricos**: GEOMETRY(POINT, 4326), GEOMETRY(POLYGON, 4326), GEOMETRY(LINESTRING, 4326)
- **SRID 4326**: WGS84 para coordenadas geográficas
- **Funcionalidades**: Armazenamento de localizações, análise de padrões, clustering espacial

## Instalação

### Pré-requisitos
- Docker e Docker Compose
- Node.js 18+ (para desenvolvimento web)
- Python 3.14+ (para desenvolvimento backend)
- Android Studio (para desenvolvimento mobile)

### Instalação Automática
```bash
# Windows PowerShell
.\install-faro.ps1

# Linux/MacOS
./install-faro.sh
```

### Iniciar Serviços
```bash
# Windows PowerShell
.\start-services.ps1

# Linux/MacOS
./start-services.sh
```

### Verificar Instalação
```bash
# Windows PowerShell
.\verify-installation.ps1

# Linux/MacOS
./verify-installation.sh
```

## Pontos de Acesso

- **Server Core**: http://localhost:8000
- **Web Console**: http://localhost:3000
- **Analytics Dashboard**: http://localhost:9002/dashboard
- **Prometheus**: http://localhost:9090
- **Grafana**: http://localhost:3000

## Estrutura do Projeto

```
FARO/
├── server-core/                 # Backend FastAPI
│   ├── app/
│   │   ├── api/                # Endpoints da API
│   │   ├── core/              # Configurações principais
│   │   ├── services/          # Lógica de negócio
│   │   ├── models/            # Models SQLAlchemy
│   │   └── schemas/           # Schemas Pydantic
│   ├── alembic/               # Database migrations
│   └── requirements.txt       # Dependências Python
├── web-intelligence-console/  # Frontend Next.js
│   ├── src/
│   │   ├── app/              # Páginas do app
│   │   ├── components/       # Componentes React
│   │   ├── services/         # APIs
│   │   └── types/           # TypeScript types
│   └── package.json         # Dependências Node.js
├── mobile-agent-field/        # App Android Kotlin
│   ├── app/src/main/java/    # Código fonte Kotlin
│   └── build.gradle.kts      # Configuração Gradle
├── analytics-dashboard/        # Dashboard Python
├── infra/                     # Configurações Docker
│   ├── docker/
│   └── nginx/
├── docs/                      # Documentação
└── scripts/                   # Scripts utilitários
```

## Desenvolvimento

### Backend (FastAPI)
```bash
cd server-core
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
pip install -r requirements.txt
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

### Frontend (Next.js)
```bash
cd web-intelligence-console
npm install
npm run dev
```

### Mobile (Android)
```bash
cd mobile-agent-field
./gradlew assembleDebug
# ou use Android Studio para desenvolvimento
```

## Configuração

### Variáveis de Ambiente
Copie `.env.example` para `.env` e configure:

```env
# Database
DATABASE_URL=postgresql://user:password@localhost:5432/faro

# Redis
REDIS_URL=redis://localhost:6379

# JWT
SECRET_KEY=your-secret-key
ACCESS_TOKEN_EXPIRE_MINUTES=30

# Storage
MINIO_ENDPOINT=localhost:9000
MINIO_ACCESS_KEY=minioadmin
MINIO_SECRET_KEY=minioadmin
```

## API Endpoints

### Inteligência (42 endpoints)
- `GET /intelligence/queue` - Fila de observações
- `POST /intelligence/analyze` - Análise estruturada
- `GET /intelligence/watchlists` - Watchlists
- `POST /intelligence/cases` - Casos

### Mobile (13 endpoints)
- `POST /mobile/observations` - Nova observação
- `GET /mobile/history` - Histórico do agente
- `POST /mobile/plate-suspicion-check` - Verificação de placa

### Alertas (11 endpoints)
- `GET /alerts/active` - Alertas ativos
- `POST /alerts/acknowledge` - Reconhecer alerta
- `GET /alerts/aggregated` - Alertas agregados

## Monitoramento

### Métricas Disponíveis
- **Health Check**: Status dos serviços
- **Performance**: Tempo de resposta, requisições/s
- **Resources**: CPU, memória, disco
- **Business**: Observações, alertas, agentes ativos

### Dashboards
- **Grafana**: http://localhost:3000 (admin/admin)
- **Prometheus**: http://localhost:9090
- **Analytics Dashboard**: http://localhost:9002/dashboard

## Testes

### Backend Tests
```bash
cd server-core
pytest tests/
```

### Frontend Tests
```bash
cd web-intelligence-console
npm test
```

## Deploy

### Docker Production
```bash
docker-compose -f docker-compose.yml up -d
```

### Kubernetes
```bash
kubectl apply -f k8s/
```

## Contribuição

1. Fork o projeto
2. Crie branch feature (`git checkout -b feature/amazing-feature`)
3. Commit suas mudanças (`git commit -m 'Add amazing feature'`)
4. Push para branch (`git push origin feature/amazing-feature`)
5. Abra Pull Request

## Licença

Este projeto está licenciado sob a MIT License - veja o arquivo [LICENSE](LICENSE) para detalhes.

## Suporte

- **Documentação**: Veja a pasta `docs/`
- **Issues**: Abra issue no GitHub
- **Contato**: [email protegido]

## Changelog

### v2.0.0 (2026-04-30)
- ✅ Implementação completa do frontend
- ✅ Interface mobile otimizada para uso policial
- ✅ Integração WebSocket em tempo real
- ✅ Dashboard de monitoramento completo
- ✅ 7 algoritmos de detecção autônoma
- ✅ Sistema de validação fechado

### v1.0.0
- ✅ Backend FastAPI completo
- ✅ Database PostgreSQL + PostGIS
- ✅ API RESTful documentada
- ✅ Autenticação JWT
- ✅ Docker compose

---

**F.A.R.O.** - Transformando dados em inteligência policial eficaz.
