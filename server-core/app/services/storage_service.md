# Storage Service - FARO Assets

## Overview

O Storage Service fornece armazenamento para assets do FARO (imagens, áudio, vídeos) com suporte a:

- **Upload S3/MinIO** (quando disponível)
- **Fallback automático** para armazenamento local (quando MinIO não está disponível)
- **Upload progressivo** em chunks para arquivos grandes
- **Checksum SHA256** para integridade

## Configuração

### Variáveis de Ambiente

| Variável | Padrão | Descrição |
|----------|---------|-----------|
| `S3_ENABLED` | `false` | Habilita uso de MinIO/S3 (default: false para usar local storage) |
| `S3_ENDPOINT` | `http://localhost:9000` | Endpoint do MinIO (porta 9000 reservada) |
| `S3_ACCESS_KEY` | `minioadmin` | Chave de acesso do MinIO |
| `S3_SECRET_KEY` | `minioadmin` | Senha do MinIO |
| `S3_BUCKET_NAME` | `faro-assets` | Nome do bucket no MinIO |
| `S3_REGION` | `us-east-1` | Região do S3 |
| `S3_SECURE` | `false` | Usa HTTPS |
| `LOCAL_STORAGE_PATH` | `./local_assets` | Caminho para armazenamento local (fallback) |
| `LOCAL_STORAGE_MAX_SIZE_MB` | `10240` | Tamanho máximo do storage local (10GB) |

## Comportamento de Fallback

### Quando MinIO NÃO está disponível:

1. **S3_ENABLED=false**: Usa armazenamento local automaticamente
2. **S3_ENABLED=true mas MinIO falha**: Detecta falha e usa armazenamento local
3. **Upload progressivo**: Fallback para upload simples se MinIO não disponível

### Estrutura de Armazenamento

**MinIO/S3:**
```
faro-assets/
└── observations/
    └── {observation_id}/
        └── {asset_type}/
            └── {uuid}_{filename}
```

**Local Storage:**
```
local_assets/
└── observations/
    └── {observation_id}/
        └── {asset_type}/
            └── {uuid}_{filename}
```

## Uso

### Upload Simples

```python
from app.services.storage_service import upload_observation_asset_bytes

uploaded = upload_observation_asset_bytes(
    observation_id="123e4567-e89b-12d3-a456-426614174000",
    asset_type="image",
    original_filename="plate.jpg",
    content_type="image/jpeg",
    payload=file_bytes,
)

# Retorna:
# UploadedAsset(
#     bucket="faro-assets" ou "local",
#     key="observations/123.../image/uuid_plate.jpg",
#     content_type="image/jpeg",
#     size_bytes=12345,
#     checksum_sha256="abc123..."
# )
```

### Upload Progressivo (requer MinIO)

```python
from app.services.storage_service import upload_observation_asset_progressive, complete_progressive_upload

# Inicializa upload
result = upload_observation_asset_progressive(
    observation_id="...",
    asset_type="video",
    original_filename="evidence.mp4",
    content_type="video/mp4",
    payload=chunk1,
)
upload_id = result["upload_id"]

# Upload chunks subsequentes
for i, chunk in enumerate(chunks[1:], 1):
    upload_observation_asset_progressive(
        observation_id="...",
        asset_type="video",
        original_filename="evidence.mp4",
        content_type="video/mp4",
        payload=chunk,
        upload_id=upload_id,
        chunk_index=i,
    )

# Completa upload
uploaded = complete_progressive_upload(
    upload_id=upload_id,
    key=result["key"],
    parts=parts_list,
)
```

## MinIO vs Local Storage

### MinIO (Recomendado para Produção)

**Vantagens:**
- Escalabilidade horizontal
- Interface web de gerenciamento (Console na porta 9001)
- Replicação e backup
- Compatível com AWS S3 (fácil migração)
- Políticas de retenção e ciclo de vida

**Desvantagens:**
- Requer serviço adicional
- Complexidade de setup
- Consumo de recursos

### Local Storage (Recomendado para Desenvolvimento)

**Vantagens:**
- Zero configuração
- Sem dependências externas
- Simples para debug
- Funciona offline

**Desvantagens:**
- Limitado ao disco local
- Sem interface web
- Sem replicação
- Backup manual necessário

## Setup MinIO (Opcional)

### Via Docker Compose

```bash
cd infra/docker
docker-compose up -d minio
```

Acesse o console: http://localhost:9001 (usuário: minioadmin, senha: minioadmin)

### Via Docker Manual

```bash
docker run -d \
  -p 9000:9000 \
  -p 9001:9001 \
  -e MINIO_ROOT_USER=minioadmin \
  -e MINIO_ROOT_PASSWORD=minioadmin \
  minio/minio server /data --console-address ":9001"
```

### Habilitar no FARO

Set variável de ambiente:
```bash
S3_ENABLED=true
```

Ou no `.env`:
```
S3_ENABLED=true
S3_ENDPOINT=http://localhost:9000
```

## Troubleshooting

### MinIO não conecta

**Sintoma:** Logs mostram "S3/MinIO not available, using local storage fallback"

**Solução:**
1. Verifique se MinIO está rodando: `docker ps | grep minio`
2. Verifique se porta 9000 está disponível: `netstat -ano | findstr ":9000"`
3. Verifique configuração de endpoint
4. Se não precisar de MinIO, deixe `S3_ENABLED=false` (default)

### Storage local cheio

**Sintoma:** Erro ao escrever arquivos em `local_assets/`

**Solução:**
1. Limpe arquivos antigos em `local_assets/`
2. Aumente `LOCAL_STORAGE_MAX_SIZE_MB`
3. Configure MinIO para armazenamento escalável

### Upload progressivo falha

**Sintoma:** Upload progressivo cai para upload simples

**Causa:** MinIO não está disponível

**Solução:**
1. Verifique disponibilidade do MinIO
2. Habilite MinIO se precisar de upload progressivo
3. Use upload simples se MinIO não for necessário

## Notas Importantes

- **MinIO é opcional**: O sistema funciona perfeitamente com apenas storage local
- **Fallback automático**: Se MinIO falhar, usa local storage sem interrupção
- **Portas reservadas**: 9000 (MinIO S3), 9001 (MinIO Console), 9002 (Analytics Dashboard)
- **Dados sensíveis**: Para operações de polícia, considere usar MinIO local ao invés de AWS S3
- **Backup**: Configure backup regular tanto de `local_assets/` quanto do bucket MinIO
