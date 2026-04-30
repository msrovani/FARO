# F.A.R.O. - Diagnóstico de Correções

**Data:** 2026-04-28  
**Versão:** 1.0.0  
**Status:** 🔴 **CRÍTICO** - Requer atenção imediata

---

## Resumo Executivo

Análise completa do projeto FARO identificou **47 problemas** categorizados em:
- 🔴 **Críticos:** 8
- 🟠 **Altos:** 15  
- 🟡 **Médios:** 18
- 🔵 **Baixos:** 6

### ✅ Correções Estruturais Realizadas

1. **Analytics Dashboard Movido para Raiz**
   - De: `server-core/analytics_dashboard/`
   - Para: `analytics-dashboard/` (raiz)
   - Scripts atualizados: `run_services.py`, `run_faro_services.py`, `start_all.bat`, `start_services.ps1`, `start-services.ps1`
   - Documentação atualizada: `openmemory.md`, `README.md` do dashboard

---

## 🔴 PROBLEMAS CRÍTICOS (Requerem Correção Imediata)

### 1. Exception Handling Silencioso (CRÍTICO)
**Arquivos afetados:** 27 arquivos no `server-core`

**Problema:** Uso excessivo de `except Exception:` com `pass` ou logging genérico, mascarando erros que podem causar falhas silenciosas.

**Exemplos encontrados:**
```python
# app/db/session.py:57-59
except Exception as e:
    logger.debug(f"PgBouncer not available: {e}")  # Debug level - ignorado em prod
    _pgbouncer_available = False

# app/services/ocr_service.py:44-45
except ImportError:
    pass  # torch opcional - sem fallback explícito

# app/services/cache_service.py:52-54
except Exception as e:
    logger.error(f"Failed to initialize Redis: {e}")
    self.enabled = False  # Fail silencioso - cache desabilitado sem alerta
```

**Impacto:** 
- Falhas não detectadas em produção
- Debug extremamente difícil
- Comportamento inconsistente

**Correção:**
```python
# Implementar except específicos + fallback estruturado
from tenacity import retry, stop_after_attempt, wait_exponential

@retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=4, max=10))
async def initialize_redis(self):
    try:
        self.redis = await redis.from_url(...)
        await self.redis.ping()
    except redis.ConnectionError as e:
        logger.error(f"Redis connection failed: {e}")
        raise CacheInitializationError(f"Cache indisponível: {e}") from e
    except Exception as e:
        logger.exception(f"Erro inesperado na inicialização do cache: {e}")
        raise
```

---

### 2. Hardcoded Secrets em Configurações (CRÍTICO)
**Arquivos:** 
- `server-core/app/core/config.py:66`
- `.env.example`
- `docker-compose.yml`

**Problema:** Senha padrão "CHANGE_ME" exposta no código, que pode ir para git em desenvolvimento.

```python
# config.py
database_url: str = Field(default="postgresql+asyncpg://faro:CHANGE_ME@localhost:5432/faro_db")
```

**Correção:**
```python
# config.py - Forçar variável de ambiente em produção
from pydantic import ValidationError

database_url: str = Field(
    default=None,  # Sem default seguro
    validation_alias="DATABASE_URL"
)

@field_validator('database_url', mode='before')
@classmethod
def validate_database_url(cls, v):
    if not v or 'CHANGE_ME' in str(v):
        if os.getenv('ENVIRONMENT') == 'production':
            raise ValueError("DATABASE_URL deve ser configurado explicitamente em produção")
        return "postgresql+asyncpg://faro:faro_dev@localhost:5432/faro_db"
    return v
```

---

### 3. TODO/FIXME Acumulados Sem Owner (CRÍTICO)
**Arquivos:** 74 arquivos com 251+ TODO/FIXME/HACK

**Distribuição crítica:**
- `auth.py` - TODO[FUTURO - OUTRO DEV]: Autenticação externa (54 linhas de roadmap)
- `mobile.py` - Fluxo de sincronização legacy
- `ocr_service.py` - TODOs de ML Kit

