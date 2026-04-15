"use client";

import React, { useState, useEffect } from "react";
import MapBase from "../components/map/MapBase";
import AlertMarker from "../components/AlertMarker";
import { AlertOctagon, AlertTriangle, Filter, RefreshCw, Check, X } from "lucide-react";

interface Alert {
  alert_type: string;
  plate_number: string;
  severity: string;
  confidence: number;
  details: any;
  triggered_at: string;
  requires_review: boolean;
  location?: { latitude: number; longitude: number };
}

export default function AlertsPage() {
  const [alerts, setAlerts] = useState<Alert[]>([]);
  const [loading, setLoading] = useState(true);
  const [selectedAlert, setSelectedAlert] = useState<Alert | null>(null);
  const [filters, setFilters] = useState({
    alert_type: "",
    severity: "",
    requires_review: null as boolean | null,
  });

  // Mock data - replace with API call
  useEffect(() => {
    setTimeout(() => {
      setAlerts([
        {
          alert_type: "suspicious_route_match",
          plate_number: "ABC-1234",
          severity: "high",
          confidence: 0.9,
          details: {
            matched_routes: [
              { name: "Rota Tráfico Porto Alegre", risk_level: "high" },
            ],
            distance_meters: 50,
          },
          triggered_at: new Date().toISOString(),
          requires_review: true,
          location: { latitude: -30.0346, longitude: -51.2177 },
        },
        {
          alert_type: "pattern_drift",
          plate_number: "XYZ-5678",
          severity: "medium",
          confidence: 0.7,
          details: {
            drift_percent: 45,
            threshold_percent: 30,
            out_of_corridor_count: 8,
            total_recent_observations: 15,
          },
          triggered_at: new Date(Date.now() - 3600000).toISOString(),
          requires_review: true,
          location: { latitude: -30.0450, longitude: -51.2300 },
        },
        {
          alert_type: "recurring_route",
          plate_number: "DEF-9012",
          severity: "critical",
          confidence: 0.95,
          details: {
            recurrence_score: 0.92,
            pattern_strength: 0.88,
            primary_corridor: "Centro-Norte",
            predominant_direction: "inbound",
            observation_count: 67,
          },
          triggered_at: new Date(Date.now() - 7200000).toISOString(),
          requires_review: true,
          location: { latitude: -30.0250, longitude: -51.2050 },
        },
      ]);
      setLoading(false);
    }, 1000);
  }, []);

  const handleRefresh = () => {
    setLoading(true);
    setTimeout(() => setLoading(false), 1000);
  };

  const handleApproveAlert = (alert: Alert) => {
    setAlerts(alerts.map(a => 
      a === alert ? { ...a, requires_review: false } : a
    ));
  };

  const handleDismissAlert = (alert: Alert) => {
    setAlerts(alerts.filter(a => a !== alert));
  };

  const filteredAlerts = alerts.filter(alert => {
    if (filters.alert_type && alert.alert_type !== filters.alert_type) return false;
    if (filters.severity && alert.severity !== filters.severity) return false;
    if (filters.requires_review !== null && alert.requires_review !== filters.requires_review) return false;
    return true;
  });

  const getSeverityColor = (severity: string) => {
    switch (severity) {
      case "critical": return "text-red-500";
      case "high": return "text-orange-500";
      case "medium": return "text-yellow-500";
      case "low": return "text-green-500";
      default: return "text-gray-500";
    }
  };

  const getAlertIcon = (type: string) => {
    switch (type) {
      case "suspicious_route_match": return AlertOctagon;
      case "pattern_drift": return AlertTriangle;
      case "recurring_route": return AlertTriangle;
      default: return AlertOctagon;
    }
  };

  return (
    <div className="flex h-screen bg-gray-900">
      {/* Sidebar */}
      <div className="w-96 bg-gray-800 p-4 overflow-y-auto">
        <div className="flex items-center justify-between mb-4">
          <h1 className="text-xl font-bold text-white flex items-center gap-2">
            <AlertOctagon className="text-red-500" />
            Alertas
          </h1>
          <button
            onClick={handleRefresh}
            disabled={loading}
            className="bg-blue-600 hover:bg-blue-700 text-white p-2 rounded disabled:opacity-50"
          >
            <RefreshCw size={20} className={loading ? "animate-spin" : ""} />
          </button>
        </div>

        {/* Filters */}
        <div className="space-y-3 mb-4 p-3 bg-gray-700 rounded-lg">
          <h3 className="text-sm font-semibold text-gray-300 flex items-center gap-2">
            <Filter size={14} />
            Filtros
          </h3>
          <div>
            <label className="block text-xs text-gray-400 mb-1">Tipo de Alerta</label>
            <select
              value={filters.alert_type}
              onChange={(e) => setFilters({ ...filters, alert_type: e.target.value })}
              className="w-full bg-gray-600 text-white px-2 py-1 rounded text-sm"
            >
              <option value="">Todos</option>
              <option value="suspicious_route_match">Match de Rota</option>
              <option value="pattern_drift">Drift de Padrão</option>
              <option value="recurring_route">Rota Recorrente</option>
            </select>
          </div>
          <div>
            <label className="block text-xs text-gray-400 mb-1">Severidade</label>
            <select
              value={filters.severity}
              onChange={(e) => setFilters({ ...filters, severity: e.target.value })}
              className="w-full bg-gray-600 text-white px-2 py-1 rounded text-sm"
            >
              <option value="">Todas</option>
              <option value="critical">Crítico</option>
              <option value="high">Alto</option>
              <option value="medium">Médio</option>
              <option value="low">Baixo</option>
            </select>
          </div>
          <div>
            <label className="block text-xs text-gray-400 mb-1">Revisão</label>
            <select
              value={filters.requires_review === null ? "" : filters.requires_review.toString()}
              onChange={(e) => setFilters({ 
                ...filters, 
                requires_review: e.target.value === "" ? null : e.target.value === "true"
              })}
              className="w-full bg-gray-600 text-white px-2 py-1 rounded text-sm"
            >
              <option value="">Todos</option>
              <option value="true">Pendente</option>
              <option value="false">Revisado</option>
            </select>
          </div>
        </div>

        {/* Summary */}
        <div className="bg-gray-700 rounded-lg p-3 mb-4">
          <h3 className="text-sm font-semibold text-gray-300 mb-2">Resumo</h3>
          <div className="grid grid-cols-2 gap-2 text-xs">
            <div className="bg-gray-600 p-2 rounded">
              <div className="text-gray-400">Total</div>
              <div className="text-white font-bold text-lg">{alerts.length}</div>
            </div>
            <div className="bg-red-900 p-2 rounded">
              <div className="text-gray-400">Críticos</div>
              <div className="text-white font-bold text-lg">
                {alerts.filter(a => a.severity === "critical").length}
              </div>
            </div>
            <div className="bg-orange-900 p-2 rounded">
              <div className="text-gray-400">Altos</div>
              <div className="text-white font-bold text-lg">
                {alerts.filter(a => a.severity === "high").length}
              </div>
            </div>
            <div className="bg-yellow-900 p-2 rounded">
              <div className="text-gray-400">Pendentes</div>
              <div className="text-white font-bold text-lg">
                {alerts.filter(a => a.requires_review).length}
              </div>
            </div>
          </div>
        </div>

        {/* Alerts List */}
        <div>
          <h3 className="text-sm font-semibold text-gray-300 mb-2">
            Alertas ({filteredAlerts.length})
          </h3>
          <div className="space-y-2">
            {filteredAlerts.map((alert, index) => {
              const Icon = getAlertIcon(alert.alert_type);
              return (
                <div
                  key={index}
                  onClick={() => setSelectedAlert(alert)}
                  className={`p-3 rounded-lg cursor-pointer transition ${
                    selectedAlert === alert ? "bg-red-600" : "bg-gray-700 hover:bg-gray-600"
                  }`}
                >
                  <div className="flex justify-between items-center mb-2">
                    <div className="flex items-center gap-2">
                      <Icon size={14} className="text-white" />
                      <span className="text-white font-semibold text-sm">{alert.plate_number}</span>
                    </div>
                    {alert.requires_review && (
                      <div className="w-2 h-2 bg-yellow-400 rounded-full animate-pulse" />
                    )}
                  </div>
                  <div className="text-xs text-gray-400 space-y-1">
                    <div className="flex justify-between">
                      <span>Tipo:</span>
                      <span>{alert.alert_type}</span>
                    </div>
                    <div className="flex justify-between">
                      <span>Severidade:</span>
                      <span className={getSeverityColor(alert.severity)}>{alert.severity}</span>
                    </div>
                    <div className="flex justify-between">
                      <span>Confiança:</span>
                      <span>{(alert.confidence * 100).toFixed(0)}%</span>
                    </div>
                  </div>
                </div>
              );
            })}
          </div>
        </div>
      </div>

      {/* Map */}
      <div className="flex-1">
        <MapBase initialView={{ latitude: -30.0346, longitude: -51.2177, zoom: 12 }}>
          {filteredAlerts.map((alert, index) => (
            <AlertMarker
              key={index}
              alert={alert}
              location={alert.location}
              onClick={() => setSelectedAlert(alert)}
            />
          ))}
        </MapBase>

        {/* Selected Alert Details */}
        {selectedAlert && (
          <div className="absolute bottom-4 right-4 bg-gray-800 rounded-lg p-4 shadow-xl w-80">
            <h3 className="text-white font-bold mb-3 flex items-center gap-2">
              <AlertOctagon size={16} className="text-red-500" />
              Detalhes do Alerta
            </h3>
            <div className="space-y-2 text-sm">
              <div className="flex justify-between">
                <span className="text-gray-400">Tipo:</span>
                <span className="text-white">{selectedAlert.alert_type}</span>
              </div>
              <div className="flex justify-between">
                <span className="text-gray-400">Placa:</span>
                <span className="text-white font-semibold">{selectedAlert.plate_number}</span>
              </div>
              <div className="flex justify-between">
                <span className="text-gray-400">Severidade:</span>
                <span className={`font-semibold ${getSeverityColor(selectedAlert.severity)}`}>
                  {selectedAlert.severity}
                </span>
              </div>
              <div className="flex justify-between">
                <span className="text-gray-400">Confiança:</span>
                <span className="text-white">{(selectedAlert.confidence * 100).toFixed(0)}%</span>
              </div>
              <div className="flex justify-between">
                <span className="text-gray-400">Revisão:</span>
                <span className="text-white">{selectedAlert.requires_review ? "Sim" : "Não"}</span>
              </div>
              <div className="flex justify-between">
                <span className="text-gray-400">Data:</span>
                <span className="text-white">{new Date(selectedAlert.triggered_at).toLocaleString()}</span>
              </div>
              {selectedAlert.location && (
                <div className="pt-2 border-t border-gray-700">
                  <span className="text-gray-400">Localização:</span>
                  <div className="text-white text-xs mt-1">
                    {selectedAlert.location.latitude.toFixed(4)}, {selectedAlert.location.longitude.toFixed(4)}
                  </div>
                </div>
              )}
            </div>
            <div className="pt-3 border-t border-gray-700 mt-3 flex gap-2">
              <button
                onClick={() => handleApproveAlert(selectedAlert)}
                className="flex-1 bg-green-600 hover:bg-green-700 text-white py-2 rounded text-xs"
              >
                <Check size={12} className="inline mr-1" />
                Aprovar
              </button>
              <button
                onClick={() => handleDismissAlert(selectedAlert)}
                className="flex-1 bg-red-600 hover:bg-red-700 text-white py-2 rounded text-xs"
              >
                <X size={12} className="inline mr-1" />
                Dispensar
              </button>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}
