"use client";

import React, { useState, useEffect } from "react";
import { Smartphone, Battery, Wifi, MapPin, Search, Filter, RefreshCw, AlertTriangle, CheckCircle, Clock, Activity } from "lucide-react";
import { ConsoleShell } from "@/app/components/console-shell";
import { devicesApi } from "@/app/services/api";

interface Device {
  id: string;
  device_id: string;
  device_type: string;
  model: string;
  os_version: string;
  app_version: string;
  agent_id?: string;
  agent_name?: string;
  status: string;
  last_heartbeat?: string;
  battery_level?: number;
  location?: {
    latitude: number;
    longitude: number;
    accuracy: number;
  };
  created_at: string;
  updated_at: string;
}

export default function DevicesManagementPage() {
  const [devices, setDevices] = useState<Device[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [searchTerm, setSearchTerm] = useState("");
  const [filters, setFilters] = useState({
    agent_id: "",
    status: "",
    device_type: "",
  });
  const [selectedDevice, setSelectedDevice] = useState<Device | null>(null);

  useEffect(() => {
    void loadDevices();
  }, [filters]);

  async function loadDevices() {
    try {
      setLoading(true);
      setError(null);
      
      const response = await devicesApi.listDevices(filters);
      setDevices(response.devices);
    } catch (err) {
      console.error(err);
      setError("Não foi possível carregar dispositivos.");
    } finally {
      setLoading(false);
    }
  }

  async function handleSendHeartbeat(deviceId: string, data: {
    battery_level?: number;
    location?: {
      latitude: number;
      longitude: number;
      accuracy: number;
    };
    network_status?: string;
  }) {
    try {
      await devicesApi.sendHeartbeat(deviceId, data);
      await loadDevices();
      setSelectedDevice(null);
    } catch (err) {
      console.error(err);
      setError("Falha ao enviar heartbeat.");
    }
  }

  const filteredDevices = devices.filter(device =>
    device.device_id.toLowerCase().includes(searchTerm.toLowerCase()) ||
    device.model.toLowerCase().includes(searchTerm.toLowerCase()) ||
    device.agent_name?.toLowerCase().includes(searchTerm.toLowerCase()) ||
    device.id.toLowerCase().includes(searchTerm.toLowerCase())
  );

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'online': return 'text-green-600 bg-green-50 border-green-200';
      case 'offline': return 'text-red-600 bg-red-50 border-red-200';
      case 'idle': return 'text-yellow-600 bg-yellow-50 border-yellow-200';
      case 'suspended': return 'text-gray-600 bg-gray-50 border-gray-200';
      default: return 'text-gray-600 bg-gray-50 border-gray-200';
    }
  };

  const getBatteryColor = (level?: number) => {
    if (!level) return 'text-gray-500';
    if (level > 60) return 'text-green-600';
    if (level > 30) return 'text-yellow-600';
    return 'text-red-600';
  };

  const getBatteryIcon = (level?: number) => {
    if (!level) return <Battery className="h-4 w-4" />;
    if (level > 80) return <Battery className="h-4 w-4 text-green-600" />;
    if (level > 40) return <Battery className="h-4 w-4 text-yellow-600" />;
    return <Battery className="h-4 w-4 text-red-600" />;
  };

  const getLastHeartbeat = (heartbeat?: string) => {
    if (!heartbeat) return 'Nunca';
    
    const now = new Date();
    const last = new Date(heartbeat);
    const diffMinutes = Math.floor((now.getTime() - last.getTime()) / (1000 * 60));
    
    if (diffMinutes < 1) return 'Agora';
    if (diffMinutes < 60) return `${diffMinutes} min`;
    if (diffMinutes < 1440) return `${Math.floor(diffMinutes / 60)} h`;
    return `${Math.floor(diffMinutes / 1440)} dias`;
  };

  return (
    <ConsoleShell
      title="Gestão de Dispositivos"
      subtitle="Monitoramento de dispositivos móveis e heartbeat em tempo real."
    >
      {error && (
        <div className="mb-6 rounded-3xl border border-red-200 bg-red-50 px-5 py-4 text-sm text-red-700">
          {error}
        </div>
      )}

      {/* Summary Cards */}
      <div className="mb-6 grid gap-4 md:grid-cols-4">
        <div className="rounded-2xl border border-gray-200 bg-white p-4">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm text-gray-600">Total Dispositivos</p>
              <p className="text-2xl font-semibold text-gray-900">{devices.length}</p>
            </div>
            <Smartphone className="h-8 w-8 text-blue-600" />
          </div>
        </div>
        <div className="rounded-2xl border border-gray-200 bg-white p-4">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm text-gray-600">Online</p>
              <p className="text-2xl font-semibold text-green-600">
                {devices.filter(d => d.status === 'online').length}
              </p>
            </div>
            <CheckCircle className="h-8 w-8 text-green-600" />
          </div>
        </div>
        <div className="rounded-2xl border border-gray-200 bg-white p-4">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm text-gray-600">Offline</p>
              <p className="text-2xl font-semibold text-red-600">
                {devices.filter(d => d.status === 'offline').length}
              </p>
            </div>
            <AlertTriangle className="h-8 w-8 text-red-600" />
          </div>
        </div>
        <div className="rounded-2xl border border-gray-200 bg-white p-4">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm text-gray-600">Bateria Média</p>
              <p className="text-2xl font-semibold text-gray-900">
                {devices.length > 0 && devices.some(d => d.battery_level)
                  ? (devices.reduce((sum, d) => sum + (d.battery_level || 0), 0) / devices.filter(d => d.battery_level).length).toFixed(0)
                  : '--'}%
              </p>
            </div>
            <Battery className="h-8 w-8 text-orange-600" />
          </div>
        </div>
      </div>

      {/* Filters and Actions */}
      <div className="mb-6 rounded-2xl border border-gray-200 bg-white p-4">
        <div className="flex items-center gap-4">
          <div className="flex-1">
            <div className="relative">
              <Search className="absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-gray-400" />
              <input
                type="text"
                placeholder="Buscar dispositivo..."
                value={searchTerm}
                onChange={(e) => setSearchTerm(e.target.value)}
                className="w-full rounded-lg border border-gray-200 pl-10 pr-4 py-2 text-sm focus:border-blue-500 focus:outline-none focus:ring-2 focus:ring-blue-500"
              />
            </div>
          </div>
          <div className="flex gap-2">
            <select
              value={filters.status}
              onChange={(e) => setFilters({ ...filters, status: e.target.value })}
              className="rounded-lg border border-gray-200 px-3 py-2 text-sm focus:border-blue-500 focus:outline-none focus:ring-2 focus:ring-blue-500"
            >
              <option value="">Todos Status</option>
              <option value="online">Online</option>
              <option value="offline">Offline</option>
              <option value="idle">Inativo</option>
              <option value="suspended">Suspenso</option>
            </select>
            <button
              onClick={loadDevices}
              className="rounded-lg border border-gray-200 bg-white px-4 py-2 text-sm font-medium text-gray-700 hover:bg-gray-50"
            >
              <RefreshCw className="mr-2 h-4 w-4" />
              Atualizar
            </button>
          </div>
        </div>
      </div>

      {/* Devices Table */}
      <div className="rounded-2xl border border-gray-200 bg-white overflow-hidden">
        <div className="px-6 py-4 border-b border-gray-200">
          <h3 className="text-lg font-semibold text-gray-900">Dispositivos</h3>
        </div>
        <div className="overflow-x-auto">
          <table className="w-full">
            <thead className="bg-gray-50">
              <tr>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Dispositivo
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Agente
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Status
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Bateria
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Localização
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Último Heartbeat
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Versões
                </th>
              </tr>
            </thead>
            <tbody className="divide-y divide-gray-200">
              {filteredDevices.map((device) => (
                <tr key={device.id} className="hover:bg-gray-50">
                  <td className="px-6 py-4 whitespace-nowrap">
                    <div>
                      <div className="text-sm font-medium text-gray-900">{device.model}</div>
                      <div className="text-xs text-gray-500">ID: {device.device_id.slice(0, 12)}...</div>
                      <div className="text-xs text-gray-500">Tipo: {device.device_type}</div>
                    </div>
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap">
                    {device.agent_name ? (
                      <div>
                        <div className="text-sm text-gray-900">{device.agent_name}</div>
                        <div className="text-xs text-gray-500">ID: {device.agent_id?.slice(0, 8)}...</div>
                      </div>
                    ) : (
                      <span className="text-sm text-gray-500">Não atribuído</span>
                    )}
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap">
                    <span className={`inline-flex px-2 py-1 text-xs font-semibold rounded-full border ${getStatusColor(device.status)}`}>
                      {device.status.toUpperCase()}
                    </span>
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap">
                    <div className="flex items-center">
                      {getBatteryIcon(device.battery_level)}
                      <span className={`ml-2 text-sm font-medium ${getBatteryColor(device.battery_level)}`}>
                        {device.battery_level ? `${device.battery_level}%` : '--'}
                      </span>
                    </div>
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap">
                    {device.location ? (
                      <div className="flex items-center text-sm text-gray-900">
                        <MapPin className="mr-2 h-3 w-3 text-gray-400" />
                        <span>
                          {device.location.latitude.toFixed(3)}, {device.location.longitude.toFixed(3)}
                        </span>
                        <span className="ml-2 text-xs text-gray-500">
                          ±{device.location.accuracy}m
                        </span>
                      </div>
                    ) : (
                      <span className="text-sm text-gray-500">Sem localização</span>
                    )}
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                    <div className="flex items-center">
                      <Clock className="mr-2 h-3 w-3 text-gray-400" />
                      {getLastHeartbeat(device.last_heartbeat)}
                    </div>
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap">
                    <div className="space-y-1">
                      <div className="text-xs text-gray-500">
                        OS: {device.os_version}
                      </div>
                      <div className="text-xs text-gray-500">
                        App: {device.app_version}
                      </div>
                    </div>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>

      {/* Device Status Distribution */}
      <div className="mt-6 rounded-2xl border border-gray-200 bg-white p-4">
        <h4 className="text-sm font-semibold text-gray-900 mb-4">Distribuição por Status</h4>
        <div className="grid gap-4 md:grid-cols-4">
          {['online', 'offline', 'idle', 'suspended'].map((status) => {
            const count = devices.filter(d => d.status === status).length;
            const percentage = devices.length > 0 ? (count / devices.length) * 100 : 0;
            return (
              <div key={status} className="text-center">
                <div className={`inline-flex px-3 py-2 text-sm font-semibold rounded-full border ${getStatusColor(status)}`}>
                  {status.toUpperCase()}
                </div>
                <div className="mt-2">
                  <div className="text-2xl font-semibold text-gray-900">{count}</div>
                  <div className="text-xs text-gray-500">{percentage.toFixed(1)}%</div>
                </div>
              </div>
            );
          })}
        </div>
      </div>

      {/* Battery Levels */}
      <div className="mt-6 rounded-2xl border border-gray-200 bg-white p-4">
        <h4 className="text-sm font-semibold text-gray-900 mb-4">Níveis de Bateria</h4>
        <div className="grid gap-4 md:grid-cols-4">
          {[
            { label: 'Crítica (<20%)', min: 0, max: 20, color: 'text-red-600' },
            { label: 'Baixa (20-40%)', min: 20, max: 40, color: 'text-orange-600' },
            { label: 'Média (40-60%)', min: 40, max: 60, color: 'text-yellow-600' },
            { label: 'Boa (>60%)', min: 60, max: 100, color: 'text-green-600' },
          ].map((range) => {
            const count = devices.filter(d => 
              d.battery_level && d.battery_level >= range.min && d.battery_level <= range.max
            ).length;
            return (
              <div key={range.label} className="text-center">
                <div className={`text-sm font-medium ${range.color}`}>
                  {range.label}
                </div>
                <div className="mt-2">
                  <div className="text-2xl font-semibold text-gray-900">{count}</div>
                  <div className="text-xs text-gray-500">dispositivos</div>
                </div>
              </div>
            );
          })}
        </div>
      </div>

      {loading && (
        <div className="mt-6 text-center text-sm text-gray-500">
          Carregando dispositivos...
        </div>
      )}
    </ConsoleShell>
  );
}
