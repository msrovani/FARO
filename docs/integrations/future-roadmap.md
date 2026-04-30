# Roadmap de Integrações Futuras - F.A.R.O.

> **Documento para desenvolvedores futuros**
> 
> Este arquivo contém as integrações planejadas que devem ser implementadas em versões futuras do sistema.
> Cada seção possui TODOs claros e especificações técnicas.

---

## 1. Consulta de Placa em Bases Oficiais

### Status
🟡 **PREPARADO** - Estrutura pronta, aguardando implementação

### Localização no Código
- **Endpoint:** `server-core/app/api/v1/endpoints/mobile.py::check_plate_suspicion()`
- **Adapter:** `server-core/app/integrations/state_registry_adapter.py`
- **Schema:** `server-core/app/schemas/observation.py::PlateSuspicionCheckResponse`

### O que já está pronto
- Endpoint `/mobile/plates/{plate}/check-suspicion` criado
- Schema de resposta com campos opcionais para dados oficiais
- Função mock em `state_registry_adapter.py` (retorna "sem conexão")
- Estrutura de chamada comentada no endpoint

### Bases a integrar

#### 1.1 DETRAN-RS (Rio Grande do Sul) - PRIORIDADE ALTA
**Dados desejados:**
- Situação do veículo (roubado/furtado/clonado)
- Débitos e restrições administrativas
- Dados cadastrais (marca, modelo, cor, ano)
- Proprietário (se autorizado por política de privacidade)

**Arquivos a criar:**
```
server-core/app/integrations/detran_rs_adapter.py
```

**Configurações (.env):**
```bash
DETRAN_RS_ENDPOINT=https://api.detran.rs.gov.br/veiculos
DETRAN_RS_API_KEY=xxx
DETRAN_RS_CERT_PATH=/certs/detran_rs.pem
```

#### 1.2 Polícia Federal - Alertas Nacionais - PRIORIDADE ALTA
**Dados desejados:**
- Veículos com alerta nacional (roubo/furto)
- Alertas INTERPOL/Fronteira
- Ocorrências federais

**Arquivos a criar:**
```
server-core/app/integrations/federal_police_adapter.py
```

**Requisitos:**
- Certificado digital ICP-Brasil
- Credenciais fornecidas pela SSI/BMRS
- Acesso à rede segura da Polícia Federal

#### 1.3 RENAVAM (Ministério da Fazenda) - PRIORIDADE MÉDIA
**Dados desejados:**
- Dados cadastrais completos do veículo
- Histórico de proprietários
- Restrições judiciais

**Arquivos a criar:**
```
server-core/app/integrations/renavam_adapter.py
```

### Implementação - Passo a Passo

1. **Criar adapter** seguindo padrão de `state_registry_adapter.py`
2. **Implementar função** `query_<source>_vehicle_registry(plate_number: str) -> dict`
3. **Descomentar chamada** no endpoint `check_plate_suspicion()` (linha ~277)
4. **Enriquecer resposta** com dados oficiais no `PlateSuspicionCheckResponse`
5. **Adicionar cache** Redis para evitar consultas repetidas
6. **Testar** com placas de teste (consultar SELOG/BMRS)

### Exemplo de implementação no endpoint

```python
# Em check_plate_suspicion(), descomentar:

from app.integrations.detran_rs_adapter import query_detran_rs
from app.integrations.federal_police_adapter import query_federal_police

# Consultar bases oficiais
official_data = await query_detran_rs(plate_number=normalized_plate)
federal_data = await query_federal_police(plate_number=normalized_plate)

# Usar dados para enriquecer resposta
if official_data.get("is_stolen") or federal_data.get("has_national_alert"):
    is_suspect = True
    alert_level = "critical"
    alert_title = "VEÍCULO ROUBADO/FURTADO - BASE OFICIAL"
    
return PlateSuspicionCheckResponse(
    plate_number=normalized_plate,
    is_suspect=is_suspect,
    # ... campos existentes ...
    # Novos campos com dados oficiais:
    state_registry_status=official_data,
    federal_alert_status=federal_data,
    official_owner_name=official_data.get("owner_name"),  # se autorizado
    official_debt_info=official_data.get("debts"),
)
```

### Contatos para obter credenciais
- **SSI/BMRS:** Solicitar através de processo administrativo
- **DETRAN-RS:** Assessoria de Tecnologia
- **Polícia Federal:** Delegacia de Polícia Federal em Porto Alegre

---

## 2. Autenticação em Bases Oficiais

### Status
🟡 **PREPARADO** - Estrutura pronta, autenticação local funcionando

### Localização no Código
- **Endpoint:** `server-core/app/api/v1/endpoints/auth.py::login()`
- **Função comentada:** `verify_with_intelligence_db()` (linha ~84)
- **Schemas:** `server-core/app/schemas/user.py::UserLogin`

### O que já está pronto
- Login aceita CPF ou email (`identifier`)
- Schema preparado para receber `badge_number`
- Função stub comentada com documentação extensa
- Lógica de detecção de CPF (11 dígitos) implementada

### Sistemas a integrar

#### 2.1 GOV.BR (Login Único Federal) - PRIORIDADE ALTA
**Funcionalidade:**
- SSO via OAuth2/OIDC
- Validação de CPF via token gov.br
- Login sem senha local (confiança no gov.br)

**Arquivos a criar:**
```
server-core/app/integrations/govbr_auth_adapter.py
```