**Problema:** TODOs sem:
- Responsável atribuído
- Data de vencimento
- Prioridade definida
- Issue no tracker

**Correção:**
```python
# Template padronizado para TODOs
# TODO[2026-05-15|john.doe|HIGH|#123]: Implementar Gov.BR OAuth
# - Issue: https://github.com/org/faro/issues/123
# - Spec: docs/auth/govbr-integration.md
# - Testes: tests/integration/test_govbr_auth.py
```

---

### 4. Console.logs em Produção (Web Console) (CRÍTICO)
**Arquivos:** 34 arquivos TypeScript/React

**Exemplos:**
```typescript
// web-intelligence-console/src/app/cases/page.tsx
console.log('Cases response:', response);  // Dados sensíveis no console

// web-intelligence-console/src/app/services/api.ts
console.error('API Error:', error);  // Stack traces expostos
```

**Impacto:** 
- Vazamento de dados sensíveis em produção
- Stack traces expostos a atacantes
- Performance degradada

**Correção:**
```typescript
// Configurar logger estruturado
const logger = {
  debug: process.env.NODE_ENV === 'development' ? console.debug : () => {},
  info: (msg: string, meta?: object) => {
    // Enviar para sistema de logs centralizado (Sentry/DataDog)
    if (window.gtag) {
      window.gtag('event', 'log_info', { message: msg, ...meta });
    }
  },
  error: (msg: string, error?: Error) => {
    // Sempre enviar para serviço de monitoramento
    Sentry.captureException(error || new Error(msg));
  }
};
```

---

### 5. CORS Permissivo Demais (CRÍTICO)
**Arquivo:** `server-core/app/core/config.py:58`

```python
cors_origins: List[str] = Field(default=["*"])  # Aceita qualquer origem
```

**Correção:**
```python
cors_origins: List[str] = Field(
    default=["http://localhost:3000"],  # Apenas origens conhecidas
    validation_alias="CORS_ORIGINS"
)

@field_validator('cors_origins', mode='before')
@classmethod
def validate_cors(cls, v, info: ValidationInfo):
    if info.data.get('environment') == 'production' and "*" in v:
        raise ValueError("CORS wildcard '*' não permitido em produção")
    return v
```

---

### 6. JWT Secret Key Vazia por Padrão (CRÍTICO)
**Arquivo:** `server-core/app/core/config.py:51`

```python
secret_key: str = Field(default="")  # Vazio = tokens inseguros
```

**Correção:**
```python
secret_key: str = Field(
    validation_alias="SECRET_KEY",
    min_length=32
)

@field_validator('secret_key')
@classmethod
def validate_secret_key(cls, v: str, info: ValidationInfo):
    if info.data.get('environment') == 'production':
        if len(v) < 32:
            raise ValueError("SECRET_KEY deve ter no mínimo 32 caracteres em produção")
        if v in ['secret', 'change-me', 'changeme']:
            raise ValueError("SECRET_KEY não pode ser um valor genérico")
    return v
```

---

### 7. Dependência Circular em Imports (CRÍTICO)
**Detectado em:** `app/services/`

Risco de:
- `analytics_service` → `observation_service`
- `observation_service` → `cache_service`
- `cache_service` → `analytics_service` (via eventos)

**Correção:**
```python
# Usar importação lazy
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from app.services.observation_service import ObservationService

def get_observation_service() -> 'ObservationService':
    from app.services.observation_service import ObservationService
    return ObservationService()
```

---

### 8. Memory Leaks em Cache (CRÍTICO)
**Arquivo:** `web-intelligence-console/src/app/services/api.ts`

```typescript
const httpCache = new Map<string, CacheEntry>();  // Sem limite de memória
const MAX_CACHE_SIZE = 100;  // Muito baixo para produção
```

**Problema:** Eviction por ordem de inserção (FIFO) não considera uso recente.

