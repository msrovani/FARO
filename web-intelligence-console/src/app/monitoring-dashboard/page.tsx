"use client";

import React, { useState, useEffect } from "react";
import { Activity, Cpu, HardDrive, Database, Wifi, Clock, TrendingUp, TrendingDown, AlertTriangle, CheckCircle, RefreshCw } from "lucide-react";
import { ConsoleShell } from "@/app/components/console-shell";
import { monitoringApi } from "@/app/services/api";

interface HealthStatus {
  status: 'healthy' | 'degraded' | 'unhealthy';
  timestamp: string;
  services: Array<{
    name: string;
    status: string;
    response_time_ms: number;
    last_check: string;
  }>;
  database: {
    status: string;
    connections: number;
    response_time_ms: number;
  };
  redis: {
    status: string;
    connections: number;
    memory_usage_mb: number;
  };
}

interface SystemMetrics {
  system: {
    cpu_usage_percent: number;
    memory_usage_percent: number;
    disk_usage_percent: number;
    uptime_seconds: number;
  };
  api: {
    requests_per_minute: number;
    avg_response_time_ms: number;
    error_rate_percent: number;
    active_connections: number;
  };
  database: {
    queries_per_second: number;
    avg_query_time_ms: number;
    active_connections: number;
    slow_queries_count: number;
  };
  cache: {
    hit_rate_percent: number;
    memory_usage_mb: number;
    keys_count: number;
    evictions_per_minute: number;
  };
}

interface PerformanceData {
  time_range: string;
  metrics: Array<{
    timestamp: string;
    cpu_usage: number;
    memory_usage: number;
    api_response_time: number;
    database_response_time: number;
    error_rate: number;
    requests_per_minute: number;
  }>;
  summary: {
    avg_cpu_usage: number;
    avg_memory_usage: number;
    avg_response_time: number;
    total_requests: number;
    error_rate: number;
  };
}

