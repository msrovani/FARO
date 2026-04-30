"use client";

import { useState, useEffect } from "react";
import { MapPin, Users, Activity, Clock, Battery, Wifi, WifiOff } from "lucide-react";
import MapBase from "../components/map/MapBase";

interface AgentLocation {
  agent_id: string;
  full_name: string;
  badge_number: string;
  email: string;
  agency_id: string;
  agency_name: string;
  is_on_duty: boolean;
  last_seen: string;
  location: {
    latitude: number;
    longitude: number;
  };
  status: "off_duty" | "unknown" | "offline" | "inactive" | "highly_active" | "active" | "normal";
  activity_level: number;
  minutes_since_last_update: number | null;
}

interface CoveragePoint {
  latitude: number;
  longitude: number;
  unique_agents: number;
  total_locations: number;
  intensity: number;
}

interface MovementSummary {
  time_window_hours: number;
  agent_stats: {
    total_agents: number;
    agents_on_duty: number;
    agents_with_location: number;
  };
  activity_stats: {
    total_locations: number;
    active_agents: number;
    avg_locations_per_agent: number;
  };
  generated_at: string;
}

export default function AgentTrackingScreen() {
  const [agents, setAgents] = useState<AgentLocation[]>([]);
  const [coverage, setCoverage] = useState<CoveragePoint[]>([]);
  const [summary, setSummary] = useState<MovementSummary | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [viewMode, setViewMode] = useState<"live" | "coverage" | "summary">("live");
  const [filters, setFilters] = useState({
    onDutyOnly: true,
    minutesThreshold: 30,
    hours: 24
  });

  useEffect(() => {
    loadData();
  }, [viewMode, filters]);

  const loadData = async () => {
    try {
      setLoading(true);
      
      if (viewMode === "live") {
        const [agentsData, summaryData] = await Promise.all([
          fetchLiveLocations(),
          fetchMovementSummary()
        ]);
        setAgents(agentsData);
        setSummary(summaryData);
      } else if (viewMode === "coverage") {
        const coverageData = await fetchCoverageMap();
        setCoverage(coverageData);
      } else if (viewMode === "summary") {
        const summaryData = await fetchMovementSummary();
        setSummary(summaryData);
      }
    } catch (err) {
      setError("Falha ao carregar dados de geolocalização");
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  const fetchLiveLocations = async (): Promise<AgentLocation[]> => {
    const response = await fetch(`/api/v1/agents/live-locations?on_duty_only=${filters.onDutyOnly}&minutes_threshold=${filters.minutesThreshold}`);
    if (!response.ok) throw new Error("Failed to fetch live locations");
    return response.json();
  };

  const fetchCoverageMap = async (): Promise<CoveragePoint[]> => {
    const response = await fetch(`/api/v1/agents/coverage-map?hours=${filters.hours}&grid_size=0.01`);
    if (!response.ok) throw new Error("Failed to fetch coverage map");
    const data = await response.json();
    return data.coverage_points;
  };

  const fetchMovementSummary = async (): Promise<MovementSummary> => {
    const response = await fetch(`/api/v1/agents/movement-summary?hours=${filters.hours}`);
    if (!response.ok) throw new Error("Failed to fetch movement summary");
    return response.json();
  };

  const getStatusColor = (status: string) => {
    switch (status) {
      case "highly_active": return "bg-green-500 text-white";
      case "active": return "bg-blue-500 text-white";
      case "normal": return "bg-gray-500 text-white";
      case "inactive": return "bg-yellow-500 text-white";
      case "offline": return "bg-red-500 text-white";
      case "off_duty": return "bg-gray-300 text-gray-700";
      default: return "bg-gray-400 text-white";
    }
  };

  const getStatusIcon = (status: string) => {
    switch (status) {
      case "highly_active": return <Activity className="h-4 w-4" />;
      case "active": return <Activity className="h-4 w-4" />;
      case "offline": return <WifiOff className="h-4 w-4" />;
      case "off_duty": return <Clock className="h-4 w-4" />;
      default: return <MapPin className="h-4 w-4" />;
    }
  };

  const getStatusText = (status: string) => {
    switch (status) {
      case "highly_active": return "Altamente Ativo";
      case "active": return "Ativo";
      case "normal": return "Normal";
      case "inactive": return "Inativo";
      case "offline": return "Offline";
      case "off_duty": return "Fora de Serviço";
      default: return "Desconhecido";
    }
  };

  // Simple components to avoid UI library dependencies
  const Badge = ({ children, className = "" }: { children: React.ReactNode; className?: string }) => (
    <span className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium ${className}`}>
      {children}
    </span>
  );

  const Card = ({ children, className = "" }: { children: React.ReactNode; className?: string }) => (
    <div className={`rounded-lg border bg-white shadow-sm ${className}`}>
      {children}
    </div>
  );

  const CardHeader = ({ children, className = "" }: { children: React.ReactNode; className?: string }) => (
    <div className={`px-6 py-4 border-b ${className}`}>
      {children}
    </div>
  );

  const CardContent = ({ children, className = "" }: { children: React.ReactNode; className?: string }) => (
    <div className={`px-6 py-4 ${className}`}>
      {children}
    </div>
  );

  const CardTitle = ({ children, className = "" }: { children: React.ReactNode; className?: string }) => (
    <h3 className={`text-lg font-semibold text-gray-900 ${className}`}>
      {children}
    </h3>
  );

  const Button = ({ children, onClick, variant = "default", className = "" }: { 
    children: React.ReactNode; 
    onClick?: () => void; 
    variant?: string;
    className?: string;
  }) => (
    <button 
      onClick={onClick}
      className={`px-4 py-2 rounded-md text-sm font-medium transition-colors ${
        variant === "outline" ? "border border-gray-300 bg-white text-gray-700 hover:bg-gray-50" :
        "bg-blue-600 text-white hover:bg-blue-700"
      } ${className}`}
    >
      {children}
    </button>
  );

  if (loading) {
    return (
      <div className="container mx-auto p-6">
        <div className="animate-pulse">
          <div className="h-8 bg-gray-200 rounded mb-4"></div>
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            {[1, 2, 3, 4, 5, 6].map((i) => (
              <div key={i} className="h-32 bg-gray-200 rounded"></div>
            ))}
          </div>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="container mx-auto p-6">
        <div className="bg-red-50 border border-red-200 rounded-lg p-4">
          <p className="text-red-800">{error}</p>
          <Button onClick={loadData} className="mt-2">
            Tentar novamente
          </Button>
        </div>
      </div>
    );
  }

  return (
    <div className="container mx-auto p-6">
      <div className="mb-6">
        <h1 className="text-3xl font-bold text-gray-900 mb-2">Geolocalização de Agentes</h1>
        <p className="text-gray-600">
          Monitoramento em tempo real da localização e status dos agentes de campo
        </p>
      </div>

      {/* View Mode Selector */}
      <div className="flex gap-2 mb-6">
        <Button 
          onClick={() => setViewMode("live")} 
          variant={viewMode === "live" ? "default" : "outline"}
        >
          <Users className="h-4 w-4 mr-2" />
          Localizações ao Vivo
        </Button>
        <Button 
          onClick={() => setViewMode("coverage")} 
          variant={viewMode === "coverage" ? "default" : "outline"}
        >
          <MapPin className="h-4 w-4 mr-2" />
          Mapa de Cobertura
        </Button>
        <Button 
          onClick={() => setViewMode("summary")} 
          variant={viewMode === "summary" ? "default" : "outline"}
        >
          <Activity className="h-4 w-4 mr-2" />
          Resumo de Movimentação
        </Button>
      </div>

      {/* Filters */}
      <div className="flex gap-4 mb-6 p-4 bg-gray-50 rounded-lg">
        <div className="flex items-center gap-2">
          <label className="text-sm font-medium">Apenas em serviço:</label>
          <input
            type="checkbox"
            checked={filters.onDutyOnly}
            onChange={(e) => setFilters({...filters, onDutyOnly: e.target.checked})}
            className="rounded"
          />
        </div>
        <div className="flex items-center gap-2">
          <label className="text-sm font-medium">Threshold (min):</label>
          <input
            type="number"
            value={filters.minutesThreshold}
            onChange={(e) => setFilters({...filters, minutesThreshold: parseInt(e.target.value)})}
            className="w-20 px-2 py-1 border rounded"
            min="5"
            max="120"
          />
        </div>
        <div className="flex items-center gap-2">
          <label className="text-sm font-medium">Análise (horas):</label>
          <input
            type="number"
            value={filters.hours}
            onChange={(e) => setFilters({...filters, hours: parseInt(e.target.value)})}
            className="w-20 px-2 py-1 border rounded"
            min="1"
            max="168"
          />
        </div>
        <Button onClick={loadData}>Atualizar</Button>
      </div>

      {/* Live Locations View */}
      {viewMode === "live" && (
        <div className="space-y-6">
          {/* Summary Cards */}
          {summary && (
            <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
              <Card>
                <CardContent className="p-4">
                  <div className="flex items-center justify-between">
                    <div>
                      <p className="text-sm text-gray-600">Total de Agentes</p>
                      <p className="text-2xl font-bold">{summary.agent_stats.total_agents}</p>
                    </div>
                    <Users className="h-8 w-8 text-blue-500" />
                  </div>
                </CardContent>
              </Card>
              <Card>
                <CardContent className="p-4">
                  <div className="flex items-center justify-between">
                    <div>
                      <p className="text-sm text-gray-600">Em Serviço</p>
                      <p className="text-2xl font-bold text-green-600">{summary.agent_stats.agents_on_duty}</p>
                    </div>
                    <Activity className="h-8 w-8 text-green-500" />
                  </div>
                </CardContent>
              </Card>
              <Card>
                <CardContent className="p-4">
                  <div className="flex items-center justify-between">
                    <div>
                      <p className="text-sm text-gray-600">Com Localização</p>
                      <p className="text-2xl font-bold">{summary.agent_stats.agents_with_location}</p>
                    </div>
                    <MapPin className="h-8 w-8 text-purple-500" />
                  </div>
                </CardContent>
              </Card>
              <Card>
                <CardContent className="p-4">
                  <div className="flex items-center justify-between">
                    <div>
                      <p className="text-sm text-gray-600">Ativos</p>
                      <p className="text-2xl font-bold text-blue-600">{summary.activity_stats.active_agents}</p>
                    </div>
                    <Wifi className="h-8 w-8 text-blue-500" />
                  </div>
                </CardContent>
              </Card>
            </div>
          )}

          {/* Agents List */}
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
            {agents.map((agent) => (
              <Card key={agent.agent_id}>
                <CardHeader>
                  <div className="flex items-center justify-between">
                    <div>
                      <CardTitle className="text-base">{agent.full_name}</CardTitle>
                      <p className="text-sm text-gray-600">{agent.badge_number}</p>
                      <p className="text-xs text-gray-500">{agent.agency_name}</p>
                    </div>
                    <Badge className={getStatusColor(agent.status)}>
                      <div className="flex items-center gap-1">
                        {getStatusIcon(agent.status)}
                        <span>{getStatusText(agent.status)}</span>
                      </div>
                    </Badge>
                  </div>
                </CardHeader>
                <CardContent>
                  <div className="space-y-2 text-sm">
                    <div className="flex justify-between">
                      <span className="text-gray-600">Localização:</span>
                      <span className="font-mono">
                        {agent.location.latitude.toFixed(4)}, {agent.location.longitude.toFixed(4)}
                      </span>
                    </div>
                    <div className="flex justify-between">
                      <span className="text-gray-600">Última atualização:</span>
                      <span>{agent.minutes_since_last_update} min atrás</span>
                    </div>
                    <div className="flex justify-between">
                      <span className="text-gray-600">Nível de atividade:</span>
                      <span>{agent.activity_level} pontos</span>
                    </div>
                    <div className="flex justify-between">
                      <span className="text-gray-600">Status serviço:</span>
                      <span className={agent.is_on_duty ? "text-green-600" : "text-gray-500"}>
                        {agent.is_on_duty ? "Em serviço" : "Fora de serviço"}
                      </span>
                    </div>
                  </div>
                </CardContent>
              </Card>
            ))}
          </div>
        </div>
      )}

      {/* Coverage Map View */}
      {viewMode === "coverage" && (
        <div className="space-y-6">
          <Card>
            <CardHeader>
              <CardTitle>Mapa de Cobertura</CardTitle>
              <p className="text-sm text-gray-600">
                Análise de cobertura baseada em {filters.hours} horas de atividade
              </p>
            </CardHeader>
            <CardContent>
              <div className="h-96 mb-4">
                <MapBase 
                  initialView={{ latitude: -23.5505, longitude: -46.6333, zoom: 10 }}
                >
                  {/* Coverage points would be rendered here as markers */}
                  {coverage.map((point, index) => (
                    <div key={index} className="absolute" style={{
                      left: '50%',
                      top: '50%',
                      transform: 'translate(-50%, -50%)'
                    }}>
                      <div className="w-4 h-4 bg-blue-500 rounded-full opacity-50"></div>
                    </div>
                  ))}
                </MapBase>
              </div>
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                <div>
                  <h4 className="font-semibold mb-2">Estatísticas de Cobertura</h4>
                  <div className="space-y-2 text-sm">
                    <div className="flex justify-between">
                      <span>Pontos de cobertura:</span>
                      <span className="font-bold">{coverage.length}</span>
                    </div>
                    <div className="flex justify-between">
                      <span>Intensidade média:</span>
                      <span className="font-bold">
                        {coverage.length > 0 
                          ? (coverage.reduce((sum, p) => sum + p.intensity, 0) / coverage.length).toFixed(1)
                          : "0"}
                        </span>
                    </div>
                  </div>
                </div>
                <div>
                  <h4 className="font-semibold mb-2">Top Áreas de Atividade</h4>
                  <div className="space-y-1 text-sm">
                    {coverage
                      .sort((a, b) => b.total_locations - a.total_locations)
                      .slice(0, 5)
                      .map((point, index) => (
                        <div key={index} className="flex justify-between">
                          <span className="font-mono text-xs">
                            {point.latitude.toFixed(3)}, {point.longitude.toFixed(3)}
                          </span>
                          <span>{point.total_locations} pts</span>
                        </div>
                      ))}
                  </div>
                </div>
              </div>
            </CardContent>
          </Card>
        </div>
      )}

      {/* Movement Summary View */}
      {viewMode === "summary" && summary && (
        <div className="space-y-6">
          <Card>
            <CardHeader>
              <CardTitle>Resumo de Movimentação</CardTitle>
              <p className="text-sm text-gray-600">
                Análise das últimas {filters.hours} horas
              </p>
            </CardHeader>
            <CardContent>
              <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                <div>
                  <h4 className="font-semibold mb-4">Estatísticas de Agentes</h4>
                  <div className="space-y-3">
                    <div className="flex justify-between items-center p-3 bg-gray-50 rounded">
                      <span>Total de Agentes</span>
                      <span className="text-xl font-bold">{summary.agent_stats.total_agents}</span>
                    </div>
                    <div className="flex justify-between items-center p-3 bg-green-50 rounded">
                      <span>Agentes em Serviço</span>
                      <span className="text-xl font-bold text-green-600">{summary.agent_stats.agents_on_duty}</span>
                    </div>
                    <div className="flex justify-between items-center p-3 bg-blue-50 rounded">
                      <span>Com Localização</span>
                      <span className="text-xl font-bold text-blue-600">{summary.agent_stats.agents_with_location}</span>
                    </div>
                  </div>
                </div>
                <div>
                  <h4 className="font-semibold mb-4">Estatísticas de Atividade</h4>
                  <div className="space-y-3">
                    <div className="flex justify-between items-center p-3 bg-gray-50 rounded">
                      <span>Total de Localizações</span>
                      <span className="text-xl font-bold">{summary.activity_stats.total_locations}</span>
                    </div>
                    <div className="flex justify-between items-center p-3 bg-purple-50 rounded">
                      <span>Agentes Ativos</span>
                      <span className="text-xl font-bold text-purple-600">{summary.activity_stats.active_agents}</span>
                    </div>
                    <div className="flex justify-between items-center p-3 bg-orange-50 rounded">
                      <span>Média por Agente</span>
                      <span className="text-xl font-bold text-orange-600">
                        {summary.activity_stats.avg_locations_per_agent.toFixed(1)}
                      </span>
                    </div>
                  </div>
                </div>
              </div>
            </CardContent>
          </Card>
        </div>
      )}
    </div>
  );
}
