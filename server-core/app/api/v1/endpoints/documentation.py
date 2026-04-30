"""
Documentation API Endpoint
Provides dynamic server optimization data, legal documentation, and usage guidelines.
"""
from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.db.session import get_db
from app.utils.hardware_detector import get_hardware_capabilities
from app.utils.performance_monitor import get_performance_monitor
from app.utils.circuit_breaker import get_circuit_breaker

router = APIRouter()


@router.get("/")
async def documentation_root():
    """Documentation API root endpoint."""
    return {
        "module": "F.A.R.O. Documentation API",
        "version": "1.0.0",
        "description": "API para documentação legal, otimização e orientações de uso",
        "endpoints": [
            "/optimization/hardware",
            "/optimization/config",
            "/optimization/performance",
            "/optimization/recommendations",
            "/optimization/circuit-breakers",
            "/legal/terms-of-service",
            "/legal/privacy-policy",
            "/usage/guidelines",
            "/usage/alerts",
        ],
    }


@router.get("/optimization/hardware")
async def get_hardware_info():
    """
    Get current hardware capabilities and configuration.
    """
    hardware = get_hardware_capabilities()
    
    return {
        "cpu_count": hardware.cpu_count,
        "cpu_count_physical": hardware.cpu_count_physical,
        "total_memory_gb": round(hardware.total_memory_gb, 2),
        "available_memory_gb": round(hardware.available_memory_gb, 2),
        "gpu_available": hardware.gpu_available,
        "gpu_type": hardware.gpu_type,
        "gpu_memory_gb": round(hardware.gpu_memory_gb, 2) if hardware.gpu_memory_gb else None,
        "platform": hardware.platform,
        "architecture": hardware.architecture,
    }


@router.get("/optimization/config")
async def get_optimization_config():
    """
    Get current optimization configuration.
    """
    return {
        "workers": settings.workers,
        "process_pool_max_workers": settings.process_pool_max_workers,
        "process_pool_cpu_bound_workers": settings.process_pool_cpu_bound_workers,
        "process_pool_io_bound_workers": settings.process_pool_io_bound_workers,
        "ocr_device": settings.ocr_device,
        "ocr_confidence_threshold": settings.ocr_confidence_threshold,
        "ocr_auto_accept_enabled": settings.ocr_auto_accept_enabled,
        "ocr_auto_accept_threshold": settings.ocr_auto_accept_threshold,
    }


@router.get("/optimization/performance")
async def get_performance_metrics():
    """
    Get current performance metrics for all task types.
    """
    monitor = get_performance_monitor()
    
    metrics = {}
    for task_type, metric in monitor.metrics.items():
        metrics[task_type] = {
            "avg_execution_time_ms": round(metric.avg_execution_time_ms, 2),
            "p95_execution_time_ms": round(metric.p95_execution_time_ms, 2),
            "p99_execution_time_ms": round(metric.p99_execution_time_ms, 2),
            "success_rate": round(metric.success_rate, 4),
            "error_count": metric.error_count,
            "total_executions": metric.total_executions,
            "state": metric.state.value,
        }
    
    return metrics


@router.get("/optimization/recommendations")
async def get_optimization_recommendations():
    """
    Get adaptive optimization recommendations for all task types.
    """
    monitor = get_performance_monitor()
    
    recommendations = {}
    for task_type in monitor.configs.keys():
        recommendation = monitor.get_adaptive_recommendation(task_type)
        recommendations[task_type] = recommendation
    
    return recommendations


@router.get("/optimization/circuit-breakers")
async def get_circuit_breaker_status():
    """
    Get status of all circuit breakers.
    """
    from app.utils.circuit_breaker import _circuit_breakers
    
    status = {}
    for name, breaker in _circuit_breakers.items():
        stats = breaker.get_stats()
        status[name] = stats
    
    return status


@router.get("/legal/terms-of-service")
async def get_terms_of_service():
    """
    Get terms of service for F.A.R.O.
    """
    return {
        "title": "Termos de Uso - F.A.R.O.",
        "version": "1.0",
        "last_updated": "2026-04-15",
        "sections": [
            {
                "title": "1. Aceitação dos Termos",
                "content": "Ao utilizar o sistema F.A.R.O. (Ferramenta de Análise de Rotas e Observações), você concorda com estes termos de uso."
            },
            {
                "title": "2. Finalidade do Sistema",
                "content": "O F.A.R.O. é uma ferramenta de análise operacional destinada exclusivamente a uso por agências de segurança pública e órgãos governamentais autorizados."
            },
            {
                "title": "3. Uso Autorizado",
                "content": "O uso do sistema é restrito a pessoal autorizado por agências de segurança pública. Qualquer uso não autorizado é estritamente proibido."
            },
            {
                "title": "4. Responsabilidades do Usuário",
                "content": "Os usuários são responsáveis por manter a confidencialidade de suas credenciais e por todas as atividades realizadas sob sua conta."
            },
            {
                "title": "5. Proteção de Dados",
                "content": "O sistema implementa criptografia AES-256 para dados em repouso e HTTPS para dados em trânsito. Todos os dados são processados em conformidade com as políticas de segurança da instituição."
            },
            {
                "title": "6. Auditoria",
                "content": "Todas as ações no sistema são registradas para fins de auditoria e conformidade. Os logs são mantidos por 7 anos conforme regulamentação."
            },
            {
                "title": "7. Limitação de Responsabilidade",
                "content": "O sistema é fornecido 'como está', sem garantias de qualquer tipo. A instituição não se responsabiliza por danos diretos ou indiretos resultantes do uso do sistema."
            },
        ]
    }


