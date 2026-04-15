"use client";

import React, { useState, useEffect } from "react";
import MapBase from "../components/map/MapBase";
import { MapPin, Calendar, Clock, Filter, Check, X, Repeat } from "lucide-react";

interface RoamingEvent {
  id: string;
  observation_id: string;
  plate_number: string;
  area_label: string;
  recurrence_count: number;
  decision: string;
  confidence: number;
  severity: string;
  explanation: string;
  false_positive_risk: number;
  location?: { latitude: number; longitude: number };
  created_at: string;
}

export default function RoamingEventsPage() {
  const [roamingEvents, setRoamingEvents] = useState<RoamingEvent[]>([]);
  const [loading, setLoading] = useState(true);
  const [selectedEvent, setSelectedEvent] = useState<RoamingEvent | null>(null);
  const [filters, setFilters] = useState({
    decision: "",
    severity: "",
    min_recurrence: 0,
  });

  // Mock data - replace with API call
  useEffect(() => {
    setTimeout(() => {
      setRoamingEvents([
        {
          id: "1",
          observation_id: "obs-001",
          plate_number: "ABC-1234",
          area_label: "Centro Histórico",
          recurrence_count: 25,
          decision: "confirmed",
          confidence: 0.88,
          severity: "high",
          explanation: "Veículo frequentemente observado em área restrita",
          false_positive_risk: 0.12,
          location: { latitude: -30.0346, longitude: -51.2177 },
          created_at: new Date().toISOString(),
        },
        {
          id: "2",
          observation_id: "obs-002",
          plate_number: "DEF-5678",
          area_label: "Zona Industrial Norte",
          recurrence_count: 18,
          decision: "pending",
          confidence: 0.75,
          severity: "medium",
          explanation: "Padrão de roaming detectado em zona industrial",
          false_positive_risk: 0.25,
          location: { latitude: -30.0450, longitude: -51.2300 },
          created_at: new Date(Date.now() - 3600000).toISOString(),
        },
        {
          id: "3",
          observation_id: "obs-003",
          plate_number: "GHI-9012",
          area_label: "Zona Portuária",
          recurrence_count: 32,
          decision: "rejected",
          confidence: 0.40,
          severity: "low",
          explanation: "Veículo de entrega regular, não suspeito",
          false_positive_risk: 0.60,
          location: { latitude: -30.0250, longitude: -51.2050 },
          created_at: new Date(Date.now() - 7200000).toISOString(),
        },
      ]);
      setLoading(false);
    }, 1000);
  }, []);

  const handleApproveEvent = (event: RoamingEvent) => {
    setRoamingEvents(roamingEvents.map(e => 
      e.id === event.id ? { ...e, decision: "confirmed" } : e
    ));
  };

  const handleRejectEvent = (event: RoamingEvent) => {
    setRoamingEvents(roamingEvents.map(e => 
      e.id === event.id ? { ...e, decision: "rejected" } : e
    ));
  };

  const filteredEvents = roamingEvents.filter(event => {
    if (filters.decision && event.decision !== filters.decision) return false;
    if (filters.severity && event.severity !== filters.severity) return false;
    if (event.recurrence_count < filters.min_recurrence) return false;
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

  const getDecisionColor = (decision: string) => {
    switch (decision) {
      case "confirmed": return "bg-green-900 text-green-400";
      case "rejected": return "bg-red-900 text-red-400";
      case "pending": return "bg-yellow-900 text-yellow-400";
      default: return "bg-gray-700 text-gray-400";
    }
  };

  return (
    <div className="flex h-screen bg-gray-900">
      {/* Sidebar */}
      <div className="w-96 bg-gray-800 p-4 overflow-y-auto">
        <h1 className="text-xl font-bold text-white mb-4 flex items-center gap-2">
          <Repeat className="text-cyan-500" />
          Eventos de Roaming
        </h1>

        {/* Filters */}
        <div className="space-y-3 mb-4 p-3 bg-gray-700 rounded-lg">
          <h3 className="text-sm font-semibold text-gray-300 flex items-center gap-2">
            <Filter size={14} />
            Filtros
          </h3>
          <div>
            <label className="block text-xs text-gray-400 mb-1">Decisão</label>
            <select
              value={filters.decision}
              onChange={(e) => setFilters({ ...filters, decision: e.target.value })}
              className="w-full bg-gray-600 text-white px-2 py-1 rounded text-sm"
            >
              <option value="">Todas</option>
              <option value="confirmed">Confirmado</option>
              <option value="pending">Pendente</option>
              <option value="rejected">Rejeitado</option>
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
            <label className="block text-xs text-gray-400 mb-1">Mínimo Recorrências</label>
            <input
              type="number"
              value={filters.min_recurrence}
              onChange={(e) => setFilters({ ...filters, min_recurrence: parseInt(e.target.value) })}
              min={0}
              className="w-full bg-gray-600 text-white px-2 py-1 rounded text-sm"
            />
          </div>
        </div>

        {/* Summary */}
        <div className="bg-gray-700 rounded-lg p-3 mb-4">
          <h3 className="text-sm font-semibold text-gray-300 mb-2">Resumo</h3>
          <div className="grid grid-cols-2 gap-2 text-xs">
            <div className="bg-gray-600 p-2 rounded">
              <div className="text-gray-400">Total</div>
              <div className="text-white font-bold text-lg">{roamingEvents.length}</div>
            </div>
            <div className="bg-green-900 p-2 rounded">
              <div className="text-gray-400">Confirmados</div>
              <div className="text-white font-bold text-lg">
                {roamingEvents.filter(e => e.decision === "confirmed").length}
              </div>
            </div>
            <div className="bg-yellow-900 p-2 rounded">
              <div className="text-gray-400">Pendentes</div>
              <div className="text-white font-bold text-lg">
                {roamingEvents.filter(e => e.decision === "pending").length}
              </div>
            </div>
            <div className="bg-red-900 p-2 rounded">
              <div className="text-gray-400">Rejeitados</div>
              <div className="text-white font-bold text-lg">
                {roamingEvents.filter(e => e.decision === "rejected").length}
              </div>
            </div>
          </div>
        </div>

        {/* Events List */}
        <div>
          <h3 className="text-sm font-semibold text-gray-300 mb-2">
            Eventos ({filteredEvents.length})
          </h3>
          <div className="space-y-2">
            {filteredEvents.map((event) => (
              <div
                key={event.id}
                onClick={() => setSelectedEvent(event)}
                className={`p-3 rounded-lg cursor-pointer transition ${
                  selectedEvent?.id === event.id ? "bg-cyan-600" : "bg-gray-700 hover:bg-gray-600"
                }`}
              >
                <div className="flex justify-between items-center mb-2">
                  <span className="text-white font-semibold text-sm">{event.plate_number}</span>
                  <span className={`px-2 py-1 rounded text-xs ${getDecisionColor(event.decision)}`}>
                    {event.decision}
                  </span>
                </div>
                <div className="text-xs text-gray-400 space-y-1">
                  <div className="flex justify-between">
                    <span>Área:</span>
                    <span className="text-white">{event.area_label}</span>
                  </div>
                  <div className="flex justify-between">
                    <span>Recorrências:</span>
                    <span className="text-white">{event.recurrence_count}</span>
                  </div>
                  <div className="flex justify-between">
                    <span>Confiança:</span>
                    <span className="text-white">{(event.confidence * 100).toFixed(0)}%</span>
                  </div>
                  <div className="flex justify-between">
                    <span>Severidade:</span>
                    <span className={getSeverityColor(event.severity)}>{event.severity}</span>
                  </div>
                </div>
              </div>
            ))}
          </div>
        </div>
      </div>

      {/* Map */}
      <div className="flex-1">
        <MapBase initialView={{ latitude: -30.0346, longitude: -51.2177, zoom: 12 }}>
          {/* Roaming event markers */}
          {filteredEvents.map((event) => (
            <div
              key={event.id}
              style={{
                position: "absolute",
                left: "50%",
                top: "50%",
                transform: `translate(-50%, -50%)`,
              }}
            >
              <div
                onClick={() => setSelectedEvent(event)}
                className="cursor-pointer"
                style={{
                  width: "40px",
                  height: "40px",
                  backgroundColor: event.decision === "confirmed" ? "#22c55e" : 
                                   event.decision === "rejected" ? "#ef4444" : "#eab308",
                  borderRadius: "50%",
                  border: "3px solid white",
                  display: "flex",
                  alignItems: "center",
                  justifyContent: "center",
                  boxShadow: "0 4px 6px rgba(0, 0, 0, 0.4)",
                }}
              >
                <Repeat size={20} color="white" />
              </div>
            </div>
          ))}
        </MapBase>

        {/* Selected Event Details */}
        {selectedEvent && (
          <div className="absolute bottom-4 right-4 bg-gray-800 rounded-lg p-4 shadow-xl w-80">
            <h3 className="text-white font-bold mb-3 flex items-center gap-2">
              <Repeat size={16} className="text-cyan-500" />
              Detalhes do Roaming
            </h3>
            <div className="space-y-2 text-sm">
              <div className="flex justify-between">
                <span className="text-gray-400">Placa:</span>
                <span className="text-white font-semibold">{selectedEvent.plate_number}</span>
              </div>
              <div className="flex justify-between">
                <span className="text-gray-400">Área:</span>
                <span className="text-white">{selectedEvent.area_label}</span>
              </div>
              <div className="flex justify-between">
                <span className="text-gray-400">Recorrências:</span>
                <span className="text-white">{selectedEvent.recurrence_count}</span>
              </div>
              <div className="flex justify-between">
                <span className="text-gray-400">Decisão:</span>
                <span className={`px-2 py-1 rounded text-xs ${getDecisionColor(selectedEvent.decision)}`}>
                  {selectedEvent.decision}
                </span>
              </div>
              <div className="flex justify-between">
                <span className="text-gray-400">Confiança:</span>
                <span className="text-white">{(selectedEvent.confidence * 100).toFixed(0)}%</span>
              </div>
              <div className="flex justify-between">
                <span className="text-gray-400">Severidade:</span>
                <span className={`font-semibold ${getSeverityColor(selectedEvent.severity)}`}>
                  {selectedEvent.severity}
                </span>
              </div>
              <div className="flex justify-between">
                <span className="text-gray-400">Risco Falso Positivo:</span>
                <span className="text-white">{(selectedEvent.false_positive_risk * 100).toFixed(0)}%</span>
              </div>
              <div className="pt-2 border-t border-gray-700">
                <span className="text-gray-400">Explicação:</span>
                <p className="text-white text-xs mt-1">{selectedEvent.explanation}</p>
              </div>
              {selectedEvent.location && (
                <div className="pt-2 border-t border-gray-700">
                  <span className="text-gray-400">Localização:</span>
                  <div className="text-white text-xs mt-1">
                    {selectedEvent.location.latitude.toFixed(4)}, {selectedEvent.location.longitude.toFixed(4)}
                  </div>
                </div>
              )}
            </div>
            <div className="pt-3 border-t border-gray-700 mt-3 flex gap-2">
              <button
                onClick={() => handleApproveEvent(selectedEvent)}
                disabled={selectedEvent.decision === "confirmed"}
                className="flex-1 bg-green-600 hover:bg-green-700 text-white py-2 rounded text-xs disabled:opacity-50"
              >
                <Check size={12} className="inline mr-1" />
                Confirmar
              </button>
              <button
                onClick={() => handleRejectEvent(selectedEvent)}
                disabled={selectedEvent.decision === "rejected"}
                className="flex-1 bg-red-600 hover:bg-red-700 text-white py-2 rounded text-xs disabled:opacity-50"
              >
                <X size={12} className="inline mr-1" />
                Rejeitar
              </button>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}
