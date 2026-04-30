#!/usr/bin/env python3
"""
F.A.R.O. Service Runner

Inicia todos os serviços do FARO de forma coordenada.
Detecta automaticamente o diretório base e verifica portas antes de iniciar.

Uso:
    python run_services.py
    python run_services.py --skip-web
    python run_services.py --skip-analytics
"""

import subprocess
import sys
import threading
import time
import os
import socket
import signal
import argparse
from pathlib import Path
from datetime import datetime

# Cores para terminal
class Colors:
    GREEN = '\033[92m'
    YELLOW = '\033[93m'
    RED = '\033[91m'
    CYAN = '\033[96m'
    RESET = '\033[0m'

def log_info(msg: str):
    print(f"{Colors.CYAN}[{datetime.now().strftime('%H:%M:%S')}] ℹ️  {msg}{Colors.RESET}")

def log_success(msg: str):
    print(f"{Colors.GREEN}[{datetime.now().strftime('%H:%M:%S')}] ✅ {msg}{Colors.RESET}")

def log_warning(msg: str):
    print(f"{Colors.YELLOW}[{datetime.now().strftime('%H:%M:%S')}] ⚠️  {msg}{Colors.RESET}")

def log_error(msg: str):
    print(f"{Colors.RED}[{datetime.now().strftime('%H:%M:%S')}] ❌ {msg}{Colors.RESET}")

def is_port_available(port: int) -> bool:
    """Verifica se uma porta está disponível."""
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        return s.connect_ex(('localhost', port)) != 0

def kill_process_on_port(port: int):
    """Tenta encerrar processo usando uma porta específica."""
    try:
        if sys.platform == 'win32':
            result = subprocess.run(
                ['netstat', '-ano'], 
                capture_output=True, 
                text=True
            )
            for line in result.stdout.split('\n'):
                if f':{port}' in line and 'LISTENING' in line:
                    parts = line.split()
                    if len(parts) >= 5:
                        pid = parts[-1]
                        subprocess.run(['taskkill', '/F', '/PID', pid], 
                                   capture_output=True)
                        log_warning(f"Processo na porta {port} encerrado (PID: {pid})")
                        return True
        else:
            subprocess.run(['lsof', '-ti', f':{port}', '-c', 'kill'], 
                         capture_output=True)
    except Exception:
        pass
    return False

# Detectar diretório base automaticamente
BASE_DIR = Path(__file__).parent.resolve()
PYTHON = sys.executable

