"use client";

import React, { useState, useEffect } from "react";
import MapBase from "../components/map/MapBase";
import { TrendingUp, Calendar, Clock, MapPin, Search, AlertCircle } from "lucide-react";
import { routesApi } from "../services/api";

interface RoutePrediction {
  plate_number: string;
  predicted_corridor: [number, number][];
  confidence: number;
  predicted_hours: number[];
  predicted_days: number[];
  last_pattern_analyzed: string;
  pattern_strength: number;
}

export default function RoutePredictionPage() {
  const [prediction, setPrediction] = useState<RoutePrediction | null>(null);
  const [loading, setLoading] = useState(false);
  const [plateNumber, setPlateNumber] = useState("");
  const [daysAhead, setDaysAhead] = useState(7);
  const [error, setError] = useState<string | null>(null);

  const handlePredict = async () => {
    if (!plateNumber) return;
    setLoading(true);
    setError(null);
    try {
      const response = await routesApi.predict(plateNumber, daysAhead);
      setPrediction(response);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Erro ao buscar previsão de rota");
      setPrediction(null);
    } finally {
      setLoading(false);
    }
  };

  const dayNames = ["Dom", "Seg", "Ter", "Qua", "Qui", "Sex", "Sáb"];

  return (
    <div className="flex h-screen bg-gray-900">
      {/* Sidebar */}
      <div className="w-96 bg-gray-800 p-4 overflow-y-auto">
        <h1 className="text-xl font-bold text-white mb-4 flex items-center gap-2">
          <TrendingUp className="text-blue-500" />
          Previsão de Rotas
        </h1>

        {/* Search */}
        <div className="space-y-3 mb-6">
          <div>
            <label className="block text-sm text-gray-400 mb-1">Placa do Veículo</label>
            <div className="flex gap-2">
              <input
                type="text"
                value={plateNumber}
                onChange={(e) => setPlateNumber(e.target.value.toUpperCase())}
                placeholder="ABC-1234"
                className="flex-1 bg-gray-700 text-white px-3 py-2 rounded uppercase"
              />
              <button
                onClick={handlePredict}
                disabled={loading || !plateNumber}
                className="bg-blue-600 hover:bg-blue-700 text-white px-4 py-2 rounded disabled:opacity-50"
              >
                <Search size={20} />
              </button>
            </div>
          </div>
          <div>
            <label className="block text-sm text-gray-400 mb-1">Dias à Frente</label>
            <input
              type="number"
              value={daysAhead}
              onChange={(e) => setDaysAhead(parseInt(e.target.value))}
              min={1}
              max={30}
              className="w-full bg-gray-700 text-white px-3 py-2 rounded"
            />
          </div>
        </div>

        {/* Error Message */}
        {error && (
          <div className="bg-red-900/50 border border-red-700 rounded-lg p-3 flex items-center gap-2 text-red-200 text-sm mb-4">
            <AlertCircle size={16} />
            <span>{error}</span>
          </div>
        )}

        {/* Prediction Details */}
        {prediction && (
          <div className="space-y-4">
            <div className="bg-gray-700 rounded-lg p-4">
              <h3 className="text-sm font-semibold text-gray-300 mb-3">Detalhes da Previsão</h3>
              <div className="space-y-2 text-sm">
                <div className="flex justify-between">
                  <span className="text-gray-400">Placa:</span>
                  <span className="text-white font-semibold">{prediction.plate_number}</span>
                </div>
                <div className="flex justify-between">
                  <span className="text-gray-400">Confiança:</span>
                  <span className="text-white font-semibold text-green-400">
                    {(prediction.confidence * 100).toFixed(0)}%
                  </span>
                </div>
                <div className="flex justify-between">
                  <span className="text-gray-400">Força do Padrão:</span>
                  <span className="text-white font-semibold">
                    {(prediction.pattern_strength * 100).toFixed(0)}%
                  </span>
                </div>
                <div className="flex justify-between">
                  <span className="text-gray-400">Analisado em:</span>
                  <span className="text-white">
                    {new Date(prediction.last_pattern_analyzed).toLocaleString()}
                  </span>
                </div>
              </div>
            </div>

            {/* Predicted Hours */}
            <div className="bg-gray-700 rounded-lg p-4">
              <h3 className="text-sm font-semibold text-gray-300 mb-3 flex items-center gap-2">
                <Clock size={14} />
                Horas Previstas
              </h3>
              <div className="flex flex-wrap gap-2">
                {Array.from({ length: 24 }, (_, i) => (
                  <div
                    key={i}
                    className={`w-8 h-8 rounded flex items-center justify-center text-xs ${
                      prediction.predicted_hours.includes(i)
                        ? "bg-blue-600 text-white"
                        : "bg-gray-600 text-gray-400"
                    }`}
                  >
                    {i}
                  </div>
                ))}
              </div>
            </div>

            {/* Predicted Days */}
            <div className="bg-gray-700 rounded-lg p-4">
              <h3 className="text-sm font-semibold text-gray-300 mb-3 flex items-center gap-2">
                <Calendar size={14} />
                Dias Previstos
              </h3>
              <div className="flex flex-wrap gap-2">
                {dayNames.map((day, i) => (
                  <div
                    key={i}
                    className={`px-3 py-2 rounded text-sm ${
                      prediction.predicted_days.includes(i)
                        ? "bg-blue-600 text-white"
                        : "bg-gray-600 text-gray-400"
                    }`}
                  >
                    {day}
                  </div>
                ))}
              </div>
            </div>

            {/* Corridor Points */}
            <div className="bg-gray-700 rounded-lg p-4">
              <h3 className="text-sm font-semibold text-gray-300 mb-3 flex items-center gap-2">
                <MapPin size={14} />
                Corridor Previsto
              </h3>
              <div className="space-y-1 text-xs">
                {prediction.predicted_corridor.map((point, i) => (
                  <div key={i} className="flex justify-between text-gray-400">
                    <span>Ponto {i + 1}:</span>
                    <span>{point[1].toFixed(4)}, {point[0].toFixed(4)}</span>
                  </div>
                ))}
              </div>
            </div>

            {/* Actions */}
            <div className="space-y-2">
              <button className="w-full bg-green-600 hover:bg-green-700 text-white py-2 rounded text-sm">
                Ver Detalhes Completos
              </button>
              <button className="w-full bg-yellow-600 hover:bg-yellow-700 text-white py-2 rounded text-sm">
                Ver Drift de Padrão
              </button>
            </div>
          </div>
        )}
      </div>

      {/* Map */}
      <div className="flex-1">
        <MapBase initialView={{ latitude: -30.0346, longitude: -51.2177, zoom: 12 }}>
          {prediction && (
            <>
              {/* Predicted corridor line */}
              <div
                style={{
                  position: "absolute",
                  top: 0,
                  left: 0,
                  width: "100%",
                  height: "100%",
                  pointerEvents: "none",
                }}
              >
                <svg width="100%" height="100%">
                  <polyline
                    points={prediction.predicted_corridor
                      .map(p => `${(p[0] + 51.2177) * 10000},${(p[1] + 30.0346) * 10000}`)
                      .join(" ")}
                    fill="none"
                    stroke="#3b82f6"
                    strokeWidth="4"
                    strokeDasharray="10,5"
                    opacity={prediction.confidence}
                  />
                </svg>
              </div>

              {/* Corridor markers */}
              {prediction.predicted_corridor.map((point, i) => (
                <div
                  key={i}
                  style={{
                    position: "absolute",
                    left: "50%",
                    top: "50%",
                    transform: `translate(-50%, -50%)`,
                  }}
                >
                  <div
                    style={{
                      width: "16px",
                      height: "16px",
                      backgroundColor: "#3b82f6",
                      borderRadius: "50%",
                      border: "2px solid white",
                    }}
                  />
                </div>
              ))}
            </>
          )}
        </MapBase>

        {/* Legend */}
        {prediction && (
          <div className="absolute bottom-4 left-4 bg-gray-800 rounded-lg p-4 shadow-xl">
            <h4 className="text-white font-semibold text-sm mb-2">Legenda</h4>
            <div className="space-y-2 text-xs">
              <div className="flex items-center gap-2">
                <div
                  style={{
                    width: "20px",
                    height: "4px",
                    backgroundColor: "#3b82f6",
                    border: "1px dashed #3b82f6",
                  }}
                />
                <span className="text-gray-300">Corridor Previsto</span>
              </div>
              <div className="flex items-center gap-2">
                <div
                  style={{
                    width: "12px",
                    height: "12px",
                    backgroundColor: "#3b82f6",
                    borderRadius: "50%",
                    border: "2px solid white",
                  }}
                />
                <span className="text-gray-300">Pontos da Rota</span>
              </div>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}
