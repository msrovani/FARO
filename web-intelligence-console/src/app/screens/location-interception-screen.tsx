"use client";

import { useState, useEffect } from "react";
import { MapPin, Users, AlertTriangle, Radar, Clock, Navigation, Shield, Bell, List } from "lucide-react";
import MapBase from "../components/map/MapBase";

interface LocationAlert {
  intercept_event_id: string;
  plate_number: string;
  location: {
    latitude: number;
    longitude: number;
  };
  distance_km: number;
  intercept_score: number;
  recommendation: "APPROACH" | "MONITOR" | "IGNORE";
  priority_level: "high" | "medium" | "low";
  created_at: string;
}

interface NearbyAgent {
  agent_id: string;
  full_name: string;
  badge_number: string;
  agency_id: string;
  agency_name: string;
  city: string;
  location: {
    latitude: number;
    longitude: number;
  };
  recorded_at: string;
  distance_meters: number;
  distance_km: number;
  within_radius: boolean;
}

interface AlertSummary {
  time_window_hours: number;
  total_alerts: number;
  by_recommendation: {
    [key: string]: {
      count: number;
      avg_score: number;
    };
  };
  by_priority: {
    high: { count: number; avg_score: number };
    medium: { count: number; avg_score: number };
    low: { count: number; avg_score: number };
  };
  generated_at: string;
}

