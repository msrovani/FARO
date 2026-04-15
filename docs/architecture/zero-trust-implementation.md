# Implementação Zero-Trust - Documentação Completa

> **F.A.R.O. - Sistema de Inteligência Operacional**
> 
> Arquitetura de segurança para sincronização mobile-server com proteção total de dados sensíveis.

---

## 1. Visão Geral da Arquitetura

### 1.1 Princípios Fundamentais

```
┌─────────────────────────────────────────────────────────────────────────┐
│                    ARQUITETURA ZERO-TRUST                              │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                          │
│  1. DISPOSITIVO MÓVEL = INSEGURO                                        │
│     - Nunca confiar no armazenamento local                              │
│     - Todos os dados são temporários e voláteis                        │
│                                                                          │
│  2. SERVER = ÚNICA FONTE DE VERDADE                                     │
│     - Supabase/PostgreSQL: persistência oficial                          │
│     - MinIO/S3: storage de assets (imagens/áudio)                       │
│                                                                          │
│  3. CRIPTOGRAFIA EM TODAS AS CAMADAS                                    │
│     - Repouso: AES-256-GCM (Android Keystore)                           │
│     - Trânsito: TLS 1.3 (HTTPS)                                         │
│     - Memória: dados descriptografados apenas durante processamento     │
│                                                                          │
│  4. ELIMINAÇÃO SEGURA APÓS CONFIRMAÇÃO                                  │
│     - DoD 5220.22-M: 3-pass overwrite                                    │
│     - Deleção da chave = irrecuperável                                  │
│                                                                          │
│  5. AUTO-DESTRUIÇÃO (TTL)                                               │
│     - 7 dias máximo sem sync                                            │
│     - Eliminação automática de dados não sincronizados                  │
│                                                                          │
└─────────────────────────────────────────────────────────────────────────┘
```

---

## 2. Componentes Implementados

### 2.1 Mobile (Android/Kotlin)

| Componente | Arquivo | Função |
|------------|---------|--------|
| **CryptoUtils** | `data/security/CryptoUtils.kt` | AES-256 via Android Keystore |
| **SecureObservationStorage** | `data/security/SecureObservationStorage.kt` | Persistência criptografada de metadados |
| **SecureImageStorage** | `data/security/SecureImageStorage.kt` | Compressão + criptografia de imagens |
| **SecureSyncWorker** | `data/worker/SecureSyncWorker.kt` | Sync com eliminação segura pós-confirmação |

### 2.2 Server (Python/FastAPI)

| Componente | Arquivo | Função |
|------------|---------|--------|
| **Sync Batch Endpoint** | `api/v1/endpoints/mobile.py:678` | Recebe observações do mobile |
| **Asset Upload Endpoint** | `api/v1/endpoints/mobile.py:854` | Recebe imagens/áudio |
| **Storage Service** | `services/storage_service.py` | Persistência em MinIO/S3 |
| **Sync Schemas** | `schemas/sync.py` | Contratos de API |

### 2.3 Infraestrutura

| Componente | Tecnologia | Função |
|------------|------------|--------|
| **Banco de Dados** | PostgreSQL + PostGIS | Persistência de observações |
| **Storage de Objetos** | MinIO (S3-compatible) | Armazenamento de imagens/áudio |
| **Cache/Fila** | Redis | Sync queue, rate limiting |
| **Orquestração** | Docker Compose | Deploy local/cloud |

---

## 3. Fluxo de Dados Detalhado

### 3.1 Fase 1: Captura no Dispositivo (Offline)

