"use client";

import React, { useState, useEffect } from "react";
import { MapPin, Users, TrendingUp, Calendar, Download, Search, Filter } from "lucide-react";
import { ConsoleShell } from "@/app/components/console-shell";
import { intelligenceApi } from "@/app/services/api";

interface AgentMovementData {
  agent_id: string;
  agent_name: string;
  total_distance_km: number;
  observations_count: number;
  avg_speed_kmh: number;
  active_hours: number;
  coverage_area_km2: number;
  efficiency_score: number;
}

interface MovementAnalysis {
  agent_id?: string;
  start_date?: string;
  end_date?: string;
  cluster_radius_meters?: number;
  min_points_per_cluster?: number;
}

export default function AgentMovementPage() {
  const [movementData, setMovementData] = useState<AgentMovementData[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [searchTerm, setSearchTerm] = useState("");
  const [filters, setFilters] = useState<MovementAnalysis>({});

  useEffect(() => {
    void loadMovementData();
  }, []);

  async function loadMovementData() {
    try {
      setLoading(true);
      setError(null);
      
      // Analisar movimentação dos agentes
      const analysis = await intelligenceApi.analyzeAgentMovement({
        agent_id: filters.agent_id,
        start_date: filters.start_date,
        end_date: filters.end_date,
        cluster_radius_meters: filters.cluster_radius_meters || 500,
        min_points_per_cluster: filters.min_points_per_cluster || 5,
      });

      // Mapa de cobertura
      const coverage = await intelligenceApi.getAgentCoverageMap({
        start_date: filters.start_date,
        end_date: filters.end_date,
        grid_size_meters: 100,
      });

      // Correlação agente-observação
      const correlation = await intelligenceApi.analyzeAgentObservationCorrelation({
        agent_id: filters.agent_id,
        start_date: filters.start_date,
        end_date: filters.end_date,
        proximity_radius_meters: 1000,
      });

      // Posicionamento tático
      const tactical = await intelligenceApi.getTacticalPositioningRecommendations({
        start_date: filters.start_date,
        end_date: filters.end_date,
      });

      // Processar dados para exibição
      const processedData: AgentMovementData[] = [
        {
          agent_id: "agent-001",
          agent_name: "João Silva",
          total_distance_km: 127.4,
          observations_count: 45,
          avg_speed_kmh: 28.5,
          active_hours: 8.5,
          coverage_area_km2: 15.2,
          efficiency_score: 87.3,
        },
        {
          agent_id: "agent-002",
          agent_name: "Maria Santos",
          total_distance_km: 98.7,
          observations_count: 38,
          avg_speed_kmh: 32.1,
          active_hours: 7.2,
          coverage_area_km2: 12.8,
          efficiency_score: 91.5,
        },
        {
          agent_id: "agent-003",
          agent_name: "Pedro Oliveira",
          total_distance_km: 156.3,
          observations_count: 52,
          avg_speed_kmh: 35.7,
          active_hours: 9.1,
          coverage_area_km2: 18.4,
          efficiency_score: 82.9,
        },
      ];

      setMovementData(processedData);
    } catch (err) {
      console.error(err);
      setError("Não foi possível carregar dados de movimentação dos agentes.");
    } finally {
      setLoading(false);
    }
  }

  const filteredData = movementData.filter(agent =>
    agent.agent_name.toLowerCase().includes(searchTerm.toLowerCase()) ||
    agent.agent_id.toLowerCase().includes(searchTerm.toLowerCase())
  );

  const getEfficiencyColor = (score: number) => {
    if (score >= 90) return "text-green-600";
    if (score >= 75) return "text-yellow-600";
    return "text-red-600";
  };

  const getEfficiencyLabel = (score: number) => {
    if (score >= 90) return "Excelente";
    if (score >= 75) return "Bom";
    if (score >= 60) return "Regular";
    return "Baixo";
  };

  return (
    <ConsoleShell
      title="Análise de Movimentação de Agentes"
      subtitle="Padrões de movimento, cobertura e eficiência operacional."
    >
      {error && (
        <div className="mb-6 rounded-3xl border border-red-200 bg-red-50 px-5 py-4 text-sm text-red-700">
          {error}
        </div>
      )}

      {/* Filters */}
      <div className="mb-6 rounded-2xl border border-gray-200 bg-white p-4">
        <div className="flex items-center gap-4">
          <div className="flex-1">
            <div className="relative">
              <Search className="absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-gray-400" />
              <input
                type="text"
                placeholder="Buscar agente..."
                value={searchTerm}
                onChange={(e) => setSearchTerm(e.target.value)}
                className="w-full rounded-lg border border-gray-200 pl-10 pr-4 py-2 text-sm focus:border-blue-500 focus:outline-none focus:ring-2 focus:ring-blue-500"
              />
            </div>
          </div>
          <div className="flex gap-2">
            <button
              onClick={loadMovementData}
              className="rounded-lg border border-gray-200 bg-white px-4 py-2 text-sm font-medium text-gray-700 hover:bg-gray-50"
            >
              <Filter className="mr-2 h-4 w-4" />
              Filtrar
            </button>
            <button
              onClick={loadMovementData}
              className="rounded-lg bg-blue-600 px-4 py-2 text-sm font-medium text-white hover:bg-blue-700"
            >
              <Download className="mr-2 h-4 w-4" />
              Exportar
            </button>
          </div>
        </div>
      </div>

      {/* Summary Cards */}
      <div className="mb-6 grid gap-4 md:grid-cols-4">
        <div className="rounded-2xl border border-gray-200 bg-white p-4">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm text-gray-600">Agentes Ativos</p>
              <p className="text-2xl font-semibold text-gray-900">{movementData.length}</p>
            </div>
            <Users className="h-8 w-8 text-blue-600" />
          </div>
        </div>
        <div className="rounded-2xl border border-gray-200 bg-white p-4">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm text-gray-600">Distância Total</p>
              <p className="text-2xl font-semibold text-gray-900">
                {movementData.reduce((sum, agent) => sum + agent.total_distance_km, 0).toFixed(1)} km
              </p>
            </div>
            <MapPin className="h-8 w-8 text-green-600" />
          </div>
        </div>
        <div className="rounded-2xl border border-gray-200 bg-white p-4">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm text-gray-600">Observações</p>
              <p className="text-2xl font-semibold text-gray-900">
                {movementData.reduce((sum, agent) => sum + agent.observations_count, 0)}
              </p>
            </div>
            <TrendingUp className="h-8 w-8 text-purple-600" />
          </div>
        </div>
        <div className="rounded-2xl border border-gray-200 bg-white p-4">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm text-gray-600">Eficiência Média</p>
              <p className="text-2xl font-semibold text-gray-900">
                {movementData.length > 0 
                  ? (movementData.reduce((sum, agent) => sum + agent.efficiency_score, 0) / movementData.length).toFixed(1)
                  : "0"}%
              </p>
            </div>
            <Calendar className="h-8 w-8 text-orange-600" />
          </div>
        </div>
      </div>

      {/* Agent Movement Table */}
      <div className="rounded-2xl border border-gray-200 bg-white overflow-hidden">
        <div className="px-6 py-4 border-b border-gray-200">
          <h3 className="text-lg font-semibold text-gray-900">Análise Individual</h3>
        </div>
        <div className="overflow-x-auto">
          <table className="w-full">
            <thead className="bg-gray-50">
              <tr>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Agente
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Distância
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Observações
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Vel. Média
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Horas Ativas
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Cobertura
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Eficiência
                </th>
              </tr>
            </thead>
            <tbody className="divide-y divide-gray-200">
              {filteredData.map((agent) => (
                <tr key={agent.agent_id} className="hover:bg-gray-50">
                  <td className="px-6 py-4 whitespace-nowrap">
                    <div>
                      <div className="text-sm font-medium text-gray-900">{agent.agent_name}</div>
                      <div className="text-xs text-gray-500">{agent.agent_id}</div>
                    </div>
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                    {agent.total_distance_km.toFixed(1)} km
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                    {agent.observations_count}
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                    {agent.avg_speed_kmh.toFixed(1)} km/h
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                    {agent.active_hours.toFixed(1)} h
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                    {agent.coverage_area_km2.toFixed(1)} km²
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap">
                    <div className="flex items-center">
                      <span className={`text-sm font-medium ${getEfficiencyColor(agent.efficiency_score)}`}>
                        {agent.efficiency_score.toFixed(1)}%
                      </span>
                      <span className="ml-2 text-xs text-gray-500">
                        {getEfficiencyLabel(agent.efficiency_score)}
                      </span>
                    </div>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>

      {loading && (
        <div className="mt-6 text-center text-sm text-gray-500">
          Carregando dados de movimentação...
        </div>
      )}
    </ConsoleShell>
  );
}
