# Arquitetura Zero-Trust - Mobile Agent Field

> **Princípio fundamental:** O dispositivo móvel é considerado **INSEGURO** por padrão.
> Todos os dados operacionais devem ser tratados como temporários e voláteis.

---

## 1. Visão Geral

```
┌─────────────────────────────────────────────────────────────────────────┐
│                         DISPOSITIVO MÓVEL                               │
│                         (considerado inseguro)                          │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                          │
│  ┌──────────────┐    ┌──────────────┐    ┌──────────────┐               │
│  │   Camera     │───▶│  Criptografia│───▶│   Buffer     │               │
│  │   (OCR)      │    │  (AES-256)   │    │   Seguro     │               │
│  └──────────────┘    └──────────────┘    └──────────────┘               │
│                                 │                                       │
│                                 ▼                                       │
│  ┌─────────────────────────────────────────────────────────┐          │
│  │           ARMAZENAMENTO LOCAL TEMPORÁRIO                │          │
│  │  - Dados criptografados em repouso (EncryptedSharedPrefs) │          │
│  │  - Imagens: baixa resolução (800x600) mas auditável      │          │
│  │  - Chaves gerenciadas pelo Android Keystore              │          │
│  │  - TTL máximo: 7 dias (168 horas) - auto-destruição se não sincronizado               │          │
│  └─────────────────────────────────────────────────────────┘          │
│                                 │                                       │
│                                 ▼ (quando online)                       │
│  ┌─────────────────────────────────────────────────────────┐          │
│  │              SYNC SEGURO (HTTPS/TLS 1.3)                │          │
│  │  - Payload criptografado em trânsito                  │          │
│  │  - Confirmação de recebimento obrigatória             │          │
│  │  - Feedback do server processado                      │          │
│  └─────────────────────────────────────────────────────────┘          │
│                                 │                                       │
│                                 ▼                                       │
└─────────────────────────────────┼───────────────────────────────────────┘
                                  │
                    ┌─────────────┴─────────────┐
                    │       SUPABASE (Server)   │
                    │   - Persistência oficial  │
                    │   - Backup e auditoria    │
                    │   - Única fonte de verdade│
                    └───────────────────────────┘
                                  │
                    ┌─────────────┴─────────────┐
                    │   Confirmação de gravação   │
                    │   (server confirma sucesso) │
                    └─────────────────────────────┘
                                  │
┌─────────────────────────────────┼───────────────────────────────────────┐
│                         DISPOSITIVO MÓVEL                            │
│                    (pós-confirmação do server)                        │
├────────────────────────────────────────────────────────────────────────┤
│                                                                        │
│  ┌───────────────────────────────────────────────────────────┐        │
│  │             ELIMINAÇÃO SEGURA (Secure Wipe)              │        │
│  │  - Sobrescrita de dados (3x padrão DoD 5220.22-M)      │        │
│  │  - Deleção da chave de criptografia (irrecuperável)    │        │
│  │  - Limpeza de cache e bitmaps                          │        │
│  │  - Confirmação de deleção                              │        │
│  └───────────────────────────────────────────────────────────┘        │
│                                                                        │
└────────────────────────────────────────────────────────────────────────┘
```

---

## 2. Camada de Criptografia Local

### 2.1 Objetivo
Proteger dados em repouso contra acesso físico ao dispositivo.

### 2.2 Implementação

```kotlin
// Configuração do Keystore
val keyStore = KeyStore.getInstance("AndroidKeyStore")
keyStore.load(null)

// Geração de chave AES-256 vinculada ao hardware (se disponível)
val keyGenerator = KeyGenerator.getInstance("AES", "AndroidKeyStore")
val spec = KeyGenParameterSpec.Builder(
    "faro_observation_key",
    KeyProperties.PURPOSE_ENCRYPT or KeyProperties.PURPOSE_DECRYPT
)
    .setBlockModes(KeyProperties.BLOCK_MODE_GCM)
    .setEncryptionPaddings(KeyProperties.ENCRYPTION_PADDING_NONE)
    .setKeySize(256)
    .setUserAuthenticationRequired(false) // Para uso background
    .setRandomizedEncryptionRequired(true)
    .build()
keyGenerator.init(spec)
val key = keyGenerator.generateKey()
```

### 2.3 Dados Criptografados
- Metadados da observação (placa, localização, timestamp)
- Path das imagens (não o conteúdo - imagens são separadas)
- Dados de suspeita e abordagem
- Cache de feedback

