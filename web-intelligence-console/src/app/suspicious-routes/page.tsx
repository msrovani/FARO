"use client";

import React, { useState, useEffect } from "react";
import MapBase from "../components/map/MapBase";
import RouteMarker from "../components/RouteMarker";
import { Route, Plus, Edit, Trash2, Check, X, Filter } from "lucide-react";
import { suspiciousRoutesApi } from "@/app/services/api";

interface SuspiciousRoutePoint {
  latitude: number;
  longitude: number;
}

interface SuspiciousRoute {
  id: string;
  name: string;
  crime_type: string;
  risk_level: string;
  route_points: SuspiciousRoutePoint[];
  direction: string;
  is_active: boolean;
  approval_status: string;
  justification?: string;
}

export default function SuspiciousRoutesPage() {
  const [routes, setRoutes] = useState<SuspiciousRoute[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [selectedRoute, setSelectedRoute] = useState<SuspiciousRoute | null>(null);
  const [isCreating, setIsCreating] = useState(false);
  const [newRoutePoints, setNewRoutePoints] = useState<SuspiciousRoutePoint[]>([]);
  const [filters, setFilters] = useState({
    crime_type: "",
    risk_level: "",
    approval_status: "",
    is_active: null as boolean | null,
  });

  const loadRoutes = async () => {
    setLoading(true);
    setError(null);
    try {
      const response = await suspiciousRoutesApi.list({
        crime_type: filters.crime_type || undefined,
        risk_level: filters.risk_level || undefined,
        approval_status: filters.approval_status || undefined,
        is_active: filters.is_active === null ? undefined : filters.is_active,
        page: 1,
        page_size: 100,
      });
      setRoutes(response.routes as SuspiciousRoute[]);
    } catch (err) {
      console.error(err);
      setError("Nao foi possivel carregar rotas suspeitas reais.");
      setRoutes([]);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    void loadRoutes();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [filters.crime_type, filters.risk_level, filters.approval_status, filters.is_active]);

  const handleMapClick = (e: any) => {
    if (isCreating) {
      const { lng, lat } = e.lngLat;
      setNewRoutePoints([...newRoutePoints, { latitude: lat, longitude: lng }]);
    }
  };

  const handleCreateRoute = () => {
    setIsCreating(true);
    setNewRoutePoints([]);
  };

  const handleSaveRoute = async () => {
    if (newRoutePoints.length < 2) {
      alert("Mínimo de 2 pontos necessários");
      return;
    }
    try {
      setLoading(true);
      setError(null);
      await suspiciousRoutesApi.create({
        name: `Nova Rota ${new Date().toLocaleString()}`,
        crime_type: "other",
        risk_level: "medium",
        direction: "bidirectional",
        route_points: newRoutePoints,
      });
      setIsCreating(false);
      setNewRoutePoints([]);
      await loadRoutes();
    } catch (err) {
      console.error(err);
      setError("Falha ao criar rota suspeita.");
      setLoading(false);
    }
  };

  const handleCancelCreate = () => {
    setIsCreating(false);
    setNewRoutePoints([]);
  };

  const handleDeleteRoute = async (id: string) => {
    if (confirm("Tem certeza que deseja desativar esta rota?")) {
      try {
        setLoading(true);
        setError(null);
        await suspiciousRoutesApi.remove(id);
        await loadRoutes();
      } catch (err) {
        console.error(err);
        setError("Falha ao desativar rota.");
        setLoading(false);
      }
    }
  };

  const handleApproveRoute = async (id: string) => {
    try {
      setLoading(true);
      setError(null);
      await suspiciousRoutesApi.approve(id, { approval_status: "approved" });
      await loadRoutes();
    } catch (err) {
      console.error(err);
      setError("Falha ao aprovar rota.");
      setLoading(false);
    }
  };

  const filteredRoutes = routes.filter(route => {
    if (filters.crime_type && route.crime_type !== filters.crime_type) return false;
    if (filters.risk_level && route.risk_level !== filters.risk_level) return false;
    if (filters.approval_status && route.approval_status !== filters.approval_status) return false;
    if (filters.is_active !== null && route.is_active !== filters.is_active) return false;
    return true;
  });

  return (
    <div className="flex h-screen bg-gray-900">
      {/* Sidebar */}
      <div className="w-96 bg-gray-800 p-4 overflow-y-auto">
        <div className="flex items-center justify-between mb-4">
          <h1 className="text-xl font-bold text-white flex items-center gap-2">
            <Route className="text-red-500" />
            Rotas Suspeitas
          </h1>
          <button
            onClick={handleCreateRoute}
            disabled={isCreating}
            className="bg-green-600 hover:bg-green-700 text-white p-2 rounded"
          >
            <Plus size={20} />
          </button>
        </div>

        {/* Filters */}
        <div className="space-y-3 mb-4 p-3 bg-gray-700 rounded-lg">
          <h3 className="text-sm font-semibold text-gray-300 flex items-center gap-2">
            <Filter size={14} />
            Filtros
          </h3>
          <div>
            <label className="block text-xs text-gray-400 mb-1">Tipo de Crime</label>
            <select
              value={filters.crime_type}
              onChange={(e) => setFilters({ ...filters, crime_type: e.target.value })}
              className="w-full bg-gray-600 text-white px-2 py-1 rounded text-sm"
            >
              <option value="">Todos</option>
              <option value="drug_trafficking">Tráfico</option>
              <option value="escape">Fuga</option>
              <option value="contraband">Contrabando</option>
              <option value="other">Outro</option>
            </select>
          </div>
          <div>
            <label className="block text-xs text-gray-400 mb-1">Nível de Risco</label>
            <select
              value={filters.risk_level}
              onChange={(e) => setFilters({ ...filters, risk_level: e.target.value })}
              className="w-full bg-gray-600 text-white px-2 py-1 rounded text-sm"
            >
              <option value="">Todos</option>
              <option value="critical">Crítico</option>
              <option value="high">Alto</option>
              <option value="medium">Médio</option>
              <option value="low">Baixo</option>
            </select>
          </div>
          <div>
            <label className="block text-xs text-gray-400 mb-1">Status</label>
            <select
              value={filters.approval_status}
              onChange={(e) => setFilters({ ...filters, approval_status: e.target.value })}
              className="w-full bg-gray-600 text-white px-2 py-1 rounded text-sm"
            >
              <option value="">Todos</option>
              <option value="approved">Aprovado</option>
              <option value="pending">Pendente</option>
              <option value="rejected">Rejeitado</option>
            </select>
          </div>
        </div>

        {/* Creating Mode */}
        {isCreating && (
          <div className="bg-blue-900 p-3 rounded-lg mb-4">
            <h3 className="text-sm font-semibold text-white mb-2">Criando Nova Rota</h3>
            <p className="text-xs text-gray-300 mb-2">Clique no mapa para adicionar pontos</p>
            <div className="flex gap-2">
              <button
                onClick={handleSaveRoute}
                disabled={newRoutePoints.length < 2}
                className="flex-1 bg-green-600 hover:bg-green-700 text-white py-2 rounded text-xs disabled:opacity-50"
              >
                <Check size={14} className="inline mr-1" />
                Salvar
              </button>
              <button
                onClick={handleCancelCreate}
                className="flex-1 bg-red-600 hover:bg-red-700 text-white py-2 rounded text-xs"
              >
                <X size={14} className="inline mr-1" />
                Cancelar
              </button>
            </div>
            <p className="text-xs text-gray-400 mt-2">Pontos: {newRoutePoints.length}</p>
          </div>
        )}

        {/* Routes List */}
        <div>
          {error && (
            <div className="mb-3 rounded-lg border border-red-500/40 bg-red-900/20 p-3 text-xs text-red-200">
              {error}
            </div>
          )}
          <h3 className="text-sm font-semibold text-gray-300 mb-2">
            Rotas ({filteredRoutes.length})
          </h3>
          <div className="space-y-2">
            {filteredRoutes.map((route) => (
              <div
                key={route.id}
                onClick={() => setSelectedRoute(route)}
                className={`p-3 rounded-lg cursor-pointer transition ${
                  selectedRoute?.id === route.id ? "bg-red-600" : "bg-gray-700 hover:bg-gray-600"
                }`}
              >
                <div className="flex justify-between items-center mb-2">
                  <span className="text-white font-semibold text-sm">{route.name}</span>
                  <div className="flex gap-1">
                    <button
                      onClick={(e) => {
                        e.stopPropagation();
                        handleApproveRoute(route.id);
                      }}
                      className="p-1 hover:bg-gray-600 rounded"
                      title="Aprovar"
                    >
                      <Check size={12} className="text-green-400" />
                    </button>
                    <button
                      onClick={(e) => {
                        e.stopPropagation();
                        handleDeleteRoute(route.id);
                      }}
                      className="p-1 hover:bg-gray-600 rounded"
                      title="Desativar"
                    >
                      <Trash2 size={12} className="text-red-400" />
                    </button>
                  </div>
                </div>
                <div className="text-xs text-gray-400 space-y-1">
                  <div className="flex justify-between">
                    <span>Tipo:</span>
                    <span>{route.crime_type}</span>
                  </div>
                  <div className="flex justify-between">
                    <span>Risco:</span>
                    <span className={
                      route.risk_level === "critical" ? "text-red-500" :
                      route.risk_level === "high" ? "text-orange-500" :
                      route.risk_level === "medium" ? "text-yellow-500" : "text-green-500"
                    }>
                      {route.risk_level}
                    </span>
                  </div>
                  <div className="flex justify-between">
                    <span>Status:</span>
                    <span className={
                      route.approval_status === "approved" ? "text-green-400" :
                      route.approval_status === "pending" ? "text-yellow-400" : "text-red-400"
                    }>
                      {route.approval_status}
                    </span>
                  </div>
                </div>
              </div>
            ))}
          </div>
        </div>
      </div>

      {/* Map */}
      <div className="flex-1 relative">
        <MapBase
          initialView={{ latitude: -30.0346, longitude: -51.2177, zoom: 12 }}
          onClick={handleMapClick}
        >
          {routes.map((route) => (
            <RouteMarker
              key={route.id}
              route={route}
              onClick={() => setSelectedRoute(route)}
            />
          ))}
          
          {/* New route being created */}
          {isCreating && newRoutePoints.length > 0 && (
            <RouteMarker
              route={{
                id: "new",
                name: "Nova Rota",
                crime_type: "other",
                risk_level: "medium",
                route_points: newRoutePoints,
                direction: "bidirectional",
                is_active: true,
                approval_status: "pending",
              }}
              editable={true}
            />
          )}
        </MapBase>

        {/* Selected Route Details */}
        {selectedRoute && !isCreating && (
          <div className="absolute bottom-4 right-4 bg-gray-800 rounded-lg p-4 shadow-xl w-80">
            <h3 className="text-white font-bold mb-3 flex items-center gap-2">
              <Route size={16} className="text-red-500" />
              Detalhes da Rota
            </h3>
            <div className="space-y-2 text-sm">
              <div className="flex justify-between">
                <span className="text-gray-400">Nome:</span>
                <span className="text-white font-semibold">{selectedRoute.name}</span>
              </div>
              <div className="flex justify-between">
                <span className="text-gray-400">Tipo:</span>
                <span className="text-white">{selectedRoute.crime_type}</span>
              </div>
              <div className="flex justify-between">
                <span className="text-gray-400">Risco:</span>
                <span className="text-white font-semibold">{selectedRoute.risk_level}</span>
              </div>
              <div className="flex justify-between">
                <span className="text-gray-400">Direção:</span>
                <span className="text-white">{selectedRoute.direction}</span>
              </div>
              <div className="flex justify-between">
                <span className="text-gray-400">Status:</span>
                <span className="text-white">{selectedRoute.approval_status}</span>
              </div>
              <div className="flex justify-between">
                <span className="text-gray-400">Ativa:</span>
                <span className="text-white">{selectedRoute.is_active ? "Sim" : "Não"}</span>
              </div>
              <div className="flex justify-between">
                <span className="text-gray-400">Pontos:</span>
                <span className="text-white">{selectedRoute.route_points.length}</span>
              </div>
              {selectedRoute.justification && (
                <div className="pt-2 border-t border-gray-700">
                  <span className="text-gray-400">Justificativa:</span>
                  <p className="text-white text-xs mt-1">{selectedRoute.justification}</p>
                </div>
              )}
            </div>
            <div className="pt-3 border-t border-gray-700 mt-3 flex gap-2">
              <button className="flex-1 bg-blue-600 hover:bg-blue-700 text-white py-2 rounded text-xs">
                <Edit size={12} className="inline mr-1" />
                Editar
              </button>
              <button className="flex-1 bg-green-600 hover:bg-green-700 text-white py-2 rounded text-xs">
                <Check size={12} className="inline mr-1" />
                Aprovar
              </button>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}