**Configurações (.env):**
```bash
GOVBR_CLIENT_ID=faro-bmrs-prod
GOVBR_CLIENT_SECRET=xxx
GOVBR_REDIRECT_URI=https://faro.bmrs.gov.br/auth/callback
GOVBR_AUTH_URL=https://sso.acesso.gov.br/authorize
GOVBR_TOKEN_URL=https://sso.acesso.gov.br/token
```

**Implementação necessária:**
- [ ] Cadastrar FARO como aplicação no gov.br
- [ ] Implementar fluxo OAuth2 completo
- [ ] Criar endpoint de callback `/auth/callback`
- [ ] Validar token e extrair CPF
- [ ] Criar/associar usuário FARO ao CPF do gov.br

#### 2.2 Sistema de RH/PESSOAL BMRS - PRIORIDADE ALTA
**Funcionalidade:**
- Verificar se policial está ativo
- Validar matrícula, CPF, unidade de lotação
- Sincronizar dados básicos (nome, posto, unidade)

**Arquivos a criar:**
```
server-core/app/integrations/bmrs_hr_adapter.py
```

**Configurações (.env):**
```bash
BMRS_HR_ENDPOINT=https://rh.intranet.bmrs.gov.br/api
BMRS_HR_API_KEY=xxx
BMRS_HR_CERT_PATH=/certs/bmrs_hr.pem
```

**Dados esperados da API interna:**
```json
{
  "cpf": "00000000000",
  "matricula": "BMRS-12345",
  "nome_completo": "Fulano de Tal",
  "posto": "Soldado",
  "unidade_lotacao": "10º BPM",
  "status": "ativo",
  "data_ingresso": "2020-01-15"
}
```

#### 2.3 SIGMIL (Sistema de Identidade Militar) - PRIORIDADE MÉDIA
**Funcionalidade:**
- Validação de credencial militar
- Verificação de autenticidade

**Arquivos a criar:**
```
server-core/app/integrations/sigmil_adapter.py
```

### Implementação - Passo a Passo

1. **Criar adapters** conforme especificação acima
2. **Descomentar função** `verify_with_intelligence_db()` em `auth.py`
3. **Implementar lógica** de fallback (tenta BMRS HR → gov.br → local)
4. **Descomentar chamada** no login (linha ~186)
5. **Criar endpoint de callback** para OAuth (gov.br)
6. **Testar** com usuários de teste

### Fluxo de Autenticação Futuro

```
┌─────────────┐     ┌──────────────┐     ┌─────────────────┐
│  Usuário    │────▶│   FARO       │────▶│  detecta CPF?   │
└─────────────┘     └──────────────┘     └─────────────────┘
                           │                           │
                           │ NÃO                       │ SIM (11 dígitos)
                           ▼                           ▼
                    ┌──────────────┐     ┌─────────────────┐
                    │ Auth local   │     │ verify_with_    │
                    │ (email/senha)│     │ intelligence_db │
                    └──────────────┘     └─────────────────┘
                                                      │
                           ┌──────────────────────────┼──────────────────┐
                           │                          │                  │
                           ▼                          ▼                  ▼
                    ┌──────────────┐        ┌──────────────┐    ┌──────────────┐
                    │ BMRS HR API  │───────▶│  Gov.br SSO │───▶│   FARO DB   │
                    └──────────────┘        └──────────────┘    └──────────────┘
```

### Segurança - Requisitos

- **Certificados ICP-Brasil:** Todos os adapters devem usar certificados válidos
- **TLS 1.3:** Conexões apenas com TLS 1.3+
- **Circuit Breaker:** Implementar fallback caso APIs externas falhem
- **Rate Limiting:** Respeitar limites das APIs externas
- **Audit Logs:** Logar todas as consultas externas (já preparado em `ExternalQuery`)
- **Cache:** Cachear resultados por 1-5 minutos para evitar consultas repetidas

### Contatos para credenciais

| Sistema | Responsável | Contato |
|---------|-------------|---------|
| GOV.BR | SSI/BMRS - TI | Processo administrativo via SSI |
| BMRS HR | Secretaria de Gestão de Pessoas | Solicitação formal à SEPLAG |
| Polícia Federal | Delegacia Federal POA | Ofício via SSI |
| DETRAN-RS | Ciretran/Assessoria TI | Processo administrativo |

---

## Checklist para Novo Desenvolvedor

Antes de começar a implementar:

- [ ] Ler TODOs em `auth.py` linha 37-132
- [ ] Ler TODOs em `mobile.py` linha 235-286
- [ ] Entender estrutura de adapters existente
- [ ] Solicitar credenciais de acesso (via SSI/BMRS)
- [ ] Configurar ambiente de desenvolvimento com certificados
- [ ] Implementar adapters em ambiente de teste primeiro
- [ ] Adicionar testes unitários com mocks
- [ ] Documentar no `onboarding.md` e `openmemory.md`

---

## Notas Importantes

1. **PRIORIDADE:** Consulta de placa (DETRAN/PF) tem prioridade sobre autenticação externa
2. **LEI DE ACESSO:** Consultar dados oficiais requer justificativa operacional (art. 7º, Lei 12.527/2011)
3. **SIGILO:** Dados de consulta oficial são sigilosos - não logar detalhes sensíveis
4. **OFFLINE:** Sistema deve funcionar mesmo com APIs externas indisponíveis (fallback para dados locais)

---

**Última atualização:** Abril 2026
**Responsável:** Sistema F.A.R.O. - SSI/BMRS
**Próxima revisão:** Quando integrações forem implementadas
