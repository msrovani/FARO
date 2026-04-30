# Análise de Gaps do INSTALL.md - Simulação de Cenários de Instalação

**Data:** 2026-04-22
**Objetivo:** Garantir que uma IA consiga fazer 100% da instalação automatizada, entregando server e serviços UP e páginas prontas para uso.

---

## 🔍 Resumo da Análise

O INSTALL.md atual é **muito detalhado e completo** (2351 linhas), mas é focado em **instruções manuais** para humanos. Para automação por IA, existem gaps críticos que impedem uma instalação 100% automatizada.

---

## 📊 Cenários Simulados

### Cenário 1: Instalação Limpa em Windows (Zero Dependencies)

**Estado Inicial:**
- Windows 10/11 limpo
- Python não instalado
- PostgreSQL não instalado
- Docker não instalado
- Node.js não instalado
- Git não instalado
- FARO clonado em `C:\Users\user\FARO`

**Simulação de Execução IA:**

1. **Verificar Python**
   - ✅ Passo claro no INSTALL.md
   - ⚠️ **GAP:** Download automático do instalador pode falhar (links mudam)
   - ⚠️ **GAP:** Instalação silenciosa pode requerer reboot
   - ⚠️ **GAP:** PATH não atualiza imediatamente após instalação

2. **Verificar PostgreSQL**
   - ✅ Passo claro no INSTALL.md
   - ⚠️ **GAP:** Download automático pode falhar
   - ⚠️ **GAP:** Instalação silenciosa requer senha do postgres
   - ⚠️ **GAP:** Service pode não iniciar automaticamente
   - ⚠️ **GAP:** pg_hba.conf location pode variar

3. **Verificar PostGIS**
   - ✅ Passo claro no INSTALL.md
   - ⚠️ **GAP:** Download do bundle pode falhar
   - ⚠️ **GAP:** Versão do PostGIS deve corresponder ao PostgreSQL 16
   - ⚠️ **GAP:** Installer pode requerer confirmação manual

4. **Configurar Database**
   - ✅ Passo claro no INSTALL.md
   - ⚠️ **GAP:** Password hardcoded ("faro") - security risk
   - ⚠️ **GAP:** Trust authentication não é seguro para produção

5. **Migrations**
   - ✅ Passo claro no INSTALL.md
   - ⚠️ **GAP:** Alembic connection string hardcoded
   - ⚠️ **GAP:** Migrations podem falhar se PostGIS não habilitado
   - ⚠️ **GAP:** Migration 0020 (pg_stat_statements) pode falhar em Windows

6. **Seed Data**
   - ✅ Passo claro no INSTALL.md
   - ⚠️ **GAP:** seed_data.py usa connection string hardcoded
   - ⚠️ **GAP:** Script não verifica se dados já existem
   - ⚠️ **GAP:** ON CONFLICT pode não funcionar corretamente

7. **Docker (Opcional)**
   - ✅ Passo claro no INSTALL.md
   - ⚠️ **GAP:** Docker Desktop requer WSL 2 (pode não estar habilitado)
   - ⚠️ **GAP:** Instalação Docker pode requerer reboot
   - ⚠️ **GAP:** docker-compose.dev.yml não existe (scripts .bat referenciam)

8. **Node.js (para Web Console)**
   - ⚠️ **GAP CRÍTICO:** Node.js não está no INSTALL.md como pré-requisito obrigatório
   - ⚠️ **GAP CRÍTICO:** npm install pode falhar com dependências quebradas
   - ⚠️ **GAP:** Port 3000 pode estar ocupado

9. **Start Services**
   - ✅ Passo claro no INSTALL.md
   - ⚠️ **GAP:** Requer múltiplas janelas/terminais
   - ⚠️ **GAP:** Analytics dashboard directory rename não está automatizado
   - ⚠️ **GAP:** Verificação de health check não está automatizada

**Resultado do Cenário 1:**
- **Status:** ❌ FALHA AUTOMAÇÃO
- **Bloqueadores Críticos:**
  1. Node.js não listado como pré-requisito obrigatório
  2. Scripts de startup não são automatizados
  3. Verificação final não está automatizada
  4. docker-compose.dev.yml não existe

---

### Cenário 2: Instalação em Ambiente Sem Docker

**Estado Inicial:**
- Windows 10/11
- Python 3.12 instalado
- PostgreSQL 16 instalado manualmente
- Docker NÃO instalado (política corporativa)
- Node.js instalado
- FARO clonado

**Simulação de Execução IA:**

