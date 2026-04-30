"use client";

import React, { useState, useEffect } from "react";
import { 
  Map, 
  Settings, 
  Users, 
  Activity, 
  CheckCircle, 
  AlertCircle, 
  TrendingUp,
  Clock,
  Shield,
  Download,
  RefreshCw
} from "lucide-react";
import { OSMPhasedRollout, OSMAutomatedTesting } from "../../components/maps/osm";

interface MigrationMetrics {
  totalUsers: number;
  migratedUsers: number;
  satisfactionScore: number;
  performanceScore: number;
  errorRate: number;
  cacheHitRate: number;
  systemUptime: number;
  lastUpdate: string;
}

interface MigrationPhase {
  id: string;
  name: string;
  status: "pending" | "active" | "completed" | "failed";
  users: number;
  percentage: number;
  startTime?: string;
  endTime?: string;
}

export default function OSMMigrationDashboard() {
  const [activeTab, setActiveTab] = useState<"overview" | "phases" | "testing" | "metrics">("overview");
  const [metrics, setMetrics] = useState<MigrationMetrics>({
    totalUsers: 1000,
    migratedUsers: 150,
    satisfactionScore: 87.5,
    performanceScore: 92.3,
    errorRate: 2.1,
    cacheHitRate: 85.7,
    systemUptime: 99.8,
    lastUpdate: new Date().toISOString(),
  });

  const [phases] = useState<MigrationPhase[]>([
    {
      id: "alpha",
      name: "Alpha Test",
      status: "completed",
      users: 50,
      percentage: 5,
      startTime: "2026-04-20T10:00:00Z",
      endTime: "2026-04-22T18:00:00Z",
    },
    {
      id: "beta",
      name: "Beta Test",
      status: "active",
      users: 150,
      percentage: 15,
      startTime: "2026-04-23T09:00:00Z",
    },
    {
      id: "gamma",
      name: "Gamma Release",
      status: "pending",
      users: 400,
      percentage: 40,
    },
    {
      id: "production",
      name: "Production Release",
      status: "pending",
      users: 1000,
      percentage: 100,
    },
  ]);

  // Simulate real-time metrics updates
  useEffect(() => {
    const interval = setInterval(() => {
      setMetrics(prev => ({
        ...prev,
        migratedUsers: Math.min(prev.totalUsers, prev.migratedUsers + Math.floor(Math.random() * 3)),
        satisfactionScore: Math.max(0, Math.min(100, prev.satisfactionScore + (Math.random() * 2 - 1))),
        performanceScore: Math.max(0, Math.min(100, prev.performanceScore + (Math.random() * 1.5 - 0.75))),
        errorRate: Math.max(0, prev.errorRate + (Math.random() * 0.4 - 0.2)),
        cacheHitRate: Math.max(0, Math.min(100, prev.cacheHitRate + (Math.random() * 2 - 1))),
        systemUptime: Math.max(95, prev.systemUptime + (Math.random() * 0.5 - 0.25)),
        lastUpdate: new Date().toISOString(),
      }));
    }, 5000);

    return () => clearInterval(interval);
  }, []);

  const getStatusColor = (status: string) => {
    switch (status) {
      case "completed": return "text-green-600 bg-green-100";
      case "active": return "text-blue-600 bg-blue-100";
      case "pending": return "text-gray-600 bg-gray-100";
      case "failed": return "text-red-600 bg-red-100";
      default: return "text-gray-600 bg-gray-100";
    }
  };

  const getStatusText = (status: string) => {
    switch (status) {
      case "completed": return "Concluído";
      case "active": return "Ativo";
      case "pending": return "Pendente";
      case "failed": return "Falhou";
      default: return "Desconhecido";
    }
  };

  const getScoreColor = (score: number) => {
    if (score >= 90) return "text-green-600";
    if (score >= 75) return "text-yellow-600";
    return "text-red-600";
  };

  const exportMetrics = () => {
    const data = {
      metrics,
      phases,
      timestamp: new Date().toISOString(),
    };
    
    const blob = new Blob([JSON.stringify(data, null, 2)], { type: "application/json" });
    const url = URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url;
    a.download = `osm-migration-metrics-${Date.now()}.json`;
    a.click();
    URL.revokeObjectURL(url);
  };

  return (
    <div className="p-6 bg-white rounded-lg shadow-lg">
      <div className="mb-6">
        <div className="flex items-center justify-between">
          <div>
            <h2 className="text-2xl font-bold text-gray-900">
              Dashboard Migração OpenStreetMap
            </h2>
            <p className="text-gray-600">
              Monitoramento completo da migração do sistema de mapas
            </p>
          </div>
          <div className="flex items-center gap-3">
            <button
              onClick={exportMetrics}
              className="flex items-center gap-2 px-4 py-2 border border-gray-300 rounded-lg font-medium hover:bg-gray-50"
            >
              <Download className="w-4 h-4" />
              Exportar Métricas
            </button>
            <div className="flex items-center gap-2 text-sm text-gray-600">
              <RefreshCw className="w-4 h-4 animate-spin" />
              Última atualização: {new Date(metrics.lastUpdate).toLocaleTimeString()}
            </div>
          </div>
        </div>
      </div>

      {/* Navigation Tabs */}
      <div className="border-b border-gray-200 mb-6">
        <nav className="flex space-x-8">
          {[
            { id: "overview", label: "Visão Geral", icon: <Map className="w-4 h-4" /> },
            { id: "phases", label: "Fases da Migração", icon: <Users className="w-4 h-4" /> },
            { id: "testing", label: "Testes Automatizados", icon: <Activity className="w-4 h-4" /> },
            { id: "metrics", label: "Métricas Detalhadas", icon: <TrendingUp className="w-4 h-4" /> },
          ].map((tab) => (
            <button
              key={tab.id}
              onClick={() => setActiveTab(tab.id as any)}
              className={`flex items-center gap-2 py-2 px-1 border-b-2 font-medium text-sm ${
                activeTab === tab.id
                  ? "border-blue-500 text-blue-600"
                  : "border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300"
              }`}
            >
              {tab.icon}
              {tab.label}
            </button>
          ))}
        </nav>
      </div>

      {/* Overview Tab */}
      {activeTab === "overview" && (
        <div className="space-y-6">
          {/* Key Metrics */}
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
            <div className="bg-blue-50 rounded-lg p-4">
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-sm text-blue-600 font-medium">Usuários Migrados</p>
                  <p className="text-2xl font-bold text-blue-900">
                    {metrics.migratedUsers} / {metrics.totalUsers}
                  </p>
                  <p className="text-sm text-blue-600">
                    {((metrics.migratedUsers / metrics.totalUsers) * 100).toFixed(1)}%
                  </p>
                </div>
                <Users className="w-8 h-8 text-blue-500" />
              </div>
            </div>

            <div className="bg-green-50 rounded-lg p-4">
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-sm text-green-600 font-medium">Satisfação</p>
                  <p className={`text-2xl font-bold ${getScoreColor(metrics.satisfactionScore)}`}>
                    {metrics.satisfactionScore.toFixed(1)}%
                  </p>
                  <p className="text-sm text-green-600">Feedback dos usuários</p>
                </div>
                <CheckCircle className="w-8 h-8 text-green-500" />
              </div>
            </div>

            <div className="bg-purple-50 rounded-lg p-4">
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-sm text-purple-600 font-medium">Performance</p>
                  <p className={`text-2xl font-bold ${getScoreColor(metrics.performanceScore)}`}>
                    {metrics.performanceScore.toFixed(1)}%
                  </p>
                  <p className="text-sm text-purple-600">Velocidade de carregamento</p>
                </div>
                <Activity className="w-8 h-8 text-purple-500" />
              </div>
            </div>

            <div className="bg-orange-50 rounded-lg p-4">
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-sm text-orange-600 font-medium">Cache Hit Rate</p>
                  <p className={`text-2xl font-bold ${getScoreColor(metrics.cacheHitRate)}`}>
                    {metrics.cacheHitRate.toFixed(1)}%
                  </p>
                  <p className="text-sm text-orange-600">Eficiência de cache</p>
                </div>
                <Shield className="w-8 h-8 text-orange-500" />
              </div>
            </div>
          </div>

          {/* Current Phase Status */}
          <div className="bg-gray-50 rounded-lg p-6">
            <h3 className="text-lg font-semibold text-gray-900 mb-4">Status Atual da Migração</h3>
            <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
              <div>
                <h4 className="font-medium text-gray-900 mb-3">Fases da Migração</h4>
                <div className="space-y-2">
                  {phases.map((phase) => (
                    <div key={phase.id} className="flex items-center justify-between">
                      <div className="flex items-center gap-3">
                        <div className={`w-3 h-3 rounded-full ${
                          phase.status === "completed" ? "bg-green-500" :
                          phase.status === "active" ? "bg-blue-500" :
                          phase.status === "failed" ? "bg-red-500" : "bg-gray-300"
                        }`} />
                        <span className="text-sm font-medium text-gray-900">{phase.name}</span>
                      </div>
                      <div className="flex items-center gap-2">
                        <span className={`px-2 py-1 rounded-full text-xs font-medium ${getStatusColor(phase.status)}`}>
                          {getStatusText(phase.status)}
                        </span>
                        <span className="text-sm text-gray-600">{phase.users} usuários</span>
                      </div>
                    </div>
                  ))}
                </div>
              </div>

              <div>
                <h4 className="font-medium text-gray-900 mb-3">Métricas de Sistema</h4>
                <div className="space-y-3">
                  <div className="flex justify-between">
                    <span className="text-sm text-gray-600">Taxa de Erros:</span>
                    <span className={`text-sm font-medium ${getScoreColor(100 - metrics.errorRate * 10)}`}>
                      {metrics.errorRate.toFixed(1)}%
                    </span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-sm text-gray-600">Uptime do Sistema:</span>
                    <span className={`text-sm font-medium ${getScoreColor(metrics.systemUptime)}`}>
                      {metrics.systemUptime.toFixed(1)}%
                    </span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-sm text-gray-600">Economia de Custos:</span>
                    <span className="text-sm font-medium text-green-600">
                      R$ 450/mês (estimado)
                    </span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-sm text-gray-600">ROI Projetado:</span>
                    <span className="text-sm font-medium text-blue-600">
                      8 meses
                    </span>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>
      )}

      {/* Phases Tab */}
      {activeTab === "phases" && (
        <OSMPhasedRollout />
      )}

      {/* Testing Tab */}
      {activeTab === "testing" && (
        <OSMAutomatedTesting />
      )}

      {/* Metrics Tab */}
      {activeTab === "metrics" && (
        <div className="space-y-6">
          <div className="bg-gray-50 rounded-lg p-6">
            <h3 className="text-lg font-semibold text-gray-900 mb-4">Métricas Detalhadas</h3>
            
            <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
              <div>
                <h4 className="font-medium text-gray-900 mb-3">Performance</h4>
                <div className="space-y-2">
                  <div className="flex justify-between">
                    <span className="text-sm text-gray-600">Tempo médio de carregamento:</span>
                    <span className="text-sm font-medium">850ms</span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-sm text-gray-600">Tempo de carregamento de tiles:</span>
                    <span className="text-sm font-medium">120ms</span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-sm text-gray-600">Uso de memória:</span>
                    <span className="text-sm font-medium">45MB</span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-sm text-gray-600">Tamanho do bundle:</span>
                    <span className="text-sm font-medium">1.2MB</span>
                  </div>
                </div>
              </div>

              <div>
                <h4 className="font-medium text-gray-900 mb-3">Qualidade</h4>
                <div className="space-y-2">
                  <div className="flex justify-between">
                    <span className="text-sm text-gray-600">Taxa de sucesso:</span>
                    <span className="text-sm font-medium text-green-600">97.9%</span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-sm text-gray-600">Bug reports resolvidos:</span>
                    <span className="text-sm font-medium">12/15</span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-sm text-gray-600">Feature requests:</span>
                    <span className="text-sm font-medium">8</span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-sm text-gray-600">Tempo médio de resposta:</span>
                    <span className="text-sm font-medium">2.3h</span>
                  </div>
                </div>
              </div>
            </div>
          </div>

          {/* Historical Data */}
          <div className="bg-gray-50 rounded-lg p-6">
            <h3 className="text-lg font-semibold text-gray-900 mb-4">Dados Históricos</h3>
            <div className="text-center text-gray-500 py-8">
              <TrendingUp className="w-12 h-12 mx-auto mb-4 text-gray-400" />
              <p>Gráficos históricos serão implementados com integração real</p>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