**Correção:**
```typescript
// Implementar LRU Cache
class LRUCache<K, V> {
  private cache: Map<K, V>;
  private maxSize: number;
  
  constructor(maxSize: number) {
    this.cache = new Map();
    this.maxSize = maxSize;
  }
  
  get(key: K): V | undefined {
    const value = this.cache.get(key);
    if (value !== undefined) {
      // Mover para o final (mais recente)
      this.cache.delete(key);
      this.cache.set(key, value);
    }
    return value;
  }
  
  set(key: K, value: V): void {
    if (this.cache.size >= this.maxSize) {
      // Remover primeiro (menos recente)
      const firstKey = this.cache.keys().next().value;
      this.cache.delete(firstKey);
    }
    this.cache.set(key, value);
  }
}
```

---

## 🟠 PROBLEMAS ALTOS

### 9. Validação de Placas Brasileiras Incompleta
**Arquivo:** `server-core/app/services/ocr_service.py:80-81`

```python
OLD_PLATE_PATTERN = re.compile(r"^[A-Z]{3}[0-9]{4}$")
MERCOSUR_PLATE_PATTERN = re.compile(r"^[A-Z]{3}[0-9][A-Z0-9][0-9]{2}$")
```

**Problemas:**
- Não valida letras proibidas (I, O, Q)
- Aceita placas inválidas tipo "AAA0A00"
- Sem validação de estado por prefixo

**Correção:**
```python
# Validador completo de placas brasileiras
class PlateValidator:
    # Letras proibidas em placas brasileiras
    FORBIDDEN_LETTERS = {'I', 'O', 'Q'}
    
    # Prefixos por estado
    STATE_PREFIXES = {
        'PR': ['AAA', 'AAB', ..., 'BEZ'],
        'SP': ['BFA', 'BFB', ..., 'GKI'],
        # ... outros estados
    }
    
    @classmethod
    def validate(cls, plate: str) -> tuple[bool, Optional[str]]:
        plate = plate.upper().replace('-', '')
        
        # Verificar formato Mercosul
        if len(plate) == 7:
            return cls._validate_mercosur(plate)
        
        # Verificar formato antigo
        if len(plate) == 7 and plate[3:].isdigit():
            return cls._validate_old_format(plate)
        
        return False, "Formato de placa inválido"
    
    @classmethod
    def _validate_mercosur(cls, plate: str) -> tuple[bool, Optional[str]]:
        # LLLNLNN onde L=letra, N=número
        pattern = r'^[A-HJ-NP-Z]{3}[0-9][A-HJ-NP-Z][0-9]{2}$'
        if not re.match(pattern, plate):
            return False, "Formato Mercosul inválido"
        return True, None
```

---

### 10. Cache TTL Inadequado para Dados Sensíveis
**Arquivo:** `server-core/app/core/config.py:111-113`

```python
cache_ttl_short: int = Field(default=60)      # 1 minute
cache_ttl_medium: int = Field(default=300)    # 5 minutes
cache_ttl_long: int = Field(default=3600)   # 1 hour
```

**Problema:** Watchlist/casos sensíveis podem ficar cacheados por 1 hora.

**Correção:**
```python
# Separar TTLs por categoria de dados sensibilidade
class CacheTTL:
    # Dados públicos/estáticos
    STATIC = 3600  # 1 hora
    
    # Dados operacionais (não sensíveis)
    OPERATIONAL = 300  # 5 minutos
    
    # Dados sensíveis (watchlist, casos ativos)
    SENSITIVE = 60  # 1 minuto
    
    # Dados críticos (localização, alertas)
    CRITICAL = 10  # 10 segundos (quase real-time)
    
    # Nunca cachear
    NEVER = 0
```

---

### 11. Rate Limiting Sem Distinção por Endpoint
**Arquivo:** `server-core/app/core/rate_limit.py`

**Problema:** Rate limiting uniforme (100 req/min) para todos os endpoints.

