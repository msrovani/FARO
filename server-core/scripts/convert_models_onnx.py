"""
Script para converter modelos OCR para ONNX (mobile deployment via ONNX Runtime)

Converte:
1. YOLOv11 para ONNX (detecção de placas)
2. EasyOCR para ONNX (reconhecimento de caracteres)

Uso:
    python scripts/convert_models_onnx.py --output-dir ./models/onnx
"""

import argparse
import logging
from pathlib import Path

import torch
from ultralytics import YOLO

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def convert_yolo_to_onnx(
    model_path: str = "yolov11n.pt",
    output_path: str = "yolov11_plate.onnx",
    input_size: int = 640
):
    """
    Converte modelo YOLO para ONNX
    
    Args:
        model_path: Caminho para modelo YOLO (.pt)
        output_path: Caminho de saída para modelo ONNX
        input_size: Tamanho de entrada (640 para YOLO padrão)
    """
    logger.info(f"Convertendo YOLO model de {model_path} para ONNX...")
    
    # Carregar modelo YOLO
    model = YOLO(model_path)
    
    # Exportar para ONNX
    model.export(
        format="onnx",
        imgsz=input_size,
        dynamic=False,
        simplify=True,
        opset=12
    )
    
    # O Ultralytics salva com extensão .onnx no mesmo diretório
    onnx_path = Path(model_path).with_suffix(".onnx")
    
    if output_path:
        # Mover para caminho desejado
        onnx_path.rename(output_path)
        logger.info(f"Modelo salvo em: {output_path}")
    else:
        logger.info(f"Modelo salvo em: {onnx_path}")
    
    return str(onnx_path)


def convert_easyocr_to_onnx(
    output_path: str = "easyocr.onnx",
    input_size: tuple = (32, 128)
):
    """
    Converte modelo EasyOCR para ONNX
    
    Nota: EasyOCR usa PyTorch. Conversão para ONNX é possível mas complexa.
    
    Args:
        output_path: Caminho de saída para modelo ONNX
        input_size: Tamanho de entrada (altura, largura)
    """
    logger.info("Convertendo EasyOCR para ONNX...")
    
    try:
        import easyocr
        
        # Carregar modelo EasyOCR
        reader = easyocr.Reader(["en", "pt"], gpu=False, verbose=False)
        
        # EasyOCR não expõe modelo PyTorch diretamente
        # A conversão requer acesso interno ao modelo
        
        logger.warning("EasyOCR não suporta exportação ONNX direta")
        logger.warning("Alternativas:")
        logger.warning("1. Usar TFLite Text Recognition API do Google")
        logger.warning("2. Treinar modelo customizado com suporte ONNX")
        logger.warning("3. Usar PaddleOCR (tem melhor suporte para ONNX)")
        
        return None
        
    except Exception as e:
        logger.error(f"Erro na conversão EasyOCR: {e}")
        return None


def convert_paddleocr_to_onnx(
    output_path: str = "paddleocr.onnx"
):
    """
    Converte PaddleOCR para ONNX
    
    PaddleOCR tem melhor suporte para ONNX que EasyOCR
    
    Args:
        output_path: Caminho de saída para modelo ONNX
    """
    logger.info("Convertendo PaddleOCR para ONNX...")
    
    try:
        from paddle2onnx import program2onnx
        import paddleocr
        
        logger.warning("PaddleOCR para ONNX requer instalação de paddle2onnx")
        logger.warning("pip install paddle2onnx paddleocr")
        
        # Exemplo de conversão (requer modelo PaddleOCR carregado)
        # model = paddleocr.PaddleOCR(use_angle_cls=True, lang='en')
        # program2onnx(model, save_file=output_path)
        
        logger.info("Para implementação completa, instalar dependências e adaptar script")
        
        return None
        
    except ImportError:
        logger.error("paddle2onnx não instalado. Execute: pip install paddle2onnx paddleocr")
        return None
    except Exception as e:
        logger.error(f"Erro na conversão PaddleOCR: {e}")
        return None


def main():
    parser = argparse.ArgumentParser(
        description="Converter modelos OCR para ONNX Runtime"
    )
    parser.add_argument(
        "--output-dir",
        type=str,
        default="./models/onnx",
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
        help="Pular conversão EasyOCR"
    )
    parser.add_argument(
        "--try-paddleocr",
        action="store_true",
        help="Tentar conversão PaddleOCR (alternativa a EasyOCR)"
    )
    
    args = parser.parse_args()
    
    # Criar diretório de saída
    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    
    # Converter YOLO
    if not args.skip_yolo:
        yolo_output = output_dir / "yolov11_plate.onnx"
        try:
            convert_yolo_to_onnx(
                model_path=args.yolo_model,
                output_path=str(yolo_output),
                input_size=args.input_size
            )
            logger.info(f"✓ YOLO convertido com sucesso")
        except Exception as e:
            logger.error(f"✗ Erro na conversão YOLO: {e}")
    
    # Converter EasyOCR
    if not args.skip_easyocr:
        easyocr_output = output_dir / "easyocr.onnx"
        try:
            result = convert_easyocr_to_onnx(output_path=str(easyocr_output))
            if result:
                logger.info(f"✓ EasyOCR convertido com sucesso")
            else:
                logger.info("⊘ EasyOCR não convertido (usar PaddleOCR ou TFLite)")
        except Exception as e:
            logger.error(f"✗ Erro na conversão EasyOCR: {e}")
    
    # Tentar PaddleOCR
    if args.try_paddleocr:
        paddleocr_output = output_dir / "paddleocr.onnx"
        try:
            result = convert_paddleocr_to_onnx(output_path=str(paddleocr_output))
            if result:
                logger.info(f"✓ PaddleOCR convertido com sucesso")
        except Exception as e:
            logger.error(f"✗ Erro na conversão PaddleOCR: {e}")
    
    logger.info("\nResumo:")
    logger.info(f"Modelos salvos em: {output_dir.absolute()}")
    logger.info("\nPróximos passos:")
    logger.info("1. Copiar modelos ONNX para: mobile-agent-field/app/src/main/assets/")
    logger.info("2. Integrar ONNX Runtime no Android")
    logger.info("3. Para OCR caracteres, considerar:")
    logger.info("   - ONNX Runtime com PaddleOCR (recomendado)")
    logger.info("   - TFLite Text Recognition API do Google")


if __name__ == "__main__":
    main()
