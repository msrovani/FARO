"use client";

import { useState } from "react";
import { intelligenceApi } from "@/app/services/api";
import { TacticalPositioningRecommendation } from "@/app/types";
import { 
  Crosshair, 
  RefreshCw, 
  Loader2,
  AlertTriangle,
  MapPin,
  TrendingUp
} from "lucide-react";

export default function TacticalPositioningPanel() {
  const [loading, setLoading] = useState(false);
  const [recommendations, setRecommendations] = useState<TacticalPositioningRecommendation[]>([]);

  const handleGenerate = async () => {
    setLoading(true);
    try {
      const data = await intelligenceApi.getTacticalPositioningRecommendations({
        start_date: new Date(new Date().setDate(new Date().getDate() - 30)).toISOString(),
        end_date: new Date().toISOString(),
      });
      setRecommendations(data);
    } catch (err) {
      console.error("Erro ao gerar recomendações táticas", err);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="space-y-6">
      {/* Controls */}
      <div className="flex items-center gap-4 rounded-2xl border border-slate-200 bg-white p-4 shadow-sm">
        <button
          onClick={handleGenerate}
          disabled={loading}
          className="flex items-center gap-2 rounded-xl bg-slate-900 px-4 py-2 text-sm font-medium text-white transition-all hover:bg-slate-800 disabled:opacity-50"
        >
          {loading ? <Loader2 className="size-4 animate-spin" /> : <RefreshCw className="size-4" />}
          {loading ? "Gerando..." : "Gerar Recomendações"}
        </button>
        <span className="text-xs text-slate-500">
          Baseado em hotspots e gaps de cobertura • Últimos 30 dias
        </span>
      </div>

      {loading && (
        <div className="flex items-center justify-center rounded-3xl border border-slate-200 bg-slate-50 p-12">
          <Loader2 className="size-8 animate-spin text-slate-400" />
        </div>
      )}

      {!loading && recommendations.length > 0 && (
        <>
          {/* Summary */}
          <div className="grid grid-cols-1 gap-4 md:grid-cols-3">
            <div className="rounded-2xl border border-slate-200 bg-white p-4 shadow-sm">
              <div className="flex items-center gap-2 text-slate-500">
                <Crosshair className="size-4" />
                <span className="text-xs font-medium uppercase">Recomendações</span>
              </div>
              <p className="mt-2 text-2xl font-bold text-slate-900">{recommendations.length}</p>
            </div>
            <div className="rounded-2xl border border-slate-200 bg-white p-4 shadow-sm">
              <div className="flex items-center gap-2 text-slate-500">
                <AlertTriangle className="size-4" />
                <span className="text-xs font-medium uppercase">Prioridade Alta</span>
              </div>
              <p className="mt-2 text-2xl font-bold text-slate-900">
                {recommendations.filter(r => r.priority === 'high').length}
              </p>
            </div>
            <div className="rounded-2xl border border-slate-200 bg-white p-4 shadow-sm">
              <div className="flex items-center gap-2 text-slate-500">
                <TrendingUp className="size-4" />
                <span className="text-xs font-medium uppercase">Gap Médio</span>
              </div>
              <p className="mt-2 text-2xl font-bold text-slate-900">
                {(recommendations.reduce((sum, r) => sum + r.coverage_gap_score, 0) / recommendations.length).toFixed(1)}
              </p>
            </div>
          </div>

          {/* Recommendations */}
          <div className="space-y-4">
            <h3 className="font-semibold text-slate-900">Recomendações de Posicionamento Tático</h3>
            <div className="grid grid-cols-1 gap-4 md:grid-cols-2">
              {recommendations.map((rec, idx) => (
                <RecommendationCard key={idx} recommendation={rec} />
              ))}
            </div>
          </div>
        </>
      )}

      {!loading && recommendations.length === 0 && (
        <div className="flex items-center justify-center rounded-3xl border border-slate-200 bg-slate-50 p-12">
          <div className="text-center text-slate-400">
            <Crosshair className="mx-auto mb-4 size-12 opacity-20" />
            <p>Clique em "Gerar Recomendações" para visualizar</p>
          </div>
        </div>
      )}
    </div>
  );
}

function RecommendationCard({ recommendation }: { recommendation: TacticalPositioningRecommendation }) {
  const priorityColor = 
    recommendation.priority === 'high' ? 'red' :
    recommendation.priority === 'medium' ? 'amber' : 'blue';

  return (
    <div className={`rounded-2xl border bg-white p-5 shadow-sm ${
      priorityColor === 'red' ? 'border-red-200' :
      priorityColor === 'amber' ? 'border-amber-200' :
      'border-slate-200'
    }`}>
      <div className="mb-4 flex items-start justify-between">
        <div className="flex items-center gap-2">
          <Crosshair className={`size-5 ${
            priorityColor === 'red' ? 'text-red-600' :
            priorityColor === 'amber' ? 'text-amber-600' :
            'text-blue-600'
          }`} />
          <h4 className="font-semibold text-slate-900">Posicionamento Recomendado</h4>
        </div>
        <span className={`rounded-full px-2 py-0.5 text-[10px] font-bold uppercase ${
          priorityColor === 'red' ? 'bg-red-100 text-red-700' :
          priorityColor === 'amber' ? 'bg-amber-100 text-amber-700' :
          'bg-blue-100 text-blue-700'
        }`}>
          {recommendation.priority}
        </span>
      </div>
      
      <div className="space-y-3 text-sm">
        <div className="flex items-start gap-2">
          <MapPin className="size-4 text-slate-400 mt-0.5 flex-shrink-0" />
          <div>
            <p className="text-xs text-slate-500">Coordenadas</p>
            <p className="font-semibold text-slate-900">
              {recommendation.recommended_latitude.toFixed(6)}, {recommendation.recommended_longitude.toFixed(6)}
            </p>
          </div>
        </div>

        <div className="flex items-start gap-2">
          <TrendingUp className="size-4 text-slate-400 mt-0.5 flex-shrink-0" />
          <div>
            <p className="text-xs text-slate-500">Gap de Cobertura</p>
            <p className="font-semibold text-slate-900">{recommendation.coverage_gap_score.toFixed(1)}</p>
          </div>
        </div>

        <div className="pt-3 border-t border-slate-100">
          <p className="text-xs text-slate-500 mb-1">Motivo</p>
          <p className="text-slate-700">{recommendation.reason}</p>
        </div>

        <div className="pt-2">
          <p className="text-xs text-slate-500 mb-1">Impacto Esperado</p>
          <p className="text-slate-700">{recommendation.expected_impact}</p>
        </div>
      </div>
    </div>
  );
}
