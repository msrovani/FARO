#!/usr/bin/env python3
"""
F.A.R.O. Server Core Status Check
Verifica o status real do server-core e endpoints implementados.
"""

import os
import json
import logging
from datetime import datetime
from pathlib import Path

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class ServerCoreStatusChecker:
    """Verificador de status do server-core F.A.R.O."""
    
    def __init__(self):
        self.server_core_path = Path("c:/Users/msrov/OneDrive/Área de Trabalho/FARO/server-core")
        self.status_report = {}
        
    def check_server_core_structure(self) -> dict:
        """Verifica estrutura do server-core."""
        logger.info("🔍 Verificando estrutura do server-core...")
        
        required_dirs = [
            "app",
            "app/api",
            "app/api/v1",
            "app/api/v1/endpoints",
            "app/services",
            "app/db",
            "app/core",
            "app/schemas"
        ]
        
        structure_status = {}
        for dir_path in required_dirs:
            full_path = self.server_core_path / dir_path
            structure_status[dir_path] = full_path.exists()
        
        return structure_status
    
    def check_endpoints_implementation(self) -> dict:
        """Verifica endpoints implementados."""
        logger.info("📡 Verificando endpoints implementados...")
        
        endpoints_dir = self.server_core_path / "app/api/v1/endpoints"
        if not endpoints_dir.exists():
            return {"error": "Endpoints directory not found"}
        
        endpoint_files = list(endpoints_dir.glob("*.py"))
        endpoint_status = {}
        
        for file_path in endpoint_files:
            if file_path.name != "__init__.py":
                try:
                    with open(file_path, 'r', encoding='utf-8') as f:
                        content = f.read()
                    
                    # Conta routers e endpoints
                    router_count = content.count("@router.")
                    endpoint_count = content.count("@router.get") + content.count("@router.post") + content.count("@router.put") + content.count("@router.delete")
                    
                    endpoint_status[file_path.stem] = {
                        "file_exists": True,
                        "router_count": router_count,
                        "endpoint_count": endpoint_count,
                        "file_size": len(content)
                    }
                except Exception as e:
                    endpoint_status[file_path.stem] = {
                        "file_exists": True,
                        "error": str(e)
                    }
        
        return endpoint_status
    
    def check_services_implementation(self) -> dict:
        """Verifica serviços implementados."""
        logger.info("⚙️ Verificando serviços implementados...")
        
        services_dir = self.server_core_path / "app/services"
        if not services_dir.exists():
            return {"error": "Services directory not found"}
        
        service_files = list(services_dir.glob("*.py"))
        service_status = {}
        
        important_services = [
            "analytics_service.py",
            "location_interception_service.py", 
            "ocr_enhancement_service.py",
            "cache_service.py",
            "intercept_adaptive_service.py",
            "event_bus.py"
        ]
        
        for file_path in service_files:
            if file_path.name != "__init__.py":
                try:
                    with open(file_path, 'r', encoding='utf-8') as f:
                        content = f.read()
                    
                    # Verifica se é um serviço importante
                    is_important = file_path.name in important_services
                    
                    # Conta funções async
                    async_func_count = content.count("async def")
                    class_count = content.count("class ")
                    
                    service_status[file_path.stem] = {
                        "file_exists": True,
                        "is_important": is_important,
                        "async_functions": async_func_count,
                        "classes": class_count,
                        "file_size": len(content)
                    }
                except Exception as e:
                    service_status[file_path.stem] = {
                        "file_exists": True,
                        "error": str(e)
                    }
        
        return service_status
    
    def check_database_models(self) -> dict:
        """Verifica modelos de banco de dados."""
        logger.info("🗄️ Verificando modelos de banco de dados...")
        
        db_file = self.server_core_path / "app/db/base.py"
        if not db_file.exists():
            return {"error": "Database models file not found"}
        
        try:
            with open(db_file, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # Procura modelos importantes
            important_models = [
                "VehicleObservation",
                "InterceptEvent", 
                "AgentLocationLog",
                "WatchlistEntry",
                "User",
                "Agency"
            ]
            
            model_status = {}
            for model in important_models:
                model_count = content.count(f"class {model}")
                model_status[model] = model_count > 0
            
            # Verifica imports PostGIS
            postgis_imports = content.count("geoalchemy2") + content.count("GEOMETRY")
            
            return {
                "file_exists": True,
                "models": model_status,
                "postgis_imports": postgis_imports > 0,
                "file_size": len(content)
            }
            
        except Exception as e:
            return {"error": str(e)}
    
    def check_routes_configuration(self) -> dict:
        """Verifica configuração de rotas."""
        logger.info("🛣️ Verificando configuração de rotas...")
        
        routes_file = self.server_core_path / "app/api/routes.py"
        if not routes_file.exists():
            return {"error": "Routes file not found"}
        
        try:
            with open(routes_file, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # Conta roteadores incluídos
            router_includes = content.count("api_router.include_router")
            
            # Verifica roteadores importantes
            important_routers = [
                "intelligence.router",
                "agents.router", 
                "mobile.router",
                "location_interception.router"
            ]
            
            router_status = {}
            for router in important_routers:
                router_status[router] = router in content
            
            return {
                "file_exists": True,
                "router_includes": router_includes,
                "important_routers": router_status,
                "file_size": len(content)
            }
            
        except Exception as e:
            return {"error": str(e)}
    
    def check_main_application(self) -> dict:
        """Verifica aplicação principal."""
        logger.info("🚀 Verificando aplicação principal...")
        
        main_file = self.server_core_path / "app/main.py"
        if not main_file.exists():
            return {"error": "Main application file not found"}
        
        try:
            with open(main_file, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # Verifica componentes FastAPI
            fastapi_imports = content.count("from fastapi")
            app_creation = content.count("FastAPI()")
            
            # Verifica configuração
            config_imports = content.count("from app.core.config")
            
            return {
                "file_exists": True,
                "fastapi_imports": fastapi_imports > 0,
                "app_creation": app_creation > 0,
                "config_imports": config_imports > 0,
                "file_size": len(content)
            }
            
        except Exception as e:
            return {"error": str(e)}
    
    def generate_comprehensive_report(self) -> dict:
        """Gera relatório completo do server-core."""
        logger.info("📊 Gerando relatório completo...")
        
        report = {
            "timestamp": datetime.utcnow().isoformat(),
            "server_core_path": str(self.server_core_path),
            "structure": self.check_server_core_structure(),
            "endpoints": self.check_endpoints_implementation(),
            "services": self.check_services_implementation(),
            "database": self.check_database_models(),
            "routes": self.check_routes_configuration(),
            "main_app": self.check_main_application()
        }
        
        # Calcula métricas
        total_dirs = len(report["structure"])
        existing_dirs = sum(1 for exists in report["structure"].values() if exists)
        
        total_endpoint_files = len(report.get("endpoints", {}))
        total_endpoints = sum(e.get("endpoint_count", 0) for e in report.get("endpoints", {}).values() if isinstance(e, dict))
        
        important_services = sum(1 for s in report.get("services", {}).values() if isinstance(s, dict) and s.get("is_important", False))
        
        models_implemented = sum(1 for implemented in report.get("database", {}).get("models", {}).values() if implemented)
        
        report["metrics"] = {
            "structure_completion": f"{existing_dirs}/{total_dirs} ({(existing_dirs/total_dirs*100):.1f}%)" if total_dirs > 0 else "0/0",
            "endpoint_files": total_endpoint_files,
            "total_endpoints": total_endpoints,
            "important_services": important_services,
            "database_models": f"{models_implemented}/6",
            "postgis_enabled": report.get("database", {}).get("postgis_imports", False),
            "ready_for_integration": self.calculate_readiness_score(report)
        }
        
        # Salva relatório
        report_file = self.server_core_path / "server_core_status_report.json"
        with open(report_file, 'w', encoding='utf-8') as f:
            json.dump(report, f, indent=2, ensure_ascii=False)
        
        return report
    
    def calculate_readiness_score(self, report: dict) -> str:
        """Calcula score de prontidão para integração."""
        score = 0
        max_score = 100
        
        # Estrutura (20 pontos)
        structure = report.get("structure", {})
        if structure:
            completed = sum(1 for exists in structure.values() if exists)
            score += (completed / len(structure)) * 20
        
        # Endpoints (25 pontos)
        endpoints = report.get("endpoints", {})
        if endpoints and not isinstance(endpoints, dict) or "error" not in endpoints:
            total_endpoints = sum(e.get("endpoint_count", 0) for e in endpoints.values() if isinstance(e, dict))
            if total_endpoints >= 20:
                score += 25
            elif total_endpoints >= 10:
                score += 15
            elif total_endpoints >= 5:
                score += 10
        
        # Serviços (25 pontos)
        services = report.get("services", {})
        if services and not isinstance(services, dict) or "error" not in services:
            important_count = sum(1 for s in services.values() if isinstance(s, dict) and s.get("is_important", False))
            if important_count >= 5:
                score += 25
            elif important_count >= 3:
                score += 15
            elif important_count >= 1:
                score += 10
        
        # Banco de dados (15 pontos)
        database = report.get("database", {})
        if database and not isinstance(database, dict) or "error" not in database:
            models = database.get("models", {})
            model_count = sum(1 for implemented in models.values() if implemented)
            if model_count >= 5:
                score += 15
            elif model_count >= 3:
                score += 10
            elif model_count >= 1:
                score += 5
        
        # Rotas (10 pontos)
        routes = report.get("routes", {})
        if routes and not isinstance(routes, dict) or "error" not in routes:
            if routes.get("router_includes", 0) >= 5:
                score += 10
            elif routes.get("router_includes", 0) >= 3:
                score += 7
            elif routes.get("router_includes", 0) >= 1:
                score += 5
        
        # App principal (5 pontos)
        main_app = report.get("main_app", {})
        if main_app and not isinstance(main_app, dict) or "error" not in main_app:
            if main_app.get("fastapi_imports", False) and main_app.get("app_creation", False):
                score += 5
            elif main_app.get("fastapi_imports", False):
                score += 3
        
        return f"{score:.0f}/100"
    
    def print_summary(self, report: dict):
        """Imprime resumo do relatório."""
        print("\n" + "="*80)
        print("📊 RELATÓRIO DE STATUS DO SERVER-CORE F.A.R.O.")
        print("="*80)
        
        metrics = report.get("metrics", {})
        print(f"📁 Estrutura: {metrics.get('structure_completion', 'N/A')}")
        print(f"📡 Endpoints: {metrics.get('total_endpoints', 0)} em {metrics.get('endpoint_files', 0)} arquivos")
        print(f"⚙️ Serviços Importantes: {metrics.get('important_services', 0)} implementados")
        print(f"🗄️ Modelos BD: {metrics.get('database_models', 'N/A')}")
        print(f"🌐 PostGIS: {'✅ Habilitado' if metrics.get('postgis_enabled', False) else '❌ Não habilitado'}")
        print(f"🎯 Prontidão: {metrics.get('ready_for_integration', 'N/A')}")
        
        print(f"\n📋 Status dos Componentes:")
        
        # Endpoints
        endpoints = report.get("endpoints", {})
        if endpoints and not isinstance(endpoints, dict) or "error" not in endpoints:
            print("  📡 Endpoints Implementados:")
            for name, info in endpoints.items():
                if isinstance(info, dict):
                    status = "✅" if info.get("endpoint_count", 0) > 0 else "⚠️"
                    print(f"    {status} {name}: {info.get('endpoint_count', 0)} endpoints")
        
        # Serviços
        services = report.get("services", {})
        if services and not isinstance(services, dict) or "error" not in services:
            print("  ⚙️ Serviços Implementados:")
            for name, info in services.items():
                if isinstance(info, dict):
                    important = "🌟" if info.get("is_important", False) else "  "
                    status = "✅" if info.get("async_functions", 0) > 0 else "⚠️"
                    print(f"    {status}{important} {name}: {info.get('async_functions', 0)} funções async")
        
        print(f"\n📄 Relatório detalhado salvo em: server_core_status_report.json")
        print("="*80)


def main():
    """Função principal."""
    checker = ServerCoreStatusChecker()
    report = checker.generate_comprehensive_report()
    checker.print_summary(report)


if __name__ == "__main__":
    main()