export default function MonitoringDashboardPage() {
  const [health, setHealth] = useState<HealthStatus | null>(null);
  const [metrics, setMetrics] = useState<SystemMetrics | null>(null);
  const [performance, setPerformance] = useState<PerformanceData | null>(null);
  const [timeRange, setTimeRange] = useState<'1h' | '6h' | '24h' | '7d'>('6h');
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [autoRefresh, setAutoRefresh] = useState(true);

  useEffect(() => {
    void loadData();
    
    if (autoRefresh) {
      const interval = setInterval(loadData, 30000); // 30 seconds
      return () => clearInterval(interval);
    }
  }, [timeRange, autoRefresh]);

  async function loadData() {
    try {
      setLoading(true);
      setError(null);
      
      const [healthData, metricsData, performanceData] = await Promise.all([
        monitoringApi.getHealth(),
        monitoringApi.getMetrics(),
        monitoringApi.getPerformance(timeRange),
      ]);

      setHealth(healthData);
      setMetrics(metricsData);
      setPerformance(performanceData);
    } catch (err) {
      console.error(err);
      setError("Não foi possível carregar dados de monitoramento.");
    } finally {
      setLoading(false);
    }
  }

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'healthy': return 'text-green-600 bg-green-50 border-green-200';
      case 'degraded': return 'text-yellow-600 bg-yellow-50 border-yellow-200';
      case 'unhealthy': return 'text-red-600 bg-red-50 border-red-200';
      default: return 'text-gray-600 bg-gray-50 border-gray-200';
    }
  };

  const getUsageColor = (percentage: number) => {
    if (percentage < 50) return 'text-green-600';
    if (percentage < 80) return 'text-yellow-600';
    return 'text-red-600';
  };

  const formatUptime = (seconds: number) => {
    const days = Math.floor(seconds / 86400);
    const hours = Math.floor((seconds % 86400) / 3600);
    const minutes = Math.floor((seconds % 3600) / 60);
    
    if (days > 0) return `${days}d ${hours}h`;
    if (hours > 0) return `${hours}h ${minutes}m`;
    return `${minutes}m`;
  };

  const overallStatus = health?.status || 'unknown';

  return (
    <ConsoleShell
      title="Dashboard de Monitoramento"
      subtitle="Saúde do sistema, métricas de performance e disponibilidade."
    >
      {error && (
        <div className="mb-6 rounded-3xl border border-red-200 bg-red-50 px-5 py-4 text-sm text-red-700">
          {error}
        </div>
      )}

      {/* Overall Status */}
      <div className="mb-6 rounded-2xl border border-gray-200 bg-white p-4">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-4">
            <div className={`inline-flex px-4 py-2 text-sm font-semibold rounded-full border ${getStatusColor(overallStatus)}`}>
              {overallStatus === 'healthy' && <CheckCircle className="mr-2 h-4 w-4" />}
              {overallStatus === 'degraded' && <AlertTriangle className="mr-2 h-4 w-4" />}
              {overallStatus === 'unhealthy' && <AlertTriangle className="mr-2 h-4 w-4" />}
              {overallStatus.toUpperCase()}
            </div>
            <div className="text-sm text-gray-500">
              Última verificação: {health?.timestamp ? new Date(health.timestamp).toLocaleString('pt-BR') : '--'}
            </div>
          </div>
          <div className="flex items-center gap-2">
            <select
              value={timeRange}
              onChange={(e) => setTimeRange(e.target.value as any)}
              className="rounded-lg border border-gray-200 px-3 py-2 text-sm focus:border-blue-500 focus:outline-none focus:ring-2 focus:ring-blue-500"
            >
              <option value="1h">Última 1h</option>
              <option value="6h">Últimas 6h</option>
              <option value="24h">Últimas 24h</option>
              <option value="7d">Últimos 7 dias</option>
            </select>
            <button
              onClick={() => setAutoRefresh(!autoRefresh)}
              className={`rounded-lg border px-4 py-2 text-sm font-medium ${
                autoRefresh 
                  ? 'border-green-200 bg-green-50 text-green-700' 
                  : 'border-gray-200 bg-white text-gray-700'
              }`}
            >
              Auto-refresh: {autoRefresh ? 'ON' : 'OFF'}
            </button>
            <button
              onClick={loadData}
              className="rounded-lg border border-gray-200 bg-white px-4 py-2 text-sm font-medium text-gray-700 hover:bg-gray-50"
            >
              <RefreshCw className="mr-2 h-4 w-4" />
              Atualizar
            </button>
          </div>
        </div>
      </div>

      {/* System Metrics */}
      {metrics && (
        <div className="mb-6 grid gap-4 md:grid-cols-4">
          <div className="rounded-2xl border border-gray-200 bg-white p-4">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-gray-600">CPU</p>
                <p className={`text-2xl font-semibold ${getUsageColor(metrics.system.cpu_usage_percent)}`}>
                  {metrics.system.cpu_usage_percent.toFixed(1)}%
                </p>
              </div>
              <Cpu className="h-8 w-8 text-blue-600" />
            </div>
          </div>
          <div className="rounded-2xl border border-gray-200 bg-white p-4">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-gray-600">Memória</p>
                <p className={`text-2xl font-semibold ${getUsageColor(metrics.system.memory_usage_percent)}`}>
                  {metrics.system.memory_usage_percent.toFixed(1)}%
                </p>
              </div>
              <Activity className="h-8 w-8 text-green-600" />
            </div>
          </div>
          <div className="rounded-2xl border border-gray-200 bg-white p-4">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-gray-600">Disco</p>
                <p className={`text-2xl font-semibold ${getUsageColor(metrics.system.disk_usage_percent)}`}>
                  {metrics.system.disk_usage_percent.toFixed(1)}%
                </p>
              </div>
              <HardDrive className="h-8 w-8 text-orange-600" />
            </div>
          </div>
          <div className="rounded-2xl border border-gray-200 bg-white p-4">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-gray-600">Uptime</p>
                <p className="text-2xl font-semibold text-gray-900">
                  {formatUptime(metrics.system.uptime_seconds)}
                </p>
              </div>
              <Clock className="h-8 w-8 text-purple-600" />
            </div>
          </div>
        </div>
      )}

      {/* API Metrics */}
      {metrics && (
        <div className="mb-6 grid gap-4 md:grid-cols-4">
          <div className="rounded-2xl border border-gray-200 bg-white p-4">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-gray-600">Req/min</p>
                <p className="text-2xl font-semibold text-blue-600">
                  {metrics.api.requests_per_minute}
                </p>
              </div>
              <TrendingUp className="h-8 w-8 text-blue-600" />
            </div>
          </div>
          <div className="rounded-2xl border border-gray-200 bg-white p-4">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-gray-600">Tempo Resp.</p>
                <p className="text-2xl font-semibold text-gray-900">
                  {metrics.api.avg_response_time_ms.toFixed(0)}ms
                </p>
              </div>
              <Clock className="h-8 w-8 text-gray-600" />
            </div>
          </div>
          <div className="rounded-2xl border border-gray-200 bg-white p-4">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-gray-600">Taxa Erro</p>
                <p className={`text-2xl font-semibold ${getUsageColor(metrics.api.error_rate_percent)}`}>
                  {metrics.api.error_rate_percent.toFixed(1)}%
                </p>
              </div>
              <AlertTriangle className="h-8 w-8 text-red-600" />
            </div>
          </div>
          <div className="rounded-2xl border border-gray-200 bg-white p-4">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-gray-600">Conexões</p>
                <p className="text-2xl font-semibold text-green-600">
                  {metrics.api.active_connections}
                </p>
              </div>
              <Wifi className="h-8 w-8 text-green-600" />
            </div>
          </div>
        </div>
      )}

      {/* Database & Cache */}
      {metrics && (
        <div className="mb-6 grid gap-6 md:grid-cols-2">
          <div className="rounded-2xl border border-gray-200 bg-white p-4">
            <h4 className="text-sm font-semibold text-gray-900 mb-4">Database</h4>
            <div className="grid gap-4 md:grid-cols-2">
              <div>
                <p className="text-sm text-gray-600">Queries/seg</p>
                <p className="text-xl font-semibold text-gray-900">
                  {metrics.database.queries_per_second.toFixed(1)}
                </p>
              </div>
              <div>
                <p className="text-sm text-gray-600">Tempo Médio</p>
                <p className="text-xl font-semibold text-gray-900">
                  {metrics.database.avg_query_time_ms.toFixed(0)}ms
                </p>
              </div>
              <div>
                <p className="text-sm text-gray-600">Conexões</p>
                <p className="text-xl font-semibold text-blue-600">
                  {metrics.database.active_connections}
                </p>
              </div>
              <div>
                <p className="text-sm text-gray-600">Slow Queries</p>
                <p className={`text-xl font-semibold ${getUsageColor(metrics.database.slow_queries_count)}`}>
                  {metrics.database.slow_queries_count}
                </p>
              </div>
            </div>
          </div>
          <div className="rounded-2xl border border-gray-200 bg-white p-4">
            <h4 className="text-sm font-semibold text-gray-900 mb-4">Cache (Redis)</h4>
            <div className="grid gap-4 md:grid-cols-2">
              <div>
                <p className="text-sm text-gray-600">Hit Rate</p>
                <p className={`text-xl font-semibold ${getUsageColor(100 - metrics.cache.hit_rate_percent)}`}>
                  {metrics.cache.hit_rate_percent.toFixed(1)}%
                </p>
              </div>
              <div>
                <p className="text-sm text-gray-600">Memória</p>
                <p className="text-xl font-semibold text-gray-900">
                  {(metrics.cache.memory_usage_mb / 1024).toFixed(1)}GB
                </p>
              </div>
              <div>
                <p className="text-sm text-gray-600">Keys</p>
                <p className="text-xl font-semibold text-purple-600">
                  {metrics.cache.keys_count.toLocaleString()}
                </p>
              </div>
              <div>
                <p className="text-sm text-gray-600">Evictions/min</p>
                <p className="text-xl font-semibold text-orange-600">
                  {metrics.cache.evictions_per_minute}
                </p>
              </div>
            </div>
          </div>
        </div>
      )}

      {/* Services Health */}
      {health && (
        <div className="mb-6 rounded-2xl border border-gray-200 bg-white overflow-hidden">
          <div className="px-6 py-4 border-b border-gray-200">
            <h3 className="text-lg font-semibold text-gray-900">Saúde dos Serviços</h3>
          </div>
          <div className="overflow-x-auto">
            <table className="w-full">
              <thead className="bg-gray-50">
                <tr>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Serviço
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Status
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Tempo Resposta
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Última Verificação
                  </th>
                </tr>
              </thead>
              <tbody className="divide-y divide-gray-200">
                {health.services.map((service) => (
                  <tr key={service.name}>
                    <td className="px-6 py-4 whitespace-nowrap text-sm font-medium text-gray-900">
                      {service.name}
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap">
                      <span className={`inline-flex px-2 py-1 text-xs font-semibold rounded-full border ${getStatusColor(service.status)}`}>
                        {service.status.toUpperCase()}
                      </span>
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                      {service.response_time_ms}ms
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                      {new Date(service.last_check).toLocaleString('pt-BR')}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      )}

      {/* Performance Summary */}
      {performance && (
        <div className="rounded-2xl border border-gray-200 bg-white p-4">
          <h4 className="text-sm font-semibold text-gray-900 mb-4">Resumo de Performance ({timeRange})</h4>
          <div className="grid gap-4 md:grid-cols-5">
            <div className="text-center">
              <p className="text-sm text-gray-600">CPU Média</p>
              <p className={`text-xl font-semibold ${getUsageColor(performance.summary.avg_cpu_usage)}`}>
                {performance.summary.avg_cpu_usage.toFixed(1)}%
              </p>
            </div>
            <div className="text-center">
              <p className="text-sm text-gray-600">Memória Média</p>
              <p className={`text-xl font-semibold ${getUsageColor(performance.summary.avg_memory_usage)}`}>
                {performance.summary.avg_memory_usage.toFixed(1)}%
              </p>
            </div>
            <div className="text-center">
              <p className="text-sm text-gray-600">Tempo Resp. Médio</p>
              <p className="text-xl font-semibold text-gray-900">
                {performance.summary.avg_response_time.toFixed(0)}ms
              </p>
            </div>
            <div className="text-center">
              <p className="text-sm text-gray-600">Total Requests</p>
              <p className="text-xl font-semibold text-blue-600">
                {performance.summary.total_requests.toLocaleString()}
              </p>
            </div>
            <div className="text-center">
              <p className="text-sm text-gray-600">Taxa Erro</p>
              <p className={`text-xl font-semibold ${getUsageColor(performance.summary.error_rate)}`}>
                {performance.summary.error_rate.toFixed(1)}%
              </p>
            </div>
          </div>
        </div>
      )}

      {loading && (
        <div className="mt-6 text-center text-sm text-gray-500">
          Carregando dados de monitoramento...
        </div>
      )}
    </ConsoleShell>
  );
}