```
┌─────────────────────────────────────────────────────────────────────────┐
│                         CAPTURA DE PLACA                                │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                          │
│  1. OCR (ML Kit)                                                        │
│     └─▶ Captura da imagem da placa                                      │
│                                                                          │
│  2. COMPRESSÃO                                                          │
│     └─▶ Redimensiona para 800x600 máximo                               │
│     └─▶ JPEG qualidade 85%                                              │
│     └─▶ ~50-100KB por imagem (vs 2-5MB original)                       │
│                                                                          │
│  3. CRIPTOGRAFIA                                                        │
│     └─▶ AES-256-GCM com IV único                                       │
│     └─▶ Chave do Android Keystore (hardware-bound)                      │
│                                                                          │
│  4. ARMAZENAMENTO LOCAL TEMPORÁRIO                                      │
│     └─▶ Metadados: EncryptedSharedPreferences                           │
│     └─▶ Imagem: Arquivo criptografado (.enc)                           │
│     └─▶ TTL: 7 dias (604.800 segundos)                                  │
│                                                                          │
└─────────────────────────────────────────────────────────────────────────┘
```

**Código - Compressão e Criptografia:**

```kotlin
// SecureImageStorage.kt
fun saveImage(bitmap: Bitmap, id: String): File {
    // 1. Compressão para resolução auditável
    val compressed = compressToAuditSize(bitmap) // 800x600 max
    
    // 2. JPEG encoding
    val stream = ByteArrayOutputStream()
    compressed.compress(Bitmap.CompressFormat.JPEG, 85, stream)
    val jpegBytes = stream.toByteArray()
    
    // 3. Criptografia AES-256-GCM
    val encrypted = CryptoUtils.encrypt(jpegBytes, key)
    
    // 4. Salvar em arquivo (IV + ciphertext)
    val file = File(storageDir, "$id.enc")
    file.writeBytes(encrypted.toCombinedByteArray())
    
    // Limpar memória
    CryptoUtils.secureClear(jpegBytes)
    
    return file
}
```

### 3.2 Fase 2: Sincronização (Online)

```
┌─────────────────────────────────────────────────────────────────────────┐
│                         SYNC BATCH                                      │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                          │
│  1. TRIGGER DE SYNC                                                      │
│     └─▶ WorkManager: periodic (15 min) + one-shot (imediatão após captura)│
│                                                                          │
│  2. LEITURA SEGURA                                                      │
│     └─▶ Lista observações pendentes do SecureStorage                    │
│     └─▶ Auto-expurgo de itens expirados (>7 dias)                       │
│                                                                          │
│  3. PREPARAÇÃO DO PAYLOAD                                               │
│     └─▶ Descriptografa em memória (apenas para transmissão)             │
│     └─▶ Gera hash SHA-256 para integridade                             │
│     └─▶ Monta SyncBatchRequest                                          │
│                                                                          │
│  4. TRANSMISSÃO                                                        │
│     └─▶ HTTPS/TLS 1.3                                                  │
│     └─▶ Endpoint: POST /mobile/sync/batch                               │
│     └─▶ Autenticação: Bearer token JWT                                  │
│                                                                          │
│  5. PROCESSAMENTO SERVER                                                │
│     └─▶ Valida payload                                                  │
│     └─▶ Persiste em PostgreSQL                                          │
│     └─▶ Retorna entity_server_id (UUID)                                │
│                                                                          │
│  6. UPLOAD DE ASSETS (se houver)                                       │
│     └─▶ Para cada imagem: descriptografa → upload → limpa memória       │
│     └─▶ Endpoint: POST /mobile/observations/{id}/assets                 │
│     └─▶ Storage: MinIO/S3                                               │
│                                                                          │
│  7. CONFIRMAÇÃO E ELIMINAÇÃO                                            │
│     └─▶ Server retorna 200 OK + server_id                              │
│     └─▶ Mobile executa secureDelete():                                  │
│         - 3-pass overwrite (DoD 5220.22-M)                             │
│         - Deleção da chave de criptografia                              │
│         - Liberação do armazenamento físico                               │
│                                                                          │
└─────────────────────────────────────────────────────────────────────────┘
```

**Código - Sync e Eliminação:**

