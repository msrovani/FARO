# Asset Display Implementation - FARO Web Intelligence Console

## Overview

Este documento descreve a implementação completa de exibição de assets (imagens, áudio, vídeo) no Web Intelligence Console do FARO, incluindo:

- Servidor de assets com fallback automático (MinIO → Local Storage)
- Componentes React para exibição de imagens
- Integração com Queue page
- Configuração e uso

## Arquitetura

### Backend (Server Core)

```
┌─────────────────────────────────────────────────────────────┐
│                     Mobile App Upload                         │
└───────────────────────┬─────────────────────────────────────┘
                        │
                        ▼
┌─────────────────────────────────────────────────────────────┐
│              POST /mobile/observations/{id}/assets           │
│              storage_service.py                               │
│  ┌───────────────────────────────────────────────────────┐  │
│  │  1. Check S3 available?                               │  │
│  │     ├─ Yes → Upload to MinIO (bucket: faro-assets)   │  │
│  │     └─ No  → Upload to local (./local_assets/)      │  │
│  └───────────────────────────────────────────────────────┘  │
└───────────────────────┬─────────────────────────────────────┘
                        │
                        ▼
┌─────────────────────────────────────────────────────────────┐
│              GET /api/v1/assets/{bucket}/{path}            │
│              assets.py (endpoint)                          │
│  ┌───────────────────────────────────────────────────────┐  │
│  │  1. bucket == "local"?                               │  │
│  │     ├─ Yes → Serve from ./local_assets/{path}         │  │
│  │     └─ No  → Try S3/MinIO                            │  │
│  │              ├─ Success → Return file                  │  │
│  │              └─ Fail    → Fallback to local            │  │
│  └───────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────┘
```

### Frontend (Web Intelligence Console)

```
┌─────────────────────────────────────────────────────────────┐
│              Queue Page (Observation Detail)                │
│  ┌───────────────────────────────────────────────────────┐  │
│  │  PlateImage Component                                │  │
│  │  - getPlateImageUrl(plateRead)                       │  │
│  │  - Display thumbnail with confidence indicator        │  │
│  └───────────────────────────────────────────────────────┘  │
│  ┌───────────────────────────────────────────────────────┐  │
│  │  EvidenceGallery Component                            │  │
│  │  - getEvidenceUrls(suspicion_report)                │  │
│  │  - Lightbox gallery for photos/audio/video           │  │
│  └───────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────┘
```

## Arquivos Modificados/Criados

### Backend

#### 1. `server-core/app/core/config.py`
**Alterações:**
- Adicionado `s3_enabled: bool = False` (MinIO opcional)
- Adicionado `local_storage_path: str = "./local_assets"` (caminho do fallback)
- Adicionado `local_storage_max_size_mb: int = 10240` (limite de 10GB)

**Propósito:** Tornar MinIO opcional com fallback automático para local storage.

#### 2. `server-core/app/services/storage_service.py`
**Alterações:**
- Adicionado `_check_s3_available()` - verifica disponibilidade do MinIO
- Adicionado `_upload_local()` - upload para filesystem local
- Modificado `upload_observation_asset_bytes()` - usa MinIO se disponível, senão local
- Modificado `upload_observation_asset_progressive()` - fallback para upload simples se MinIO indisponível
- Adicionado `_ensure_local_storage_dir()` - cria diretório de storage local

**Propósito:** Implementar fallback automático para armazenamento local.

#### 3. `server-core/app/api/v1/endpoints/assets.py` (NOVO)
**Criado:** Endpoint para servir assets do storage

**Endpoints:**
- `GET /api/v1/assets/{bucket}/{path}` - Serve arquivo (imagem/áudio/vídeo)
- `HEAD /api/v1/assets/{bucket}/{path}` - Verifica existência sem baixar

**Comportamento:**
- Se bucket == "local": serve de `./local_assets/{path}`
- Se bucket != "local": tenta MinIO primeiro, fallback para local se falhar
- Cache headers: `Cache-Control: public, max-age=3600` (1 hora)

#### 4. `server-core/app/api/routes.py`
**Alterações:**
- Importado `assets` endpoint
- Adicionado rota: `api_router.include_router(assets.router, prefix="/v1", tags=["Assets"])`

**Propósito:** Expor endpoint de assets na API.

#### 5. `server-core/app/services/storage_service.md` (NOVO)
**Criado:** Documentação completa do storage service

**Conteúdo:**
- Configuração de variáveis de ambiente
- Comportamento de fallback
- Estrutura de armazenamento
- Uso (upload simples e progressivo)
- Comparação MinIO vs Local Storage
- Setup MinIO (opcional)
- Troubleshooting

### Frontend

#### 6. `web-intelligence-console/src/app/components/PlateImage.tsx` (NOVO)
**Criado:** Componente para exibir imagem da placa

