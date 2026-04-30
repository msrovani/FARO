"use client";

import { useState, useEffect, useCallback } from "react";
import { ConsoleShell } from "@/app/components/console-shell";
import { intelligenceApi, authApi } from "@/app/services/api";
import { AgentLocationEntry, User, GeolocationAuditFilter } from "@/app/types";
import MapBase from "@/app/components/map/MapBase";
import { Marker, Source, Layer } from "react-map-gl";
import { 
  BarChart, 
  Map as MapIcon, 
  Table as TableIcon, 
  Download, 
  ShieldCheck,
  Calendar,
  User as UserIcon,
  Filter,
  ArrowRight,
  Activity,
  Layers,
  Link2,
  Crosshair
} from "lucide-react";
import MovementAnalysisPanel from "./MovementAnalysisPanel";
import CoverageMapPanel from "./CoverageMapPanel";
import CorrelationPanel from "./CorrelationPanel";
import TacticalPositioningPanel from "./TacticalPositioningPanel";

export default function GeolocationAuditPage() {
  const [agents, setAgents] = useState<User[]>([]);
  const [geotrail, setGeotrail] = useState<AgentLocationEntry[]>([]);
  const [loading, setLoading] = useState(false);
  const [filters, setFilters] = useState<GeolocationAuditFilter>({
    start_date: new Date(new Date().setHours(0, 0, 0, 0)).toISOString(),
    end_date: new Date().toISOString()
  });
  const [viewMode, setViewMode] = useState<'map' | 'table'>('map');
  const [exporting, setExporting] = useState<string | null>(null);
  const [activeTab, setActiveTab] = useState<'geotrail' | 'movement' | 'coverage' | 'correlation' | 'tactical'>('geotrail');

  // Load field agents for filter
  useEffect(() => {
    const loadAgents = async () => {
      try {
        const response = await authApi.listUsers({ role: 'field_agent' });
        setAgents(response.items || []);
      } catch (err) {
        console.error("Erro ao carregar agentes", err);
      }
    };
    loadAgents();
  }, []);

  const handleSearch = useCallback(async () => {
    if (!filters.agent_id) return;
    setLoading(true);
    try {
      const data = await intelligenceApi.getAgentGeotrail(filters);
      setGeotrail(data);
    } catch (err) {
      console.error("Erro ao carregar geotrail", err);
    } finally {
      setLoading(false);
    }
  }, [filters]);

  const handleExport = async (format: 'pdf' | 'docx' | 'xlsx') => {
    if (!filters.agent_id) return;
    setExporting(format);
    try {
      const blob = await intelligenceApi.exportGeotrail(filters, format);
      const url = window.URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = `audit_geotrail_${filters.agent_id}_${new Date().getTime()}.${format}`;
      document.body.appendChild(a);
      a.click();
      a.remove();
    } catch (err) {
      console.error("Erro na exportação", err);
    } finally {
      setExporting(null);
    }
  };

  // GeoJSON for the path
  const lineFeature = {
    type: 'Feature',
    properties: {},
    geometry: {
      type: 'LineString',
      coordinates: geotrail.map(item => [item.location.longitude, item.location.latitude])
    }
  };

  return (
    <ConsoleShell
      title="Auditoria de Geolocalizacao"
      subtitle="Reconstrucao de trilhas taticas e cadeia de custodia de ativos de campo."
    >
      <div className="grid grid-cols-1 gap-6 lg:grid-cols-4">
        {/* Filters Sidebar */}
        <aside className="lg:col-span-1 space-y-4">
          <div className="rounded-3xl border border-slate-200 bg-white p-5 shadow-sm">
            <div className="mb-4 flex items-center gap-2">
              <Filter className="size-4 text-slate-500" />
              <h3 className="font-semibold text-slate-900">Filtros Taticos</h3>
            </div>
            
            <div className="space-y-4">
              <div className="space-y-1.5">
                <label className="text-xs font-medium text-slate-500 uppercase">Agente de Campo</label>
                <select 
                  className="w-full rounded-2xl border border-slate-200 bg-slate-50 px-3 py-2.5 text-sm"
                  value={filters.agent_id || ''}
                  onChange={(e) => setFilters({...filters, agent_id: e.target.value})}
                >
                  <option value="">Selecionar Agente...</option>
                  {agents.map(agent => (
                    <option key={agent.id} value={agent.id}>{agent.full_name}</option>
                  ))}
                </select>
              </div>

              <div className="space-y-1.5">
                <label className="text-xs font-medium text-slate-500 uppercase">Inicio do Periodo</label>
                <input 
                  type="datetime-local"
                  className="w-full rounded-2xl border border-slate-200 bg-slate-50 px-3 py-2.5 text-sm"
                  value={filters.start_date?.split('.')[0]}
                  onChange={(e) => setFilters({...filters, start_date: new Date(e.target.value).toISOString()})}
                />
              </div>

              <div className="space-y-1.5">
                <label className="text-xs font-medium text-slate-500 uppercase">Fim do Periodo</label>
                <input 
                  type="datetime-local"
                  className="w-full rounded-2xl border border-slate-200 bg-slate-50 px-3 py-2.5 text-sm"
                  value={filters.end_date?.split('.')[0]}
                  onChange={(e) => setFilters({...filters, end_date: new Date(e.target.value).toISOString()})}
                />
              </div>

              <button 
                onClick={handleSearch}
                disabled={!filters.agent_id || loading}
                className="w-full flex items-center justify-center gap-2 rounded-2xl bg-slate-900 py-3 text-sm font-semibold text-white transition-all hover:bg-slate-800 disabled:opacity-50"
              >
                {loading ? "Processando..." : "Pesquisar Trilha"}
                {!loading && <ArrowRight className="size-4" />}
              </button>
            </div>
          </div>

          {/* Export Section */}
          <div className="rounded-3xl border border-amber-100 bg-amber-50 p-5 shadow-sm">
            <div className="mb-4 flex items-center gap-2">
              <ShieldCheck className="size-4 text-amber-600" />
              <h3 className="font-semibold text-amber-900">Cadeia de Custodia</h3>
            </div>
            <p className="mb-4 text-xs text-amber-700">
              Toda exportacao gera um Hash SHA-256 e registra o analista responsavel para fins de prova judicial.
            </p>
            <div className="grid grid-cols-1 gap-2">
              {(['pdf', 'docx', 'xlsx'] as const).map(format => (
                <button
                  key={format}
                  onClick={() => handleExport(format)}
                  disabled={geotrail.length === 0 || !!exporting}
                  className="flex items-center justify-between rounded-xl bg-white px-3 py-2 text-xs font-medium text-slate-700 shadow-sm hover:bg-slate-50 disabled:opacity-50"
                >
                  <span className="uppercase text-slate-500">{format} Certificado</span>
                  {exporting === format ? <div className="size-3 animate-spin rounded-full border-2 border-slate-300 border-t-slate-600" /> : <Download className="size-3" />}
                </button>
              ))}
            </div>
          </div>
        </aside>

        {/* Content Area */}
        <main className="lg:col-span-3 space-y-6">
          <div className="flex items-center justify-between rounded-3xl border border-slate-200 bg-white p-2 shadow-sm">
            <div className="flex gap-1 flex-wrap">
              <button 
                onClick={() => setActiveTab('geotrail')}
                className={`flex items-center gap-2 rounded-2xl px-4 py-2 text-sm font-medium transition-all ${activeTab === 'geotrail' ? 'bg-slate-900 text-white' : 'text-slate-500 hover:bg-slate-50'}`}
              >
                <MapIcon className="size-4" /> Geotrail
              </button>
              <button 
                onClick={() => setActiveTab('movement')}
                className={`flex items-center gap-2 rounded-2xl px-4 py-2 text-sm font-medium transition-all ${activeTab === 'movement' ? 'bg-slate-900 text-white' : 'text-slate-500 hover:bg-slate-50'}`}
              >
                <Activity className="size-4" /> Padrões de Movimento
              </button>
              <button 
                onClick={() => setActiveTab('coverage')}
                className={`flex items-center gap-2 rounded-2xl px-4 py-2 text-sm font-medium transition-all ${activeTab === 'coverage' ? 'bg-slate-900 text-white' : 'text-slate-500 hover:bg-slate-50'}`}
              >
                <Layers className="size-4" /> Mapa de Cobertura
              </button>
              <button 
                onClick={() => setActiveTab('correlation')}
                className={`flex items-center gap-2 rounded-2xl px-4 py-2 text-sm font-medium transition-all ${activeTab === 'correlation' ? 'bg-slate-900 text-white' : 'text-slate-500 hover:bg-slate-50'}`}
              >
                <Link2 className="size-4" /> Correlação
              </button>
              <button 
                onClick={() => setActiveTab('tactical')}
                className={`flex items-center gap-2 rounded-2xl px-4 py-2 text-sm font-medium transition-all ${activeTab === 'tactical' ? 'bg-slate-900 text-white' : 'text-slate-500 hover:bg-slate-50'}`}
              >
                <Crosshair className="size-4" /> Posicionamento Tático
              </button>
            </div>
          </div>

          <div className="min-h-[600px]">
            {activeTab === 'geotrail' && (
              <>
                <div className="flex items-center justify-between rounded-3xl border border-slate-200 bg-white p-2 shadow-sm mb-4">
                  <div className="flex gap-1">
                    <button 
                      onClick={() => setViewMode('map')}
                      className={`flex items-center gap-2 rounded-2xl px-4 py-2 text-sm font-medium transition-all ${viewMode === 'map' ? 'bg-slate-900 text-white' : 'text-slate-500 hover:bg-slate-50'}`}
                    >
                      <MapIcon className="size-4" /> Mapa
                    </button>
                    <button 
                      onClick={() => setViewMode('table')}
                      className={`flex items-center gap-2 rounded-2xl px-4 py-2 text-sm font-medium transition-all ${viewMode === 'table' ? 'bg-slate-900 text-white' : 'text-slate-500 hover:bg-slate-50'}`}
                    >
                      <TableIcon className="size-4" /> Tabela
                    </button>
                  </div>
                </div>

                <div className="h-[600px] overflow-hidden rounded-3xl border border-slate-200 bg-slate-100 shadow-lg">
                  {viewMode === 'map' ? (
                    <MapBase>
                      {geotrail.length > 0 && (
                        <>
                          <Source id="geotrail-path" type="geojson" data={lineFeature as any}>
                            <Layer
                              id="path-line"
                              type="line"
                              paint={{
                                'line-color': '#0ea5e9',
                                'line-width': 3,
                                'line-dasharray': [2, 1]
                              }}
                            />
                          </Source>
                          {geotrail.map((pos, idx) => (
                            <Marker 
                              key={pos.id} 
                              latitude={pos.location.latitude} 
                              longitude={pos.location.longitude}
                            >
                              <div className={`size-3 rounded-full border-2 border-white shadow-sm ${idx === 0 ? 'bg-green-500' : idx === geotrail.length - 1 ? 'bg-red-500' : 'bg-sky-500'}`} />
                            </Marker>
                          ))}
                        </>
                      )}
                      {geotrail.length === 0 && (
                        <div className="flex h-full items-center justify-center p-12 text-center text-slate-400">
                          <div>
                            <MapIcon className="mx-auto mb-4 size-12 opacity-20" />
                            <p>Selecione um agente e periodo para reconstruir a trilha.</p>
                          </div>
                        </div>
                      )}
                    </MapBase>
                  ) : (
                    <div className="h-full overflow-y-auto bg-white">
                      <table className="w-full text-left text-sm">
                        <thead className="sticky top-0 bg-slate-50 text-slate-500 uppercase text-[10px] font-bold">
                          <tr>
                            <th className="px-6 py-4">Timestamp</th>
                            <th className="px-6 py-4">Latitude / Longitude</th>
                            <th className="px-6 py-4">Conectividade</th>
                            <th className="px-6 py-4">Precisao</th>
                            <th className="px-6 py-4">Bateria</th>
                          </tr>
                        </thead>
                        <tbody className="divide-y divide-slate-100">
                          {geotrail.map(item => (
                            <tr key={item.id} className="hover:bg-slate-50 transition-colors">
                              <td className="px-6 py-4 text-slate-900 font-mono">
                                {new Date(item.recorded_at).toLocaleString('pt-BR')}
                              </td>
                              <td className="px-6 py-4 text-slate-600">
                                {item.location.latitude.toFixed(6)}, {item.location.longitude.toFixed(6)}
                              </td>
                              <td className="px-6 py-4">
                                <span className={`rounded-full px-2 py-0.5 text-[10px] font-bold uppercase ${item.connectivity_status === 'online' ? 'bg-green-100 text-green-700' : 'bg-amber-100 text-amber-700'}`}>
                                  {item.connectivity_status}
                                </span>
                              </td>
                              <td className="px-6 py-4 text-slate-500">
                                {item.accuracy_meters?.toFixed(1) || '--'}m
                              </td>
                              <td className="px-6 py-4">
                                <div className="flex items-center gap-1.5">
                                  <div className="h-1.5 w-8 rounded-full bg-slate-100">
                                    <div 
                                      className={`h-full rounded-full ${item.battery_level && item.battery_level < 20 ? 'bg-red-500' : 'bg-green-500'}`}
                                      style={{ width: `${item.battery_level || 0}%` }}
                                    />
                                  </div>
                                  <span className="text-[10px] text-slate-500">{item.battery_level}%</span>
                                </div>
                              </td>
                            </tr>
                          ))}
                          {geotrail.length === 0 && (
                            <tr>
                              <td colSpan={5} className="py-20 text-center text-slate-400 italic">
                                Nenhum registro encontrado para este periodo.
                              </td>
                            </tr>
                          )}
                        </tbody>
                      </table>
                    </div>
                  )}
                </div>
              </>
            )}

            {activeTab === 'movement' && <MovementAnalysisPanel />}
            {activeTab === 'coverage' && <CoverageMapPanel />}
            {activeTab === 'correlation' && <CorrelationPanel />}
            {activeTab === 'tactical' && <TacticalPositioningPanel />}
          </div>
        </main>
      </div>
    </ConsoleShell>
  );
}