```kotlin
// SecureSyncWorker.kt
override suspend fun doWork(): Result {
    // 1. Lista pendentes
    val pending = observationStorage.listPending()
    
    // 2. Envia para server
    val response = faroMobileApi.syncBatch(request)
    
    // 3. Processa resultados
    response.results.forEach { result ->
        if (result.status == "completed") {
            // Upload de imagens
            uploadImagesIfAny(result.entityLocalId, result.entityServerId!!)
            
            // CRITICAL: Eliminação segura após confirmação
            secureDeleteObservation(result.entityLocalId)
        }
    }
}

private fun secureDeleteObservation(localId: String) {
    // Eliminação DoD 5220.22-M
    imageStorage.secureDelete(localId)      // 3-pass overwrite
    observationStorage.secureDelete(localId) // Remove metadados
    System.gc()                              // Hint para GC
}
```

### 3.3 Fase 3: Persistência Server

```
┌─────────────────────────────────────────────────────────────────────────┐
│                    PERSISTÊNCIA SERVER                                  │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                          │
│  BANCO DE DADOS (PostgreSQL + PostGIS)                                  │
│  ├── Table: vehicle_observations                                        │
│  │   ├── id (UUID, PK)                                                  │
│  │   ├── client_id (string, unique)                                     │
│  │   ├── plate_number (string)                                         │
│  │   ├── location (geometry/POINT)                                     │
│  │   ├── observed_at_local (timestamp)                                  │
│  │   ├── observed_at_server (timestamp)                                  │
│  │   ├── agent_id (UUID, FK)                                           │
│  │   ├── agency_id (UUID, FK)                                           │
│  │   ├── device_id (UUID, FK)                                           │
│  │   ├── sync_status (enum)                                             │
│  │   └── metadata_snapshot (JSONB)                                       │
│  │                                                                        │
│  ├── Table: plate_reads                                                 │
│  │   ├── id (UUID, PK)                                                   │
│  │   ├── observation_id (UUID, FK)                                       │
│  │   ├── ocr_raw_text (string)                                           │
│  │   ├── ocr_confidence (float)                                           │
│  │   └── ocr_engine (string)                                              │
│  │                                                                        │
│  └── Table: assets                                                        │
│      ├── id (UUID, PK)                                                     │
│      ├── asset_type (enum: image, audio)                                   │
│      ├── storage_bucket (string)                                           │
│      ├── storage_key (string)                                              │
│      ├── checksum_sha256 (string)                                          │
│      └── uploaded_by (UUID, FK)                                            │
│                                                                            │
│  STORAGE DE OBJETOS (MinIO/S3)                                            │
│  └── Bucket: faro-assets                                                   │
│      └── Key: observations/{observation_id}/{asset_type}/{uuid}_{filename}  │
│                                                                            │
└─────────────────────────────────────────────────────────────────────────┘
```

---

## 4. APIs e Contratos

### 4.1 Mobile → Server: Sync Batch

**Endpoint:** `POST /mobile/sync/batch`

**Request:**
```json
{
  "device_id": "device_abc123",
  "app_version": "1.2.0",
  "client_timestamp": "2026-04-14T10:30:00Z",
  "items": [
    {
      "entity_type": "observation",
      "entity_local_id": "obs_123_local",
      "operation": "create",
      "payload_hash": "a1b2c3d4...",
      "created_at_local": "2026-04-14T10:25:00Z",
      "payload": {
        "client_id": "client_xyz789",
        "plate_number": "ABC1234",
        "plate_state": "MS",
        "observed_at_local": "2026-04-14T10:25:00Z",
        "location": {
          "latitude": -20.4697,
          "longitude": -54.6201,
          "accuracy": 8.5
        },
        "device_id": "device_abc123",
        "connectivity_type": "wifi",
        "plate_read": {
          "ocr_raw_text": "ABC1234",
          "ocr_confidence": 0.94,
          "ocr_engine": "mlkit_v2"
        }
      }
    }
  ]
}
```

