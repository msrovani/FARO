# Changelog F.A.R.O.

## [1.1.0] - 2026-04-14

### Funcionalidades Implementadas

#### Web Intelligence Console (Frontend)
- **Visualizações de Mapa para Inteligência Policial**: Implementação completa de componentes e páginas
  - MapBase: Componente base usando react-map-gl com OpenStreetMap
  - HotspotMarker: Marcadores circulares com tamanho/color por intensidade
  - RouteMarker: Renderização de linhas para rotas com pontos editáveis
  - AlertMarker: Marcadores para alertas com ícones por tipo/severidade
  - Página de hotspots: Visualização com filtros, timeline e placas frequentes
  - Página de rotas suspeitas: Cadastro/visualização com criação via cliques no mapa
  - Página de previsão de rotas: Previsão baseada em padrões históricos
  - Página de alertas: Visualização com filtros e ações de aprovação
  - Página de eventos de convoy: Visualização com coocorrências e aprovação
  - Página de eventos de roaming: Visualização com recorrência em áreas
  - Tema escuro consistente com layout split-screen (sidebar + mapa)
  - Mock data pronto para integração com backend

#### Server Core (Backend Avançado)
- **Cadastro de Rotas Suspeitas (SuspiciousRoute)**:
  - Modelo com enums (CrimeType, RouteDirection, RiskLevel)
  - Geometria LINESTRING com PostGIS
  - Índice GiST para queries espaciais eficientes
  - Restrições temporais (horário e dias)
  - Workflow de aprovação (pending/approved/rejected)
  - Service com match checking usando ST_Intersects e ST_Distance

- **Análise de Hotspots de Criminalidade**:
  - Clustering espacial simplificado
  - Cálculo de centroides e estatísticas por cluster
  - Intensity score (0-1) baseado em densidade e suspeitas
  - Timeline de atividade por hora do dia
  - Placas mais frequentes em área específica
  - Uso de ST_DWithin do PostGIS para busca espacial

- **Previsão de Rotas**:
  - Previsão baseada em padrões históricos
  - Detecção de pattern drift
  - Identificação de rotas recorrentes
  - Confiança da predição
  - Horas e dias previstos de atividade

- **Serviço de Alertas Automáticos**:
  - Alertas para matches de rotas suspeitas
  - Alertas para pattern drifts
  - Alertas para rotas recorrentes
  - Agregação de alertas por observação

- **Expansão de Modelos**:
  - ConvoyEvent: padrões temporais, análise de rotas, tracking de recorrencia
  - RoamingEvent: padrões de área, tracking de recorrencia, análise de zona

### Migrations
- `0004_suspicious_routes`: Criação de tabela SuspiciousRoute com enums e índices espaciais
- `0005_advanced_convoy_roaming`: Expansão de ConvoyEvent e RoamingEvent

### API Endpoints
- `POST /intelligence/suspicious-routes`: Criar rota
- `GET /intelligence/suspicious-routes`: Listar rotas
- `GET /intelligence/suspicious-routes/{route_id}`: Detalhes da rota
- `PUT /intelligence/suspicious-routes/{route_id}`: Atualizar rota
- `DELETE /intelligence/suspicious-routes/{route_id}`: Desativar rota
- `POST /intelligence/suspicious-routes/{route_id}/approve`: Aprovar/rejeitar rota
- `POST /intelligence/suspicious-routes/match`: Verificar match de observação
- `POST /intelligence/hotspots/analyze`: Analisar hotspots
- `POST /intelligence/hotspots/timeline`: Timeline de área
- `POST /intelligence/hotspots/plates`: Placas em área
- `POST /intelligence/route-prediction/predict`: Prever rota para placa
- `GET /intelligence/route-prediction/{plate}/n-days`: Previsão N dias
- `POST /intelligence/route-prediction/pattern-drift`: Verificar pattern drift
- `GET /intelligence/route-prediction/recurring-routes`: Rotas recorrentes
- `POST /intelligence/alerts/check`: Verificar alertas de observação
- `GET /intelligence/alerts/aggregated`: Alertas agregados
- `POST /intelligence/alerts/recurring-check`: Verificar rotas recorrentes

