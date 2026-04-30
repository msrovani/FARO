"""
Script para converter modelos OCR para TensorFlow Lite (mobile deployment)

Converte:
1. YOLOv11 para TFLite (detecção de placas)
2. EasyOCR para TFLite (reconhecimento de caracteres)

Uso:
    python scripts/convert_models_tflite.py --output-dir ./models/tflite
"""

import argparse
import logging
from pathlib import Path

import torch
from ultralytics import YOLO

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def convert_yolo_to_tflite(
    model_path: str = "yolov11n.pt",
    output_path: str = "yolov11_plate.tflite",
    input_size: int = 640
):
    """
    Converte modelo YOLO para TFLite
    
    Args:
        model_path: Caminho para modelo YOLO (.pt)
        output_path: Caminho de saída para modelo TFLite
        input_size: Tamanho de entrada (640 para YOLO padrão)
    """
    logger.info(f"Convertendo YOLO model de {model_path} para TFLite...")
    
    # Carregar modelo YOLO
    model = YOLO(model_path)
    
    # Exportar para TFLite
    model.export(
        format="tflite",
        imgsz=input_size,
        dynamic=False,
        simplify=True
    )
    
    # O Ultralytics salva com extensão .tflite no mesmo diretório
    tflite_path = Path(model_path).with_suffix(".tflite")
    
    if output_path:
        # Mover para caminho desejado
        tflite_path.rename(output_path)
        logger.info(f"Modelo salvo em: {output_path}")
    else:
        logger.info(f"Modelo salvo em: {tflite_path}")
    
    return str(tflite_path)


def convert_easyocr_to_tflite(
    output_path: str = "easyocr.tflite",
    input_size: tuple = (32, 128)
):
    """
    Converte modelo EasyOCR para TFLite
    
    Nota: EasyOCR usa PyTorch. Conversão para TFLite requer:
    1. Exportar para ONNX primeiro
    2. Converter ONNX para TFLite
    
    Args:
        output_path: Caminho de saída para modelo TFLite
        input_size: Tamanho de entrada (altura, largura)
    """
    logger.info("Convertendo EasyOCR para TFLite...")
    logger.warning("Conversão EasyOCR para TFLite é complexa.")
    logger.warning("Requer exportação via ONNX como intermediário.")
    logger.warning("Considere usar ONNX Runtime no Android como alternativa.")
    
    # EasyOCR não suporta exportação direta para TFLite
    # Alternativas:
    # 1. Usar ONNX Runtime no Android (recomendado)
    # 2. Treinar modelo customizado com suporte TFLite
    # 3. Usar TFLite Text Recognition API do Google
    
    logger.info("Recomendação: Usar ONNX Runtime no Android para EasyOCR")
    logger.info("Script para conversão ONNX: convert_models_onnx.py")
    
    return None


def main():
    parser = argparse.ArgumentParser(
        description="Converter modelos OCR para TensorFlow Lite"
    )
    parser.add_argument(
        "--output-dir",
        type=str,
        default="./models/tflite",
        help="Diretório de saída para modelos convertidos"
    )
    parser.add_argument(
        "--yolo-model",
        type=str,
        default="yolov11n.pt",
        help="Caminho para modelo YOLO (.pt)"
    )
    parser.add_argument(
        "--input-size",
        type=int,
        default=640,
        help="Tamanho de entrada para YOLO (padrão: 640)"
    )
    parser.add_argument(
        "--skip-yolo",
        action="store_true",
        help="Pular conversão YOLO"
    )
    parser.add_argument(
        "--skip-easyocr",
        action="store_true",
        help="Pular conversão EasyOCR (recomendado - usar ONNX)"
    )
    
    args = parser.parse_args()
    
    # Criar diretório de saída
    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    
    # Converter YOLO
    if not args.skip_yolo:
        yolo_output = output_dir / "yolov11_plate.tflite"
        try:
            convert_yolo_to_tflite(
                model_path=args.yolo_model,
                output_path=str(yolo_output),
                input_size=args.input_size
            )
            logger.info(f"✓ YOLO convertido com sucesso")
        except Exception as e:
            logger.error(f"✗ Erro na conversão YOLO: {e}")
    
    # Converter EasyOCR
    if not args.skip_easyocr:
        easyocr_output = output_dir / "easyocr.tflite"
        try:
            result = convert_easyocr_to_tflite(
                output_path=str(easyocr_output)
            )
            if result:
                logger.info(f"✓ EasyOCR convertido com sucesso")
            else:
                logger.info("⊘ EasyOCR não convertido (usar ONNX Runtime)")
        except Exception as e:
            logger.error(f"✗ Erro na conversão EasyOCR: {e}")
    
    logger.info("\nResumo:")
    logger.info(f"Modelos salvos em: {output_dir.absolute()}")
    logger.info("\nPróximos passos:")
    logger.info("1. Copiar modelos TFLite para: mobile-agent-field/app/src/main/assets/")
    logger.info("2. Integrar TFLite no Android usando TFLite Task Vision API")
    logger.info("3. Para EasyOCR, considerar ONNX Runtime no Android")


if __name__ == "__main__":
    main()
