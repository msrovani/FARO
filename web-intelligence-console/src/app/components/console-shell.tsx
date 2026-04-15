"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import { BriefcaseBusiness, Car, FileSearch, LayoutDashboard, Lock, Map, MessageSquare, Radar, ScrollText, Shield, Workflow } from "lucide-react";

const NAV_ITEMS = [
  { href: "/", label: "Mesa Analítica", icon: LayoutDashboard },
  { href: "/queue", label: "Fila de Triagem", icon: Workflow },
  { href: "/routes", label: "Rotas e Recorrência", icon: Map },
  { href: "/convoys", label: "Comboio", icon: Car },
  { href: "/roaming", label: "Roaming", icon: Radar },
  { href: "/sensitive-assets", label: "Ativo Sensível", icon: Shield },
  { href: "/feedback", label: "Feedback", icon: MessageSquare },
  { href: "/watchlist", label: "Watchlist", icon: Radar },
  { href: "/cases", label: "Casos", icon: BriefcaseBusiness },
  { href: "/audit", label: "Auditoria", icon: ScrollText },
];

export function ConsoleShell({
  title,
  subtitle,
  children,
}: {
  title: string;
  subtitle: string;
  children: React.ReactNode;
}) {
  const pathname = usePathname();

  return (
    <div className="min-h-screen bg-[#eef1f4] text-slate-900 relative">
      {/* Marca d'água de classificação */}
      <div className="fixed inset-0 pointer-events-none z-0 overflow-hidden opacity-[0.03]">
        <div className="absolute inset-0 flex items-center justify-center rotate-[-45deg]">
          <span className="text-[200px] font-bold tracking-widest text-[#8B0000] select-none whitespace-nowrap">
            SIGILOSO • BMRS • SIGILOSO • BMRS • SIGILOSO
          </span>
        </div>
      </div>

      <div className="grid min-h-screen lg:grid-cols-[280px_1fr] relative z-10">
        {/* Sidebar BMRS */}
        <aside className="border-r border-[#5C0000] bg-[#8B0000] px-5 py-6 text-white">
          {/* Brasão BMRS */}
          <div className="flex items-center gap-3 pb-4 border-b border-[#5C0000]">
            <div className="rounded-2xl bg-white p-2 text-[#8B0000] border-2 border-[#FFD700]">
              <Shield className="h-6 w-6" />
            </div>
            <div>
              <div className="text-lg font-bold tracking-wide text-white">F.A.R.O.</div>
              <div className="text-[10px] uppercase tracking-[0.2em] text-[#FFD700]">
                BRIGADA MILITAR RS
              </div>
            </div>
          </div>

          {/* Alerta de classificação */}
          <div className="mt-4 rounded-xl border border-[#742a2a] bg-[#742a2a]/20 p-3">
            <div className="flex items-center gap-2 text-xs font-semibold text-[#ff6b6b]">
              <Lock className="h-3 w-3" />
              SISTEMA CLASSIFICADO
            </div>
            <p className="mt-1 text-[10px] text-gray-300 leading-relaxed">
              Uso restrito a policiais militares credenciados. 
              Lei nº 12.527/2011.
            </p>
          </div>

          <nav className="mt-6 space-y-1">
            {NAV_ITEMS.map((item) => {
              const selected = pathname === item.href;
              const Icon = item.icon;

              return (
                <Link
                  key={item.href}
                  href={item.href}
                  className={`flex items-center gap-3 rounded-xl px-4 py-3 text-sm transition font-medium ${
                    selected
                      ? "bg-[#FFD700] text-[#8B0000] shadow-lg"
                      : "text-gray-200 hover:bg-[#5C0000] hover:text-white"
                  }`}
                >
                  <Icon className="h-4 w-4" />
                  {item.label}
                </Link>
              );
            })}
          </nav>

          {/* Informações do sistema */}
          <div className="mt-auto pt-6 border-t border-[#5C0000]">
            <div className="rounded-xl border border-dashed border-[#5C0000] p-3 bg-[#5C0000]">
              <div className="text-xs font-semibold text-[#FFD700]">SSI/BMRS</div>
              <div className="mt-1 text-[10px] text-gray-400">
                Versão 2.1.4 • Build 20250413
              </div>
              <div className="mt-1 text-[10px] text-gray-500">
                Ambiente: PRODUÇÃO
              </div>
            </div>
          </div>
        </aside>

        {/* Conteúdo principal */}
        <div className="flex min-h-screen flex-col">
          {/* Header com identidade BMRS */}
          <header className="border-b border-slate-200 bg-white/95 px-6 py-4 backdrop-blur">
            <div className="flex flex-col gap-2 lg:flex-row lg:items-end lg:justify-between">
              <div>
                <div className="flex items-center gap-2 text-[#8B0000] text-sm font-semibold mb-1">
                  <Shield className="h-4 w-4" />
                  <span className="tracking-wider">INTELIGÊNCIA OPERACIONAL</span>
                </div>
                <h1 className="text-2xl font-bold tracking-tight text-slate-900">{title}</h1>
                <p className="mt-1 text-sm text-slate-600">{subtitle}</p>
              </div>
              <div className="flex items-center gap-3">
                <div className="rounded-full border border-[#742a2a] bg-[#742a2a]/10 px-3 py-1.5 text-xs font-semibold uppercase tracking-wider text-[#742a2a]">
                  <span className="flex items-center gap-1">
                    <Lock className="h-3 w-3" />
                    SIGILOSO
                  </span>
                </div>
                <div className="rounded-xl bg-[#8B0000] px-4 py-2 text-sm font-medium text-white border border-[#FFD700]">
                  BMRS-8847
                </div>
              </div>
            </div>
          </header>

          <main className="flex-1 px-6 py-6">{children}</main>

          {/* Footer institucional */}
          <footer className="border-t border-slate-200 bg-white px-6 py-3">
            <div className="flex flex-col sm:flex-row justify-between items-center gap-2 text-xs text-gray-500">
              <div className="flex items-center gap-2">
                <Shield className="h-3 w-3 text-[#8B0000]" />
                <span>Brigada Militar do Rio Grande do Sul</span>
              </div>
              <div className="flex items-center gap-4">
                <span>SSI - Secretaria de Segurança Pública</span>
                <span className="text-[#FFD700] font-medium">Sistema Oficial de Uso Restrito</span>
              </div>
            </div>
          </footer>
        </div>
      </div>
    </div>
  );
}