### 2.4 Imagens - Tratamento Especial
As imagens são **compressão + criptografia separada**:

```kotlin
// Fluxo: Captura → Compressão → Criptografia → Armazenamento

// 1. Captura em resolução moderada
val imageCapture = ImageCapture.Builder()
    .setTargetResolution(Size(1280, 720)) // HD suficiente para OCR
    .setCaptureMode(ImageCapture.CAPTURE_MODE_MINIMIZE_LATENCY)
    .build()

// 2. Compressão para resolução auditável
fun compressForAudit(original: Bitmap): Bitmap {
    // Resolução suficiente para:
    // - OCR futuro (reprocessamento)
    // - Visualização humana
    // - Evidência em processo
    val targetWidth = 800
    val targetHeight = 600
    return Bitmap.createScaledBitmap(original, targetWidth, targetHeight, true)
}

// 3. Criptografia da imagem
fun encryptImage(bitmap: Bitmap, key: SecretKey): EncryptedImage {
    val stream = ByteArrayOutputStream()
    bitmap.compress(Bitmap.CompressFormat.JPEG, 85, stream) // Qualidade auditável
    val bytes = stream.toByteArray()
    
    val cipher = Cipher.getInstance("AES/GCM/NoPadding")
    cipher.init(Cipher.ENCRYPT_MODE, key)
    val iv = cipher.iv
    val encrypted = cipher.doFinal(bytes)
    
    return EncryptedImage(iv, encrypted)
}
```

---

## 3. Fluxo de Dados Seguro

### 3.1 Fase 1: Captura (Offline)

```
┌─────────────┐     ┌──────────────┐     ┌──────────────┐
│   OCR       │────▶│  Comprimir   │────▶│  Criptografar│
│   + Foto    │     │  (800x600)   │     │  (AES-256)   │
└─────────────┘     └──────────────┘     └──────────────┘
                                                 │
                                                 ▼
                                        ┌────────────────┐
                                        │ Salvar em cache│
                                        │ temporário     │
                                        │ (TTL 24h)      │
                                        └────────────────┘
```

### 3.2 Fase 2: Sync (Online)

```
┌────────────────┐     ┌──────────────┐     ┌──────────────┐
│ Ler do cache   │────▶│ Descriptograf│────▶│ Preparar     │
│ criptografado  │     │ (memória)    │     │ payload JSON │
└────────────────┘     └──────────────┘     └──────────────┘
                                                   │
                                                   ▼
                                          ┌────────────────┐
                                          │ HTTPS/TLS 1.3  │
                                          │ para Supabase  │
                                          └────────────────┘
                                                   │
                                                   ▼
                                          ┌────────────────┐
                                          │ Server confirma│
                                          │ gravação       │
                                          │ (200 OK + id)  │
                                          └────────────────┘
```

### 3.3 Fase 3: Eliminação Segura (Pós-confirmação)

```
┌────────────────┐     ┌──────────────┐     ┌──────────────┐
│ Server confirma│────▶│ Sobrescrever │────▶│ Deletar chave│
│ recebimento    │     │ dados (3x)   │     │ criptografia │
└────────────────┘     └──────────────┘     └──────────────┘
                                                 │
                                                 ▼
                                        ┌────────────────┐
                                        │ Liberar        │
                                        │ armazenamento  │
                                        │ físico         │
                                        └────────────────┘
```

---

## 4. Implementação - Componentes

### 4.1 SecureStorage (Wrapper EncryptedSharedPreferences)