### Documentação Atualizada
- `docs/implementation/advanced-features-implementation.md`: Documentação completa de funcionalidades avançadas
- `README.md`: Atualizado com frontend de mapas e backend avançado
- `openmemory.md`: Atualizado com novas funcionalidades

### Dependências Frontend
- maplibre-gl (já instalado)
- react-map-gl (já instalado)
- lucide-react (já instalado)

### Próximos Passos
- Integrar frontend com endpoints reais (substituir mock data)
- Criar endpoints para ConvoyEvents e RoamingEvents no backend
- Implementar autenticação e autorização no frontend
- Criar dashboard consolidado de inteligência

---

## [1.0.0] - 2026-04-11

### Funcionalidades Implementadas

#### Mobile Agent Field (APK)
- **CameraX + ML Kit**: Implementação completa de captura de câmera com OCR assistido
  - CameraPreview Composable com preview ao vivo
  - ML Kit Text Recognition v2 para detecção de placas brasileiras
  - Regex específico para formato ABC1D23
  - Confiança dinâmica com callback em tempo real
- **Room Database**: Persistência offline-first completa
  - Entidades: ObservationEntity, PlateReadEntity, SuspicionReportEntity
  - DAOs com operações CRUD completas
  - TypeConverters para Instant
- **WorkManager**: Sincronização em background
  - SyncWorker com Hilt injection
  - SyncManager para agendamento periódico e imediato
- **Clean Architecture**: Implementação completa
  - Domain layer: Models, Repositories, UseCases
  - Data layer: Room + Repository pattern
  - Presentation layer: Compose UI integrada
- **Hilt DI**: Módulos para injeção de dependência
  - DatabaseModule, RepositoryModule, UseCaseModule

#### Server Core (Backend)
- **Route Analysis Service**: Algoritmos completos de análise de padrões
  - Cálculo de recorrência baseado em intervalos temporais
  - Pontuação de força do padrão (weak/moderate/strong)
  - Análise geospatial com centroides e bounding boxes
  - Detecção de corredores recorrentes
- **API Endpoints**: Novos endpoints para análise de rotas
  - `POST /api/v1/intelligence/route-analysis`: Análise de padrões
  - `GET /api/v1/intelligence/route-timeline/{plate_number}`: Timeline para visualização
- **Event Publishing**: Integração com Redis Streams
  - Eventos de análise de rotas publicados no event bus
- **Database Models**: RoutePattern para persistência de padrões

### Validações Realizadas
- ✅ Sintaxe Python validada (py_compile)
- ✅ Imports testados sem erros
- ✅ Estrutura de arquivos Kotlin verificada
- ✅ Compatibilidade com arquitetura existente confirmada
- ✅ Endpoints da API integrados ao router principal

### Documentação Atualizada
- **ADR 0002**: Decisão de implementação CameraX/ML Kit e análise de rotas
- **Architecture Overview**: Funcionalidades implementadas documentadas
- **API Contracts**: Novos endpoints documentados com exemplos
- **Clean Architecture**: Padrões implementados descritos

### Arquitetura Mantida
- **Modular Monolith**: Backend continua como monólito modular
- **Offline-First**: Mobile totalmente funcional sem conectividade
- **OCR Assistido**: ML Kit sugere, agente confirma
- **Event-Driven**: Backend ativo com publicação de eventos
- **Clean Separation**: Três componentes mantêm separação real

### Dependências Adicionadas
- **Mobile**: CameraX, ML Kit, Room, WorkManager (já estavam no build.gradle.kts)
- **Backend**: Algoritmos implementados sem novas dependências externas

### Próximos Passos
- Testes de integração end-to-end
- Validação com dados reais
- Otimização de performance
- Documentação de deployment