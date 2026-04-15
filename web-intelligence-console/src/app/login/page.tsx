"use client";

import { useState, FormEvent } from "react";
import { useRouter } from "next/navigation";
import { Shield, Lock, Eye, EyeOff, AlertTriangle } from "lucide-react";
import { authApi } from "@/app/services/api";

export default function LoginPage() {
  const router = useRouter();
  const [identifier, setIdentifier] = useState("");
  const [password, setPassword] = useState("");
  const [showPassword, setShowPassword] = useState(false);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  // Check if identifier is CPF (11 digits) or email
  const isCPF = /^\d{11}$/.test(identifier.replace(/\D/g, ""));
  const identifierType = isCPF ? "CPF" : "E-mail";
  const displayIdentifier = isCPF 
    ? identifier.replace(/(\d{3})(\d{3})(\d{3})(\d{2})/, "$1.$2.$3-$4")
    : identifier;

  async function handleSubmit(e: FormEvent) {
    e.preventDefault();
    setLoading(true);
    setError(null);

    try {
      // Clean CPF if needed (remove dots and dashes)
      const cleanIdentifier = isCPF 
        ? identifier.replace(/\D/g, "")
        : identifier;

      const response = await authApi.login(cleanIdentifier, password, {
        device_id: `web-${navigator.userAgent.slice(0, 50)}`,
        device_model: "Web Browser",
        os_version: navigator.platform,
        app_version: "2.1.4-web",
      });

      // Store tokens
      localStorage.setItem("access_token", response.access_token);
      localStorage.setItem("refresh_token", response.refresh_token);
      localStorage.setItem("user", JSON.stringify(response.user));

      // Redirect to dashboard
      router.push("/");
    } catch (err: any) {
      console.error("Login error:", err);
      setError(
        err.response?.data?.detail || 
        "Credenciais inválidas. Verifique CPF/e-mail e senha."
      );
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="min-h-screen bg-[#eef1f4] flex items-center justify-center px-4 py-12">
      {/* Marca d'água de classificação */}
      <div className="fixed inset-0 pointer-events-none z-0 overflow-hidden opacity-[0.03]">
        <div className="absolute inset-0 flex items-center justify-center rotate-[-45deg]">
          <span className="text-[150px] font-bold tracking-widest text-[#8B0000] select-none whitespace-nowrap">
            SIGILOSO • BMRS • SIGILOSO
          </span>
        </div>
      </div>

      <div className="w-full max-w-md relative z-10">
        {/* Header BMRS */}
        <div className="text-center mb-8">
          <div className="flex items-center justify-center gap-3 mb-4">
            <div className="rounded-2xl bg-[#8B0000] p-3 border-2 border-[#FFD700]">
              <Shield className="h-8 w-8 text-white" />
            </div>
            <div className="text-left">
              <div className="text-2xl font-bold text-[#8B0000]">F.A.R.O.</div>
              <div className="text-xs uppercase tracking-[0.2em] text-[#FFD700] font-semibold">
                BRIGADA MILITAR RS
              </div>
            </div>
          </div>
          <h1 className="text-xl font-semibold text-slate-800">
            Sistema de Inteligência Operacional
          </h1>
          <p className="text-sm text-slate-500 mt-1">
            Acesso restrito a policiais militares credenciados
          </p>
        </div>

        {/* Alerta de classificação */}
        <div className="mb-6 rounded-xl border border-[#742a2a] bg-[#742a2a]/10 p-3">
          <div className="flex items-center gap-2 text-xs font-semibold text-[#742a2a]">
            <Lock className="h-3 w-3" />
            SISTEMA CLASSIFICADO - SIGILOSO
          </div>
          <p className="mt-1 text-[10px] text-[#742a2a]/80 leading-relaxed">
            Lei nº 12.527/2011 - Acesso indevido configura crime conforme legislação vigente.
          </p>
        </div>

        {/* Formulário de login */}
        <div className="bg-white rounded-2xl shadow-xl border border-slate-200 p-8">
          <h2 className="text-lg font-semibold text-slate-800 mb-6">
            Autenticação
          </h2>

          {error && (
            <div className="mb-4 rounded-xl border border-red-200 bg-red-50 p-4 flex items-start gap-3">
              <AlertTriangle className="h-5 w-5 text-red-600 mt-0.5 flex-shrink-0" />
              <p className="text-sm text-red-700">{error}</p>
            </div>
          )}

          <form onSubmit={handleSubmit} className="space-y-5">
            <div>
              <label className="block text-sm font-medium text-slate-700 mb-2">
                CPF ou E-mail
              </label>
              <input
                type="text"
                value={identifier}
                onChange={(e) => setIdentifier(e.target.value)}
                placeholder={isCPF ? "000.000.000-00" : "seu@email.gov.br"}
                className="w-full rounded-xl border border-slate-300 px-4 py-3 text-slate-900 placeholder-slate-400 focus:border-[#8B0000] focus:outline-none focus:ring-1 focus:ring-[#8B0000]"
                required
              />
              {identifier && (
                <p className="mt-1 text-xs text-slate-500">
                  Tipo detectado: <span className="font-medium text-[#8B0000]">{identifierType}</span>
                  {isCPF && (
                    <span className="ml-1">({displayIdentifier})</span>
                  )}
                </p>
              )}
            </div>

            <div>
              <label className="block text-sm font-medium text-slate-700 mb-2">
                Senha
              </label>
              <div className="relative">
                <input
                  type={showPassword ? "text" : "password"}
                  value={password}
                  onChange={(e) => setPassword(e.target.value)}
                  placeholder="••••••••"
                  className="w-full rounded-xl border border-slate-300 px-4 py-3 pr-12 text-slate-900 placeholder-slate-400 focus:border-[#8B0000] focus:outline-none focus:ring-1 focus:ring-[#8B0000]"
                  required
                />
                <button
                  type="button"
                  onClick={() => setShowPassword(!showPassword)}
                  className="absolute right-3 top-1/2 -translate-y-1/2 text-slate-400 hover:text-slate-600"
                >
                  {showPassword ? (
                    <EyeOff className="h-5 w-5" />
                  ) : (
                    <Eye className="h-5 w-5" />
                  )}
                </button>
              </div>
            </div>

            <button
              type="submit"
              disabled={loading || !identifier || !password}
              className="w-full rounded-xl bg-[#8B0000] px-4 py-3 text-sm font-semibold text-white shadow-lg hover:bg-[#5C0000] focus:outline-none focus:ring-2 focus:ring-[#8B0000] focus:ring-offset-2 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
            >
              {loading ? (
                <span className="flex items-center justify-center gap-2">
                  <svg className="h-5 w-5 animate-spin" viewBox="0 0 24 24">
                    <circle
                      className="opacity-25"
                      cx="12"
                      cy="12"
                      r="10"
                      stroke="currentColor"
                      strokeWidth="4"
                      fill="none"
                    />
                    <path
                      className="opacity-75"
                      fill="currentColor"
                      d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"
                    />
                  </svg>
                  Autenticando...
                </span>
              ) : (
                "Entrar"
              )}
            </button>
          </form>

          <div className="mt-6 pt-6 border-t border-slate-200">
            <p className="text-xs text-slate-500 text-center leading-relaxed">
              Em caso de problemas de acesso, entre em contato com o SSI/BMRS.
            </p>
          </div>
        </div>

        {/* Footer institucional */}
        <div className="mt-8 text-center text-xs text-slate-500">
          <div className="flex items-center justify-center gap-2 mb-2">
            <Shield className="h-3 w-3 text-[#8B0000]" />
            <span>Brigada Militar do Rio Grande do Sul</span>
          </div>
          <p>SSI - Secretaria de Segurança Pública</p>
          <p className="mt-1 text-[#FFD700] font-medium">Sistema Oficial de Uso Restrito</p>
        </div>
      </div>
    </div>
  );
}
