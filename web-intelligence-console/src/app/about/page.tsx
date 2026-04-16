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
          <div className="fixed inset-0 z-50 bg-[#c6f6d5]/10 backdrop-blur-md pointer-events-none flex items-center justify-center overflow-hidden animate-in fade-in duration-500">
            <div className="absolute inset-0 opacity-10">
              <div className="grid grid-cols-8 gap-4 text-[12px] text-slate-900 font-mono leading-none p-10">
                {Array.from({ length: 400 }).map((_, i) => (
                  <div key={i} className="animate-pulse flex items-center gap-1" style={{ animationDelay: `${i * 20}ms` }}>
                    <Star className="h-2 w-2" />
                    {["ITARARÉ", "RIBEIRÃO", "ITAPORANGA", "PELEGRINO"][i % 4]}
                  </div>
                ))}
              </div>
            </div>
            <div className="text-center space-y-8 animate-in zoom-in duration-700 bg-white/90 p-16 rounded-[4rem] shadow-2xl border-8 border-[#FFD700]">
              <div className="relative inline-block">
                <Shield className="h-40 w-40 text-[#8B0000] mx-auto animate-pulse" />
                <Award className="absolute -bottom-4 -right-4 h-16 w-16 text-[#FFD700] animate-bounce" />
              </div>
              <div className="space-y-2">
                <h2 className="text-7xl font-black italic tracking-tighter text-[#8B0000]">
                  REGIMENTO CORONEL PELEGRINO
                </h2>
                <div className="flex items-center justify-center gap-6">
                  <div className="h-[2px] w-20 bg-[#FFD700]" />
                  <p className="text-[#8B0000] text-2xl font-black tracking-[0.3em] uppercase">
                    O REGIMENTO DO PLANALTO
                  </p>
                  <div className="h-[2px] w-20 bg-[#FFD700]" />
                </div>
              </div>
              <div className="flex justify-center gap-12 pt-4">
                {["1930", "PASSO FUNDO", "BMRS"].map((tag) => (
                  <span key={tag} className="px-4 py-2 bg-[#8B0000] text-white text-sm font-bold skew-x-[-12deg]">
                    {tag}
                  </span>
                ))}
              </div>
            </div>
          </div>
        )}

        {/* Hero Section: The Vision */}
        <section className="relative overflow-hidden rounded-[2.5rem] bg-gradient-to-br from-[#8B0000] to-[#5C0000] p-12 text-white shadow-2xl border-4 border-white/10">
          <div className="absolute top-0 right-0 p-8 opacity-10">
            <Shield className="h-64 w-64" />
          </div>
          <div className="relative z-10 max-w-3xl">
            <div className="inline-flex items-center gap-2 rounded-full bg-[#FFD700]/20 px-4 py-2 text-sm font-bold text-[#FFD700] mb-6 border border-[#FFD700]/30">
              <Award className="h-4 w-4" />
              REGIMENTO CORONEL PELEGRINO
            </div>
            <h1 className="text-6xl font-black tracking-tighter mb-6 leading-[0.9]">
              F.A.R.O. <br/>
              <span className="text-3xl font-light opacity-80">Ferramenta de Análise e Resposta Operacional</span>
            </h1>
            <p className="text-lg leading-relaxed text-gray-200">
              Nascido no âmago do <span onClick={handleUnitClick} className="cursor-pointer underline decoration-[#FFD700] underline-offset-4 hover:text-[#FFD700] transition-colors font-bold uppercase tracking-wide">3º RPMon</span>, o F.A.R.O. não é apenas um software; 
              é o braço tecnológico da força pública. Uma plataforma concebida para antecipar o crime, integrar a inteligência e proteger quem nos protege nas ruas.
            </p>
          </div>
        </section>

        {/* The Commanders: Leadership */}
        <div className="grid md:grid-cols-2 gap-8 relative">
          
          {/* Commander Card */}
          <div className="group relative rounded-[2rem] bg-white p-8 shadow-xl border border-slate-200 hover:border-[#8B0000] transition-all duration-500 overflow-hidden">
            <div className="absolute top-0 right-0 p-6 text-slate-100 group-hover:text-[#8B0000]/5 transition-colors">
              <Award className="h-32 w-32" />
            </div>
            <div className="relative z-10">
              <div className="mb-4 inline-flex h-12 w-12 items-center justify-center rounded-2xl bg-[#8B0000]/10 text-[#8B0000]">
                <Shield className="h-6 w-6" />
              </div>
              <h3 className="text-xs font-bold uppercase tracking-[0.2em] text-[#8B0000] mb-1">Comandante do 3º RPMon</h3>
              <h2 className="text-2xl font-black text-slate-900 mb-4">Ten Cel PM Marcelo Scapin ROVANI</h2>
              <p className="text-sm text-slate-600 leading-relaxed mb-6">
                Liderança estratégica e patrono intelectual do sistema. Sob seu comando, o Regimento abraçou a transformação digital, elevando a segurança pública ao patamar da inteligência baseada em dados.
              </p>
              <div className="flex items-center gap-2 text-xs font-semibold text-slate-400">
                <ChevronRight className="h-4 w-4" />
                VISÃO ESTRATÉGICA NO PLANALTO
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
