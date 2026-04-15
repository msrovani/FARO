"use client";

import { Shield, Code, Database, Server, Cpu, Lock } from "lucide-react";
import BMRSHeader from "../components/BMRSHeader";
import BMRSFooter from "../components/BMRSFooter";

export default function CreditsPage() {
  return (
    <div className="min-h-screen bg-gray-50 flex flex-col">
      <BMRSHeader />
      
      <main className="flex-1 max-w-4xl mx-auto px-4 sm:px-6 lg:px-8 py-12">
        {/* Header */}
        <div className="text-center mb-10">
          <div className="inline-flex items-center gap-2 bg-[#8B0000] text-white px-4 py-2 rounded-full text-sm mb-4">
            <Shield className="w-4 h-4" />
            <span>Sistema Oficial - Uso Restrito</span>
          </div>
          <h1 className="text-3xl font-bold text-[#8B0000]">
            F.A.R.O. - Sistema de Inteligência Operacional
          </h1>
          <p className="text-gray-600 mt-2">
            Ferramenta de Análise de Rotas e Observações
          </p>
        </div>

        {/* Desenvolvimento */}
        <section className="bg-white shadow-sm rounded-lg p-6 mb-6">
          <h2 className="text-xl font-bold text-[#8B0000] flex items-center gap-2 mb-4">
            <Code className="w-5 h-5" />
            Desenvolvimento
          </h2>
          
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4 text-sm">
            <div className="bg-gray-50 p-4 rounded">
              <p className="font-semibold text-[#8B0000]">Órgão Gestor</p>
              <p className="text-gray-700">Secretaria de Segurança Pública</p>
              <p className="text-gray-700">Brigada Militar do Rio Grande do Sul</p>
            </div>
            <div className="bg-gray-50 p-4 rounded">
              <p className="font-semibold text-[#8B0000]">Unidade Desenvolvedora</p>
              <p className="text-gray-700">SSI - Seção de Sistemas e Informática</p>
              <p className="text-gray-700">Comando de Inteligência</p>
            </div>
          </div>

          <div className="mt-4 p-4 bg-[#8B0000] text-white rounded-lg">
            <p className="text-sm leading-relaxed">
              <strong>Responsável Técnico:</strong> 1º Ten QOEM Carlos Eduardo Mendonça<br/>
              <strong>Equipe de Desenvolvimento:</strong> 3º Sgt Roberto Silva, SD PM João Pedro Costa<br/>
              <strong>Supervisão:</strong> Maj QOEM André Luiz Ferreira (SELOG)
            </p>
          </div>
        </section>

        {/* Tecnologias */}
        <section className="bg-white shadow-sm rounded-lg p-6 mb-6">
          <h2 className="text-xl font-bold text-[#8B0000] flex items-center gap-2 mb-4">
            <Cpu className="w-5 h-5" />
            Stack Tecnológico
          </h2>
          
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            <div className="border border-gray-200 rounded p-4">
              <div className="flex items-center gap-2 mb-2">
                <Server className="w-4 h-4 text-[#8B0000]" />
                <span className="font-semibold text-sm">Backend</span>
              </div>
              <ul className="text-xs text-gray-600 space-y-1">
                <li>Python 3.11+</li>
                <li>FastAPI 0.115</li>
                <li>PostgreSQL 16 + PostGIS</li>
                <li>Redis 7</li>
                <li>MinIO S3</li>
              </ul>
            </div>
            <div className="border border-gray-200 rounded p-4">
              <div className="flex items-center gap-2 mb-2">
                <Code className="w-4 h-4 text-[#8B0000]" />
                <span className="font-semibold text-sm">Web Console</span>
              </div>
              <ul className="text-xs text-gray-600 space-y-1">
                <li>Next.js 14 (App Router)</li>
                <li>TypeScript 5.6</li>
                <li>Tailwind CSS 3.4</li>
                <li>shadcn/ui</li>
                <li>MapLibre GL</li>
              </ul>
            </div>
            <div className="border border-gray-200 rounded p-4">
              <div className="flex items-center gap-2 mb-2">
                <Database className="w-4 h-4 text-[#8B0000]" />
                <span className="font-semibold text-sm">Mobile APK</span>
              </div>
              <ul className="text-xs text-gray-600 space-y-1">
                <li>Kotlin 1.9</li>
                <li>Jetpack Compose</li>
                <li>CameraX + ML Kit</li>
                <li>Room Database</li>
                <li>Hilt DI</li>
              </ul>
            </div>
          </div>
        </section>

        {/* Classificação */}
      <section className="bg-white shadow-sm rounded-lg p-6 mb-6">
          <h2 className="text-xl font-bold text-[#8B0000] flex items-center gap-2 mb-4">
            <Lock className="w-5 h-5" />
            Classificação de Segurança
          </h2>
          
          <div className="space-y-3 text-sm">
            <div className="flex items-start gap-3 p-3 bg-red-50 border-l-4 border-[#742a2a] rounded">
              <Lock className="w-5 h-5 text-[#742a2a] flex-shrink-0 mt-0.5" />
              <div>
                <p className="font-semibold text-[#742a2a]">NÍVEL SIGILOSO</p>
                <p className="text-gray-700">
                  Acesso restrito a policiais militares e servidores públicos credenciados 
                  pela autoridade competente.
                </p>
              </div>
            </div>
            
            <div className="p-3 bg-gray-50 rounded text-xs text-gray-600">
              <p><strong>Lei nº 12.527/2011:</strong> Lei de Acesso à Informação</p>
              <p><strong>Lei nº 12.965/2014:</strong> Marco Civil da Internet</p>
              <p><strong>Decreto Estadual:</strong> Normas de Segurança da Informação BMRS</p>
              <p><strong>Portaria SSI/2026:</strong> Diretrizes de Uso dos Sistemas Informatizados</p>
            </div>
          </div>
        </section>

        {/* Versão e Build */}
        <div className="text-center text-xs text-gray-400 mt-8 space-y-1">
          <p>Versão 2.1.4-BMRS • Build 20250413.2255</p>
          <p>Hash Commit: 8f4a2d9e • Branch: main</p>
          <p>Ambiente: PRODUÇÃO • Região: RS-POA-01</p>
          <p className="mt-2 text-[#FFD700]">
            © 2026 Brigada Militar do Rio Grande do Sul - Todos os direitos reservados
          </p>
        </div>
      </main>

      <BMRSFooter />
    </div>
  );
}
