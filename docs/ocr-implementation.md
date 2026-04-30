# Implementação OCR - FARO (Offline-First + Mobile-First)

## Visão Geral

Implementação de OCR (Optical Character Recognition) para reconhecimento de placas veiculares brasileiras, seguindo princípios offline-first e mobile-first do FARO.

**Stack Técnico:**
- **Backend:** YOLOv11 + EasyOCR (Python)
- **Mobile:** TensorFlow Lite / ONNX Runtime (Android)
- **Fallback:** ML Kit (implementação atual)

**Princípios:**
- OCR assistido (humano confirma)
- Inteligência humana no loop
- Processamento local (offline-first)
- Fallbacks em múltiplos níveis

## Arquitetura

### Camada 1: OCR Local (Mobile)

**Primário:** YOLOv11 + EasyOCR via TFLite/ONNX
- Modelo específico para placas brasileiras (antigas + Mercosul)
- Execução 100% local (sem dependência de rede)
- Confiança real do modelo

**Fallback 1:** ML Kit (atual)
- OCR genérico mas funciona offline
- Aciona se TFLite/ONNX falhar

**Fallback 2:** Entrada manual
- Agente digita placa se ambos OCRs falharem
- Campo editável sempre disponível

### Camada 2: Validação Local

- Regex para placas antigas: `[A-Z]{3}[0-9]{4}`
- Regex para placas Mercosur: `[A-Z]{3}[0-9][A-Z0-9][0-9]{2}`
- Histórico local de placas observadas
- Watchlist local (sincronizada periodicamente)

### Camada 3: Sincronização Offline

- `PlateReadEntity` mantém OCR raw + confiança
- Imagem comprimida (800x600, 85%) armazenada localmente
- Criptografada (AES-256 + Android Keystore)
- Sync quando online com reprocessamento opcional no backend

### Camada 4: Validação Backend (Opcional)

Endpoint `/api/v1/mobile/ocr/validate` para:
- Reprocessar imagens quando online
- Validar OCR mobile com modelo mais robusto
- Comparar mobile vs backend
- Feedback se correção necessária

## Implementação Backend

### Dependências (requirements.txt)

```python
# OCR / Computer Vision
torch==2.5.0
torchvision==0.20.0
ultralytics==8.3.0
easyocr==1.7.1
Pillow==11.0.0
opencv-python-headless==4.10.0.84
```

### Serviço OCR (`app/services/ocr_service.py`)

**Classe `OcrService`:**
- `process_image()`: Processa imagem de arquivo
- `process_image_bytes()`: Processa imagem de bytes
- `validate_plate_number()`: Valida formato placa
- Lazy loading de modelos (YOLO + EasyOCR)

**Singleton:**
- `get_ocr_service()`: Instância única para injeção de dependência

### Endpoint OCR (`app/api/v1/endpoints/mobile.py`)

**POST `/api/v1/mobile/ocr/validate`**

Request:
```json
{
  "image_base64": "base64_encoded_image",
  "mobile_ocr_text": "ABC1234",
  "mobile_ocr_confidence": 0.85,
  "confidence_threshold": 0.5
}
```

Response:
```json
{
  "plate_number": "ABC1234",
  "confidence": 0.92,
  "plate_format": "old",
  "processing_time_ms": 150.5,
  "ocr_engine": "yolov11_easyocr",
  "is_valid_format": true,
  "improved_over_mobile": true,
  "mobile_comparison": {
    "mobile_text": "ABC1234",
    "mobile_confidence": 0.85,
    "backend_text": "ABC1234",
    "backend_confidence": 0.92,
    "match": true
  }
}
```

## Conversão de Modelos para Mobile

### Script TFLite (`scripts/convert_models_tflite.py`)

Converte YOLO para TensorFlow Lite:

```bash
python scripts/convert_models_tflite.py \
  --output-dir ./models/tflite \
  --yolo-model yolov11n.pt \
  --input-size 640
```

**Nota:** EasyOCR não suporta exportação direta para TFLite. Recomenda-se ONNX Runtime.

### Script ONNX (`scripts/convert_models_onnx.py`)

Converte YOLO para ONNX Runtime:

```bash
python scripts/convert_models_onnx.py \
  --output-dir ./models/onnx \
  --yolo-model yolov11n.pt \
  --input-size 640
```