1. **PostgreSQL Manual**
   - ✅ Install.md tem "Option B: Manual Installation"
   - ⚠️ **GAP:** PostGIS manual installation não é trivial no Windows
   - ⚠️ **GAP:** TimescaleDB manual installation não documentado claramente
   - ⚠️ **GAP:** Citus não disponível manualmente (requer compilação)

2. **MinIO (Opcional)**
   - ✅ Install.md diz "system works with local storage fallback"
   - ⚠️ **GAP:** Não está claro quando usar MinIO vs local storage
   - ⚠️ **GAP:** Configuração .env não está documentada para ativar MinIO

3. **PgBouncer (Opcional)**
   - ✅ Install.md tem instruções
   - ⚠️ **GAP:** userlist.txt não existe no projeto
   - ⚠️ **GAP:** MD5 hash hardcoded pode não corresponder à senha real

4. **Prometheus (Opcional)**
   - ✅ Install.md tem instruções
   - ⚠️ **GAP:** prometheus.yml não existe em infra/observability/prometheus/
   - ⚠️ **GAP:** Configuração não está pronta

5. **Web Services**
   - ✅ Install.md tem instruções
   - ⚠️ **GAP:** Analytics dashboard rename não está automatizado
   - ⚠️ **GAP:** Port conflicts não são detectados automaticamente

**Resultado do Cenário 2:**
- **Status:** ⚠️ PARCIAL
- **Bloqueadores:**
  1. PostGIS manual installation complexo
  2. Configuração MinIO vs local storage não clara
  3. Arquivos de configuração faltando (userlist.txt, prometheus.yml)

---

### Cenário 3: Instalação com Conflitos de Portas

**Estado Inicial:**
- Windows 10/11
- Todas as dependências instaladas
- Port 5432 ocupado (outro PostgreSQL)
- Port 8000 ocupado (outro serviço)
- Port 3000 ocupado (outro Next.js)
- Port 9000 ocupado (outro MinIO)

**Simulação de Execução IA:**

1. **PostgreSQL Port Conflict**
   - ⚠️ **GAP CRÍTICO:** Install.md não documenta como mudar porta do PostgreSQL
   - ⚠️ **GAP:** Connection string em alembic.ini e .env não usa variável
   - ⚠️ **GAP:** seed_data.py usa connection string hardcoded

2. **Server Core Port Conflict**
   - ✅ Install.md sugere usar porta diferente (8001)
   - ⚠️ **GAP:** Web console não sabe qual porta usar
   - ⚠️ **GAP:** CORS_ORIGINS não está configurado para porta alternativa

3. **Web Console Port Conflict**
   - ✅ Install.md sugere usar PORT=3001
   - ⚠️ **GAP:** API URL no frontend pode estar hardcoded para 8000
   - ⚠️ **GAP:** Navegador aberto automaticamente usa porta errada (INICIAR_FARO.bat)

4. **MinIO Port Conflict**
   - ⚠️ **GAP:** Install.md não documenta como mudar portas do MinIO
   - ⚠️ **GAP:** docker-compose.yml não usa variáveis de ambiente para portas
   - ⚠️ **GAP:** .env não tem variáveis para portas MinIO

**Resultado do Cenário 3:**
- **Status:** ❌ FALHA
- **Bloqueadores Críticos:**
  1. Portas hardcoded em múltiplos arquivos
  2. Não há script de detecção de portas ocupadas
  3. Não há configuração centralizada de portas

---

### Cenário 4: Instalação com Dependências Faltantes

**Estado Inicial:**
- Windows 10/11
- Python 3.11 (versão incorreta)
- PostgreSQL 15 (versão incorreta)
- Docker Desktop não instalado
- Node.js 16 (versão incorreta)
- FARO clonado

**Simulação de Execução IA:**

1. **Python Version Wrong**
   - ✅ Install.md verifica versão
   - ⚠️ **GAP:** Não há script automático de downgrade/upgrade
   - ⚠️ **GAP:** py launcher pode não estar instalado
   - ⚠️ **GAP:** Múltiplas versões Python podem causar conflitos

2. **PostgreSQL Version Wrong**
   - ✅ Install.md verifica versão
   - ⚠️ **GAP:** Não há script automático de upgrade PostgreSQL
   - ⚠️ **GAP:** Upgrade PostgreSQL requer dump/restore manual
   - ⚠️ **GAP:** PostGIS bundle deve corresponder à versão PostgreSQL

3. **Node.js Version Wrong**
   - ⚠️ **GAP CRÍTICO:** Node.js não está nos pré-requisitos do INSTALL.md
   - ⚠️ **GAP:** Next.js 15.x requer Node.js 18.x+
   - ⚠️ **GAP:** Não há verificação automática de versão Node.js