@router.get("/legal/privacy-policy")
async def get_privacy_policy():
    """
    Get privacy policy for F.A.R.O.
    """
    return {
        "title": "Política de Privacidade - F.A.R.O.",
        "version": "1.0",
        "last_updated": "2026-04-15",
        "sections": [
            {
                "title": "1. Coleta de Dados",
                "content": "O sistema coleta dados de observações veiculares, incluindo localização GPS, imagens, e informações de placas. Todos os dados são coletados exclusivamente para fins operacionais de segurança pública."
            },
            {
                "title": "2. Armazenamento Seguro",
                "content": "Todos os dados são armazenados com criptografia AES-256 em repouso. Dados sensíveis são protegidos com Android Keystore no mobile."
            },
            {
                "title": "3. Retenção de Dados",
                "content": "Os dados são retidos por 7 anos para fins de auditoria, conforme regulamentação. Dados temporários no mobile são eliminados após 7 dias ou sync bem-sucedido."
            },
            {
                "title": "4. Compartilhamento de Dados",
                "content": "Os dados são compartilhados exclusivamente entre agências de segurança pública autorizadas. Não há compartilhamento com terceiros não autorizados."
            },
            {
                "title": "5. Direitos do Usuário",
                "content": "Os usuários têm direito a acessar seus dados pessoais, solicitar correções, e solicitar exclusão quando aplicável, conforme LGPD."
            },
            {
                "title": "6. Cookies e Rastreamento",
                "content": "O sistema não utiliza cookies de rastreamento. O monitoramento de performance é estritamente para fins operacionais e não coleta dados pessoais."
            },
        ]
    }


@router.get("/usage/guidelines")
async def get_usage_guidelines():
    """
    Get usage guidelines for F.A.R.O.
    """
    return {
        "title": "Orientações de Uso - F.A.R.O.",
        "version": "1.0",
        "last_updated": "2026-04-15",
        "sections": [
            {
                "title": "1. Uso do Mobile (Agente de Campo)",
                "content": [
                    "Registre observações apenas durante patrulhas oficiais",
                    "Confirme OCR manualmente quando confiança < 85%",
                    "Sincronize dados regularmente (mínimo 1x por turno)",
                    "Mantenha dispositivo carregado para operações prolongadas",
                    "Use WiFi quando disponível para sync de grandes volumes",
                ]
            },
            {
                "title": "2. Uso do Console de Inteligência",
                "content": [
                    "Revise fila analítica regularmente (mínimo 2x por turno)",
                    "Classifique suspeições com precisão para melhorar algoritmos",
                    "Forneça feedback construtivo ao campo",
                    "Use filtros de agência para visão apropriada",
                    "Monitore hotspots e rotas recorrentes",
                ]
            },
            {
                "title": "3. Boas Práticas de Segurança",
                "content": [
                    "Nunca compartilhe credenciais de acesso",
                    "Faça logout ao finalizar turno",
                    "Não use em dispositivos pessoais não autorizados",
                    "Reporte incidentes de segurança imediatamente",
                    "Mantenha software atualizado",
                ]
            },
            {
                "title": "4. Procedimentos em Caso de Falha",
                "content": [
                    "Se sync falhar: dados são mantidos localmente por 7 dias",
                    "Se OCR falhar: use entrada manual de placa",
                    "Se app crashar: reinicie e verifique dados não sincronizados",
                    "Se servidor indisponível: continue operação offline, sync quando disponível",
                ]
            },
        ]
    }


@router.get("/usage/alerts")
async def get_usage_alerts():
    """
    Get current system alerts and warnings.
    """
    monitor = get_performance_monitor()
    
    alerts = []
    
    # Check for degraded performance
    for task_type, metric in monitor.metrics.items():
        if metric.state.value == "degraded":
            alerts.append({
                "type": "warning",
                "severity": "medium",
                "message": f"Performance degradada para {task_type}",
                "details": f"Tempo médio: {metric.avg_execution_time_ms:.2f}ms, Taxa de sucesso: {metric.success_rate:.2%}",
                "timestamp": "now",
            })
        elif metric.state.value == "critical":
            alerts.append({
                "type": "error",
                "severity": "high",
                "message": f"Performance crítica para {task_type}",
                "details": f"Tempo médio: {metric.avg_execution_time_ms:.2f}ms, Taxa de sucesso: {metric.success_rate:.2%}",
                "timestamp": "now",
            })
    
    # Check for low memory
    hardware = get_hardware_capabilities()
    if hardware.available_memory_gb < 2.0:
        alerts.append({
            "type": "warning",
            "severity": "medium",
            "message": "Memória disponível baixa",
            "details": f"Disponível: {hardware.available_memory_gb:.2f}GB",
            "timestamp": "now",
        })
    
    # Check for circuit breakers
    from app.utils.circuit_breaker import _circuit_breakers
    for name, breaker in _circuit_breakers.items():
        if breaker.state.value == "open":
            alerts.append({
                "type": "error",
                "severity": "high",
                "message": f"Circuit breaker aberto para {name}",
                "details": "Operação temporariamente desabilitada devido a falhas consecutivas",
                "timestamp": "now",
            })
    
    return {
        "total_alerts": len(alerts),
        "alerts": alerts,
    }