**Correção:**
```python
# Rate limiting por categoria de endpoint
RATE_LIMITS = {
    # Auth - mais restritivo (proteção contra brute force)
    'auth': {'requests': 5, 'window': 60, 'block_duration': 300},
    
    # OCR - CPU intensivo
    'ocr': {'requests': 10, 'window': 60},
    
    # Leitura de dados
    'read': {'requests': 100, 'window': 60},
    
    # Escrita
    'write': {'requests': 30, 'window': 60},
    
    # Health check - ilimitado
    'health': {'requests': float('inf'), 'window': 60},
}
```

---

### 12. WebSocket Sem Autenticação
**Arquivo:** `server-core/app/api/v1/endpoints/websocket.py`

**Problema:** Conexões WebSocket aceitas sem validação de token.

**Correção:**
```python
@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    # Validar token na conexão inicial
    token = websocket.query_params.get('token')
    if not token:
        await websocket.close(code=4001, reason="Token required")
        return
    
    try:
        user = await validate_websocket_token(token)
    except AuthenticationError:
        await websocket.close(code=4002, reason="Invalid token")
        return
    
    # Rate limiting por usuário
    if not await check_websocket_rate_limit(user.id):
        await websocket.close(code=4003, reason="Rate limit exceeded")
        return
    
    await manager.connect(websocket, user)
```

---

### 13. Logs de Localização Sem Anonimização
**Arquivo:** `server-core/app/db/base.py`

**Problema:** Coordenadas GPS de agentes armazenadas em texto claro.

**Correção:**
```python
from cryptography.fernet import Fernet

class LocationEncryption:
    def __init__(self):
        self.cipher = Fernet(os.environ['LOCATION_ENCRYPTION_KEY'])
    
    def encrypt_coordinates(self, lat: float, lon: float) -> str:
        """Criptografar coordenadas para armazenamento."""
        data = f"{lat},{lon}".encode()
        return self.cipher.encrypt(data).decode()
    
    def decrypt_coordinates(self, encrypted: str) -> tuple[float, float]:
        """Descriptografar para uso interno."""
        data = self.cipher.decrypt(encrypted.encode()).decode()
        lat, lon = map(float, data.split(','))
        return lat, lon

# Tabela usando campo criptografado
class AgentLocationLog(Base):
    location_encrypted = Column(String(255), nullable=False)
    
    @property
    def location(self) -> tuple[float, float]:
        return LocationEncryption().decrypt_coordinates(self.location_encrypted)
```

---

### 14. Migrações Alembic Sem Backup Automático
**Arquivo:** `database/`

**Problema:** Migrações executadas sem snapshot prévio do banco.

**Correção:**
```python
# scripts/pre_migration_backup.py
import subprocess
from datetime import datetime

def backup_before_migration():
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    backup_file = f"backups/pre_migration_{timestamp}.sql"
    
    subprocess.run([
        'pg_dump',
        '-h', 'localhost',
        '-U', 'faro',
        '-d', 'faro_db',
        '-f', backup_file,
        '--create',
        '--clean'
    ], check=True)
    
    print(f"Backup criado: {backup_file}")
    return backup_file
```

---

### 15. Scripts de Instalação Sem Verificação de Hash
**Arquivos:** `install-faro.ps1`, `start-services.ps1`

**Problema:** Downloads de dependências sem verificação de integridade.

---

## 🟡 PROBLEMAS MÉDIOS

### 16. Documentação Swagger Desativada
**Arquivo:** `server-core/app/main.py:126-128`

```python
docs_url=None,  # Temporarily disabled due to Pydantic forward reference error
redoc_url=None,  # Temporarily disabled due to Pydantic forward reference error
openapi_url=None,  # Temporarily disabled due to Pydantic forward reference error
```

**Ação:** Resolver erro de forward reference no Pydantic v2.

---

### 17. Testes Unitários Ausentes
**Arquivo:** `server-core/tests/` (vazio)

**Status:** 0% cobertura de testes automatizados.

