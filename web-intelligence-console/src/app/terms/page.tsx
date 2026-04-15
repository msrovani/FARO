"use client";

import { Shield, Lock, FileText, AlertTriangle, CheckCircle } from "lucide-react";
import BMRSHeader from "../components/BMRSHeader";
import BMRSFooter from "../components/BMRSFooter";

export default function TermsPage() {
  return (
    <div className="min-h-screen bg-gray-50 flex flex-col">
      <BMRSHeader />
      
      <main className="flex-1 max-w-4xl mx-auto px-4 sm:px-6 lg:px-8 py-12">
        {/* Cabeçalho do documento */}
        <div className="text-center mb-8">
          <div className="flex items-center justify-center gap-2 text-[#8B0000] mb-2">
            <Shield className="w-6 h-6" />
            <span className="text-sm font-semibold tracking-wider">TERMO DE USO OFICIAL</span>
          </div>
          <h1 className="text-2xl font-bold text-[#8B0000]">
            TERMO DE RESPONSABILIDADE E USO DO SISTEMA F.A.R.O.
          </h1>
          <p className="text-sm text-gray-500 mt-2">
            Brigada Militar do Rio Grande do Sul - SSI/BMRS
          </p>
          <div className="text-xs text-gray-400 mt-1">
            Documento nº SSI/2026/00047 • Atualizado em 13/04/2026
          </div>
        </div>

        {/* Alerta de segurança */}
        <div className="bg-[#742a2a] text-white p-4 rounded-lg mb-8 flex items-start gap-3">
          <AlertTriangle className="w-5 h-5 flex-shrink-0 mt-0.5" />
          <div>
            <p className="font-semibold text-sm">ATENÇÃO - SISTEMA CLASSIFICADO</p>
            <p className="text-xs mt-1 text-red-100">
              O acesso não autorizado, uso indevido, tentativa de violação ou divulgação 
              de informações contidas neste sistema constitui crime nos termos da Lei 
              nº 12.737/2012 (Lei Carolina Dieckmann) e Lei nº 7.960/1989 (Segurança do Estado).
            </p>
          </div>
        </div>

        {/* Conteúdo */}
        <div className="bg-white shadow-sm rounded-lg p-8 space-y-6">
          <section>
            <h2 className="text-lg font-bold text-[#8B0000] flex items-center gap-2 mb-3">
              <FileText className="w-5 h-5" />
              1. DISPOSIÇÕES GERAIS
            </h2>
            <p className="text-sm text-gray-700 leading-relaxed">
              O presente Termo de Responsabilidade regula o acesso e uso do Sistema 
              <strong> F.A.R.O. (Ferramenta de Análise de Rotas e Observações)</strong>, 
              desenvolvido pela <strong>Secretaria de Segurança Pública da 
              Brigada Militar do Rio Grande do Sul</strong>, doravante denominada BMRS, 
              através da <strong>Seção de Sistemas e Informática (SSI)</strong>.
            </p>
          </section>

          <section>
            <h2 className="text-lg font-bold text-[#8B0000] flex items-center gap-2 mb-3">
              <Lock className="w-5 h-5" />
              2. CLASSIFICAÇÃO E SIGILO
            </h2>
            <div className="bg-gray-50 p-4 rounded border-l-4 border-[#742a2a]">
              <p className="text-sm text-gray-700 leading-relaxed">
                As informações contidas no sistema F.A.R.O. são classificadas como 
                <strong> SIGILOSAS</strong>, nos termos da Lei de Acesso à Informação 
                (Lei nº 12.527/2011), e seu acesso é restrito a servidores públicos 
                devidamente autorizados e credenciados pela autoridade competente.
              </p>
            </div>
          </section>

          <section>
            <h2 className="text-lg font-bold text-[#8B0000] flex items-center gap-2 mb-3">
              <CheckCircle className="w-5 h-5" />
              3. OBRIGAÇÕES DO USUÁRIO
            </h2>
            <ul className="text-sm text-gray-700 space-y-2 list-disc pl-5">
              <li>Manter sigilo absoluto das informações acessadas</li>
              <li>Não compartilhar credenciais de acesso (matrícula/senha)</li>
              <li>Registrar apenas informações verídicas e oficiais</li>
              <li>Utilizar o sistema exclusivamente para fins institucionais</li>
              <li>Preservar a cadeia de custódia das evidências registradas</li>
              <li>Reportar imediatamente qualquer anomalia de segurança</li>
              <li>Bloquear a estação ao se ausentar</li>
            </ul>
          </section>

          <section>
            <h2 className="text-lg font-bold text-[#8B0000] flex items-center gap-2 mb-3">
              <Shield className="w-5 h-5" />
              4. RESPONSABILIDADE DISCIPLINAR E JURÍDICA
            </h2>
            <p className="text-sm text-gray-700 leading-relaxed">
              O descumprimento das disposições deste Termo sujeitará o usuário às 
              sanções disciplinares previstas na legislação específica, bem como 
              às responsabilidades civil e penal cabíveis, conforme disposto na 
              Lei nº 13.869/2019 (Abuso de Autoridade) e Decreto-Lei nº 667/1969 
              (Crimes de Segurança do Estado).
            </p>
          </section>

          <section>
            <h2 className="text-lg font-bold text-[#8B0000] flex items-center gap-2 mb-3">
              <FileText className="w-5 h-5" />
              5. DECLARAÇÃO DE CIÊNCIA
            </h2>
            <div className="bg-[#8B0000] text-white p-4 rounded-lg">
              <p className="text-sm leading-relaxed">
                DECLARO, sob as penas da lei, que li e compreendi integralmente o 
                presente Termo de Responsabilidade, assumindo o compromisso de utilizar 
                o sistema F.A.R.O. em estrita conformidade com as normas institucionais 
                e legislação vigente.
              </p>
            </div>
          </section>

          {/* Assinatura digital simulada */}
          <div className="border-t pt-6 mt-8">
            <div className="grid grid-cols-1 md:grid-cols-2 gap-8">
              <div>
                <p className="text-xs text-gray-500 mb-1">Assinatura Digital ICP-Brasil:</p>
                <div className="bg-gray-100 p-3 rounded font-mono text-xs text-gray-600 break-all">
                  3F:A2:9C:84:E7:11:DD:09:77:8A:91:B3:4C:F2:55:E8:99:01:33:7D:12:A4:5B:...
                </div>
                <p className="text-xs text-gray-400 mt-1">Certificado válido até 13/04/2027</p>
              </div>
              <div className="text-right">
                <p className="text-xs text-gray-500">Usuário:</p>
                <p className="font-semibold text-sm">BMRS-8847</p>
                <p className="text-xs text-gray-400">Aceite em 13/04/2026 22:45:33</p>
                <p className="text-xs text-gray-400">IP: 10.243.17.82 • Estação: SSI-WS-47</p>
              </div>
            </div>
          </div>
        </div>
      </main>

      <BMRSFooter />
    </div>
  );
}