4. **Docker Missing**
   - ✅ Install.md tem "Option B: Manual Installation"
   - ⚠️ **GAP:** MinIO fallback não está claramente documentado
   - ⚠️ **GAP:** TimescaleDB/Citus não funcionam sem Docker

**Resultado do Cenário 4:**
- **Status:** ❌ FALHA
- **Bloqueadores Críticos:**
  1. Node.js não documentado como pré-requisito
  2. Não há scripts de upgrade automático
  3. Dependências de versão não estão claramente documentadas

---

### Cenário 5: Instalação com DB Já Existente

**Estado Inicial:**
- Windows 10/11
- PostgreSQL 16 rodando
- Database faro_db já existe com dados
- FARO clonado

**Simulação de Execução IA:**

1. **DB Existing Check**
   - ✅ Install.md tem "Rotina de Verificação assistida por IA"
   - ⚠️ **GAP:** Requer pergunta ao usuário ("Manter dados ou limpar?")
   - ⚠️ **GAP:** IA não pode tomar decisão automática
   - ⚠️ **GAP:** Script de verificação não existe

2. **Admin DINT Check**
   - ✅ Install.md verifica se admin@dint.pol existe
   - ⚠️ **GAP:** Se não existir, cria vinculado à agência DINT
   - ⚠️ **GAP:** Agência DINT pode não existir
   - ⚠️ **GAP:** Fluxo de decisão não está automatizado

3. **Migrations on Existing DB**
   - ⚠️ **GAP:** alembic upgrade head pode falhar se DB está em versão diferente
   - ⚠️ **GAP:** Não há script de detectar versão atual do DB
   - ⚠️ **GAP:** Não há rollback automático em caso de falha

**Resultado do Cenário 5:**
- **Status:** ⚠️ PARCIAL
- **Bloqueadores:**
  1. Requer decisão humana (não automatizável)
  2. Script de verificação não existe
  3. Não há detecção automática de versão do DB

---

## 🚨 Gaps Críticos Identificados

### 1. **Node.js Não Documentado como Pré-Requisito Obrigatório**
- **Impacto:** CRÍTICO
- **Problema:** Web Intelligence Console (Next.js) requer Node.js 18.x+, mas não está listado nos pré-requisitos do INSTALL.md
- **Solução:** Adicionar Node.js 18.x+ como pré-requisito obrigatório

### 2. **Scripts de Startup Não Automatizados**
- **Impacto:** CRÍTICO
- **Problema:** INICIAR_FARO.bat e start-dev.bat são específicos para BMRS (hardcoded) e referenciam docker-compose.dev.yml que não existe
- **Solução:** Criar script genérico de automação PowerShell

### 3. **Verificação Final Não Automatizada**
- **Impacto:** CRÍTICO
- **Problema:** Não há script que verifique automaticamente se todos os serviços estão UP e saudáveis
- **Solução:** Criar script de health check automatizado

### 4. **docker-compose.dev.yml Não Existe**
- **Impacto:** CRÍTICO
- **Problema:** Scripts .bat referenciam docker-compose.dev.yml mas o arquivo não existe no projeto
- **Solução:** Criar docker-compose.dev.yml ou remover referência dos scripts

### 5. **Portas Hardcoded em Múltiplos Arquivos**
- **Impacto:** ALTO
- **Problema:** Portas estão hardcoded em alembic.ini, .env, seed_data.py, docker-compose.yml
- **Solução:** Centralizar configuração de portas em arquivo .env

### 6. **Analytics Dashboard Directory Rename Não Automatizado**
- **Impacto:** ALTO
- **Problema:** Directory `analytics-dashboard` precisa ser renomeado para `analytics_dashboard` mas não está automatizado
- **Solução:** Automatizar rename no script de startup

### 7. **Configuração MinIO vs Local Storage Não Clara**
- **Impacto:** MÉDIO
- **Problema:** Não está claro quando usar MinIO vs local storage fallback
- **Solução:** Documentar claramente quando usar cada opção

### 8. **Arquivos de Configuração Faltando**
- **Impacto:** MÉDIO
- **Problema:** userlist.txt (PgBouncer), prometheus.yml não existem no projeto
- **Solução:** Criar templates de configuração

### 9. **Detecção de Portas Ocupadas Ausente**
- **Impacto:** MÉDIO
- **Problema:** Não há script que detecte automaticamente portas ocupadas antes de iniciar serviços
- **Solução:** Criar script de detecção de portas

