"use client";

import React, { useState, useEffect } from "react";
import { ConsoleShell } from "@/app/components/console-shell";
import { 
  Activity, 
  Server, 
  Database, 
  Wifi, 
  AlertTriangle, 
  CheckCircle, 
  TrendingUp, 
  TrendingDown,
  RefreshCw,
  Clock,
  Users,
  HardDrive,
  Zap
} from "lucide-react";
import { monitoringApi } from "@/app/services/api";

interface SystemHealth {
  status: 'healthy' | 'degraded' | 'unhealthy';
  timestamp: string;
  services: {
    server: { status: string; response_time: number; uptime: number };
    database: { status: string; connections: number; query_time: number };
    redis: { status: string; memory_usage: number; connections: number };
    storage: { status: string; available_space: number; total_space: number };
  };
  metrics: {
    requests_per_second: number;
    average_response_time: number;
    error_rate: number;
    active_users: number;
    cpu_usage: number;
    memory_usage: number;
    disk_usage: number;
  };
}

export default function MonitoringPage() {
  const [health, setHealth] = useState<SystemHealth | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [autoRefresh, setAutoRefresh] = useState(true);
  const [refreshInterval, setRefreshInterval] = useState(30000); // 30 seconds

  useEffect(() => {
    loadHealth();
  }, []);

  useEffect(() => {
    if (!autoRefresh) return;

    const interval = setInterval(loadHealth, refreshInterval);
    return () => clearInterval(interval);
  }, [autoRefresh, refreshInterval]);

  const loadHealth = async () => {
    try {
      setLoading(true);
      const data = await monitoringApi.getHealth();
      setHealth(data);
      setError(null);
    } catch (err) {
      console.error("Failed to load health data:", err);
      setError("Falha ao carregar dados de monitoramento.");
    } finally {
      setLoading(false);
    }
  };

  const getStatusColor = (status: string) => {
    switch (status) {
      case "healthy":
      case "online":
      case "ok":
        return "text-green-600 bg-green-50";
      case "degraded":
      case "warning":
        return "text-yellow-600 bg-yellow-50";
      case "unhealthy":
      case "error":
      case "offline":
        return "text-red-600 bg-red-50";
      default:
        return "text-gray-600 bg-gray-50";
    }
  };

  const getStatusIcon = (status: string) => {
    switch (status) {
      case "healthy":
      case "online":
      case "ok":
        return <CheckCircle size={16} />;
      case "degraded":
      case "warning":
        return <AlertTriangle size={16} />;
      case "unhealthy":
      case "error":
      case "offline":
        return <Activity size={16} />;
      default:
        return <Activity size={16} />;
    }
  };

  const getTrendIcon = (current: number, threshold: number) => {
    if (current > threshold) return <TrendingUp size={16} className="text-red-600" />;
    if (current > threshold * 0.8) return <TrendingUp size={16} className="text-yellow-600" />;
    return <TrendingDown size={16} className="text-green-600" />;
  };

  if (loading && !health) {
    return (
      <ConsoleShell
        title="Monitoramento do Sistema"
        subtitle="Visão geral da saúde e performance dos serviços F.A.R.O."
      >
        <div className="bg-white rounded-lg shadow-sm p-8 text-center">
          <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600 mx-auto"></div>
          <p className="mt-4 text-gray-600">Carregando dados de monitoramento...</p>
        </div>
      </ConsoleShell>
    );
  }

  if (error) {
    return (
      <ConsoleShell
        title="Monitoramento do Sistema"
        subtitle="Visão geral da saúde e performance dos serviços F.A.R.O."
      >
        <div className="bg-red-50 border border-red-200 rounded-md p-4">
          <div className="flex">
            <AlertTriangle className="h-5 w-5 text-red-400" />
            <div className="ml-3">
              <h3 className="text-sm font-medium text-red-800">Erro de Monitoramento</h3>
              <p className="mt-2 text-sm text-red-700">{error}</p>
            </div>
          </div>
        </div>
      </ConsoleShell>
    );
  }

  return (
    <ConsoleShell
      title="Monitoramento do Sistema"
      subtitle="Visão geral da saúde e performance dos serviços F.A.R.O."
    >
      <div className="space-y-6">
        {/* Controls */}
        <div className="bg-white rounded-lg shadow-sm p-6">
          <div className="flex items-center justify-between">
            <div className="flex items-center space-x-4">
              <div className="flex items-center">
                <input
                  type="checkbox"
                  id="auto-refresh"
                  checked={autoRefresh}
                  onChange={(e) => setAutoRefresh(e.target.checked)}
                  className="h-4 w-4 text-blue-600 focus:ring-blue-500 border-gray-300 rounded"
                />
                <label htmlFor="auto-refresh" className="ml-2 block text-sm text-gray-700">
                  Atualização Automática
                </label>
              </div>
              
              <select
                value={refreshInterval}
                onChange={(e) => setRefreshInterval(Number(e.target.value))}
                disabled={!autoRefresh}
                className="block w-full px-3 py-2 border border-gray-300 bg-white rounded-md shadow-sm focus:outline-none focus:ring-blue-500 focus:border-blue-500 sm:text-sm"
              >
                <option value={10000}>10 segundos</option>
                <option value={30000}>30 segundos</option>
                <option value={60000}>1 minuto</option>
                <option value={300000}>5 minutos</option>
              </select>
            </div>

            <button
              onClick={loadHealth}
              className="inline-flex items-center px-4 py-2 border border-gray-300 rounded-md shadow-sm text-sm font-medium text-gray-700 bg-white hover:bg-gray-50 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500"
            >
              <RefreshCw size={16} className="mr-2" />
              Atualizar Agora
            </button>
          </div>
        </div>

        {/* Overall Status */}
        <div className="bg-white rounded-lg shadow-sm p-6">
          <div className="flex items-center justify-between">
            <div className="flex items-center">
              <div className={`p-3 rounded-full ${getStatusColor(health?.status || 'unknown')}`}>
                {getStatusIcon(health?.status || 'unknown')}
              </div>
              <div className="ml-4">
                <h3 className="text-lg font-medium text-gray-900">Status Geral do Sistema</h3>
                <p className="text-sm text-gray-500">
                  {health?.timestamp ? new Date(health.timestamp).toLocaleString() : 'N/A'}
                </p>
              </div>
            </div>
            
            <div className="text-right">
              <span className={`inline-flex items-center px-3 py-1 rounded-full text-lg font-medium ${getStatusColor(health?.status || 'unknown')}`}>
                {health?.status === 'healthy' ? 'Saudável' : 
                 health?.status === 'degraded' ? 'Degradado' : 
                 health?.status === 'unhealthy' ? 'Não Saudável' : 'Desconhecido'}
              </span>
            </div>
          </div>
        </div>

        {/* Services Status */}
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
          {/* Server */}
          <div className="bg-white rounded-lg shadow-sm p-6">
            <div className="flex items-center justify-between mb-4">
              <div className="flex items-center">
                <Server className="h-6 w-6 text-blue-600" />
                <h4 className="ml-2 text-sm font-medium text-gray-900">Servidor</h4>
              </div>
              <span className={`inline-flex items-center px-2 py-1 rounded-full text-xs font-medium ${getStatusColor(health?.services.server.status || 'unknown')}`}>
                {getStatusIcon(health?.services.server.status || 'unknown')}
                <span className="ml-1">{health?.services.server.status || 'N/A'}</span>
              </span>
            </div>
            
            <div className="space-y-2">
              <div className="flex justify-between text-sm">
                <span className="text-gray-500">Tempo Resposta:</span>
                <span className="font-medium">{health?.services.server.response_time}ms</span>
              </div>
              <div className="flex justify-between text-sm">
                <span className="text-gray-500">Uptime:</span>
                <span className="font-medium">{health?.services.server.uptime}%</span>
              </div>
            </div>
          </div>

          {/* Database */}
          <div className="bg-white rounded-lg shadow-sm p-6">
            <div className="flex items-center justify-between mb-4">
              <div className="flex items-center">
                <Database className="h-6 w-6 text-green-600" />
                <h4 className="ml-2 text-sm font-medium text-gray-900">Database</h4>
              </div>
              <span className={`inline-flex items-center px-2 py-1 rounded-full text-xs font-medium ${getStatusColor(health?.services.database.status || 'unknown')}`}>
                {getStatusIcon(health?.services.database.status || 'unknown')}
                <span className="ml-1">{health?.services.database.status || 'N/A'}</span>
              </span>
            </div>
            
            <div className="space-y-2">
              <div className="flex justify-between text-sm">
                <span className="text-gray-500">Conexões:</span>
                <span className="font-medium">{health?.services.database.connections}</span>
              </div>
              <div className="flex justify-between text-sm">
                <span className="text-gray-500">Tempo Query:</span>
                <span className="font-medium">{health?.services.database.query_time}ms</span>
              </div>
            </div>
          </div>

          {/* Redis */}
          <div className="bg-white rounded-lg shadow-sm p-6">
            <div className="flex items-center justify-between mb-4">
              <div className="flex items-center">
                <Database className="h-6 w-6 text-red-600" />
                <h4 className="ml-2 text-sm font-medium text-gray-900">Redis</h4>
              </div>
              <span className={`inline-flex items-center px-2 py-1 rounded-full text-xs font-medium ${getStatusColor(health?.services.redis.status || 'unknown')}`}>
                {getStatusIcon(health?.services.redis.status || 'unknown')}
                <span className="ml-1">{health?.services.redis.status || 'N/A'}</span>
              </span>
            </div>
            
            <div className="space-y-2">
              <div className="flex justify-between text-sm">
                <span className="text-gray-500">Memória:</span>
                <span className="font-medium">{health?.services.redis.memory_usage}%</span>
              </div>
              <div className="flex justify-between text-sm">
                <span className="text-gray-500">Conexões:</span>
                <span className="font-medium">{health?.services.redis.connections}</span>
              </div>
            </div>
          </div>

          {/* Storage */}
          <div className="bg-white rounded-lg shadow-sm p-6">
            <div className="flex items-center justify-between mb-4">
              <div className="flex items-center">
                <HardDrive className="h-6 w-6 text-purple-600" />
                <h4 className="ml-2 text-sm font-medium text-gray-900">Armazenamento</h4>
              </div>
              <span className={`inline-flex items-center px-2 py-1 rounded-full text-xs font-medium ${getStatusColor(health?.services.storage.status || 'unknown')}`}>
                {getStatusIcon(health?.services.storage.status || 'unknown')}
                <span className="ml-1">{health?.services.storage.status || 'N/A'}</span>
              </span>
            </div>
            
            <div className="space-y-2">
              <div className="flex justify-between text-sm">
                <span className="text-gray-500">Disponível:</span>
                <span className="font-medium">{(health?.services.storage.available_space / 1024).toFixed(1)}GB</span>
              </div>
              <div className="flex justify-between text-sm">
                <span className="text-gray-500">Total:</span>
                <span className="font-medium">{(health?.services.storage.total_space / 1024).toFixed(1)}GB</span>
              </div>
            </div>
          </div>
        </div>

        {/* System Metrics */}
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
          <div className="bg-white rounded-lg shadow-sm p-6">
            <div className="flex items-center justify-between mb-4">
              <div className="flex items-center">
                <Activity className="h-6 w-6 text-blue-600" />
                <h4 className="ml-2 text-sm font-medium text-gray-900">Requisições/s</h4>
              </div>
              {getTrendIcon(health?.metrics.requests_per_second || 0, 1000)}
            </div>
            <div className="text-2xl font-bold text-gray-900">
              {health?.metrics.requests_per_second || 0}
            </div>
            <p className="text-xs text-gray-500 mt-1">por segundo</p>
          </div>

          <div className="bg-white rounded-lg shadow-sm p-6">
            <div className="flex items-center justify-between mb-4">
              <div className="flex items-center">
                <Clock className="h-6 w-6 text-green-600" />
                <h4 className="ml-2 text-sm font-medium text-gray-900">Tempo Resposta</h4>
              </div>
              {getTrendIcon(health?.metrics.average_response_time || 0, 500)}
            </div>
            <div className="text-2xl font-bold text-gray-900">
              {health?.metrics.average_response_time || 0}ms
            </div>
            <p className="text-xs text-gray-500 mt-1">média</p>
          </div>

          <div className="bg-white rounded-lg shadow-sm p-6">
            <div className="flex items-center justify-between mb-4">
              <div className="flex items-center">
                <AlertTriangle className="h-6 w-6 text-red-600" />
                <h4 className="ml-2 text-sm font-medium text-gray-900">Taxa Erro</h4>
              </div>
              {getTrendIcon(health?.metrics.error_rate || 0, 5)}
            </div>
            <div className="text-2xl font-bold text-gray-900">
              {(health?.metrics.error_rate || 0).toFixed(1)}%
            </div>
            <p className="text-xs text-gray-500 mt-1">última hora</p>
          </div>

          <div className="bg-white rounded-lg shadow-sm p-6">
            <div className="flex items-center justify-between mb-4">
              <div className="flex items-center">
                <Users className="h-6 w-6 text-purple-600" />
                <h4 className="ml-2 text-sm font-medium text-gray-900">Usuários Ativos</h4>
              </div>
              {getTrendIcon(health?.metrics.active_users || 0, 100)}
            </div>
            <div className="text-2xl font-bold text-gray-900">
              {health?.metrics.active_users || 0}
            </div>
            <p className="text-xs text-gray-500 mt-1">online</p>
          </div>
        </div>

        {/* Resource Usage */}
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          <div className="bg-white rounded-lg shadow-sm p-6">
            <div className="flex items-center justify-between mb-4">
              <div className="flex items-center">
                <Zap className="h-6 w-6 text-yellow-600" />
                <h4 className="ml-2 text-sm font-medium text-gray-900">CPU</h4>
              </div>
              {getTrendIcon(health?.metrics.cpu_usage || 0, 80)}
            </div>
            <div className="relative">
              <div className="w-full bg-gray-200 rounded-full h-4">
                <div 
                  className={`h-4 rounded-full ${
                    (health?.metrics.cpu_usage || 0) > 80 ? 'bg-red-600' :
                    (health?.metrics.cpu_usage || 0) > 60 ? 'bg-yellow-600' : 'bg-green-600'
                  }`}
                  style={{ width: `${health?.metrics.cpu_usage || 0}%` }}
                ></div>
              </div>
              <div className="text-center mt-2">
                <span className="text-lg font-bold text-gray-900">{health?.metrics.cpu_usage || 0}%</span>
              </div>
            </div>
          </div>

          <div className="bg-white rounded-lg shadow-sm p-6">
            <div className="flex items-center justify-between mb-4">
              <div className="flex items-center">
                <Database className="h-6 w-6 text-blue-600" />
                <h4 className="ml-2 text-sm font-medium text-gray-900">Memória</h4>
              </div>
              {getTrendIcon(health?.metrics.memory_usage || 0, 80)}
            </div>
            <div className="relative">
              <div className="w-full bg-gray-200 rounded-full h-4">
                <div 
                  className={`h-4 rounded-full ${
                    (health?.metrics.memory_usage || 0) > 80 ? 'bg-red-600' :
                    (health?.metrics.memory_usage || 0) > 60 ? 'bg-yellow-600' : 'bg-green-600'
                  }`}
                  style={{ width: `${health?.metrics.memory_usage || 0}%` }}
                ></div>
              </div>
              <div className="text-center mt-2">
                <span className="text-lg font-bold text-gray-900">{health?.metrics.memory_usage || 0}%</span>
              </div>
            </div>
          </div>

          <div className="bg-white rounded-lg shadow-sm p-6">
            <div className="flex items-center justify-between mb-4">
              <div className="flex items-center">
                <HardDrive className="h-6 w-6 text-purple-600" />
                <h4 className="ml-2 text-sm font-medium text-gray-900">Disco</h4>
              </div>
              {getTrendIcon(health?.metrics.disk_usage || 0, 85)}
            </div>
            <div className="relative">
              <div className="w-full bg-gray-200 rounded-full h-4">
                <div 
                  className={`h-4 rounded-full ${
                    (health?.metrics.disk_usage || 0) > 85 ? 'bg-red-600' :
                    (health?.metrics.disk_usage || 0) > 70 ? 'bg-yellow-600' : 'bg-green-600'
                  }`}
                  style={{ width: `${health?.metrics.disk_usage || 0}%` }}
                ></div>
              </div>
              <div className="text-center mt-2">
                <span className="text-lg font-bold text-gray-900">{health?.metrics.disk_usage || 0}%</span>
              </div>
            </div>
          </div>
        </div>

        {/* Last Update */}
        <div className="text-center text-sm text-gray-500">
          Última atualização: {health?.timestamp ? new Date(health.timestamp).toLocaleString() : 'N/A'}
        </div>
      </div>
    </ConsoleShell>
  );
}