**Response:**
```json
{
  "processed_count": 1,
  "success_count": 1,
  "failed_count": 0,
  "server_timestamp": "2026-04-14T10:30:05Z",
  "results": [
    {
      "entity_local_id": "obs_123_local",
      "entity_server_id": "550e8400-e29b-41d4-a716-446655440000",
      "status": "completed",
      "synced_at": "2026-04-14T10:30:05Z"
    }
  ],
  "pending_feedback": []
}
```

### 4.2 Mobile → Server: Asset Upload

**Endpoint:** `POST /mobile/observations/{observation_id}/assets`

**Request:**
```http
POST /mobile/observations/550e8400-e29b-41d4-a716-446655440000/assets
Content-Type: multipart/form-data
Authorization: Bearer {jwt_token}

asset_type: image
file: [binary JPEG data]
```

**Response:**
```json
{
  "asset_id": "660e8400-e29b-41d4-a716-446655440001",
  "observation_id": "550e8400-e29b-41d4-a716-446655440000",
  "asset_type": "image",
  "storage_bucket": "faro-assets",
  "storage_key": "observations/550e8400-e29b-41d4-a716-446655440000/image/uuid_plate.jpg",
  "content_type": "image/jpeg",
  "size_bytes": 87542,
  "checksum_sha256": "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855"
}
```

---

## 5. Segurança e Criptografia

### 5.1 Android Keystore

```kotlin
// CryptoUtils.kt
fun getOrCreateKey(alias: String): SecretKey {
    val keyStore = KeyStore.getInstance("AndroidKeyStore").apply { load(null) }
    
    // Verifica se chave existe
    keyStore.getEntry(alias, null)?.let { entry ->
        if (entry is KeyStore.SecretKeyEntry) return entry.secretKey
    }
    
    // Gera nova chave AES-256
    val keyGenerator = KeyGenerator.getInstance("AES", "AndroidKeyStore")
    val spec = KeyGenParameterSpec.Builder(
        alias,
        KeyProperties.PURPOSE_ENCRYPT or KeyProperties.PURPOSE_DECRYPT
    )
        .setBlockModes(KeyProperties.BLOCK_MODE_GCM)
        .setEncryptionPaddings(KeyProperties.ENCRYPTION_PADDING_NONE)
        .setKeySize(256)
        .setIsStrongBoxBacked(true) // Hardware-backed se disponível
        .build()
    
    keyGenerator.init(spec)
    return keyGenerator.generateKey()
}
```

### 5.2 Criptografia AES-256-GCM

```kotlin
// Criptografiaun encrypt(plaintext: ByteArray, key: SecretKey): EncryptedData {
    val cipher = Cipher.getInstance("AES/GCM/NoPadding")
    cipher.init(Cipher.ENCRYPT_MODE, key)
    
    val iv = cipher.iv                    // 12 bytes
    val ciphertext = cipher.doFinal(plaintext)
    
    return EncryptedData(iv, ciphertext)  // IV + ciphertext
}

// Descriptografia
fun decrypt(encryptedData: EncryptedData, key: SecretKey): ByteArray {
    val cipher = Cipher.getInstance("AES/GCM/NoPadding")
    val spec = GCMParameterSpec(128, encryptedData.iv)
    cipher.init(Cipher.DECRYPT_MODE, key, spec)
    
    return cipher.doFinal(encryptedData.ciphertext)
}
```

### 5.3 Eliminação Segura (DoD 5220.22-M)

```kotlin
// SecureObservationStorage.kt
fun secureDelete(localId: String) {
    val json = securePrefs.getString(localId, "") ?: ""
    
    if (json.isNotEmpty()) {
        // 3-pass overwrite com dados aleatórios
        repeat(3) { pass ->
            val garbage = generateRandomString(json.length)
            securePrefs.edit().putString(localId, garbage).commit()
        }
    }
    
    // Deleção final
    securePrefs.edit()
        .remove(localId)
        .remove("${localId}_ttl")
        .commit()
}
```

