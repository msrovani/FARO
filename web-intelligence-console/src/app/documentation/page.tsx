"use client";

import { useState, useEffect } from "react";

interface HardwareInfo {
  cpu_count: number;
  cpu_count_physical: number;
  total_memory_gb: number;
  available_memory_gb: number;
  gpu_available: boolean;
  gpu_type: string | null;
  gpu_memory_gb: number | null;
  platform: string;
  architecture: string;
}

interface OptimizationConfig {
  workers: number;
  process_pool_max_workers: number;
  process_pool_cpu_bound_workers: number;
  process_pool_io_bound_workers: number;
  ocr_device: string;
  ocr_confidence_threshold: number;
  ocr_auto_accept_enabled: boolean;
  ocr_auto_accept_threshold: number;
}

interface PerformanceMetric {
  avg_execution_time_ms: number;
  p95_execution_time_ms: number;
  p99_execution_time_ms: number;
  success_rate: number;
  error_count: number;
  total_executions: number;
  state: string;
}

interface Recommendation {
  task_type: string;
  current_state: string;
  current_workers: number;
  current_batch_size: number;
  recommended_workers: number;
  recommended_batch_size: number;
  reason: string;
}

interface SystemAlert {
  type: string;
  severity: string;
  message: string;
  details: string;
  timestamp: string;
}

interface LegalSection {
  title: string;
  content: string | string[];
}

interface LegalDocument {
  title: string;
  version: string;
  last_updated: string;
  sections: LegalSection[];
}