class ServiceManager:
    def __init__(self, skip_web: bool = False, skip_analytics: bool = False):
        self.skip_web = skip_web
        self.skip_analytics = skip_analytics
        self.processes = []
        self.running = True
        
    def get_services(self):
        """Retorna lista de serviços configurados."""
        services = []
        
        # Server Core (sempre inicia)
        services.append({
            'name': 'Server Core',
            'port': 8000,
            'cmd': [PYTHON, '-m', 'uvicorn', 'app.main:app', 
                   '--host', '127.0.0.1', '--port', '8000'],
            'cwd': BASE_DIR / 'server-core',
            'url': 'http://127.0.0.1:8000',
            'required': True
        })
        
        # Analytics Dashboard
        if not self.skip_analytics:
            services.append({
                'name': 'Analytics Dashboard',
                'port': 9002,
                'cmd': [PYTHON, 'analytics-dashboard/app.py'],
                'cwd': BASE_DIR / 'analytics-dashboard',
                'url': 'http://localhost:9002/dashboard',
                'required': False
            })
        
        # Web Console
        if not self.skip_web:
            services.append({
                'name': 'Web Console',
                'port': 3000,
                'cmd': ['npm', 'run', 'dev'],
                'cwd': BASE_DIR / 'web-intelligence-console',
                'url': 'http://localhost:3000',
                'required': False
            })
        
        return services
    
    def check_ports(self, services):
        """Verifica portas e oferece para encerrar processos conflitantes."""
        log_info("Verificando portas disponíveis...")
        conflicts = []
        
        for svc in services:
            if not is_port_available(svc['port']):
                conflicts.append(svc)
                log_warning(f"Porta {svc['port']} ({svc['name']}) está em uso")
        
        if conflicts:
            print("\nDeseja encerrar os processos nessas portas? (s/n): ", end='')
            response = input().strip().lower()
            
            if response == 's':
                for svc in conflicts:
                    if kill_process_on_port(svc['port']):
                        time.sleep(1)
                        if is_port_available(svc['port']):
                            log_success(f"Porta {svc['port']} liberada")
                        else:
                            log_error(f"Não foi possível liberar porta {svc['port']}")
                            if svc['required']:
                                sys.exit(1)
            else:
                log_error("Portas em conflito. Encerrando.")
                sys.exit(1)
        
        log_success("Todas as portas disponíveis")
    
    def start_service(self, service):
        """Inicia um serviço individual."""
        log_info(f"Iniciando {service['name']} (porta {service['port']})...")
        
        try:
            # Criar arquivo de log para o serviço
            log_file = BASE_DIR / f"logs\{service['name'].lower().replace(' ', '_')}.log"
            log_file.parent.mkdir(exist_ok=True)
            
            # Para Windows, usar creationflags
            if sys.platform == 'win32':
                creationflags = subprocess.CREATE_NEW_CONSOLE
                proc = subprocess.Popen(
                    service['cmd'],
                    cwd=service['cwd'],
                    stdout=open(log_file, 'w'),
                    stderr=subprocess.STDOUT,
                    creationflags=creationflags
                )
            else:
                proc = subprocess.Popen(
                    service['cmd'],
                    cwd=service['cwd'],
                    stdout=open(log_file, 'w'),
                    stderr=subprocess.STDOUT
                )
            
            log_success(f"{service['name']} iniciado (PID: {proc.pid})")
            self.processes.append({
                'process': proc,
                'service': service,
                'log_file': log_file
            })
            
            # Aguardar serviço iniciar
            time.sleep(2)
            return True
            
        except Exception as e:
            log_error(f"Falha ao iniciar {service['name']}: {e}")
            return False
    
    def print_summary(self):
        """Imprime resumo de URLs."""
        print("\n" + "="*50)
        log_success("SERVIÇOS INICIADOS")
        print("="*50)
        
        for proc_info in self.processes:
            svc = proc_info['service']
            print(f"\n{Colors.GREEN}{svc['name']}{Colors.RESET}")
            print(f"  URL: {Colors.CYAN}{svc['url']}{Colors.RESET}")
            print(f"  PID: {proc_info['process'].pid}")
            print(f"  Log: {proc_info['log_file']}")
        
        print("\n" + "-"*50)
        print(f"{Colors.YELLOW}Pressione Ctrl+C para encerrar todos os serviços{Colors.RESET}")
        print("="*50 + "\n")
    
    def shutdown(self, signum=None, frame=None):
        """Encerra todos os serviços de forma graceosa."""
        if not self.running:
            return
        
        self.running = False
        print("\n")
        log_info("Encerrando serviços...")
        
        for proc_info in self.processes:
            proc = proc_info['process']
            name = proc_info['service']['name']
            
            try:
                if proc.poll() is None:  # Processo ainda rodando
                    log_info(f"Encerrando {name} (PID: {proc.pid})...")
                    proc.terminate()
                    proc.wait(timeout=5)
                    log_success(f"{name} encerrado")
            except Exception as e:
                log_warning(f"Forçando encerramento de {name}: {e}")
                try:
                    proc.kill()
                except:
                    pass
        
        log_success("Todos os serviços encerrados")
        sys.exit(0)
    
    def run(self):
        """Loop principal de execução."""
        # Registrar handlers de sinal
        signal.signal(signal.SIGINT, self.shutdown)
        if hasattr(signal, 'SIGTERM'):
            signal.signal(signal.SIGTERM, self.shutdown)
        
        # Obter serviços
        services = self.get_services()
        
        # Verificar portas
        self.check_ports(services)
        
        # Iniciar serviços
        for svc in services:
            if not self.start_service(svc):
                if svc['required']:
                    log_error(f"Serviço obrigatório {svc['name']} falhou")
                    self.shutdown()
                    return
        
        # Imprimir resumo
        self.print_summary()
        
        # Monitorar serviços
        try:
            while self.running:
                for proc_info in self.processes:
                    proc = proc_info['process']
                    svc = proc_info['service']
                    
                    if proc.poll() is not None:  # Processo morreu
                        log_warning(f"{svc['name']} parou inesperadamente (código: {proc.returncode})")
                        
                        if svc['required']:
                            log_error("Serviço obrigatório parou. Encerrando.")
                            self.shutdown()
                            return
                        else:
                            # Tentar reiniciar serviços não obrigatórios
                            log_info(f"Tentando reiniciar {svc['name']}...")
                            if self.start_service(svc):
                                self.processes.remove(proc_info)
                
                time.sleep(2)
                
        except KeyboardInterrupt:
            self.shutdown()

def main():
    parser = argparse.ArgumentParser(
        description='Inicia todos os serviços do F.A.R.O.',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Exemplos:
    python run_services.py              # Inicia todos os serviços
    python run_services.py --skip-web   # Inicia apenas server e dashboard
    python run_services.py --skip-analytics  # Inicia server e web
        """
    )
    parser.add_argument(
        '--skip-web', 
        action='store_true',
        help='Pular Web Console'
    )
    parser.add_argument(
        '--skip-analytics',
        action='store_true', 
        help='Pular Analytics Dashboard'
    )
    
    args = parser.parse_args()
    
    print("\n" + "="*50)
    print(f"{Colors.CYAN}  F.A.R.O. - Service Runner{Colors.RESET}")
    print("="*50 + "\n")
    
    manager = ServiceManager(
        skip_web=args.skip_web,
        skip_analytics=args.skip_analytics
    )
    manager.run()

if __name__ == '__main__':
    main()