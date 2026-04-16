"use client";

import React, { useState, useEffect } from "react";
import MapBase from "../components/map/MapBase";
import HotspotMarker from "../components/map/HotspotMarker";
import { Activity, MapPin, Clock, Users, AlertTriangle, Play, Pause } from "lucide-react";

interface HotspotPoint {
  latitude: number;
  longitude: number;
  observation_count: number;
  suspicion_count: number;
  unique_plates: number;
  radius_meters: number;
  intensity_score: number;
}

interface HotspotAnalysisResult {
  hotspots: HotspotPoint[];
  total_observations: number;
  total_suspicions: number;
  analysis_period_days: number;
  cluster_radius_meters: number;
  min_points_per_cluster: number;
}

export default function HotspotsPage() {
  const [hotspots, setHotspots] = useState<HotspotPoint[]>([]);
  const [loading, setLoading] = useState(true);
  const [selectedHotspot, setSelectedHotspot] = useState<HotspotPoint | null>(null);
  const [filters, setFilters] = useState({
    clusterRadius: 500,
    minPoints: 5,
    days: 30,
  });
  const [timeRange, setTimeRange] = useState(24);
  const [isPlaying, setIsPlaying] = useState(false);

  // Mock data - replace with API call
  useEffect(() => {
    setTimeout(() => {
      setHotspots([
        {
          latitude: -30.0346,
          longitude: -51.2177,
          observation_count: 45,
          suspicion_count: 12,
          unique_plates: 28,
          radius_meters: 500,
          intensity_score: 0.85,
        },
        {
          latitude: -30.0450,
          longitude: -51.2300,
          observation_count: 32,
          suspicion_count: 8,
          unique_plates: 19,
          radius_meters: 500,
          intensity_score: 0.65,
        },
        {
          latitude: -30.0250,
          longitude: -51.2050,
          observation_count: 28,
          suspicion_count: 15,
          unique_plates: 22,
          radius_meters: 500,
          intensity_score: 0.72,
        },
      ]);
      setLoading(false);
    }, 1000);
  }, []);

  const handleAnalyze = async () => {
    setLoading(true);
    // Replace with actual API call
    // const response = await fetch('/api/intelligence/hotspots/analyze', { ... });
    setTimeout(() => setLoading(false), 1000);
  };

  useEffect(() => {
    let interval: any;
    if (isPlaying) {
      interval = setInterval(() => {
        setTimeRange((prev) => (prev > 0 ? prev - 1 : 24));
      }, 800);
    }
    return () => clearInterval(interval);
  }, [isPlaying]);

  return (
    <div className="flex h-screen bg-gray-900">
      {/* Sidebar */}
      <div className="w-80 bg-gray-800 p-4 overflow-y-auto">
        <h1 className="text-xl font-bold text-white mb-4 flex items-center gap-2">
          <Activity className="text-red-500" />
          Hotspots de Criminalidade
        </h1>

        {/* Filters */}
        <div className="space-y-4 mb-6">
          <div>
            <label className="block text-sm text-gray-400 mb-1">Raio de Clustering (m)</label>
            <input
              type="number"
              value={filters.clusterRadius}
              onChange={(e) => setFilters({ ...filters, clusterRadius: parseInt(e.target.value) })}
              className="w-full bg-gray-700 text-white px-3 py-2 rounded"
            />
          </div>
          <div>
            <label className="block text-sm text-gray-400 mb-1">Mínimo de Pontos</label>
            <input
              type="number"
              value={filters.minPoints}
              onChange={(e) => setFilters({ ...filters, minPoints: parseInt(e.target.value) })}
              className="w-full bg-gray-700 text-white px-3 py-2 rounded"
            />
          </div>
          <div>
            <label className="block text-sm text-gray-400 mb-1">Período (dias)</label>
            <input
              type="number"
              value={filters.days}
              onChange={(e) => setFilters({ ...filters, days: parseInt(e.target.value) })}
              className="w-full bg-gray-700 text-white px-3 py-2 rounded"
            />
          </div>

          <div className="pt-4 border-t border-gray-700">
            <div className="flex justify-between items-center mb-2">
              <label className="text-sm font-semibold text-gray-300 flex items-center gap-2">
                <Clock size={16} />
                Timeline (h)
              </label>
              <button 
                onClick={() => setIsPlaying(!isPlaying)}
                className="p-1 rounded bg-gray-600 hover:bg-gray-500 text-white"
              >
                {isPlaying ? <Pause size={14} /> : <Play size={14} />}
              </button>
            </div>
            <input
              type="range"
              min="0"
              max="24"
              value={timeRange}
              onChange={(e) => setTimeRange(parseInt(e.target.value))}
              className="w-full accent-red-500"
            />
            <div className="flex justify-between text-[10px] text-gray-500 mt-1 uppercase font-bold tracking-widest">
              <span>H-24</span>
              <span>H-12</span>
              <span>Agora</span>
            </div>
          </div>
          <button
            onClick={handleAnalyze}
            disabled={loading}
            className="w-full bg-red-600 hover:bg-red-700 text-white py-2 rounded font-semibold"
          >
            {loading ? "Analisando..." : "Analisar Hotspots"}
          </button>
        </div>

        {/* Statistics */}
        <div className="bg-gray-700 rounded-lg p-4 mb-4">
          <h3 className="text-sm font-semibold text-gray-300 mb-3">Estatísticas</h3>
          <div className="space-y-2">
            <div className="flex justify-between text-sm">
              <span className="text-gray-400 flex items-center gap-1">
                <MapPin size={14} />
                Hotspots
              </span>
              <span className="text-white font-semibold">{hotspots.length}</span>
            </div>
            <div className="flex justify-between text-sm">
              <span className="text-gray-400 flex items-center gap-1">
                <Activity size={14} />
                Total Observações
              </span>
              <span className="text-white font-semibold">
                {hotspots.reduce((sum, h) => sum + h.observation_count, 0)}
              </span>
            </div>
            <div className="flex justify-between text-sm">
              <span className="text-gray-400 flex items-center gap-1">
                <AlertTriangle size={14} />
                Total Suspeitas
              </span>
              <span className="text-white font-semibold">
                {hotspots.reduce((sum, h) => sum + h.suspicion_count, 0)}
              </span>
            </div>
            <div className="flex justify-between text-sm">
              <span className="text-gray-400 flex items-center gap-1">
                <Users size={14} />
                Placas Únicas
              </span>
              <span className="text-white font-semibold">
                {hotspots.reduce((sum, h) => sum + h.unique_plates, 0)}
              </span>
            </div>
          </div>
        </div>

        {/* Hotspots List */}
        <div>
          <h3 className="text-sm font-semibold text-gray-300 mb-2">Hotspots Detectados</h3>
          <div className="space-y-2">
            {hotspots.map((hotspot, index) => (
              <div
                key={index}
                onClick={() => setSelectedHotspot(hotspot)}
                className={`p-3 rounded-lg cursor-pointer transition ${
                  selectedHotspot === hotspot ? "bg-red-600" : "bg-gray-700 hover:bg-gray-600"
                }`}
              >
                <div className="flex justify-between items-center mb-1">
                  <span className="text-white font-semibold text-sm">Hotspot #{index + 1}</span>
                  <span className="text-xs text-gray-300">
                    {(hotspot.intensity_score * 100).toFixed(0)}%
                  </span>
                </div>
                <div className="text-xs text-gray-400 space-y-1">
                  <div className="flex justify-between">
                    <span>Observações:</span>
                    <span>{hotspot.observation_count}</span>
                  </div>
                  <div className="flex justify-between">
                    <span>Suspeitas:</span>
                    <span>{hotspot.suspicion_count}</span>
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
          {hotspots.map((hotspot, index) => (
            <HotspotMarker
              key={index}
              hotspot={hotspot}
              onClick={() => setSelectedHotspot(hotspot)}
            />
          ))}
        </MapBase>
      </div>

      {/* Selected Hotspot Details */}
      {selectedHotspot && (
        <div className="absolute bottom-4 right-4 bg-gray-800 rounded-lg p-4 shadow-xl w-72">
          <h3 className="text-white font-bold mb-3 flex items-center gap-2">
            <MapPin size={16} className="text-red-500" />
            Detalhes do Hotspot
          </h3>
          <div className="space-y-2 text-sm">
            <div className="flex justify-between">
              <span className="text-gray-400">Intensidade:</span>
              <span className="text-white font-semibold">
                {(selectedHotspot.intensity_score * 100).toFixed(0)}%
              </span>
            </div>
            <div className="flex justify-between">
              <span className="text-gray-400">Observações:</span>
              <span className="text-white font-semibold">{selectedHotspot.observation_count}</span>
            </div>
            <div className="flex justify-between">
              <span className="text-gray-400">Suspeitas:</span>
              <span className="text-white font-semibold">{selectedHotspot.suspicion_count}</span>
            </div>
            <div className="flex justify-between">
              <span className="text-gray-400">Placas Únicas:</span>
              <span className="text-white font-semibold">{selectedHotspot.unique_plates}</span>
            </div>
            <div className="flex justify-between">
              <span className="text-gray-400">Raio:</span>
              <span className="text-white font-semibold">{selectedHotspot.radius_meters}m</span>
            </div>
            <div className="pt-2 border-t border-gray-700">
              <button className="w-full bg-blue-600 hover:bg-blue-700 text-white py-2 rounded text-sm">
                Ver Timeline
              </button>
              <button className="w-full bg-green-600 hover:bg-green-700 text-white py-2 rounded text-sm mt-2">
                Ver Placas
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
