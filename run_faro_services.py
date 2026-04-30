#!/usr/bin/env python3
"""
F.A.R.O. Service Runner (Alternative)

Versão simplificada para iniciar serviços com consoles visíveis.
Útil para desenvolvimento e debugging.

Uso:
    python run_faro_services.py
    python run_faro_services.py --skip-web
"""

import subprocess
import sys
import os
import time
import signal
import argparse
from pathlib import Path

# Detectar diretório base automaticamente
BASE = Path(__file__).parent.resolve()
PYTHON = sys.executable

class Colors:
    GREEN = '\033[92m'
    CYAN = '\033[96m'
    YELLOW = '\033[93m'
    RESET = '\033[0m'

def start_service(cmd, name, cwd):
    """Inicia um serviço em uma nova janela de console."""
    print(f"{Colors.CYAN}[START] {name}{Colors.RESET}")
    print(f"  Command: {cmd}")
    print(f"  Working: {cwd}")
    
    try:
        proc = subprocess.Popen(
            cmd,
            shell=True,
            cwd=cwd,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            creationflags=subprocess.CREATE_NEW_CONSOLE
        )
        print(f"  {Colors.GREEN}PID: {proc.pid}{Colors.RESET}")
        return proc
    except Exception as e:
        print(f"  ❌ Erro: {e}")
        return None

def main():
    parser = argparse.ArgumentParser(description='F.A.R.O. Service Runner (Simplified)')
    parser.add_argument('--skip-web', action='store_true', help='Pular Web Console')
    parser.add_argument('--skip-analytics', action='store_true', help='Pular Analytics Dashboard')
    args = parser.parse_args()
    
    print(f"\n{Colors.CYAN}========================================{Colors.RESET}")
    print(f"{Colors.CYAN}  F.A.R.O. - Service Runner{Colors.RESET}")
    print(f"{Colors.CYAN}========================================{Colors.RESET}\n")
    
    services = [
        (f'"{PYTHON}" -m uvicorn app.main:app --host 127.0.0.1 --port 8000', 
         "Server Core (8000)", BASE / "server-core"),
    ]
    
    if not args.skip_analytics:
        services.append(
            (f'"{PYTHON}" analytics-dashboard/app.py', 
             "Dashboard (9002)", f"{BASE}/analytics-dashboard")
        )
    
    if not args.skip_web:
        services.append(
            ('npm run dev', 
             "Web Console (3000)", BASE / "web-intelligence-console")
        )
    
    procs = []
    for cmd, name, cwd in services:
        proc = start_service(cmd, name, cwd)
        if proc:
            procs.append((proc, name))
            time.sleep(2)
    
    print(f"\n{Colors.GREEN}[READY] Serviços iniciados:{Colors.RESET}")
    print(f"  Server Core:       {Colors.CYAN}http://127.0.0.1:8000{Colors.RESET}")
    if not args.skip_analytics:
        print(f"  Analytics Dashboard: {Colors.CYAN}http://localhost:9002/dashboard{Colors.RESET}")
    if not args.skip_web:
        print(f"  Web Console:       {Colors.CYAN}http://localhost:3000{Colors.RESET}")
    
    print(f"\n{Colors.YELLOW}Pressione Ctrl+C para encerrar...{Colors.RESET}\n")
    
    def shutdown(signum=None, frame=None):
        print(f"\n{Colors.CYAN}[STOP] Encerrando serviços...{Colors.RESET}")
        for proc, name in procs:
            try:
                if proc.poll() is None:
                    proc.terminate()
                    print(f"  {Colors.GREEN}[STOP] {name}{Colors.RESET}")
            except:
                pass
        sys.exit(0)
    
    signal.signal(signal.SIGINT, shutdown)
    
    try:
        while True:
            time.sleep(1)
            # Verificar se algum processo morreu
            for i, (proc, name) in enumerate(procs):
                if proc.poll() is not None:
                    print(f"\n{Colors.YELLOW}[WARN] {name} parou (código: {proc.returncode}){Colors.RESET}")
    except KeyboardInterrupt:
        shutdown()

if __name__ == '__main__':
    main()