export default function DocumentationPage() {
  const [activeTab, setActiveTab] = useState("optimization");
  const [hardware, setHardware] = useState<HardwareInfo | null>(null);
  const [config, setConfig] = useState<OptimizationConfig | null>(null);
  const [performance, setPerformance] = useState<Record<string, PerformanceMetric>>({});
  const [recommendations, setRecommendations] = useState<Record<string, Recommendation>>({});
  const [alerts, setAlerts] = useState<SystemAlert[]>([]);
  const [termsOfService, setTermsOfService] = useState<LegalDocument | null>(null);
  const [privacyPolicy, setPrivacyPolicy] = useState<LegalDocument | null>(null);
  const [usageGuidelines, setUsageGuidelines] = useState<LegalDocument | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetchAllData();
    const interval = setInterval(fetchPerformanceData, 30000);
    return () => clearInterval(interval);
  }, []);

  const fetchAllData = async () => {
    setLoading(true);
    try {
      await Promise.all([
        fetchHardware(),
        fetchConfig(),
        fetchPerformanceData(),
        fetchRecommendations(),
        fetchAlerts(),
        fetchLegalDocs(),
      ]);
    } catch (error) {
      console.error("Error fetching documentation data:", error);
    } finally {
      setLoading(false);
    }
  };

  const fetchHardware = async () => {
    const response = await fetch("/api/v1/documentation/optimization/hardware");
    const data = await response.json();
    setHardware(data);
  };

  const fetchConfig = async () => {
    const response = await fetch("/api/v1/documentation/optimization/config");
    const data = await response.json();
    setConfig(data);
  };

  const fetchPerformanceData = async () => {
    const response = await fetch("/api/v1/documentation/optimization/performance");
    const data = await response.json();
    setPerformance(data);
  };

  const fetchRecommendations = async () => {
    const response = await fetch("/api/v1/documentation/optimization/recommendations");
    const data = await response.json();
    setRecommendations(data);
  };

  const fetchAlerts = async () => {
    const response = await fetch("/api/v1/documentation/usage/alerts");
    const data = await response.json();
    setAlerts(data.alerts || []);
  };

  const fetchLegalDocs = async () => {
    const [terms, privacy, guidelines] = await Promise.all([
      fetch("/api/v1/documentation/legal/terms-of-service").then(r => r.json()),
      fetch("/api/v1/documentation/legal/privacy-policy").then(r => r.json()),
      fetch("/api/v1/documentation/usage/guidelines").then(r => r.json()),
    ]);
    setTermsOfService(terms);
    setPrivacyPolicy(privacy);
    setUsageGuidelines(guidelines);
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center h-screen">
        <div className="text-center">
          <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-gray-900 mx-auto mb-4"></div>
          <p>Carregando documentação...</p>
        </div>
      </div>
    );
  }

  return (
    <div className="container mx-auto p-6 space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold">Documentação F.A.R.O.</h1>
          <p className="text-gray-600">Documentação técnica, legal e orientações de uso</p>
        </div>
        <div className="flex gap-2">
          <span className="px-3 py-1 bg-green-100 text-green-800 rounded-full text-sm">Online</span>
          <span className="px-3 py-1 bg-blue-100 text-blue-800 rounded-full text-sm">v1.0</span>
        </div>
      </div>

      <div className="border-b border-gray-200">
        <nav className="flex space-x-8">
          {["optimization", "performance", "legal", "usage"].map((tab) => (
            <button
              key={tab}
              onClick={() => setActiveTab(tab)}
              className={`py-4 px-1 border-b-2 font-medium text-sm ${
                activeTab === tab
                  ? "border-blue-500 text-blue-600"
                  : "border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300"
              }`}
            >
              {tab.charAt(0).toUpperCase() + tab.slice(1)}
            </button>
          ))}
        </nav>
      </div>

      {activeTab === "optimization" && (
        <div className="space-y-4">
          <div className="grid gap-4 md:grid-cols-2">
            <div className="bg-white shadow rounded-lg p-6">
              <h3 className="text-lg font-semibold mb-4">Hardware</h3>
              <div className="space-y-2">
                <div className="flex justify-between">
                  <span className="text-gray-600">CPU Cores:</span>
                  <span className="font-semibold">{hardware?.cpu_count_physical} físicos / {hardware?.cpu_count} lógicos</span>
                </div>
                <div className="flex justify-between">
                  <span className="text-gray-600">Memória:</span>
                  <span className="font-semibold">{hardware?.total_memory_gb?.toFixed(2)} GB total / {hardware?.available_memory_gb?.toFixed(2)} GB disponível</span>
                </div>
                <div className="flex justify-between">
                  <span className="text-gray-600">GPU:</span>
                  <span className="font-semibold">{hardware?.gpu_available ? `${hardware?.gpu_type} (${hardware?.gpu_memory_gb?.toFixed(2)} GB)` : "Não disponível"}</span>
                </div>
                <div className="flex justify-between">
                  <span className="text-gray-600">Plataforma:</span>
                  <span className="font-semibold">{hardware?.platform} ({hardware?.architecture})</span>
                </div>
              </div>
            </div>

            <div className="bg-white shadow rounded-lg p-6">
              <h3 className="text-lg font-semibold mb-4">Configuração</h3>
              <div className="space-y-2">
                <div className="flex justify-between">
                  <span className="text-gray-600">Workers (Uvicorn):</span>
                  <span className="font-semibold">{config?.workers}</span>
                </div>
                <div className="flex justify-between">
                  <span className="text-gray-600">Process Pool (Geral):</span>
                  <span className="font-semibold">{config?.process_pool_max_workers}</span>
                </div>
                <div className="flex justify-between">
                  <span className="text-gray-600">Process Pool (CPU-bound):</span>
                  <span className="font-semibold">{config?.process_pool_cpu_bound_workers}</span>
                </div>
                <div className="flex justify-between">
                  <span className="text-gray-600">Process Pool (I/O-bound):</span>
                  <span className="font-semibold">{config?.process_pool_io_bound_workers}</span>
                </div>
                <div className="flex justify-between">
                  <span className="text-gray-600">OCR Device:</span>
                  <span className="font-semibold">{config?.ocr_device}</span>
                </div>
                <div className="flex justify-between">
                  <span className="text-gray-600">OCR Auto-Accept:</span>
                  <span className="font-semibold">{config?.ocr_auto_accept_enabled ? `Sim (threshold: ${config?.ocr_auto_accept_threshold})` : "Não"}</span>
                </div>
              </div>
            </div>
          </div>

          <div className="bg-white shadow rounded-lg p-6">
            <h3 className="text-lg font-semibold mb-4">Recomendações Adaptativas</h3>
            <div className="space-y-4">
              {Object.entries(recommendations).map(([taskType, rec]) => (
                <div key={taskType} className="flex items-center justify-between p-4 border rounded-lg">
                  <div>
                    <div className="font-semibold">{taskType}</div>
                    <div className="text-sm text-gray-600">{rec.reason}</div>
                  </div>
                  <div className="flex items-center gap-4">
                    <div className="text-right">
                      <div className="text-xs text-gray-600">Workers</div>
                      <div className="font-semibold">{rec.current_workers} → {rec.recommended_workers}</div>
                    </div>
                    <div className="text-right">
                      <div className="text-xs text-gray-600">Batch</div>
                      <div className="font-semibold">{rec.current_batch_size} → {rec.recommended_batch_size}</div>
                    </div>
                    <span className={`px-2 py-1 rounded text-xs ${
                      rec.current_state === "healthy" ? "bg-green-100 text-green-800" :
                      rec.current_state === "degraded" ? "bg-yellow-100 text-yellow-800" :
                      "bg-red-100 text-red-800"
                    }`}>
                      {rec.current_state}
                    </span>
                  </div>
                </div>
              ))}
            </div>
          </div>
        </div>
      )}

      {activeTab === "performance" && (
        <div className="space-y-4">
          <div className="bg-white shadow rounded-lg p-6">
            <h3 className="text-lg font-semibold mb-4">Métricas de Performance</h3>
            <div className="space-y-4">
              {Object.entries(performance).map(([taskType, metric]) => (
                <div key={taskType} className="p-4 border rounded-lg">
                  <div className="flex items-center justify-between mb-3">
                    <div className="font-semibold">{taskType}</div>
                    <span className={`px-2 py-1 rounded text-xs ${
                      metric.state === "healthy" ? "bg-green-100 text-green-800" :
                      metric.state === "degraded" ? "bg-yellow-100 text-yellow-800" :
                      "bg-red-100 text-red-800"
                    }`}>
                      {metric.state}
                    </span>
                  </div>
                  <div className="grid grid-cols-4 gap-4 text-sm">
                    <div>
                      <div className="text-gray-600">Tempo Médio</div>
                      <div className="font-semibold">{metric.avg_execution_time_ms?.toFixed(2)} ms</div>
                    </div>
                    <div>
                      <div className="text-gray-600">P95</div>
                      <div className="font-semibold">{metric.p95_execution_time_ms?.toFixed(2)} ms</div>
                    </div>
                    <div>
                      <div className="text-gray-600">P99</div>
                      <div className="font-semibold">{metric.p99_execution_time_ms?.toFixed(2)} ms</div>
                    </div>
                    <div>
                      <div className="text-gray-600">Taxa de Sucesso</div>
                      <div className="font-semibold">{(metric.success_rate * 100)?.toFixed(2)}%</div>
                    </div>
                  </div>
                  <div className="mt-2 text-xs text-gray-600">
                    Total: {metric.total_executions} execuções | Erros: {metric.error_count}
                  </div>
                </div>
              ))}
            </div>
          </div>

          <div className="bg-white shadow rounded-lg p-6">
            <h3 className="text-lg font-semibold mb-4">Alertas do Sistema</h3>
            {alerts.length === 0 ? (
              <div className="text-center py-8 text-gray-600">
                <p>Nenhum alerta ativo</p>
              </div>
            ) : (
              <div className="space-y-3">
                {alerts.map((alert, index) => (
                  <div key={index} className={`p-4 rounded-lg border ${
                    alert.type === "error" ? "bg-red-50 border-red-200" : "bg-yellow-50 border-yellow-200"
                  }`}>
                    <div className="font-semibold">{alert.message}</div>
                    <div className="text-sm text-gray-600">{alert.details}</div>
                  </div>
                ))}
              </div>
            )}
          </div>
        </div>
      )}

      {activeTab === "legal" && (
        <div className="space-y-4">
          <div className="border-b border-gray-200">
            <nav className="flex space-x-8">
              <button
                onClick={() => setTermsOfService(termsOfService)}
                className="py-2 px-1 border-b-2 border-blue-500 text-blue-600 font-medium text-sm"
              >
                Termos de Uso
              </button>
              <button
                onClick={() => setPrivacyPolicy(privacyPolicy)}
                className="py-2 px-1 border-b-2 border-transparent text-gray-500 hover:text-gray-700 font-medium text-sm"
              >
                Política de Privacidade
              </button>
            </nav>
          </div>

          <div className="bg-white shadow rounded-lg p-6">
            <h2 className="text-xl font-semibold mb-2">{termsOfService?.title}</h2>
            <p className="text-gray-600 mb-6">Versão {termsOfService?.version} - Atualizado em {termsOfService?.last_updated}</p>
            <div className="space-y-6">
              {termsOfService?.sections.map((section, index) => (
                <div key={index}>
                  <h3 className="font-semibold mb-2">{section.title}</h3>
                  <p className="text-gray-600">{section.content}</p>
                </div>
              ))}
            </div>
          </div>
        </div>
      )}

      {activeTab === "usage" && (
        <div className="space-y-4">
          <div className="bg-white shadow rounded-lg p-6">
            <h2 className="text-xl font-semibold mb-2">{usageGuidelines?.title}</h2>
            <p className="text-gray-600 mb-6">Versão {usageGuidelines?.version} - Atualizado em {usageGuidelines?.last_updated}</p>
            <div className="space-y-6">
              {usageGuidelines?.sections.map((section, index) => (
                <div key={index}>
                  <h3 className="font-semibold mb-3">{section.title}</h3>
                  {Array.isArray(section.content) ? (
                    <ul className="list-disc list-inside space-y-1 text-gray-600">
                      {section.content.map((item, i) => (
                        <li key={i}>{item}</li>
                      ))}
                    </ul>
                  ) : (
                    <p className="text-gray-600">{section.content}</p>
                  )}
                </div>
              ))}
            </div>
          </div>

          <div className="bg-white shadow rounded-lg p-6">
            <h3 className="text-lg font-semibold mb-4">Alertas de Uso</h3>
            {alerts.length === 0 ? (
              <div className="text-center py-8 text-gray-600">
                <p>Nenhum alerta de uso ativo</p>
              </div>
            ) : (
              <div className="space-y-3">
                {alerts.map((alert, index) => (
                  <div key={index} className={`p-4 rounded-lg border ${
                    alert.type === "error" ? "bg-red-50 border-red-200" : "bg-yellow-50 border-yellow-200"
                  }`}>
                    <div className="font-semibold">{alert.message}</div>
                    <div className="text-sm text-gray-600">{alert.details}</div>
                  </div>
                ))}
              </div>
            )}
          </div>
        </div>
      )}
    </div>
  );
}