---

## 6. Configuração e Deploy

### 6.1 Variáveis de Ambiente (Server)

```bash
# Database
DATABASE_URL=postgresql+asyncpg://user:pass@localhost:5432/faro

# Redis
REDIS_URL=redis://localhost:6379/0

# MinIO/S3 Storage
S3_ENDPOINT=http://localhost:9000
S3_ACCESS_KEY=minioadmin
S3_SECRET_KEY=minioadmin
S3_BUCKET_NAME=faro-assets
S3_REGION=us-east-1
S3_SECURE=false

# JWT
SECRET_KEY=your-secret-key-here
ACCESS_TOKEN_EXPIRE_MINUTES=60
```

### 6.2 Docker Compose (Infraestrutura)

```yaml
# infra/docker/docker-compose.yml
version: '3.8'

services:
  postgres:
    image: postgis/postgis:15-3.4
    environment:
      POSTGRES_USER: faro
      POSTGRES_PASSWORD: faro
      POSTGRES_DB: faro
    volumes:
      - postgres_data:/var/lib/postgresql/data
    ports:
      - "5432:5432"

  redis:
    image: redis:7-alpine
    ports:
      - "6379:6379"

  minio:
    image: minio/minio:latest
    command: server /data --console-address ":9001"
    environment:
      MINIO_ROOT_USER: minioadmin
      MINIO_ROOT_PASSWORD: minioadmin
    volumes:
      - minio_data:/data
    ports:
      - "9000:9000"
      - "9001:9001"

  backend:
    build: ../../server-core
    environment:
      DATABASE_URL: postgresql+asyncpg://faro:faro@postgres:5432/faro
      REDIS_URL: redis://redis:6379/0
      S3_ENDPOINT: http://minio:9000
      S3_ACCESS_KEY: minioadmin
      S3_SECRET_KEY: minioadmin
    depends_on:
      - postgres
      - redis
      - minio
    ports:
      - "8000:8000"

volumes:
  postgres_data:
  minio_data:
```

### 6.3 Dependências Android

```gradle
// app/build.gradle
dependencies {
    // Security
    implementation "androidx.security:security-crypto:1.1.0-alpha06"
    
    // WorkManager (background sync)
    implementation "androidx.work:work-runtime-ktx:2.9.0"
    
    // Networking
    implementation "com.squareup.retrofit2:retrofit:2.9.0"
    implementation "com.squareup.retrofit2:converter-gson:2.9.0"
    implementation "com.squareup.okhttp3:logging-interceptor:4.12.0"
    
    // Camera/OCR
    implementation "androidx.camera:camera-core:1.3.0"
    implementation "androidx.camera:camera-camera2:1.3.0"
    implementation "androidx.camera:camera-lifecycle:1.3.0"
    implementation "com.google.mlkit:text-recognition:16.0.0"
    
    // DI
    implementation "com.google.dagger:hilt-android:2.50"
    kapt "com.google.dagger:hilt-compiler:2.50"
    implementation "androidx.hilt:hilt-work:1.1.0"
}
```

---

## 7. Testes e Validação

### 7.1 Testes Unitários (Server)

```python
# tests/test_sync.py
import pytest
from httpx import AsyncClient

@pytest.mark.asyncio
async def test_sync_batch_success(client: AsyncClient, auth_headers):
    payload = {
        "device_id": "test_device",
        "app_version": "1.0.0",
        "items": [{
            "entity_type": "observation",
            "entity_local_id": "obs_test_001",
            "operation": "create",
            "payload_hash": "abc123",
            "created_at_local": "2026-04-14T10:00:00Z",
            "payload": {
                "client_id": "client_test_001",
                "plate_number": "TEST1234",
                "observed_at_local": "2026-04-14T10:00:00Z",
                "location": {"latitude": -20.0, "longitude": -54.0, "accuracy": 10.0},
                "device_id": "test_device"
            }
        }]
    }
    
    response = await client.post(
        "/api/v1/mobile/sync/batch",
        json=payload,
        headers=auth_headers
    )
    
    assert response.status_code == 200
    data = response.json()
    assert data["success_count"] == 1
    assert data["results"][0]["status"] == "completed"
    assert data["results"][0]["entity_server_id"] is not None
```

