"use client";

import { useState } from "react";
import { intelligenceApi } from "@/app/services/api";
import { CoverageMapCell } from "@/app/types";
import { 
  Map as MapIcon, 
  RefreshCw, 
  Loader2,
  Layers
} from "lucide-react";
import MapBase from "@/app/components/map/MapBase";
import { Source, Layer, FillLayer } from "react-map-gl";

export default function CoverageMapPanel() {
  const [loading, setLoading] = useState(false);
  const [coverageData, setCoverageData] = useState<CoverageMapCell[]>([]);

  const handleGenerate = async () => {
    setLoading(true);
    try {
      const data = await intelligenceApi.getAgentCoverageMap({
        start_date: new Date(new Date().setDate(new Date().getDate() - 7)).toISOString(),
        end_date: new Date().toISOString(),
        grid_size_meters: 100,
      });
      setCoverageData(data);
    } catch (err) {
      console.error("Erro ao gerar mapa de cobertura", err);
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
          {loading ? "Gerando..." : "Gerar Mapa de Cobertura"}
        </button>
        <span className="text-xs text-slate-500">
          Grid de 100m • Últimos 7 dias
        </span>
      </div>

      {loading && (
        <div className="flex items-center justify-center rounded-3xl border border-slate-200 bg-slate-50 p-12">
          <Loader2 className="size-8 animate-spin text-slate-400" />
        </div>
      )}

      {!loading && coverageData.length > 0 && (
        <>
          {/* Stats */}
          <div className="grid grid-cols-1 gap-4 md:grid-cols-3">
            <div className="rounded-2xl border border-slate-200 bg-white p-4 shadow-sm">
              <div className="flex items-center gap-2 text-slate-500">
                <Layers className="size-4" />
                <span className="text-xs font-medium uppercase">Células Cobertas</span>
              </div>
              <p className="mt-2 text-2xl font-bold text-slate-900">{coverageData.length}</p>
            </div>
            <div className="rounded-2xl border border-slate-200 bg-white p-4 shadow-sm">
              <div className="flex items-center gap-2 text-slate-500">
                <MapIcon className="size-4" />
                <span className="text-xs font-medium uppercase">Máximo por Célula</span>
              </div>
              <p className="mt-2 text-2xl font-bold text-slate-900">
                {Math.max(...coverageData.map(c => c.location_count))}
              </p>
            </div>
            <div className="rounded-2xl border border-slate-200 bg-white p-4 shadow-sm">
              <div className="flex items-center gap-2 text-slate-500">
                <MapIcon className="size-4" />
                <span className="text-xs font-medium uppercase">Média por Célula</span>
              </div>
              <p className="mt-2 text-2xl font-bold text-slate-900">
                {(coverageData.reduce((sum, c) => sum + c.location_count, 0) / coverageData.length).toFixed(1)}
              </p>
            </div>
          </div>

          {/* Map */}
          <div className="h-[600px] overflow-hidden rounded-3xl border border-slate-200 shadow-lg">
            <MapBase>
              {coverageData.map((cell, idx) => {
                const geometry = JSON.parse(cell.cell_geometry);
                const intensity = Math.min(cell.location_count / 10, 1);
                return (
                  <Source key={idx} id={`coverage-${idx}`} type="geojson" data={geometry as any}>
                    <Layer
                      id={`coverage-fill-${idx}`}
                      type="fill"
                      paint={{
                        'fill-color': `rgba(14, 165, 233, ${0.3 + intensity * 0.5})`,
                        'fill-opacity': 0.6,
                      }}
                    />
                  </Source>
                );
              })}
            </MapBase>
          </div>

          {/* Top Cells */}
          <div className="space-y-4">
            <h3 className="font-semibold text-slate-900">Top 10 Áreas Mais Cobertas</h3>
            <div className="rounded-2xl border border-slate-200 bg-white p-4 shadow-sm">
              <table className="w-full text-left text-sm">
                <thead className="text-slate-500 uppercase text-[10px] font-bold">
                  <tr>
                    <th className="px-4 py-3">Latitude</th>
                    <th className="px-4 py-3">Longitude</th>
                    <th className="px-4 py-3">Observações</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-slate-100">
                  {coverageData.slice(0, 10).map((cell, idx) => (
                    <tr key={idx} className="hover:bg-slate-50 transition-colors">
                      <td className="px-4 py-3 text-slate-600 font-mono">
                        {cell.latitude.toFixed(6)}
                      </td>
                      <td className="px-4 py-3 text-slate-600 font-mono">
                        {cell.longitude.toFixed(6)}
                      </td>
                      <td className="px-4 py-3">
                        <span className="inline-flex items-center rounded-full bg-sky-100 px-2 py-0.5 text-xs font-semibold text-sky-700">
                          {cell.location_count}
                        </span>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>
        </>
      )}

      {!loading && coverageData.length === 0 && (
        <div className="flex items-center justify-center rounded-3xl border border-slate-200 bg-slate-50 p-12">
          <div className="text-center text-slate-400">
            <MapIcon className="mx-auto mb-4 size-12 opacity-20" />
            <p>Clique em "Gerar Mapa de Cobertura" para visualizar</p>
          </div>
        </div>
      )}
    </div>
  );
}