export default function LocationInterceptionScreen() {
  const [alerts, setAlerts] = useState<LocationAlert[]>([]);
  const [nearbyAgents, setNearbyAgents] = useState<NearbyAgent[]>([]);
  const [summary, setSummary] = useState<AlertSummary | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [viewMode, setViewMode] = useState<"map" | "list" | "summary">("map");
  const [selectedAlert, setSelectedAlert] = useState<LocationAlert | null>(null);
  const [filters, setFilters] = useState({
    latitude: -23.5505, // São Paulo default
    longitude: -46.6333,
    radiusKm: 50,
    hours: 24
  });

  useEffect(() => {
    loadData();
  }, [viewMode, filters]);

  const loadData = async () => {
    try {
      setLoading(true);
      
      if (viewMode === "map") {
        const [alertsData, summaryData] = await Promise.all([
          fetchLocationAlerts(),
          fetchAlertSummary()
        ]);
        setAlerts(alertsData);
        setSummary(summaryData);
      } else if (viewMode === "list") {
        const alertsData = await fetchLocationAlerts();
        setAlerts(alertsData);
      } else if (viewMode === "summary") {
        const summaryData = await fetchAlertSummary();
        setSummary(summaryData);
      }
    } catch (err) {
      setError("Falha ao carregar dados de interceptação por localização");
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  const fetchLocationAlerts = async (): Promise<LocationAlert[]> => {
    const response = await fetch(
      `/api/v1/intelligence/location-interception/location-alerts?` +
      `latitude=${filters.latitude}&longitude=${filters.longitude}&` +
      `radius_km=${filters.radiusKm}&hours=${filters.hours}`
    );
    if (!response.ok) throw new Error("Failed to fetch location alerts");
    return response.json();
  };

  const fetchNearbyAgents = async (eventId: string): Promise<NearbyAgent[]> => {
    const response = await fetch(
      `/api/v1/intelligence/location-interception/nearby-agents/${eventId}?radius_km=${filters.radiusKm}`
    );
    if (!response.ok) throw new Error("Failed to fetch nearby agents");
    return response.json();
  };

  const fetchAlertSummary = async (): Promise<AlertSummary> => {
    const response = await fetch(
      `/api/v1/intelligence/location-interception/alert-summary?hours=${filters.hours}`
    );
    if (!response.ok) throw new Error("Failed to fetch alert summary");
    return response.json();
  };

  const handleAlertClick = async (alert: LocationAlert) => {
    setSelectedAlert(alert);
    try {
      const agents = await fetchNearbyAgents(alert.intercept_event_id);
      setNearbyAgents(agents);
    } catch (err) {
      console.error("Failed to fetch nearby agents:", err);
    }
  };

  const getRecommendationColor = (recommendation: string) => {
    switch (recommendation) {
      case "APPROACH": return "bg-red-500 text-white";
      case "MONITOR": return "bg-yellow-500 text-white";
      case "IGNORE": return "bg-green-500 text-white";
      default: return "bg-gray-500 text-white";
    }
  };

  const getPriorityColor = (priority: string) => {
    switch (priority) {
      case "high": return "border-red-200 bg-red-50";
      case "medium": return "border-yellow-200 bg-yellow-50";
      case "low": return "border-green-200 bg-green-50";
      default: return "border-gray-200 bg-gray-50";
    }
  };

  const formatScore = (score: number) => (score * 100).toFixed(1);

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
        <h1 className="text-3xl font-bold text-gray-900 mb-2">Interceptação por Localização</h1>
        <p className="text-gray-600">
          Alertas INTERCEPT direcionados com base em geolocalização e contexto urbano/rodoviário
        </p>
      </div>

      {/* View Mode Selector */}
      <div className="flex gap-2 mb-6">
        <Button 
          onClick={() => setViewMode("map")} 
          variant={viewMode === "map" ? "default" : "outline"}
        >
          <MapPin className="h-4 w-4 mr-2" />
          Mapa de Alertas
        </Button>
        <Button 
          onClick={() => setViewMode("list")} 
          variant={viewMode === "list" ? "default" : "outline"}
        >
          <List className="h-4 w-4 mr-2" />
          Lista de Alertas
        </Button>
        <Button 
          onClick={() => setViewMode("summary")} 
          variant={viewMode === "summary" ? "default" : "outline"}
        >
          <Radar className="h-4 w-4 mr-2" />
            Resumo
        </Button>
      </div>

      {/* Location Filters */}
      <div className="flex gap-4 mb-6 p-4 bg-gray-50 rounded-lg">
        <div className="flex items-center gap-2">
          <label className="text-sm font-medium">Latitude:</label>
          <input
            type="number"
            step="0.0001"
            value={filters.latitude}
            onChange={(e) => setFilters({...filters, latitude: parseFloat(e.target.value)})}
            className="w-32 px-2 py-1 border rounded"
          />
        </div>
        <div className="flex items-center gap-2">
          <label className="text-sm font-medium">Longitude:</label>
          <input
            type="number"
            step="0.0001"
            value={filters.longitude}
            onChange={(e) => setFilters({...filters, longitude: parseFloat(e.target.value)})}
            className="w-32 px-2 py-1 border rounded"
          />
        </div>
        <div className="flex items-center gap-2">
          <label className="text-sm font-medium">Raio (km):</label>
          <input
            type="number"
            value={filters.radiusKm}
            onChange={(e) => setFilters({...filters, radiusKm: parseInt(e.target.value)})}
            className="w-20 px-2 py-1 border rounded"
            min="1"
            max="200"
          />
        </div>
        <div className="flex items-center gap-2">
          <label className="text-sm font-medium">Horas:</label>
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

      {/* Map View */}
      {viewMode === "map" && (
        <div className="space-y-6">
          {/* Summary Cards */}
          {summary && (
            <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
              <Card>
                <CardContent className="p-4">
                  <div className="flex items-center justify-between">
                    <div>
                      <p className="text-sm text-gray-600">Total de Alertas</p>
                      <p className="text-2xl font-bold">{summary.total_alerts}</p>
                    </div>
                    <Bell className="h-8 w-8 text-blue-500" />
                  </div>
                </CardContent>
              </Card>
              <Card>
                <CardContent className="p-4">
                  <div className="flex items-center justify-between">
                    <div>
                      <p className="text-sm text-gray-600">Abordar</p>
                      <p className="text-2xl font-bold text-red-600">
                        {summary.by_recommendation.APPROACH?.count || 0}
                      </p>
                    </div>
                    <AlertTriangle className="h-8 w-8 text-red-500" />
                  </div>
                </CardContent>
              </Card>
              <Card>
                <CardContent className="p-4">
                  <div className="flex items-center justify-between">
                    <div>
                      <p className="text-sm text-gray-600">Monitorar</p>
                      <p className="text-2xl font-bold text-yellow-600">
                        {summary.by_recommendation.MONITOR?.count || 0}
                      </p>
                    </div>
                    <Shield className="h-8 w-8 text-yellow-500" />
                  </div>
                </CardContent>
              </Card>
              <Card>
                <CardContent className="p-4">
                  <div className="flex items-center justify-between">
                    <div>
                      <p className="text-sm text-gray-600">Prioridade Alta</p>
                      <p className="text-2xl font-bold text-red-600">
                        {summary.by_priority.high.count}
                      </p>
                    </div>
                    <Navigation className="h-8 w-8 text-red-500" />
                  </div>
                </CardContent>
              </Card>
            </div>
          )}

          {/* Alerts Map */}
          <Card>
            <CardHeader>
              <CardTitle>Mapa de Alertas na Área</CardTitle>
              <p className="text-sm text-gray-600">
                Alertas INTERCEPT em {filters.radiusKm}km raio de ({filters.latitude.toFixed(3)}, {filters.longitude.toFixed(3)})
              </p>
            </CardHeader>
            <CardContent>
              <div className="h-96">
                <MapBase 
                  initialView={{ 
                    latitude: filters.latitude, 
                    longitude: filters.longitude, 
                    zoom: 12 
                  }}
                >
                  {/* Alert markers would be rendered here */}
                  {alerts.map((alert, index) => (
                    <div key={alert.intercept_event_id} className="absolute" style={{
                      left: '50%',
                      top: '50%',
                      transform: 'translate(-50%, -50%)'
                    }}>
                      <div className={`w-4 h-4 rounded-full ${
                        alert.priority_level === 'high' ? 'bg-red-500' :
                        alert.priority_level === 'medium' ? 'bg-yellow-500' :
                        'bg-blue-500'
                      }`} />
                    </div>
                  ))}
                </MapBase>
              </div>
              
              {/* Alert List Below Map */}
              <div className="mt-6 space-y-3">
                <h4 className="font-semibold">Alertas na Área ({alerts.length})</h4>
                {alerts.map((alert) => (
                  <div 
                    key={alert.intercept_event_id}
                    className={`border rounded-lg p-4 cursor-pointer transition-colors hover:bg-gray-50 ${getPriorityColor(alert.priority_level)}`}
                    onClick={() => handleAlertClick(alert)}
                  >
                    <div className="flex items-center justify-between">
                      <div className="flex items-center gap-3">
                        <Badge className={getRecommendationColor(alert.recommendation)}>
                          {alert.recommendation}
                        </Badge>
                        <div>
                          <p className="font-semibold">{alert.plate_number}</p>
                          <p className="text-sm text-gray-600">
                            {alert.distance_km.toFixed(1)}km do centro • Score: {formatScore(alert.intercept_score)}%
                          </p>
                        </div>
                      </div>
                      <div className="text-right">
                        <p className="text-sm text-gray-500">
                          {new Date(alert.created_at).toLocaleString('pt-BR')}
                        </p>
                        <p className="text-xs text-gray-400">
                          {alert.priority_level.toUpperCase()}
                        </p>
                      </div>
                    </div>
                  </div>
                ))}
              </div>
            </CardContent>
          </Card>
        </div>
      )}

      {/* List View */}
      {viewMode === "list" && (
        <div className="space-y-4">
          <div className="flex justify-between items-center">
            <h3 className="text-lg font-semibold">Alertas de Interceptação ({alerts.length})</h3>
            <div className="text-sm text-gray-600">
              Raio: {filters.radiusKm}km • Período: {filters.hours}h
            </div>
          </div>
          
          {alerts.map((alert) => (
            <Card key={alert.intercept_event_id} className={`cursor-pointer transition-colors hover:shadow-md ${getPriorityColor(alert.priority_level)}`}>
              <CardContent className="p-6">
                <div className="flex items-center justify-between">
                  <div className="flex items-center gap-4">
                    <Badge className={getRecommendationColor(alert.recommendation)}>
                      {alert.recommendation}
                    </Badge>
                    <div>
                      <h4 className="font-semibold text-lg">{alert.plate_number}</h4>
                      <div className="flex items-center gap-4 text-sm text-gray-600 mt-1">
                        <span className="flex items-center gap-1">
                          <MapPin className="h-3 w-3" />
                          {alert.distance_km.toFixed(1)}km
                        </span>
                        <span className="flex items-center gap-1">
                          <Radar className="h-3 w-3" />
                          Score: {formatScore(alert.intercept_score)}%
                        </span>
                        <span className="flex items-center gap-1">
                          <Clock className="h-3 w-3" />
                          {new Date(alert.created_at).toLocaleString('pt-BR')}
                        </span>
                      </div>
                    </div>
                  </div>
                  <div className="text-right">
                    <Badge className={`${getPriorityColor(alert.priority_level)} border mb-1`}>
                      {alert.priority_level.toUpperCase()}
                    </Badge>
                    <p className="text-xs text-gray-500 mt-1">
                      {alert.location.latitude.toFixed(4)}, {alert.location.longitude.toFixed(4)}
                    </p>
                  </div>
                </div>
              </CardContent>
            </Card>
          ))}
        </div>
      )}

      {/* Summary View */}
      {viewMode === "summary" && summary && (
        <div className="space-y-6">
          <Card>
            <CardHeader>
              <CardTitle>Resumo de Alertas de Interceptação</CardTitle>
              <p className="text-sm text-gray-600">
                Análise das últimas {filters.hours} horas
              </p>
            </CardHeader>
            <CardContent>
              <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                <div>
                  <h4 className="font-semibold mb-4">Por Recomendação</h4>
                  <div className="space-y-3">
                    {Object.entries(summary.by_recommendation).map(([rec, data]) => (
                      <div key={rec} className="flex justify-between items-center p-3 bg-gray-50 rounded">
                        <div className="flex items-center gap-2">
                          <Badge className={getRecommendationColor(rec)}>
                            {rec}
                          </Badge>
                          <span className="font-medium">{data.count} alertas</span>
                        </div>
                        <span className="text-sm text-gray-600">
                          Score médio: {formatScore(data.avg_score)}%
                        </span>
                      </div>
                    ))}
                  </div>
                </div>
                <div>
                  <h4 className="font-semibold mb-4">Por Prioridade</h4>
                  <div className="space-y-3">
                    {Object.entries(summary.by_priority).map(([priority, data]) => (
                      <div key={priority} className="flex justify-between items-center p-3 bg-gray-50 rounded">
                        <div className="flex items-center gap-2">
                          <Badge className={`${getPriorityColor(priority)} border`}>
                            {priority.toUpperCase()}
                          </Badge>
                          <span className="font-medium">{data.count} alertas</span>
                        </div>
                        <span className="text-sm text-gray-600">
                          Score médio: {formatScore(data.avg_score)}%
                        </span>
                      </div>
                    ))}
                  </div>
                </div>
              </div>
            </CardContent>
          </Card>
        </div>
      )}

      {/* Selected Alert Detail */}
      {selectedAlert && (
        <Card className="mt-6 border-blue-200">
          <CardHeader>
            <CardTitle>Detalhes do Alerta - {selectedAlert.plate_number}</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
              <div>
                <h4 className="font-semibold mb-3">Informações do Alerta</h4>
                <div className="space-y-2 text-sm">
                  <div className="flex justify-between">
                    <span className="text-gray-600">Placa:</span>
                    <span className="font-medium">{selectedAlert.plate_number}</span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-gray-600">Recomendação:</span>
                    <Badge className={getRecommendationColor(selectedAlert.recommendation)}>
                      {selectedAlert.recommendation}
                    </Badge>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-gray-600">Prioridade:</span>
                    <Badge variant="outline" className={getPriorityColor(selectedAlert.priority_level)}>
                      {selectedAlert.priority_level.toUpperCase()}
                    </Badge>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-gray-600">Score INTERCEPT:</span>
                    <span className="font-medium">{formatScore(selectedAlert.intercept_score)}%</span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-gray-600">Localização:</span>
                    <span className="font-mono text-xs">
                      {selectedAlert.location.latitude.toFixed(4)}, {selectedAlert.location.longitude.toFixed(4)}
                    </span>
                  </div>
                </div>
              </div>
              <div>
                <h4 className="font-semibold mb-3">Agentes Próximos ({nearbyAgents.length})</h4>
                <div className="space-y-2 max-h-48 overflow-y-auto">
                  {nearbyAgents.map((agent) => (
                    <div key={agent.agent_id} className="flex justify-between items-center p-2 bg-gray-50 rounded text-sm">
                      <div>
                        <span className="font-medium">{agent.full_name}</span>
                        <span className="text-gray-600 ml-2">({agent.badge_number})</span>
                      </div>
                      <div className="text-right">
                        <span className="text-gray-600">{agent.distance_km.toFixed(1)}km</span>
                        <span className="text-xs text-gray-500 block">{agent.agency_name}</span>
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            </div>
          </CardContent>
        </Card>
      )}
    </div>
  );
}