**Props:**
- `imageUrl?: string` - URL da imagem
- `plateNumber?: string` - número da placa
- `confidence?: number` - confiança do OCR (0-1)
- `size?: "sm" | "md" | "lg"` - tamanho do componente
- `className?: string` - classes CSS adicionais

**Comportamento:**
- Loading spinner enquanto carrega
- Placeholder com ícone se imagem não disponível
- Indicador de alerta se confiança < 80%
- Tratamento de erro de carregamento

#### 7. `web-intelligence-console/src/app/components/EvidenceGallery.tsx` (NOVO)
**Criado:** Componente galeria lightbox para evidências

**Props:**
- `items: EvidenceItem[]` - array de evidências (url, type, filename)
- `className?: string` - classes CSS adicionais

**Comportamento:**
- Grid de thumbnails (4 colunas)
- Lightbox modal ao clicar
- Navegação entre itens (setas)
- Download button
- Contador de itens
- Suporte a imagens, áudio e vídeo

#### 8. `web-intelligence-console/src/app/services/api.ts`
**Alterações:**
- Adicionado `getAssetUrl(bucket, key)` - gera URL completa do asset
- Adicionado `getPlateImageUrl(plateRead)` - gera URL da imagem da placa
- Adicionado `getEvidenceUrls(report)` - gera URLs das evidências

**Propósito:** Helper functions para gerar URLs de assets.

#### 9. `web-intelligence-console/src/app/queue/page.tsx`
**Alterações:**
- Importado `PlateImage` e `EvidenceGallery` componentes
- Importado `getPlateImageUrl` e `getEvidenceUrls` do API service
- Adicionado seção "Imagem da Placa" após informações de OCR
- Adicionado seção "Evidências Anexadas" após Intel Debrief

**Propósito:** Exibir imagens na Queue page.

### Documentação

#### 10. `INSTALL.md`
**Alterações:**
- Adicionado seção "10.5 💾 Install MinIO for Asset Storage (Optional)"
- Documentado MinIO como opcional com fallback local
- Atualizado Summary para incluir MinIO como passo opcional
- Atualizado Installation Report para mencionar MinIO como opcional
- Atualizado Alternative Options para incluir como habilitar MinIO

#### 11. `infra/docker/docker-compose.yml`
**Alterações:**
- Adicionado comentários detalhados sobre MinIO ser opcional
- Documentado portas reservadas (9000, 9001) e uso de 9002
- Instruções para iniciar ou pular MinIO

#### 12. `docs/architecture/zero-trust-implementation.md`
**Alterações:**
- Adicionado comentários sobre portas reservadas para MinIO

#### 13. `server-core/docs/prometheus-alerts-full.yaml`
**Alterações:**
- Atualizado referência de porta 9001 para 9002
- Adicionado nota sobre portas reservadas

#### 14. `server-core/analytics_dashboard/README.md`
**Alterações:**
- Adicionado nota sobre portas reservadas para MinIO
- Atualizado porta padrão para 9002

#### 15. `server-core/app/core/config.py`
**Alterações:**
- Adicionado comentário sobre porta 9000 reservada para MinIO

## Configuração

### Variáveis de Ambiente (Server Core)

```bash
# MinIO/S3 Storage (Opcional - default: usa local storage)
S3_ENABLED=false                              # Habilita MinIO (default: false)
S3_ENDPOINT=http://localhost:9000             # Endpoint do MinIO
S3_ACCESS_KEY=minioadmin                      # Chave de acesso
S3_SECRET_KEY=minioadmin                      # Senha
S3_BUCKET_NAME=faro-assets                     # Nome do bucket
S3_REGION=us-east-1                           # Região
S3_SECURE=false                               # Usa HTTPS
S3_PRESIGNED_URL_EXPIRY=3600                  # Expiração de URLs (1 hora)

# Local Storage Fallback (usado quando MinIO não disponível)
LOCAL_STORAGE_PATH=./local_assets              # Caminho do storage local
LOCAL_STORAGE_MAX_SIZE_MB=10240               # Limite (10GB)
```

### Variáveis de Ambiente (Web Console)

```bash
NEXT_PUBLIC_API_URL=http://localhost:8000      # URL do Server Core
```

## Uso

### Upload de Assets (Mobile App)

```python
# Upload simples (pequenos arquivos)
POST /api/v1/mobile/observations/{observation_id}/assets
Content-Type: multipart/form-data

{
  "asset_type": "image",
  "file": <binary data>
}

# Upload progressivo (arquivos grandes)
POST /api/v1/mobile/observations/{observation_id}/assets/progressive
Content-Type: multipart/form-data

{
  "asset_type": "video",
  "file": <chunk data>,
  "upload_id": "uuid",  # null na primeira requisição
  "chunk_index": 0
}
```

### Acesso a Assets (Web Console)

