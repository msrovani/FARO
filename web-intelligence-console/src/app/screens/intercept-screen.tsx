"use client";

import { useState, useEffect } from "react";
import { interceptApi } from "@/app/services/api";
import { AlertTriangle, Shield, Eye, Clock, MapPin } from "lucide-react";
import MapBase from "../components/map/MapBase";

interface InterceptEvent {
  id: string;
  observation_id: string;
  plate_number: string;
  intercept_score: number;
  recommendation: "APPROACH" | "MONITOR" | "IGNORE";
  priority_level: "high" | "medium" | "low";
  decision: string;
  confidence: number;
  severity: string;
  explanation: string;
  false_positive_risk: string;
  triggers: {
    watchlist: boolean;
    route_anomaly: boolean;
    impossible_travel: boolean;
    sensitive_zone: boolean;
    convoy: boolean;
    roaming: boolean;
  };
  individual_scores: {
    watchlist?: number;
    route_anomaly?: number;
    impossible_travel?: number;
    sensitive_zone?: number;
    convoy?: number;
    roaming?: number;
  };
  time_factors: {
    time_of_day_risk?: number;
    day_of_week_risk?: number;
  };
  geographic_context: {
    nearby_critical_assets?: number;
    proximity_sensitive_zone?: boolean;
  };
  created_at: string;
}