```kotlin
class SecureObservationStorage(context: Context) {
    private val masterKey = MasterKey.Builder(context)
        .setKeyScheme(MasterKey.KeyScheme.AES256_GCM)
        .build()
    
    private val securePrefs = EncryptedSharedPreferences.create(
        context,
        "faro_secure_observations",
        masterKey,
        EncryptedSharedPreferences.PrefKeyEncryptionScheme.AES256_SIV,
        EncryptedSharedPreferences.PrefValueEncryptionScheme.AES256_GCM
    )
    
    // Salva observação pendente
    fun savePending(observation: SecureObservationPayload) {
        val json = gson.toJson(observation)
        securePrefs.edit()
            .putString(observation.id, json)
            .putLong("${observation.id}_ttl", System.currentTimeMillis() + TTL_24H)
            .apply()
    }
    
    // Recupera e remove (para sync)
    fun retrieveAndRemove(id: String): SecureObservationPayload? {
        val json = securePrefs.getString(id, null) ?: return null
        securePrefs.edit().remove(id).remove("${id}_ttl").apply()
        return gson.fromJson(json, SecureObservationPayload::class.java)
    }
    
    // Lista pendentes (não expirados)
    fun listPending(): List<SecureObservationPayload> {
        val now = System.currentTimeMillis()
        return securePrefs.all
            .filter { (key, _) -> !key.endsWith("_ttl") }
            .mapNotNull { (id, json) ->
                val ttl = securePrefs.getLong("${id}_ttl", 0)
                if (ttl > now) {
                    gson.fromJson(json as String, SecureObservationPayload::class.java)
                } else {
                    // Auto-expurgo
                    securePrefs.edit().remove(id).remove("${id}_ttl").apply()
                    null
                }
            }
    }
    
    // Eliminação segura
    fun secureDelete(id: String) {
        val json = securePrefs.getString(id, "") ?: ""
        // Sobrescrever 3x
        repeat(3) {
            securePrefs.edit().putString(id, randomGarbage(json.length)).apply()
        }
        // Remover
        securePrefs.edit().remove(id).remove("${id}_ttl").apply()
    }
    
    companion object {
        const val TTL_24H = 24 * 60 * 60 * 1000L
    }
}
```

### 4.2 SecureImageStorage

```kotlin
class SecureImageStorage(context: Context) {
    private val keyStore = CryptoUtils.getOrCreateKey("faro_image_key")
    private val storageDir = context.getDir("secure_images", Context.MODE_PRIVATE)
    
    // Salva imagem criptografada
    fun saveEncryptedImage(bitmap: Bitmap, id: String): File {
        // 1. Comprimir
        val compressed = compressForAudit(bitmap)
        
        // 2. Converter para bytes
        val stream = ByteArrayOutputStream()
        compressed.compress(Bitmap.CompressFormat.JPEG, 85, stream)
        val bytes = stream.toByteArray()
        
        // 3. Criptografar
        val encrypted = CryptoUtils.encrypt(bytes, keyStore)
        
        // 4. Salvar em arquivo
        val file = File(storageDir, "$id.enc")
        file.writeBytes(encrypted.iv + encrypted.ciphertext)
        
        return file
    }
    
    // Recupera para upload
    fun retrieveForUpload(id: String): ByteArray? {
        val file = File(storageDir, "$id.enc")
        if (!file.exists()) return null
        
        val bytes = file.readBytes()
        val iv = bytes.sliceArray(0 until 12)
        val ciphertext = bytes.sliceArray(12 until bytes.size)
        
        return CryptoUtils.decrypt(EncryptedData(iv, ciphertext), keyStore)
    }
    
    // Eliminação segura
    fun secureDelete(id: String) {
        val file = File(storageDir, "$id.enc")
        if (file.exists()) {
            // Sobrescrever com lixo
            val size = file.length()
            repeat(3) {
                file.writeBytes(Random.nextBytes(size.toInt()))
            }
            file.delete()
        }
    }
    
    // Comprimir para resolução auditável
    private fun compressForAudit(bitmap: Bitmap): Bitmap {
        // Dimensões máximas para auditoria
        val maxWidth = 800
        val maxHeight = 600
        
        val ratio = minOf(
            maxWidth.toFloat() / bitmap.width,
            maxHeight.toFloat() / bitmap.height
        )
        
        return if (ratio < 1) {
            val newWidth = (bitmap.width * ratio).toInt()
            val newHeight = (bitmap.height * ratio).toInt()
            Bitmap.createScaledBitmap(bitmap, newWidth, newHeight, true)
        } else {
            bitmap
        }
    }
}
```

### 4.3 SecureSyncWorker