**Alternativas para OCR caracteres:**
- ONNX Runtime + PaddleOCR (recomendado)
- TFLite Text Recognition API (Google)

## Integração Mobile (Android)

### Estrutura de Arquivos

```
mobile-agent-field/app/src/main/assets/
├── yolov11_plate.tflite  (ou .onnx)
└── easyocr.tflite        (ou .onnx)
```

### Integração no CameraPreview.kt

**Atualizar `processImageForOCR()`:**

```kotlin
private fun processImageForOCR(
    imageProxy: ImageProxy,
    onTextRecognized: (String, Float) -> Unit
) {
    // 1. Detectar placa com YOLO TFLite
    val plateRegion = yoloDetector.detect(imageProxy)
    
    // 2. Crop placa
    val plateImage = cropImage(imageProxy, plateRegion)
    
    // 3. OCR com EasyOCR TFLite
    val (text, confidence) = textRecognizer.recognize(plateImage)
    
    // 4. Callback com confiança real
    onTextRecognized(text, confidence)
}
```

**Fallback para ML Kit:**
- Se TFLite/ONNX falhar → usar ML Kit atual
- Se ML Kit falhar → entrada manual

## Fluxo Operacional

### Cenário 1: Offline (padrão FARO)

1. Camera captura frame
2. YOLO TFLite detecta placa
3. EasyOCR TFLite lê caracteres
4. Validação formato local
5. Sugestão exibida com confiança
6. Agente aceita ou corrige
7. Armazenado local (criptografado)
8. Sync pendente até conexão

### Cenário 2: Online

1-6. Mesmo fluxo offline
7. Sync imediato para backend
8. Backend revalida OCR opcionalmente
9. Feedback instantâneo se disponível

### Cenário 3: Fallback OCR

1. YOLO TFLite falha → ML Kit
2. ML Kit falha → entrada manual
3. Operação nunca bloqueada

## Formatos de Placa Brasileira

### Placa Antiga (LLL-NNNN)
- Padrão: 3 letras + 4 números
- Regex: `^[A-Z]{3}[0-9]{4}$`
- Exemplo: ABC-1234

### Placa Mercosur (LLLNLNN)
- Padrão: 3 letras + 1 número + 1 letra/número + 2 números
- Regex: `^[A-Z]{3}[0-9][A-Z0-9][0-9]{2}$`
- Exemplo: ABC1D23

## Próximos Passos

### Fase 1 - Backend (concluída)
- ✅ Implementar YOLOv11 + EasyOCR em Python
- ✅ Criar serviço OCR
- ✅ Criar endpoint `/mobile/ocr/validate`
- ⏳ Testar com dataset FARO
- ⏳ Medir accuracy/confiança

### Fase 2 - Mobile (pendente)
- ⏳ Converter modelos para TFLite/ONNX
- ⏳ Integrar no `CameraPreview.kt`
- ⏳ Manter ML Kit como fallback
- ⏳ Testar performance/bateria

### Fase 3 - Sync Backend (pendente)
- ⏳ Backend reprocessa OCR quando online
- ⏳ Comparar resultado mobile vs backend
- ⏳ Atualizar `plateReads` se backend melhor
- ⏳ Feedback ao campo se discrepância

### Fase 4 - Monitoramento (pendente)
- ⏳ Logar accuracy OCR mobile vs backend
- ⏳ Calibrar threshold de confiança
- ⏳ Ajustar modelo com dados operacionais

## Considerações

### Performance Mobile
- TFLite otimizado para mobile (GPU/NNAPI)
- Intervalo de processamento: 300ms
- Deduplicação 1.5s
- Parar OCR se bateria < 20%

### Armazenamento
- Modelos TFLite: ~10-20MB cada
- Cache de imagens: 7 dias TTL
- Eliminação segura pós-sync

### Privacidade
- Processamento 100% local
- Imagens não saem do dispositivo até sync
- Criptografia em repouso

## Referências

- **YOLOv11:** https://github.com/ultralytics/ultralytics
- **EasyOCR:** https://github.com/JaidedAI/EasyOCR
- **TensorFlow Lite:** https://www.tensorflow.org/lite
- **ONNX Runtime:** https://onnxruntime.ai
- **Hugging Face Models:**
  - morsetechlab/yolov11-license-plate-detection
  - MKgoud/License-Plate-Recognizer