### 10. **Rotina de Decisão Requer Intervenção Humana**
- **Impacto:** MÉDIO
- **Problema:** "Manter dados ou limpar?" requer decisão humana, não automatizável por IA
- **Solução:** Definir comportamento padrão (ex: manter dados sempre)

---

## 📋 Recomendações para Instalação 100% Automatizável

### 1. Criar Script de Automação Principal (install-faro.ps1)

```powershell
# Script principal que:
# 1. Verifica todos os pré-requisitos (Python 3.12, PostgreSQL 16, Node.js 18, Docker)
# 2. Instala dependências faltantes automaticamente
# 3. Configura PostgreSQL + PostGIS
# 4. Executa migrations
# 5. Cria seed data
# 6. Inicia todos os serviços (PostgreSQL, Server Core, Web Console, Analytics Dashboard)
# 7. Verifica health check de todos os serviços
# 8. Gera relatório final de instalação
```

### 2. Criar Script de Verificação (verify-installation.ps1)

```powershell
# Script que verifica:
# 1. PostgreSQL rodando na porta 5432
# 2. Server Core respondendo na porta 8000
# 3. Web Console respondendo na porta 3000
# 4. Analytics Dashboard respondendo na porta 9002
# 5. Database connection funcionando
# 6. Migrations aplicadas
# 7. Seed data criado
# 8. Login funcionando
```

### 3. Criar Script de Startup (start-services.ps1)

```powershell
# Script que:
# 1. Detecta portas ocupadas e sugere alternativas
# 2. Renomeia analytics-dashboard -> analytics_dashboard automaticamente
# 3. Inicia PostgreSQL se não estiver rodando
# 4. Inicia Server Core em background
# 5. Inicia Web Console em background
# 6. Inicia Analytics Dashboard em background
# 7. Aguarda serviços estabilizarem
# 8. Abre navegador automaticamente
```

### 4. Criar docker-compose.dev.yml

```yaml
# Versão simplificada do docker-compose.yml para desenvolvimento
# Inclui apenas: PostgreSQL, Redis, MinIO
# Exclui: Nginx, Prometheus, Grafana, etc.
```

### 5. Centralizar Configuração em .env

```env
# Portas
POSTGRES_PORT=5432
SERVER_PORT=8000
WEB_CONSOLE_PORT=3000
ANALYTICS_DASHBOARD_PORT=9002
MINIO_PORT=9000
MINIO_CONSOLE_PORT=9001

# Database
DATABASE_URL=postgresql+asyncpg://faro:faro@localhost:${POSTGRES_PORT}/faro_db

# Storage
S3_ENABLED=false  # ou true
S3_ENDPOINT=http://localhost:${MINIO_PORT}
```

### 6. Atualizar INSTALL.md

Adicionar seção "Instalação Automatizada por IA":

```markdown
## 🤖 Instalação Automatizada por IA (Recomendado)

Para instalação 100% automatizada sem intervenção manual:

```powershell
cd $env:FARO_HOME
.\install-faro.ps1
```

Este script irá:
- ✅ Verificar e instalar todos os pré-requisitos automaticamente
- ✅ Configurar PostgreSQL + PostGIS
- ✅ Executar migrations
- ✅ Criar seed data
- ✅ Iniciar todos os serviços
- ✅ Verificar health check
- ✅ Gerar relatório final
```

### 7. Adicionar Node.js aos Pré-Requisitos

```markdown
### Required Software
- Python 3.12 LTS
- PostgreSQL 16
- PostGIS Extension for PostgreSQL 16
- Node.js 18.x or higher (for Web Intelligence Console)
- Git (for cloning repository)
```

---

## 🎯 Conclusão

O INSTALL.md atual é **excelente para humanos** mas **não adequado para automação por IA**. Para tornar o processo 100% automatizável, são necessários:

1. **Script principal de automação PowerShell** (install-faro.ps1)
2. **Script de verificação de instalação** (verify-installation.ps1)
3. **Script de startup de serviços** (start-services.ps1)
4. **Arquivo docker-compose.dev.yml** (ou remover referência dos scripts)
5. **Centralização de configuração** em .env
6. **Adicionar Node.js** aos pré-requisitos
7. **Automatizar rename** do analytics-dashboard
8. **Script de detecção de portas ocupadas**

Com essas mudanças, uma IA conseguirá:
- ✅ Instalar todas as dependências automaticamente
- ✅ Configurar o banco de dados
- ✅ Executar migrations
- ✅ Iniciar todos os serviços
- ✅ Verificar que tudo está funcionando
- ✅ Entregar o sistema pronto para uso

**Status Atual:** ❌ Não automatizável por IA
**Status com Melhorias:** ✅ 100% automatizável por IA
