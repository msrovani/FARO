"use client";

import { Shield, Lock, FileText } from "lucide-react";

export default function BMRSFooter() {
  return (
    <footer className="bg-[#8B0000] text-white border-t-4 border-[#FFD700]">
      {/* Seção de alerta de segurança */}
      <div className="bg-[#742a2a] py-2 px-4">
        <div className="max-w-7xl mx-auto flex items-center justify-center gap-4 text-sm">
          <Lock className="w-4 h-4" />
          <span className="font-semibold">
            ATENÇÃO: Sistema sujeito a monitoramento e auditoria conforme Lei nº 12.965/2014 (Marco Civil da Internet)
          </span>
          <Lock className="w-4 h-4" />
        </div>
      </div>
      
      {/* Conteúdo principal */}
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-6">
        <div className="grid grid-cols-1 md:grid-cols-4 gap-6 text-sm">
          {/* Identidade institucional */}
          <div className="col-span-1 md:col-span-2">
            <div className="flex items-center gap-3 mb-3">
              <Shield className="w-6 h-6 text-[#d4af37]" />
              <span className="font-bold text-lg">BMRS - F.A.R.O.</span>
            </div>
            <p className="text-gray-300 text-xs leading-relaxed max-w-md">
              Sistema desenvolvido pela Secretaria de Segurança Pública 
              da Brigada Militar do Rio Grande do Sul para inteligência operacional 
              e análise de dados estratégicos em operações de segurança pública.
            </p>
            <div className="mt-3 text-xs text-gray-400">
              <p>SSI - Seção de Sistemas e Informática</p>
              <p>Comando de Inteligência e Operações</p>
            </div>
          </div>
          
          {/* Links institucionais */}
          <div>
            <h4 className="font-semibold text-[#d4af37] mb-3 uppercase text-xs tracking-wider">
              Documentação
            </h4>
            <ul className="space-y-2 text-xs">
              <li>
                <a href="/terms" className="text-gray-300 hover:text-white flex items-center gap-1">
                  <FileText className="w-3 h-3" />
                  Termos de Uso Oficial
                </a>
              </li>
              <li>
                <a href="/security" className="text-gray-300 hover:text-white flex items-center gap-1">
                  <Lock className="w-3 h-3" />
                  Diretrizes de Segurança
                </a>
              </li>
              <li>
                <a href="/credits" className="text-gray-300 hover:text-white flex items-center gap-1">
                  <Shield className="w-3 h-3" />
                  Créditos do Sistema
                </a>
              </li>
              <li>
                <a href="/manual" className="text-gray-300 hover:text-white flex items-center gap-1">
                  <FileText className="w-3 h-3" />
                  Manual do Operador
                </a>
              </li>
            </ul>
          </div>
          
          {/* Informações técnicas */}
          <div>
            <h4 className="font-semibold text-[#d4af37] mb-3 uppercase text-xs tracking-wider">
              Sistema
            </h4>
            <ul className="space-y-1 text-xs text-gray-300">
              <li className="flex justify-between">
                <span>Versão:</span>
                <span className="text-[#FFD700]">2.1.4-BMRS</span>
              </li>
              <li className="flex justify-between">
                <span>Build:</span>
                <span>20250413.2255</span>
              </li>
              <li className="flex justify-between">
                <span>Ambiente:</span>
                <span className="text-green-400">PRODUÇÃO</span>
              </li>
              <li className="flex justify-between">
                <span>Certificação:</span>
                <span className="text-[#d4af37]">ICP-Brasil</span>
              </li>
            </ul>
          </div>
        </div>
        
        {/* Barra inferior */}
        <div className="mt-6 pt-4 border-t border-[#5C0000] flex flex-col md:flex-row justify-between items-center gap-4 text-xs text-gray-400">
          <div className="flex items-center gap-4">
            <span>© 2026 Brigada Militar do Rio Grande do Sul</span>
            <span className="hidden md:inline">|</span>
            <span>Todos os direitos reservados</span>
          </div>
          <div className="flex items-center gap-4">
            <span>Desenvolvimento: SSI/BMRS</span>
            <span className="hidden md:inline">|</span>
            <span className="text-[#FFD700]">Sistema Oficial de Uso Restrito</span>
          </div>
        </div>
      </div>
    </footer>
  );
}