```typescript
// Gerar URL da imagem da placa
const plateImageUrl = getPlateImageUrl(plateRead);
// Retorna: "http://localhost:8000/api/v1/assets/faro-assets/observations/123/image/abc.jpg"

// Gerar URLs das evidências
const evidenceUrls = getEvidenceUrls(suspicion_report);
// Retorna: [{ url: "...", type: "image", filename: "evidence.jpg" }]
```

### Endpoint de Assets

```bash
# Obter arquivo
GET /api/v1/assets/faro-assets/observations/{id}/image/{filename}
GET /api/v1/assets/local/observations/{id}/image/{filename}

# Verificar existência
HEAD /api/v1/assets/faro-assets/observations/{id}/image/{filename}
```

## Comportamento de Fallback

### Cenário 1: MinIO Habilitado e Disponível
1. `S3_ENABLED=true`
2. MinIO rodando em `http://localhost:9000`
3. Upload → MinIO bucket `faro-assets`
4. Acesso → Serve do MinIO

### Cenário 2: MinIO Habilitado mas Indisponível
1. `S3_ENABLED=true`
2. MinIO NÃO está rodando
3. Upload → Detecta falha → Upload para `./local_assets/`
4. Acesso → Tenta MinIO → Falha → Fallback para local

### Cenário 3: MinIO Desabilitado (Default)
1. `S3_ENABLED=false` (default)
2. Upload → Diretamente para `./local_assets/`
3. Acesso → Serve de `./local_assets/`

## Estrutura de Armazenamento

### MinIO (S3)
```
faro-assets/
└── observations/
    └── {observation_id}/
        └── {asset_type}/
            └── {uuid}_{filename}
```

### Local Storage
```
local_assets/
└── observations/
    └── {observation_id}/
        └── {asset_type}/
            └── {uuid}_{filename}
```

## Componentes React

### PlateImage

```tsx
<PlateImage
  imageUrl={getPlateImageUrl(plateRead)}
  plateNumber="ABC1234"
  confidence={0.95}
  size="lg"
  className="w-full"
/>
```

**Features:**
- Loading spinner
- Placeholder se imagem não disponível
- Indicador de confiança (< 80%)
- Tratamento de erro
- Tamanhos: sm, md, lg

### EvidenceGallery

```tsx
<EvidenceGallery
  items={getEvidenceUrls(suspicion_report)}
  className="mt-4"
/>
```

**Features:**
- Grid de thumbnails
- Lightbox modal
- Navegação (setas)
- Download button
- Contador de itens
- Suporte a image/audio/video

## Troubleshooting

### MinIO não conecta

**Sintoma:** Logs mostram "S3/MinIO not available, using local storage fallback"

**Soluções:**
1. Verifique se MinIO está rodando: `docker ps | grep minio`
2. Verifique porta 9000: `netstat -ano | findstr ":9000"`
3. Verifique configuração de endpoint
4. Se não precisar de MinIO, deixe `S3_ENABLED=false` (default)

### Storage local cheio

**Sintoma:** Erro ao escrever arquivos em `local_assets/`

**Soluções:**
1. Limpe arquivos antigos em `local_assets/`
2. Aumente `LOCAL_STORAGE_MAX_SIZE_MB`
3. Configure MinIO para armazenamento escalável

### Imagens não carregam no Web Console

**Sintoma:** Componente PlateImage mostra placeholder

**Soluções:**
1. Verifique se asset foi uploadado corretamente
2. Verifique endpoint de assets: `GET /api/v1/assets/{bucket}/{path}`
3. Verifique console do browser para erros de rede
4. Verifique se `NEXT_PUBLIC_API_URL` está configurado corretamente

### Upload progressivo falha

**Sintoma:** Upload progressivo cai para upload simples

**Causa:** MinIO não está disponível

**Solução:**
1. Verifique disponibilidade do MinIO
2. Habilite MinIO se precisar de upload progressivo
3. Use upload simples se MinIO não for necessário

## Notas Importantes

- **MinIO é opcional:** O sistema funciona perfeitamente com apenas storage local
- **Fallback automático:** Se MinIO falhar, usa local storage sem interrupção
- **Portas reservadas:** 9000 (MinIO S3), 9001 (MinIO Console), 9002 (Analytics Dashboard)
- **Dados sensíveis:** Para operações de polícia, considere usar MinIO local ao invés de AWS S3
- **Backup:** Configure backup regular tanto de `local_assets/` quanto do bucket MinIO
- **Cache:** Assets são cacheados por 1 hora no navegador para melhor performance

## Próximos Passos (Opcionais)

1. **Implementar presigned URLs** para acesso direto ao MinIO (bypass do servidor)
2. **Adicionar compressão de imagens** automaticamente no upload
3. **Implementar thumbnails** automáticos para imagens grandes
4. **Adicionar metadados** (EXIF) extração de imagens
5. **Implementar CDN** para distribuição de assets em produção
6. **Adicionar watermarking** para evidências sensíveis
7. **Implementar retenção automática** de assets antigos
8. **Adicionar criptografia** de assets sensíveis