export default function InterceptScreen() {
  const [events, setEvents] = useState<InterceptEvent[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [recommendationFilter, setRecommendationFilter] = useState<string>("");
  const [priorityFilter, setPriorityFilter] = useState<string>("");

  useEffect(() => {
    loadInterceptEvents();
  }, [recommendationFilter, priorityFilter]);

  const loadInterceptEvents = async () => {
    try {
      setLoading(true);
      const params: any = {};
      if (recommendationFilter) params.recommendation = recommendationFilter;
      if (priorityFilter) params.priority_level = priorityFilter;
      
      const data = await interceptApi.getInterceptEvents(params);
      setEvents(data);
    } catch (err) {
      setError("Falha ao carregar eventos INTERCEPT");
      console.error(err);
    } finally {
      setLoading(false);
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

  const getRecommendationIcon = (recommendation: string) => {
    switch (recommendation) {
      case "APPROACH": return <AlertTriangle className="h-4 w-4" />;
      case "MONITOR": return <Eye className="h-4 w-4" />;
      case "IGNORE": return <Shield className="h-4 w-4" />;
      default: return null;
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

  // Simple badge component
  const Badge = ({ children, className = "", variant = "default" }: { children: React.ReactNode; className?: string; variant?: string }) => (
    <span className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium ${className} ${
      variant === "destructive" ? "bg-red-100 text-red-800" :
      variant === "secondary" ? "bg-gray-100 text-gray-800" :
      variant === "outline" ? "border border-gray-300 text-gray-700" :
      "bg-blue-100 text-blue-800"
    }`}>
      {children}
    </span>
  );

  // Simple card components
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

  // Simple button component
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

  // Simple select components
  const Select = ({ children, value, onValueChange, className = "" }: { 
    children: React.ReactNode; 
    value: string; 
    onValueChange: (value: string) => void;
    className?: string;
  }) => (
    <select 
      value={value} 
      onChange={(e) => onValueChange(e.target.value)}
      className={`w-48 px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-1 focus:ring-blue-500 focus:border-blue-500 ${className}`}
    >
      {children}
    </select>
  );

  const SelectItem = ({ children, value }: { children: React.ReactNode; value: string }) => (
    <option value={value}>{children}</option>
  );

  if (loading) {
    return (
      <div className="container mx-auto p-6">
        <div className="animate-pulse">
          <div className="h-8 bg-gray-200 rounded mb-4"></div>
          <div className="space-y-4">
            {[1, 2, 3, 4, 5].map((i) => (
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
          <Button onClick={loadInterceptEvents} className="mt-2">
            Tentar novamente
          </Button>
        </div>
      </div>
    );
  }

  return (
    <div className="container mx-auto p-6">
      <div className="mb-6">
        <h1 className="text-3xl font-bold text-gray-900 mb-2">Algoritmo INTERCEPT</h1>
        <p className="text-gray-600">
          Análise combinada para recomendações de abordagem qualificada
        </p>
      </div>

      {/* Filters */}
      <div className="flex gap-4 mb-6">
        <Select value={recommendationFilter} onValueChange={setRecommendationFilter}>
          <SelectItem value="">Todas</SelectItem>
          <SelectItem value="APPROACH">Abordar</SelectItem>
          <SelectItem value="MONITOR">Monitorar</SelectItem>
          <SelectItem value="IGNORE">Ignorar</SelectItem>
        </Select>

        <Select value={priorityFilter} onValueChange={setPriorityFilter}>
          <SelectItem value="">Todas</SelectItem>
          <SelectItem value="high">Alta</SelectItem>
          <SelectItem value="medium">Média</SelectItem>
          <SelectItem value="low">Baixa</SelectItem>
        </Select>

        <Button onClick={loadInterceptEvents} variant="outline">
          Atualizar
        </Button>
      </div>

      {/* Map Overview */}
      <div className="mb-6">
        <Card>
          <CardHeader>
            <CardTitle>Visão Geográfica dos Eventos</CardTitle>
            <p className="text-sm text-gray-600">
              Localização aproximada dos eventos INTERCEPT recentes
            </p>
          </CardHeader>
          <CardContent>
            <div className="h-96">
              <MapBase 
                initialView={{ latitude: -23.5505, longitude: -46.6333, zoom: 10 }}
              >
                {/* Event markers would be rendered here */}
                {events.slice(0, 10).map((event, index) => (
                  <div key={event.id} className="absolute" style={{
                    left: `${20 + index * 8}%`,
                    top: `${30 + index * 5}%`,
                  }}>
                    <div className={`w-4 h-4 rounded-full ${
                      event.priority_level === 'high' ? 'bg-red-500' :
                      event.priority_level === 'medium' ? 'bg-yellow-500' :
                      'bg-blue-500'
                    }`} />
                  </div>
                ))}
              </MapBase>
            </div>
          </CardContent>
        </Card>
      </div>

      {/* Events List */}
      <div className="space-y-4">
        {events.length === 0 ? (
          <div className="text-center py-12">
            <Shield className="h-12 w-12 text-gray-400 mx-auto mb-4" />
            <p className="text-gray-500">
              Nenhum evento INTERCEPT encontrado com os filtros aplicados.
            </p>
          </div>
        ) : (
          events.map((event) => (
            <Card key={event.id} className={`border-2 ${getPriorityColor(event.priority_level)}`}>
              <CardHeader className="pb-3">
                <div className="flex items-center justify-between">
                  <div className="flex items-center gap-3">
                    <Badge className={getRecommendationColor(event.recommendation)}>
                      <div className="flex items-center gap-1">
                        {getRecommendationIcon(event.recommendation)}
                        <span>{event.recommendation}</span>
                      </div>
                    </Badge>
                    <div>
                      <CardTitle className="text-lg">{event.plate_number}</CardTitle>
                      <p className="text-sm text-gray-600">
                        Score: {formatScore(event.intercept_score)}% | Confiança: {formatScore(event.confidence)}%
                      </p>
                    </div>
                  </div>
                  <div className="text-right">
                    <Badge variant="outline" className="mb-1">
                      {event.severity}
                    </Badge>
                    <p className="text-xs text-gray-500">
                      {new Date(event.created_at).toLocaleString('pt-BR')}
                    </p>
                  </div>
                </div>
              </CardHeader>
              <CardContent>
                <p className="text-sm text-gray-700 mb-4">{event.explanation}</p>
                
                {/* Triggers */}
                <div className="mb-4">
                  <h4 className="text-sm font-semibold text-gray-900 mb-2">Triggers Ativados:</h4>
                  <div className="flex flex-wrap gap-2">
                    {event.triggers.watchlist && (
                      <Badge variant="secondary" className="text-xs">Watchlist</Badge>
                    )}
                    {event.triggers.impossible_travel && (
                      <Badge variant="destructive" className="text-xs">Viagem Impossível</Badge>
                    )}
                    {event.triggers.route_anomaly && (
                      <Badge variant="secondary" className="text-xs">Rota Anômala</Badge>
                    )}
                    {event.triggers.sensitive_zone && (
                      <Badge variant="secondary" className="text-xs">Zona Sensível</Badge>
                    )}
                    {event.triggers.convoy && (
                      <Badge variant="secondary" className="text-xs">Comboio</Badge>
                    )}
                    {event.triggers.roaming && (
                      <Badge variant="secondary" className="text-xs">Circulação</Badge>
                    )}
                  </div>
                </div>

                {/* Individual Scores */}
                <div className="mb-4">
                  <h4 className="text-sm font-semibold text-gray-900 mb-2">Scores Individuais:</h4>
                  <div className="grid grid-cols-3 gap-2 text-xs">
                    {event.individual_scores.watchlist && (
                      <div className="flex justify-between">
                        <span>Watchlist:</span>
                        <span className="font-mono">{formatScore(event.individual_scores.watchlist)}%</span>
                      </div>
                    )}
                    {event.individual_scores.impossible_travel && (
                      <div className="flex justify-between">
                        <span>Viagem Impossível:</span>
                        <span className="font-mono">{formatScore(event.individual_scores.impossible_travel)}%</span>
                      </div>
                    )}
                    {event.individual_scores.route_anomaly && (
                      <div className="flex justify-between">
                        <span>Rota Anômala:</span>
                        <span className="font-mono">{formatScore(event.individual_scores.route_anomaly)}%</span>
                      </div>
                    )}
                    {event.individual_scores.sensitive_zone && (
                      <div className="flex justify-between">
                        <span>Zona Sensível:</span>
                        <span className="font-mono">{formatScore(event.individual_scores.sensitive_zone)}%</span>
                      </div>
                    )}
                    {event.individual_scores.convoy && (
                      <div className="flex justify-between">
                        <span>Comboio:</span>
                        <span className="font-mono">{formatScore(event.individual_scores.convoy)}%</span>
                      </div>
                    )}
                    {event.individual_scores.roaming && (
                      <div className="flex justify-between">
                        <span>Circulação:</span>
                        <span className="font-mono">{formatScore(event.individual_scores.roaming)}%</span>
                      </div>
                    )}
                  </div>
                </div>

                {/* Context Factors */}
                <div className="flex items-center gap-4 text-xs text-gray-600">
                  <div className="flex items-center gap-1">
                    <Clock className="h-3 w-3" />
                    <span>Risco Temporal: {event.time_factors.time_of_day_risk ? formatScore(event.time_factors.time_of_day_risk) : 'N/A'}%</span>
                  </div>
                  <div className="flex items-center gap-1">
                    <MapPin className="h-3 w-3" />
                    <span>Zona Sensível: {event.geographic_context.proximity_sensitive_zone ? 'Sim' : 'Não'}</span>
                  </div>
                  <div>
                    <span>Risco Falso Positivo: {event.false_positive_risk}</span>
                  </div>
                </div>
              </CardContent>
            </Card>
          ))
        )}
      </div>
    </div>
  );
}