```kotlin
@HiltWorker
class SecureSyncWorker @AssistedInject constructor(
    @Assisted context: Context,
    @Assisted workerParams: WorkerParameters,
    private val observationStorage: SecureObservationStorage,
    private val imageStorage: SecureImageStorage,
    private val faroMobileApi: FaroMobileApi,
    private val sessionRepository: SessionRepository,
) : CoroutineWorker(context, workerParams) {

    override suspend fun doWork(): Result {
        return try {
            sessionRepository.refreshTokenIfNeeded()
            
            // 1. Listar pendentes
            val pending = observationStorage.listPending()
            if (pending.isEmpty()) return Result.success()
            
            // 2. Preparar batch
            val items = pending.map { it.toSyncItem() }
            
            // 3. Enviar
            val response = faroMobileApi.syncBatch(SyncBatchRequestDto(
                deviceId = sessionRepository.deviceId,
                appVersion = BuildConfig.VERSION_NAME,
                items = items,
                clientTimestamp = Instant.now().toString()
            ))
            
            // 4. Processar resultados
            response.results.forEach { result ->
                if (result.status == "completed" && result.entityServerId != null) {
                    // Upload de assets se houver
                    uploadAssetsSecure(result.entityLocalId, result.entityServerId)
                    
                    // ELIMINAÇÃO SEGURA (ponto crítico)
                    secureDeleteObservation(result.entityLocalId)
                }
            }
            
            Result.success()
        } catch (e: Exception) {
            Timber.e(e, "Secure sync failed")
            Result.retry()
        }
    }
    
    private suspend fun uploadAssetsSecure(localId: String, serverId: String) {
        // Recuperar imagem descriptografada em memória
        val imageBytes = imageStorage.retrieveForUpload(localId) ?: return
        
        // Upload
        val requestBody = imageBytes.toRequestBody("image/jpeg".toMediaTypeOrNull())
        val part = MultipartBody.Part.createFormData(
            "file", 
            "$localId.jpg", 
            requestBody
        )
        
        faroMobileApi.uploadObservationAsset(
            observationId = serverId,
            assetType = "image".toRequestBody(),
            file = part
        )
        
        // Limpar memória
        imageBytes.fill(0)
    }
    
    private fun secureDeleteObservation(id: String) {
        // Eliminação segura da imagem
        imageStorage.secureDelete(id)
        // Eliminação segura dos metadados
        observationStorage.secureDelete(id)
        
        Timber.d("Securely deleted observation $id")
    }
}
```

---

## 5. Resolução de Imagens

### 5.1 Requisitos de Auditoria

| Aspecto | Especificação |
|---------|---------------|
| Resolução mínima | 800x600 (0.5 MP) |
| Resolução máxima | 1280x720 (1 MP) |
| Formato | JPEG |
| Qualidade | 85% |
| OCR reprocessável | Sim (Tesseract/ML Kit consegue ler) |
| Evidência legal | Suficiente para identificação visual |

### 5.2 Por que não maior?

- **Segurança:** Menor volume de dados = menor exposição
- **Performance:** Upload rápido mesmo em 3G
- **Armazenamento:** Múltiplas observações no cache
- **Custo:** Menos banda e storage no servidor

### 5.3 Por que não menor?

- **Auditoria:** Deve permitir re-OCR se necessário
- **Legal:** Deve permitir identificação humana
- **Qualidade:** Não pode comprometer a operação

---

## 6. Checklist de Implementação

- [ ] Implementar `SecureObservationStorage` (EncryptedSharedPrefs)
- [ ] Implementar `SecureImageStorage` (compressão + criptografia)
- [ ] Implementar `CryptoUtils` (wrapper Android Keystore)
- [ ] Atualizar `SyncWorker` para eliminação segura pós-confirmação
- [ ] Implementar TTL automático (24h) com auto-destruição
- [ ] Adicionar testes de criptografia/decriptografia
- [ ] Verificar integração com Android Keystore em devices target
- [ ] Documentar recovery process (se Keystore falhar)

---

## 7. Cenários de Falha

### 7.1 Keystore Corrompido
```kotlin
// Fallback: Limpar tudo e notificar usuário
fun onKeystoreFailure() {
    secureWipeAll()
    notifyUser("Segurança comprometida. Dados locais eliminados. Faça login novamente.")
}
```

### 7.2 Sync Falha por >7 dias
```kotlin
// TTL expira - auto-destruição
if (System.currentTimeMillis() > ttl) {
    secureDelete(id)
    Timber.w("Observation $id expired and securely deleted")
}
```

### 7.3 Dispositivo Perdido/Roubado
- Dados criptografados com chave no Keystore (hardware-bound se disponível)
- Chave não exportável
- TTL garante eliminação automática

---

**Documento:** mobile-zero-trust.md  
**Versão:** 1.0  
**Data:** Abril 2026  
**Autor:** SSI/BMRS - Sistema F.A.R.O.
