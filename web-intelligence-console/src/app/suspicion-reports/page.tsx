"use client";

import React, { useState, useEffect } from "react";
import { 
  FileText, 
  Search, 
  Filter, 
  Plus, 
  Eye, 
  Edit, 
  Trash2, 
  Download, 
  Clock, 
  CheckCircle, 
  XCircle, 
  AlertTriangle,
  MapPin,
  Calendar,
  BarChart3,
  User,
  MessageSquare,
  RefreshCw,
  ArrowRight
} from "lucide-react";
import { ConsoleShell } from "@/app/components/console-shell";
import { suspicionApi } from "@/app/services/api";
import { PaginatedResponse, SuspicionReport } from "@/app/types";

export default function SuspicionReportsPage() {
  const [reports, setReports] = useState<SuspicionReport[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [filters, setFilters] = useState({
    status: "",
    agent_id: "",
    plate_number: "",
    start_date: "",
    end_date: "",
    suspicion_level: ""
  });
  const [pagination, setPagination] = useState({
    page: 1,
    page_size: 20
  });
  const [selectedReport, setSelectedReport] = useState<SuspicionReport | null>(null);

  useEffect(() => {
    loadReports();
  }, [filters, pagination.page]);

  const loadReports = async () => {
    try {
      setLoading(true);
      setError(null);
      const response = await suspicionApi.listReports({
        ...filters,
        ...pagination
      });
      setReports(response.items || []);
    } catch (err) {
      console.error("Failed to load suspicion reports:", err);
      setError("Falha ao carregar relatórios de suspeição.");
    } finally {
      setLoading(false);
    }
  };

      setReports(reportsData.reports);
      setStatistics(statsData);
    } catch (err) {
      console.error(err);
      setError("Não foi possível carregar relatórios de suspeita.");
    } finally {
      setLoading(false);
    }
  }

  async function handleAddFeedback(reportId: string, feedback: {
    feedback_type: string;
    message: string;
    rating?: number;
  }) {
    try {
      await suspicionApi.addFeedback(reportId, feedback);
      await loadData();
      setShowFeedbackModal(false);
    } catch (err) {
      console.error(err);
      setError("Falha ao adicionar feedback.");
    }
  }

  async function handleCloseReport(reportId: string, data: {
    closing_reason: string;
    final_outcome: string;
  }) {
    try {
      await suspicionApi.closeReport(reportId, data);
      await loadData();
      setSelectedReport(null);
    } catch (err) {
      console.error(err);
      setError("Falha ao fechar relatório.");
    }
  }

  const filteredReports = reports.filter(report =>
    report.agent_name.toLowerCase().includes(searchTerm.toLowerCase()) ||
    report.plate_number.toLowerCase().includes(searchTerm.toLowerCase()) ||
    report.id.toLowerCase().includes(searchTerm.toLowerCase())
  );

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'open': return 'text-blue-600 bg-blue-50 border-blue-200';
      case 'confirmed': return 'text-green-600 bg-green-50 border-green-200';
      case 'discarded': return 'text-red-600 bg-red-50 border-red-200';
      case 'monitoring': return 'text-yellow-600 bg-yellow-50 border-yellow-200';
      default: return 'text-gray-600 bg-gray-50 border-gray-200';
    }
  };

  const getLevelColor = (level: string) => {
    switch (level) {
      case 'critical': return 'text-red-600 bg-red-50 border-red-200';
      case 'high': return 'text-orange-600 bg-orange-50 border-orange-200';
      case 'medium': return 'text-yellow-600 bg-yellow-50 border-yellow-200';
      case 'low': return 'text-green-600 bg-green-50 border-green-200';
      default: return 'text-gray-600 bg-gray-50 border-gray-200';
    }
  };

  const getStatusIcon = (status: string) => {
    switch (status) {
      case 'open': return <Clock className="h-4 w-4" />;
      case 'confirmed': return <CheckCircle className="h-4 w-4" />;
      case 'discarded': return <XCircle className="h-4 w-4" />;
      case 'monitoring': return <AlertCircle className="h-4 w-4" />;
      default: return <FileText className="h-4 w-4" />;
    }
  };

  return (
    <ConsoleShell
      title="Relatórios de Suspeita"
      subtitle="Gestão completa de suspeitas com feedback e segunda abordagem."
    >
      {error && (
        <div className="mb-6 rounded-3xl border border-red-200 bg-red-50 px-5 py-4 text-sm text-red-700">
          {error}
        </div>
      )}

      {/* Statistics Overview */}
      {statistics && (
        <div className="mb-6 grid gap-4 md:grid-cols-5">
          <div className="rounded-2xl border border-gray-200 bg-white p-4">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-gray-600">Total</p>
                <p className="text-2xl font-semibold text-gray-900">{statistics.total_reports}</p>
              </div>
              <FileText className="h-8 w-8 text-blue-600" />
            </div>
          </div>
          <div className="rounded-2xl border border-gray-200 bg-white p-4">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-gray-600">Taxa Confirmação</p>
                <p className="text-2xl font-semibold text-green-600">
                  {(statistics.confirmation_rate * 100).toFixed(1)}%
                </p>
              </div>
              <CheckCircle className="h-8 w-8 text-green-600" />
            </div>
          </div>
          <div className="rounded-2xl border border-gray-200 bg-white p-4">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-gray-600">Tempo Médio</p>
                <p className="text-2xl font-semibold text-gray-900">
                  {statistics.avg_resolution_time_hours.toFixed(1)}h
                </p>
              </div>
              <Clock className="h-8 w-8 text-orange-600" />
            </div>
          </div>
          <div className="rounded-2xl border border-gray-200 bg-white p-4">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-gray-600">Abertos</p>
                <p className="text-2xl font-semibold text-blue-600">
                  {statistics.by_status.open || 0}
                </p>
              </div>
              <AlertCircle className="h-8 w-8 text-blue-600" />
            </div>
          </div>
          <div className="rounded-2xl border border-gray-200 bg-white p-4">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-gray-600">Críticos</p>
                <p className="text-2xl font-semibold text-red-600">
                  {statistics.by_level.critical || 0}
                </p>
              </div>
              <AlertTriangle className="h-8 w-8 text-red-600" />
            </div>
          </div>
        </div>
      )}

      {/* Filters and Actions */}
      <div className="mb-6 rounded-2xl border border-gray-200 bg-white p-4">
        <div className="flex items-center gap-4">
          <div className="flex-1">
            <div className="relative">
              <Search className="absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-gray-400" />
              <input
                type="text"
                placeholder="Buscar relatório..."
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
              <option value="open">Aberto</option>
              <option value="confirmed">Confirmado</option>
              <option value="discarded">Descartado</option>
              <option value="monitoring">Monitoramento</option>
            </select>
            <button
              onClick={loadData}
              className="rounded-lg border border-gray-200 bg-white px-4 py-2 text-sm font-medium text-gray-700 hover:bg-gray-50"
            >
              <RefreshCw className="mr-2 h-4 w-4" />
              Atualizar
            </button>
            <button
              onClick={() => setShowCreateForm(true)}
              className="rounded-lg bg-blue-600 px-4 py-2 text-sm font-medium text-white hover:bg-blue-700"
            >
              <Plus className="mr-2 h-4 w-4" />
              Novo Relatório
            </button>
          </div>
        </div>
      </div>

      {/* Reports Table */}
      <div className="rounded-2xl border border-gray-200 bg-white overflow-hidden">
        <div className="px-6 py-4 border-b border-gray-200">
          <h3 className="text-lg font-semibold text-gray-900">Relatórios</h3>
        </div>
        <div className="overflow-x-auto">
          <table className="w-full">
            <thead className="bg-gray-50">
              <tr>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  ID
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Agente
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Placa
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Motivo
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Nível
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Status
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Feedback
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Data
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Ações
                </th>
              </tr>
            </thead>
            <tbody className="divide-y divide-gray-200">
              {filteredReports.map((report) => (
                <tr key={report.id} className="hover:bg-gray-50">
                  <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                    {report.id.slice(0, 8)}...
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap">
                    <div>
                      <div className="text-sm font-medium text-gray-900">{report.agent_name}</div>
                      <div className="text-xs text-gray-500">{report.agent_id.slice(0, 8)}...</div>
                    </div>
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap text-sm font-medium text-gray-900">
                    {report.plate_number}
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                    {report.suspicion_reason}
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap">
                    <span className={`inline-flex px-2 py-1 text-xs font-semibold rounded-full border ${getLevelColor(report.suspicion_level)}`}>
                      {report.suspicion_level.toUpperCase()}
                    </span>
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap">
                    <span className={`inline-flex items-center px-2 py-1 text-xs font-semibold rounded-full border ${getStatusColor(report.status)}`}>
                      {getStatusIcon(report.status)}
                      <span className="ml-1">{report.status.toUpperCase()}</span>
                    </span>
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                    <div className="flex items-center gap-2">
                      <span>{report.feedback_count}</span>
                      {report.has_second_approach && (
                        <span className="text-xs bg-purple-100 text-purple-700 px-2 py-1 rounded-full">
                          2ª
                        </span>
                      )}
                    </div>
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                    {new Date(report.created_at).toLocaleString('pt-BR', {
                      day: '2-digit',
                      month: '2-digit',
                      hour: '2-digit',
                      minute: '2-digit'
                    })}
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap text-sm font-medium">
                    <div className="flex items-center gap-2">
                      <button
                        onClick={() => setSelectedReport(report)}
                        className="text-blue-600 hover:text-blue-900"
                      >
                        <Eye className="h-4 w-4" />
                      </button>
                      <button
                        onClick={() => setShowFeedbackModal(true)}
                        className="text-green-600 hover:text-green-900"
                      >
                        <MessageSquare className="h-4 w-4" />
                      </button>
                      <button
                        onClick={() => handleCloseReport(report.id, {
                          closing_reason: "Resolvido",
                          final_outcome: "Confirmado"
                        })}
                        className="text-red-600 hover:text-red-900"
                      >
                        <CheckCircle className="h-4 w-4" />
                      </button>
                    </div>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>

      {/* Charts Section */}
      {statistics && (
        <div className="mt-6 grid gap-6 md:grid-cols-3">
          <div className="rounded-2xl border border-gray-200 bg-white p-4">
            <h4 className="text-sm font-semibold text-gray-900 mb-4">Por Status</h4>
            <div className="space-y-2">
              {Object.entries(statistics.by_status).map(([status, count]) => (
                <div key={status} className="flex items-center justify-between">
                  <span className={`inline-flex items-center px-2 py-1 text-xs font-semibold rounded-full border ${getStatusColor(status)}`}>
                    {getStatusIcon(status)}
                    <span className="ml-1">{status}</span>
                  </span>
                  <span className="text-sm font-medium text-gray-900">{count}</span>
                </div>
              ))}
            </div>
          </div>
          <div className="rounded-2xl border border-gray-200 bg-white p-4">
            <h4 className="text-sm font-semibold text-gray-900 mb-4">Por Nível</h4>
            <div className="space-y-2">
              {Object.entries(statistics.by_level).map(([level, count]) => (
                <div key={level} className="flex items-center justify-between">
                  <span className={`inline-flex px-2 py-1 text-xs font-semibold rounded-full border ${getLevelColor(level)}`}>
                    {level.toUpperCase()}
                  </span>
                  <span className="text-sm font-medium text-gray-900">{count}</span>
                </div>
              ))}
            </div>
          </div>
          <div className="rounded-2xl border border-gray-200 bg-white p-4">
            <h4 className="text-sm font-semibold text-gray-900 mb-4">Por Motivo</h4>
            <div className="space-y-2">
              {Object.entries(statistics.by_reason).slice(0, 5).map(([reason, count]) => (
                <div key={reason} className="flex items-center justify-between">
                  <span className="text-sm text-gray-600">{reason}</span>
                  <span className="text-sm font-medium text-gray-900">{count}</span>
                </div>
              ))}
            </div>
          </div>
        </div>
      )}

      {loading && (
        <div className="mt-6 text-center text-sm text-gray-500">
          Carregando relatórios de suspeita...
        </div>
      )}
    </ConsoleShell>
  );
}
