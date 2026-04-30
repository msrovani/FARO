"use client";

import { useState } from "react";
import { intelligenceApi } from "@/app/services/api";
import { AgentObservationCorrelation } from "@/app/types";
import { 
  Link2, 
  RefreshCw, 
  Loader2,
  TrendingUp,
  Clock,
  Target
} from "lucide-react";

export default function CorrelationPanel() {
  const [loading, setLoading] = useState(false);
  const [correlations, setCorrelations] = useState<AgentObservationCorrelation[]>([]);

  const handleAnalyze = async () => {
    setLoading(true);
    try {
      const data = await intelligenceApi.analyzeAgentObservationCorrelation({
        start_date: new Date(new Date().setDate(new Date().getDate() - 30)).toISOString(),
        end_date: new Date().toISOString(),
        proximity_radius_meters: 500,
      });
      setCorrelations(data);
    } catch (err) {
      console.error("Erro ao analisar correlação", err);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="space-y-6">
      {/* Controls */}
      <div className="flex items-center gap-4 rounded-2xl border border-slate-200 bg-white p-4 shadow-sm">
        <button
          onClick={handleAnalyze}
          disabled={loading}
          className="flex items-center gap-2 rounded-xl bg-slate-900 px-4 py-2 text-sm font-medium text-white transition-all hover:bg-slate-800 disabled:opacity-50"
        >
          {loading ? <Loader2 className="size-4 animate-spin" /> : <RefreshCw className="size-4" />}
          {loading ? "Analisando..." : "Analisar Correlação"}
        </button>
        <span className="text-xs text-slate-500">
          Raio de 500m • Últimos 30 dias
        </span>
      </div>

      {loading && (
        <div className="flex items-center justify-center rounded-3xl border border-slate-200 bg-slate-50 p-12">
          <Loader2 className="size-8 animate-spin text-slate-400" />
        </div>
      )}

      {!loading && correlations.length > 0 && (
        <>
          {/* Summary */}
          <div className="grid grid-cols-1 gap-4 md:grid-cols-4">
            <div className="rounded-2xl border border-slate-200 bg-white p-4 shadow-sm">
              <div className="flex items-center gap-2 text-slate-500">
                <Link2 className="size-4" />
                <span className="text-xs font-medium uppercase">Agentes Analisados</span>
              </div>
              <p className="mt-2 text-2xl font-bold text-slate-900">{correlations.length}</p>
            </div>
            <div className="rounded-2xl border border-slate-200 bg-white p-4 shadow-sm">
              <div className="flex items-center gap-2 text-slate-500">
                <Target className="size-4" />
                <span className="text-xs font-medium uppercase">Taxa Média Correlação</span>
              </div>
              <p className="mt-2 text-2xl font-bold text-slate-900">
                {(correlations.reduce((sum, c) => sum + c.correlation_rate, 0) / correlations.length * 100).toFixed(0)}%
              </p>
            </div>
            <div className="rounded-2xl border border-slate-200 bg-white p-4 shadow-sm">
              <div className="flex items-center gap-2 text-slate-500">
                <TrendingUp className="size-4" />
                <span className="text-xs font-medium uppercase">Total Observações</span>
              </div>
              <p className="mt-2 text-2xl font-bold text-slate-900">
                {correlations.reduce((sum, c) => sum + c.total_observations, 0)}
              </p>
            </div>
            <div className="rounded-2xl border border-slate-200 bg-white p-4 shadow-sm">
              <div className="flex items-center gap-2 text-slate-500">
                <Clock className="size-4" />
                <span className="text-xs font-medium uppercase">Observações Próximas</span>
              </div>
              <p className="mt-2 text-2xl font-bold text-slate-900">
                {correlations.reduce((sum, c) => sum + c.observations_near_agent, 0)}
              </p>
            </div>
          </div>

          {/* Agent Correlations */}
          <div className="space-y-4">
            <h3 className="font-semibold text-slate-900">Correlação por Agente</h3>
            <div className="grid grid-cols-1 gap-4 md:grid-cols-2">
              {correlations.map((correlation) => (
                <CorrelationCard key={correlation.agent_id} correlation={correlation} />
              ))}
            </div>
          </div>
        </>
      )}

      {!loading && correlations.length === 0 && (
        <div className="flex items-center justify-center rounded-3xl border border-slate-200 bg-slate-50 p-12">
          <div className="text-center text-slate-400">
            <Link2 className="mx-auto mb-4 size-12 opacity-20" />
            <p>Clique em "Analisar Correlação" para visualizar</p>
          </div>
        </div>
      )}
    </div>
  );
}

function CorrelationCard({ correlation }: { correlation: AgentObservationCorrelation }) {
  const correlationPercent = (correlation.correlation_rate * 100).toFixed(1);
  const correlationColor = 
    correlation.correlation_rate >= 0.7 ? 'green' :
    correlation.correlation_rate >= 0.4 ? 'amber' : 'red';

  return (
    <div className="rounded-2xl border border-slate-200 bg-white p-5 shadow-sm">
      <div className="mb-4 flex items-center justify-between">
        <h4 className="font-semibold text-slate-900">{correlation.agent_name}</h4>
        <span className={`rounded-full px-3 py-1 text-xs font-bold uppercase ${
          correlationColor === 'green' ? 'bg-green-100 text-green-700' :
          correlationColor === 'amber' ? 'bg-amber-100 text-amber-700' :
          'bg-red-100 text-red-700'
        }`}>
          {correlationPercent}% correlação
        </span>
      </div>
      
      <div className="grid grid-cols-2 gap-3 text-sm">
        <div>
          <p className="text-xs text-slate-500">Total Observações</p>
          <p className="font-semibold text-slate-900">{correlation.total_observations}</p>
        </div>
        <div>
          <p className="text-xs text-slate-500">Observações Próximas</p>
          <p className="font-semibold text-slate-900">{correlation.observations_near_agent}</p>
        </div>
        <div>
          <p className="text-xs text-slate-500">Distância Média</p>
          <p className="font-semibold text-slate-900">{correlation.average_distance_to_observations.toFixed(1)}m</p>
        </div>
        <div>
          <p className="text-xs text-slate-500">Localizações</p>
          <p className="font-semibold text-slate-900">{correlation.total_agent_locations}</p>
        </div>
      </div>

      {correlation.most_productive_areas.length > 0 && (
        <div className="mt-4 pt-4 border-t border-slate-100">
          <p className="mb-2 text-xs font-medium text-slate-500 uppercase">Áreas Produtivas</p>
          <div className="space-y-1">
            {correlation.most_productive_areas.slice(0, 3).map((area, idx) => (
              <div key={idx} className="flex items-center gap-2 text-xs">
                <Target className="size-3 text-slate-400" />
                <span className="text-slate-600">
                  {area.count} observações
                </span>
              </div>
            ))}
          </div>
        </div>
      )}

      {correlation.peak_detection_hours.length > 0 && (
        <div className="mt-4 pt-4 border-t border-slate-100">
          <p className="mb-2 text-xs font-medium text-slate-500 uppercase">Horários de Pico</p>
          <div className="flex flex-wrap gap-1">
            {correlation.peak_detection_hours.map((hour, idx) => (
              <span key={idx} className="inline-flex items-center rounded-full bg-sky-100 px-2 py-0.5 text-[10px] font-semibold text-sky-700">
                {hour}:00
              </span>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}