### 7.2 Testes de Integração (Mobile)

```kotlin
// test/SecureStorageTest.kt
@RunWith(AndroidJUnit4::class)
class SecureStorageTest {
    
    @Test
    fun testEncryptDecrypt() {
        val key = CryptoUtils.getOrCreateKey("test_key")
        val plaintext = "test data".toByteArray()
        
        // Encrypt
        val encrypted = CryptoUtils.encrypt(plaintext, key)
        
        // Decrypt
        val decrypted = CryptoUtils.decrypt(encrypted, key)
        
        assertArrayEquals(plaintext, decrypted)
    }
    
    @Test
    fun testSecureDelete() {
        val context = ApplicationProvider.getApplicationContext<Context>()
        val storage = SecureObservationStorage(context)
        
        // Save
        val observation = createTestObservation()
        storage.savePending(observation)
        
        // Verify exists
        assertNotNull(storage.retrieve(observation.localId))
        
        // Secure delete
        storage.secureDelete(observation.localId)
        
        // Verify deleted
        assertNull(storage.retrieve(observation.localId))
    }
}
```

---

## 8. Troubleshooting

### 8.1 Problemas Comuns

| Sintoma | Causa | Solução |
|---------|-------|---------|
| Sync falha com 401 | Token expirado | Verificar refresh token no WorkManager |
| Sync falha com 413 | Payload muito grande | Reduzir batch size (max 10 observações) |
| Imagem não aparece | Upload falhou | Verificar tamanho (max 5MB) e formato |
| Dados não deletados | Confirmação não recebida | Verificar response do server |
| Keystore erro | Chave corrompida | Fallback: secureWipeAll() + re-login |

### 8.2 Logs Importantes

```kotlin
// Mobile - Timber logs
Timber.d("Saved observation $id (TTL: $ttl)")
Timber.d("Syncing ${pending.size} observations")
Timber.d("Uploaded asset for $serverId -> $bucket/$key")
Timber.d("Securely deleted observation $id")
Timber.w("Observation $id expired, deleting")

// Server - Python logs
logger.info(f"Sync batch received: {len(payload.items)} items")
logger.info(f"Observation created: {synced.id}")
logger.info(f"Asset uploaded: {uploaded.key}")
```

---

## 9. Roadmap e Melhorias Futuras

### 9.1 Implementações Futuras

- [ ] **Compressão de áudio** (Opus codec) para reduzir tamanho
- [ ] **Delta sync** - sincronizar apenas mudanças
- [ ] **Multi-device sync** - resolver conflitos entre devices
- [ ] **Backup criptografado** - backup opcional na nuvem
- [ ] **Biometria** - proteção com fingerprint/face

### 9.2 Integrações Oficiais (aguardando credenciais)

- [ ] **DETRAN-RS** - consulta de placa oficial
- [ ] **GOV.BR** - autenticação SSO
- [ ] **BMRS HR** - validação de policial

---

## 10. Referências

- [NIST SP 800-57](https://csrc.nist.gov/publications/detail/sp/800-57-part-1/rev-5/final) - Key Management
- [DoD 5220.22-M](https://www.esd.whs.mil/Portals/54/Documents/DD/issuances/dodm/522022m.pdf) - Data Sanitization
- [Android Security Best Practices](https://developer.android.com/topic/security/best-practices)
- [OWASP Mobile Security](https://owasp.org/www-project-mobile-security/)

---

**Documento:** zero-trust-implementation.md  
**Versão:** 1.0  
**Data:** Abril 2026  
**Responsável:** SSI/BMRS - Sistema F.A.R.O.
