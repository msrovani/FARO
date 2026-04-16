"use client";

import { useState, useEffect } from "react";
import { ConsoleShell } from "../components/console-shell";
import { 
  Shield, 
  Cpu, 
  Users, 
  Target, 
  Lock, 
  Award, 
  Star, 
  ChevronRight,
  Zap,
  Sword,
  Search
} from "lucide-react";

export default function AboutPage() {
  const [clicks, setClicks] = useState(0);
  const [easterEgg, setEasterEgg] = useState(false);
  const [mounted, setMounted] = useState(false);

  useEffect(() => {
    setMounted(true);
  }, []);

  const handleUnitClick = () => {
    const newClicks = clicks + 1;
    setClicks(newClicks);
    if (newClicks === 3) {
      setEasterEgg(true);
      // Reset after a while
      setTimeout(() => {
        setEasterEgg(false);
        setClicks(0);
      }, 10000);
    }
  };

  if (!mounted) return null;

  return (
    <ConsoleShell title="Sobre o Projeto" subtitle="Gênese, Liderança e Engenharia do F.A.R.O.">
      <div className="relative max-w-6xl mx-auto space-y-12 pb-20">
        
        {/* Easter Egg Overlay: Regimento do Planalto */}
        {easterEgg && (
          <div className="fixed inset-0 z-50 bg-[#004225]/40 backdrop-blur-xl pointer-events-none flex items-center justify-center overflow-hidden animate-in fade-in duration-500">
            <div className="absolute inset-0 opacity-20">
              <div className="grid grid-cols-6 gap-8 text-[14px] text-white font-mono leading-none p-10">
                {Array.from({ length: 200 }).map((_, i) => (
                  <div key={i} className="animate-pulse flex items-center gap-2" style={{ animationDelay: `${i * 30}ms` }}>
                    <Star className="h-3 w-3 text-[#FFD700]" />
                    {["ITARARÉ", "RIBEIRÃO", "ITAPORANGA", "DISCIPLINA"][i % 4]}
                  </div>
                ))}
              </div>
            </div>
            <div className="text-center space-y-8 animate-in zoom-in duration-1000 bg-white/95 p-20 rounded-[5rem] shadow-[0_0_100px_rgba(255,215,0,0.3)] border-[12px] border-[#FFD700] relative">
              <div className="absolute -top-12 left-1/2 -translate-x-1/2 bg-[#8B0000] text-[#FFD700] px-10 py-3 rounded-full font-black text-xl border-4 border-[#FFD700] shadow-xl">
                7 DE OUTUBRO DE 1930
              </div>
              
              <div className="relative inline-block scale-125 mb-6">
                <img 
                  src="https://www.brigadamilitar.rs.gov.br/upload/recortes/201910/25174513_15948_GDO.jpg" 
                  alt="Brasão Oficial 3º RPMon"
                  className="h-64 h-64 object-contain drop-shadow-[0_20px_20px_rgba(0,0,0,0.3)]"
                />
              </div>

              <div className="space-y-4">
                <h2 className="text-7xl font-black italic tracking-tighter text-[#8B0000] drop-shadow-sm">
                  REGIMENTO <br/> CORONEL PELEGRINO
                </h2>
                <div className="flex flex-col items-center gap-2">
                  <div className="h-[3px] w-48 bg-gradient-to-r from-transparent via-[#FFD700] to-transparent" />
                  <p className="text-[#004225] text-3xl font-black tracking-[0.4em] uppercase">
                    PLANALTO
                  </p>
                  <p className="text-[#8B0000] text-lg font-bold italic tracking-widest mt-2">
                    "DISCIPLINA PRAESIDIUM CIVITATIS"
                  </p>
                </div>
              </div>

              <div className="flex justify-center gap-6 pt-8">
                {["CAVALARIA", "PASSO FUNDO", "BMRS", "SSO"].map((tag) => (
                  <span key={tag} className="px-6 py-3 bg-[#004225] text-[#FFD700] text-sm font-black border-2 border-[#FFD700] skew-x-[-15deg] shadow-lg">
                    {tag}
                  </span>
                ))}
              </div>
            </div>
          </div>
        )}

        {/* Hero Section: The Vision */}
        <section className="relative overflow-hidden rounded-[3rem] bg-gradient-to-br from-[#8B0000] via-[#5C0000] to-[#004225] p-16 text-white shadow-2xl border-b-8 border-[#FFD700]">
          <div className="absolute top-0 right-0 p-12 opacity-15 overflow-hidden">
            <img 
              src="https://www.brigadamilitar.rs.gov.br/upload/recortes/201910/25174513_15948_GDO.jpg" 
              alt="" 
              className="h-96 w-96 object-contain rotate-12"
            />
          </div>
          <div className="relative z-10 max-w-4xl">
            <div className="inline-flex items-center gap-3 rounded-full bg-[#FFD700] px-6 py-2 text-xs font-black text-[#8B0000] mb-8 shadow-xl uppercase tracking-[0.2em]">
              <Award className="h-4 w-4" />
              Regimento Coronel Pelegrino
            </div>
            <h1 className="text-7xl font-black tracking-tighter mb-8 leading-[0.85]">
              F.A.R.O. <br/>
              <span className="text-3xl font-light text-[#FFD700]">Ferramenta de Análise de Rotas e Observações</span>
            </h1>
            <p className="text-xl leading-relaxed text-gray-100 max-w-2xl font-medium">
              Desenvolvido no coração do <span onClick={handleUnitClick} className="cursor-pointer text-[#FFD700] font-black uppercase tracking-wider hover:scale-105 inline-block transition-transform duration-300">3º RPMon</span> em Passo Fundo, o FARO personifica o lema institucional: 
              <span className="block mt-4 text-[#FFD700] italic text-2xl font-serif">"A Disciplina é a Defesa do Estado"</span>
            </p>
          </div>
        </section>

        {/* Gallery Section */}
        <section className="space-y-6">
          <div className="flex items-center gap-4 px-4">
            <div className="h-1 flex-1 bg-slate-200" />
            <h2 className="text-sm font-black uppercase tracking-[0.3em] text-slate-400">Registros do Regimento</h2>
            <div className="h-1 flex-1 bg-slate-200" />
          </div>
          <div className="relative group overflow-hidden rounded-[2.5rem] bg-white p-2 shadow-2xl border border-slate-200">
            <img 
              src="https://www.brigadamilitar.rs.gov.br/upload/arquivos/201902/26094942-redesocial-facebook.png" 
              alt="Galeria do 3º RPMon"
              className="w-full h-auto object-cover rounded-[2rem] filter contrast-[1.1] brightness-[1.1]"
            />
            <div className="absolute bottom-10 left-10 right-10 p-8 bg-black/60 backdrop-blur-md rounded-2xl border border-white/20 text-white">
              <h3 className="text-xl font-black uppercase mb-1">Passo Fundo - RS</h3>
              <p className="text-sm text-gray-300 font-medium">Sede do Comando Regional do Planalto • Fundação: 07 de Outubro de 1930</p>
            </div>
          </div>
        </section>

        {/* The Commanders: Leadership */}
        <div className="grid md:grid-cols-2 gap-10 relative">
          
          {/* Commander Card */}
          <div className="group relative rounded-[2.5rem] bg-white p-10 shadow-xl border-t-8 border-[#8B0000] hover:translate-y-[-8px] transition-all duration-500 overflow-hidden">
            <div className="absolute top-0 right-0 p-8 text-slate-100 group-hover:text-[#8B0000]/10 transition-colors">
              <Award className="h-40 w-40" />
            </div>
            <div className="relative z-10">
              <div className="mb-6 inline-flex h-16 w-16 items-center justify-center rounded-3xl bg-[#8B0000]/10 text-[#8B0000]">
                <img 
                  src="https://www.brigadamilitar.rs.gov.br/upload/recortes/201910/25174513_15948_GDO.jpg" 
                  alt="" 
                  className="h-10 w-10 object-contain"
                />
              </div>
              <h3 className="text-xs font-black uppercase tracking-[0.2em] text-[#8B0000] mb-2">Comandante do 3º RPMon</h3>
              <h2 className="text-3xl font-black text-slate-900 mb-6">Ten Cel PM Marcelo Scapin ROVANI</h2>
              <p className="text-base text-slate-600 leading-relaxed mb-8">
                Sob o comando do Ten Cel Rovani, o 3º RPMon consolidou-se como polo de inovação na Brigada Militar. Sua visão estratégica foi o catalisador para a criação do FARO, integrando a mística da Cavalaria com a precisão dos dados.
              </p>
              <div className="flex items-center gap-3 text-xs font-black text-[#8B0000]">
                <div className="h-[2px] w-8 bg-[#8B0000]" />
                LIDERANÇA E ESTRATÉGIA NO PLANALTO
              </div>
            </div>
          </div>

          {/* Developer Card */}
          <div className="group relative rounded-[2rem] bg-slate-900 p-8 shadow-xl border border-slate-800 hover:border-[#FFD700] transition-all duration-500 overflow-hidden text-white">
            <div className="absolute top-0 right-0 p-6 text-slate-800 group-hover:text-white/5 transition-colors">
              <Cpu className="h-32 w-32" />
            </div>
            <div className="relative z-10">
              <div className="mb-4 inline-flex h-12 w-12 items-center justify-center rounded-2xl bg-[#FFD700]/10 text-[#FFD700]">
                <Cpu className="h-6 w-6" />
              </div>
              <h3 className="text-xs font-bold uppercase tracking-[0.2em] text-[#FFD700] mb-1">Tecnologia da Informação - 3º RPMon</h3>
              <h2 className="text-2xl font-black mb-4">Sd Diego POLLIPO</h2>
              <p className="text-sm text-gray-400 leading-relaxed mb-6">
                Arquiteto de sistemas e desenvolvedor principal. Transformou requisitos operacionais complexos em linhas de código eficientes, garantindo que o FARO seja rápido no campo e preciso na inteligência.
              </p>
              <div className="flex items-center gap-2 text-xs font-semibold text-gray-500">
                <Zap className="h-4 w-4" />
                ENGENHARIA DE FULLSTACK & ANALYTICS
              </div>
            </div>
          </div>
        </div>

        {/* Pillars Section */}
        <section className="bg-white rounded-[2rem] p-12 border border-slate-200 shadow-sm overflow-hidden relative">
          <div className="absolute inset-0 opacity-[0.02] pointer-events-none" style={{ backgroundImage: 'radial-gradient(#8B0000 1px, transparent 1px)', backgroundSize: '24px 24px' }} />
          
          <div className="text-center mb-16">
            <h2 className="text-3xl font-black tracking-tight text-slate-900 mb-2">Pilares do Sistema</h2>
            <div className="h-1.5 w-20 bg-[#8B0000] mx-auto rounded-full" />
          </div>

          <div className="grid sm:grid-cols-3 gap-12">
            {[
              { icon: Target, title: "Precisão", desc: "Algoritmos treinados para identificar padrões críticos em milissegundos." },
              { icon: Users, title: "Integração", desc: "Elo indissolúvel entre a inteligência central e a ponta da linha." },
              { icon: Lock, title: "Sigilo", desc: "Arquitetura blindada sob os mais rigorosos protocolos governamentais." }
            ].map((p, i) => (
              <div key={i} className="text-center space-y-4">
                <div className="inline-flex h-16 w-16 items-center justify-center rounded-3xl bg-slate-50 text-[#8B0000] mb-2 border border-slate-100 group-hover:bg-[#8B0000] group-hover:text-white transition-all">
                  <p.icon className="h-8 w-8" />
                </div>
                <h4 className="text-lg font-bold text-slate-900">{p.title}</h4>
                <p className="text-sm text-slate-500 leading-relaxed">{p.desc}</p>
              </div>
            ))}
          </div>
        </section>

        {/* Unit Identity Footer */}
        <div className="flex items-center justify-center gap-8 py-10 opacity-30 grayscale hover:grayscale-0 transition-all duration-700">
          <div className="flex items-center gap-3">
            <Sword className="h-8 w-8" />
            <span className="text-xl font-black italic tracking-tighter">3º RPMon</span>
          </div>
          <div className="h-8 w-[1px] bg-slate-400" />
          <div className="flex items-center gap-3">
            <Shield className="h-8 w-8" />
            <span className="text-xl font-black italic tracking-tighter">BRIGADA MILITAR</span>
          </div>
        </div>

      </div>
    </ConsoleShell>
  );
}