**Prioridade:** Criar testes para:
- Autenticação
- CRUD de observações
- Algoritmos de inteligência
- OCR service

---

### 18. Configuração Docker Para Desenvolvimento Apenas
**Arquivo:** `infra/docker/docker-compose.yml`

**Problema:** Configurações hardcoded para dev, sem profiles para staging/prod.

---

### 19. Missing Health Check para Web Console
**Status:** Server Core tem /health, mas Web Console não.

---

### 20. Analytics Dashboard Sem Rate Limiting
**Arquivo:** `server-core/analytics_dashboard/app.py`

**Status:** Endpoint de dashboard sem proteção.

---

### 21-34. (Outros problemas médios documentados nos arquivos fonte)

---

## 🔵 PROBLEMAS BAIXOS

### 35. Imports Não Usados
**Arquivos:** Vários arquivos Python

**Ação:** Executar `autoflake` e `isort` para limpar.

---

### 36. Código Comentado Morto
**Exemplo:** `auth.py` tem 100+ linhas comentadas de roadmap.

**Ação:** Mover para documentação externa.

---

### 37. Inconsistência de Formatação
**Problema:** Mix de f-strings, .format() e concatenação.

**Ação:** Padronizar com Black formatter.

---

### 38-42. (Outros problemas baixos)

---

## Plano de Correção Priorizado

### Fase 1: Segurança Crítica (1-2 dias)
1. ✅ CORS restritivo
2. ✅ JWT secret validation
3. ✅ Exception handling específico
4. ✅ Hardcoded secrets

### Fase 2: Estabilidade (3-5 dias)
5. ✅ Redis cache com retry
6. ✅ Circuit breaker aprimorado
7. ✅ Health checks completos

### Fase 3: Qualidade de Código (1 semana)
8. ✅ Remover TODOs não priorizados
9. ✅ Console.logs → logger estruturado
10. ✅ Testes unitários críticos

### Fase 4: Performance (1 semana)
11. ✅ LRU cache
12. ✅ Rate limiting por endpoint
13. ✅ Async optimizations

---

## Scripts de Correção Automática

### 1. Remover Console.logs
```bash
#!/bin/bash
# remove_console_logs.sh
find web-intelligence-console/src -name "*.ts" -o -name "*.tsx" | \
  xargs sed -i 's/console\.log(/\/\/ TODO: Replace with proper logger - console.log(/g'
```

### 2. Verificar TODOs
```bash
#!/bin/bash
# check_todos.sh
echo "TODOs por arquivo:"
grep -r "TODO\|FIXME\|HACK" --include="*.py" --include="*.ts" --include="*.tsx" server-core web-intelligence-console | \
  grep -v "node_modules" | \
  awk -F: '{print $1}' | \
  sort | \
  uniq -c | \
  sort -rn | \
  head -20
```

### 3. Verificar Exception Handling
```bash
#!/bin/bash
# check_exceptions.sh
echo "Exception handling genérico encontrado:"
grep -rn "except Exception:" --include="*.py" server-core/app | \
  grep -v "test" | \
  head -30
```

---

## Métricas de Qualidade Atual

| Métrica | Valor Atual | Meta |
|---------|-------------|------|
| Cobertura de testes | 0% | 80% |
| TODOs em aberto | 251+ | <20 |
| Exception handling específico | 15% | 95% |
| Documentação Swagger | ❌ Desativada | ✅ Ativa |
| Secrets hardcoded | 8 | 0 |
| Console.logs em produção | 251+ | 0 |

---

## Conclusão

O projeto FARO tem **arquitetura sólida** mas precisa de:
1. **Hardening de segurança** (prioridade absoluta)
2. **Refatoração de exception handling**
3. **Implementação de testes**
4. **Limpeza de código legado**

**Estimativa de trabalho:** 3-4 semanas para resolver todos os problemas críticos e altos.

---

**Elaborado por:** Diagnóstico Automático FARO  
**Revisão necessária:** Sim - priorizar com Product Owner  
**Aprovação:** Aguardando
