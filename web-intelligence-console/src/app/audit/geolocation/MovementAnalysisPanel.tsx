"use client";

import { useState } from "react";
import { intelligenceApi } from "@/app/services/api";
import { AgentMovementAnalysisResult, AgentMovementSummary, MovementAnomaly } from "@/app/types";
import { 
  Activity, 
  AlertTriangle, 
  Battery, 
  MapPin, 
  TrendingUp,
  Loader2,
  RefreshCw
} from "lucide-react";

export default function MovementAnalysisPanel() {
  const [loading, setLoading] = useState(false);
  const [data, setData] = useState<AgentMovementAnalysisResult | null>(null);
  const [selectedAgent, setSelectedAgent] = useState<string | null>(null);

  const handleAnalyze = async () => {
    setLoading(true);
    try {
      const result = await intelligenceApi.analyzeAgentMovement({
        agent_id: selectedAgent || undefined,
        start_date: new Date(new Date().setDate(new Date().getDate() - 7)).toISOString(),
        end_date: new Date().toISOString(),
        cluster_radius_meters: 500,
        min_points_per_cluster: 5,
      });
      setData(result);
    } catch (err) {
      console.error("Erro ao analisar movimento", err);
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
          {loading ? "Analisando..." : "Analisar Padrões"}
        </button>
        <span className="text-xs text-slate-500">
          Análise dos últimos 7 dias
        </span>
      </div>

      {loading && (
        <div className="flex items-center justify-center rounded-3xl border border-slate-200 bg-slate-50 p-12">
          <Loader2 className="size-8 animate-spin text-slate-400" />
        </div>
      )}

      {data && !loading && (
        <>
          {/* Summary Stats */}
          <div className="grid grid-cols-1 gap-4 md:grid-cols-4">
            <div className="rounded-2xl border border-slate-200 bg-white p-4 shadow-sm">
              <div className="flex items-center gap-2 text-slate-500">
                <Activity className="size-4" />
                <span className="text-xs font-medium uppercase">Agentes Analisados</span>
              </div>
              <p className="mt-2 text-2xl font-bold text-slate-900">{data.total_agents}</p>
            </div>
            <div className="rounded-2xl border border-slate-200 bg-white p-4 shadow-sm">
              <div className="flex items-center gap-2 text-slate-500">
                <MapPin className="size-4" />
                <span className="text-xs font-medium uppercase">Localizações</span>
              </div>
              <p className="mt-2 text-2xl font-bold text-slate-900">{data.total_locations_analyzed}</p>
            </div>
            <div className="rounded-2xl border border-slate-200 bg-white p-4 shadow-sm">
              <div className="flex items-center gap-2 text-slate-500">
                <TrendingUp className="size-4" />
                <span className="text-xs font-medium uppercase">Período (dias)</span>
              </div>
              <p className="mt-2 text-2xl font-bold text-slate-900">{data.analysis_period_days}</p>
            </div>
            <div className="rounded-2xl border border-slate-200 bg-white p-4 shadow-sm">
              <div className="flex items-center gap-2 text-slate-500">
                <AlertTriangle className="size-4" />
                <span className="text-xs font-medium uppercase">Anomalias</span>
              </div>
              <p className="mt-2 text-2xl font-bold text-slate-900">{data.anomalies.length}</p>
            </div>
          </div>

          {/* Agent Summaries */}
          <div className="space-y-4">
            <h3 className="font-semibold text-slate-900">Resumo por Agente</h3>
            <div className="grid grid-cols-1 gap-4 md:grid-cols-2">
              {data.summaries.map((summary) => (
                <AgentSummaryCard key={summary.agent_id} summary={summary} />
              ))}
            </div>
          </div>

          {/* Anomalies */}
          {data.anomalies.length > 0 && (
            <div className="space-y-4">
              <h3 className="font-semibold text-slate-900">Anomalias Detectadas</h3>
              <div className="rounded-2xl border border-amber-200 bg-amber-50 p-4 shadow-sm">
                {data.anomalies.map((anomaly, idx) => (
                  <div key={idx} className="flex items-start gap-3 border-b border-amber-200 pb-3 last:border-0 last:pb-0">
                    <AlertTriangle className="size-5 text-amber-600 flex-shrink-0 mt-0.5" />
                    <div className="flex-1">
                      <div className="flex items-center gap-2">
                        <span className="text-sm font-semibold text-amber-900">
                          {anomaly.anomaly_type}
                        </span>
                        <span className={`rounded-full px-2 py-0.5 text-[10px] font-bold uppercase ${
                          anomaly.severity === 'warning' ? 'bg-amber-100 text-amber-700' : 
                          anomaly.severity === 'critical' ? 'bg-red-100 text-red-700' : 
                          'bg-blue-100 text-blue-700'
                        }`}>
                          {anomaly.severity}
                        </span>
                      </div>
                      <p className="mt-1 text-xs text-amber-700">{anomaly.description}</p>
                      <p className="mt-1 text-[10px] text-amber-600">
                        {new Date(anomaly.recorded_at).toLocaleString('pt-BR')} • 
                        {anomaly.location_latitude.toFixed(4)}, {anomaly.location_longitude.toFixed(4)}
                      </p>
                    </div>
                  </div>
                ))}
              </div>
            </div>
          )}
        </>
      )}
    </div>
  );
}

function AgentSummaryCard({ summary }: { summary: AgentMovementSummary }) {
  return (
    <div className="rounded-2xl border border-slate-200 bg-white p-5 shadow-sm">
      <div className="mb-4 flex items-center justify-between">
        <h4 className="font-semibold text-slate-900">{summary.agent_name}</h4>
        <span className="text-xs text-slate-500">
          {summary.total_locations} localizações
        </span>
      </div>
      
      <div className="grid grid-cols-2 gap-3 text-sm">
        <div>
          <p className="text-xs text-slate-500">Distância Total</p>
          <p className="font-semibold text-slate-900">{summary.total_distance_km.toFixed(1)} km</p>
        </div>
        <div>
          <p className="text-xs text-slate-500">Velocidade Média</p>
          <p className="font-semibold text-slate-900">
            {summary.average_speed_kmh ? `${summary.average_speed_kmh.toFixed(1)} km/h` : '--'}
          </p>
        </div>
        <div>
          <p className="text-xs text-slate-500">Bateria Média</p>
          <p className="font-semibold text-slate-900">
            {summary.battery_stats.avg ? `${summary.battery_stats.avg.toFixed(0)}%` : '--'}
          </p>
        </div>
        <div>
          <p className="text-xs text-slate-500">Áreas de Patrulha</p>
          <p className="font-semibold text-slate-900">{summary.patrol_areas.length}</p>
        </div>
      </div>

      {summary.patrol_areas.length > 0 && (
        <div className="mt-4 pt-4 border-t border-slate-100">
          <p className="mb-2 text-xs font-medium text-slate-500 uppercase">Top Áreas de Patrulha</p>
          <div className="space-y-2">
            {summary.patrol_areas.slice(0, 3).map((area, idx) => (
              <div key={idx} className="flex items-center gap-2 text-xs">
                <MapPin className="size-3 text-slate-400" />
                <span className="text-slate-600">
                  {area.observation_count} obs • {area.unique_hours}h único
                </span>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}
