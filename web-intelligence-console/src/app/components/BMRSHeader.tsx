"use client";

import { Shield, Lock, AlertTriangle } from "lucide-react";

export default function BMRSHeader() {
  return (
    <header className="bg-[#8B0000] text-white border-b-4 border-[#FFD700]">
      {/* Barra de segurança superior */}
      <div className="bg-[#2d3748] text-xs py-1 px-4 text-center">
        <span className="text-[#fc8181] font-semibold flex items-center justify-center gap-2">
          <Lock className="w-3 h-3" />
          SISTEMA CLASSIFICADO - USO OFICIAL RESTRITO - BMRS/SSI
          <Shield className="w-3 h-3" />
        </span>
      </div>
      
      {/* Header principal */}
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="flex justify-between items-center h-20">
          {/* Lado esquerdo - Brasão e identidade */}
          <div className="flex items-center gap-4">
            {/* Brasão BMRS - representação simplificada */}
            <div className="relative w-14 h-14 bg-white rounded-full flex items-center justify-center border-4 border-[#FFD700]">
              <Shield className="w-8 h-8 text-[#8B0000]" />
              <div className="absolute -bottom-1 -right-1 w-5 h-5 bg-[#FFD700] rounded-full flex items-center justify-center text-[10px] font-bold text-[#8B0000]">
                RS
              </div>
            </div>
            
            <div className="flex flex-col">
              <h1 className="text-xl font-bold tracking-wider">
                BRIGADA MILITAR
              </h1>
              <span className="text-xs text-[#FFD700] tracking-widest uppercase">
                Rio Grande do Sul
              </span>
              <span className="text-[10px] text-gray-300 mt-0.5">
                Secretaria de Segurança Pública
              </span>
            </div>
          </div>
          
          {/* Centro - Sistema */}
          <div className="hidden md:flex flex-col items-center">
            <div className="flex items-center gap-2">
              <AlertTriangle className="w-5 h-5 text-[#d4af37]" />
              <span className="text-lg font-bold tracking-wide text-[#FFD700]">
                F.A.R.O.
              </span>
            </div>
            <span className="text-xs text-gray-300">
              Ferramenta de Análise de Rotas e Observações
            </span>
            <span className="text-[10px] text-gray-400 mt-0.5">
              Sistema de Inteligência Operacional
            </span>
          </div>
          
          {/* Lado direito - Info usuário e classificação */}
          <div className="flex flex-col items-end gap-1">
            <div className="flex items-center gap-2 bg-[#2d3748] px-3 py-1.5 rounded text-xs">
              <span className="text-gray-400">Matrícula:</span>
              <span className="font-semibold text-[#FFD700]">BMRS-8847</span>
            </div>
            <div className="flex items-center gap-2 bg-[#742a2a] px-3 py-1 rounded text-[10px]">
              <Lock className="w-3 h-3" />
              <span>NÍVEL SIGILOSO - CONFIDENCIAL</span>
            </div>
            <span className="text-[10px] text-gray-400">
              Último acesso: 13/04/2026 22:45
            </span>
          </div>
        </div>
      </div>
      
      {/* Barra de navegação institucional */}
      <nav className="bg-[#5C0000] border-t border-[#8B0000]">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex items-center space-x-8 h-10 text-sm">
            <a href="/" className="text-[#FFD700] hover:text-white transition-colors flex items-center gap-1">
              <Shield className="w-4 h-4" />
              Dashboard
            </a>
            <a href="/queue" className="text-gray-300 hover:text-white transition-colors">
              Fila de Triagem
            </a>
            <a href="/observations" className="text-gray-300 hover:text-white transition-colors">
              Observações
            </a>
            <a href="/routes" className="text-gray-300 hover:text-white transition-colors">
              Análise de Rotas
            </a>
            <a href="/alerts" className="text-gray-300 hover:text-white transition-colors">
              Alertas
            </a>
            <div className="flex-1" />
            <a href="/terms" className="text-gray-400 hover:text-white transition-colors text-xs">
              Termos de Uso
            </a>
            <a href="/credits" className="text-gray-400 hover:text-white transition-colors text-xs">
              Créditos
            </a>
          </div>
        </div>
      </nav>
    </header>
  );
}
