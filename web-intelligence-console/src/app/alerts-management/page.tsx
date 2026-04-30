"use client";

import React, { useState, useEffect } from "react";
import { AlertTriangle, Bell, Settings, Plus, Edit, Trash2, Check, X, Clock, TrendingUp } from "lucide-react";
import { ConsoleShell } from "@/app/components/console-shell";
import { alertsApi } from "@/app/services/api";

interface AlertRule {
  id: string;
  name: string;
  alert_type: string;
  severity: 'info' | 'warning' | 'critical';
  threshold_value?: number;
  conditions: Record<string, any>;
  is_active: boolean;
  created_at: string;
  updated_at: string;
  trigger_count: number;
  last_triggered?: string;
}

interface AlertStats {
  total_rules: number;
  active_rules: number;
  total_alerts_today: number;
  alerts_by_type: Record<string, number>;
  alerts_by_severity: Record<string, number>;
}

export default function AlertsManagementPage() {
  const [rules, setRules] = useState<AlertRule[]>([]);
  const [stats, setStats] = useState<AlertStats | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [showCreateForm, setShowCreateForm] = useState(false);
  const [editingRule, setEditingRule] = useState<AlertRule | null>(null);

  useEffect(() => {
    void loadData();
  }, []);

  async function loadData() {
    try {
      setLoading(true);
      setError(null);
      
      const [rulesData, statsData] = await Promise.all([
        alertsApi.getAlertRules(),
        alertsApi.getAlertStats(),
      ]);

      setRules(rulesData);
      setStats(statsData);
    } catch (err) {
      console.error(err);
      setError("Não foi possível carregar dados de alertas.");
    } finally {
      setLoading(false);
    }
  }

  async function toggleRule(ruleId: string, isActive: boolean) {
    try {
      await alertsApi.updateAlertRule(ruleId, { is_active: !isActive });
      setRules(rules.map(rule => 
        rule.id === ruleId ? { ...rule, is_active: !isActive } : rule
      ));
    } catch (err) {
      console.error(err);
      setError("Falha ao atualizar regra de alerta.");
    }
  }

  async function deleteRule(ruleId: string) {
    if (!confirm("Tem certeza que deseja excluir esta regra de alerta?")) return;
    
    try {
      await alertsApi.deleteAlertRule(ruleId);
      setRules(rules.filter(rule => rule.id !== ruleId));
    } catch (err) {
      console.error(err);
      setError("Falha ao excluir regra de alerta.");
    }
  }

  const getSeverityColor = (severity: string) => {
    switch (severity) {
      case 'critical': return 'text-red-600 bg-red-50 border-red-200';
      case 'warning': return 'text-orange-600 bg-orange-50 border-orange-200';
      case 'info': return 'text-blue-600 bg-blue-50 border-blue-200';
      default: return 'text-gray-600 bg-gray-50 border-gray-200';
    }
  };

  const getAlertTypeLabel = (type: string) => {
    const labels: Record<string, string> = {
      'watchlist_match': 'Match Watchlist',
      'suspicious_route': 'Rota Suspeita',
      'convoy_detected': 'Comboio Detectado',
      'impossible_travel': 'Viagem Impossível',
      'route_anomaly': 'Anomalia de Rota',
      'high_score': 'Score Elevado',
      'frequency_anomaly': 'Anomalia de Frequência',
    };
    return labels[type] || type;
  };

  return (
    <ConsoleShell
      title="Gestão de Alertas"
      subtitle="Configuração e monitoramento de regras de alerta automáticas."
    >
      {error && (
        <div className="mb-6 rounded-3xl border border-red-200 bg-red-50 px-5 py-4 text-sm text-red-700">
          {error}
        </div>
      )}

      {/* Stats Overview */}
      {stats && (
        <div className="mb-6 grid gap-4 md:grid-cols-4">
          <div className="rounded-2xl border border-gray-200 bg-white p-4">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-gray-600">Regras Ativas</p>
                <p className="text-2xl font-semibold text-gray-900">{stats.active_rules}</p>
                <p className="text-xs text-gray-500">de {stats.total_rules} totais</p>
              </div>
              <Settings className="h-8 w-8 text-blue-600" />
            </div>
          </div>
          <div className="rounded-2xl border border-gray-200 bg-white p-4">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-gray-600">Alertas Hoje</p>
                <p className="text-2xl font-semibold text-gray-900">{stats.total_alerts_today}</p>
              </div>
              <Bell className="h-8 w-8 text-orange-600" />
            </div>
          </div>
          <div className="rounded-2xl border border-gray-200 bg-white p-4">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-gray-600">Alertas Críticos</p>
                <p className="text-2xl font-semibold text-red-600">
                  {stats.alerts_by_severity?.critical || 0}
                </p>
              </div>
              <AlertTriangle className="h-8 w-8 text-red-600" />
            </div>
          </div>
          <div className="rounded-2xl border border-gray-200 bg-white p-4">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-gray-600">Taxa de Disparo</p>
                <p className="text-2xl font-semibold text-gray-900">
                  {stats.total_rules > 0 
                    ? ((stats.total_alerts_today / stats.total_rules) * 100).toFixed(1)
                    : "0"}%
                </p>
              </div>
              <TrendingUp className="h-8 w-8 text-green-600" />
            </div>
          </div>
        </div>
      )}

      {/* Actions */}
      <div className="mb-6 flex items-center justify-between">
        <div className="flex items-center gap-4">
          <button
            onClick={() => setShowCreateForm(true)}
            className="rounded-lg bg-blue-600 px-4 py-2 text-sm font-medium text-white hover:bg-blue-700"
          >
            <Plus className="mr-2 h-4 w-4 inline" />
            Nova Regra
          </button>
          <button
            onClick={loadData}
            className="rounded-lg border border-gray-200 bg-white px-4 py-2 text-sm font-medium text-gray-700 hover:bg-gray-50"
          >
            <Clock className="mr-2 h-4 w-4 inline" />
            Atualizar
          </button>
        </div>
      </div>

      {/* Alert Rules Table */}
      <div className="rounded-2xl border border-gray-200 bg-white overflow-hidden">
        <div className="px-6 py-4 border-b border-gray-200">
          <h3 className="text-lg font-semibold text-gray-900">Regras de Alerta</h3>
        </div>
        <div className="overflow-x-auto">
          <table className="w-full">
            <thead className="bg-gray-50">
              <tr>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Nome
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Tipo
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Severidade
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Status
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Disparos
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Último
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Ações
                </th>
              </tr>
            </thead>
            <tbody className="divide-y divide-gray-200">
              {rules.map((rule) => (
                <tr key={rule.id} className="hover:bg-gray-50">
                  <td className="px-6 py-4 whitespace-nowrap">
                    <div>
                      <div className="text-sm font-medium text-gray-900">{rule.name}</div>
                      <div className="text-xs text-gray-500">ID: {rule.id.slice(0, 8)}...</div>
                    </div>
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap">
                    <span className="text-sm text-gray-900">
                      {getAlertTypeLabel(rule.alert_type)}
                    </span>
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap">
                    <span className={`inline-flex px-2 py-1 text-xs font-semibold rounded-full border ${getSeverityColor(rule.severity)}`}>
                      {rule.severity.toUpperCase()}
                    </span>
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap">
                    <button
                      onClick={() => toggleRule(rule.id, rule.is_active)}
                      className={`inline-flex items-center px-2 py-1 text-xs font-semibold rounded-full ${
                        rule.is_active 
                          ? 'bg-green-100 text-green-800' 
                          : 'bg-gray-100 text-gray-800'
                      }`}
                    >
                      {rule.is_active ? (
                        <>
                          <Check className="mr-1 h-3 w-3" />
                          ATIVA
                        </>
                      ) : (
                        <>
                          <X className="mr-1 h-3 w-3" />
                          INATIVA
                        </>
                      )}
                    </button>
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                    {rule.trigger_count}
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                    {rule.last_triggered 
                      ? new Date(rule.last_triggered).toLocaleString('pt-BR', {
                          day: '2-digit',
                          month: '2-digit',
                          hour: '2-digit',
                          minute: '2-digit'
                        })
                      : 'Nunca'
                    }
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap text-sm font-medium">
                    <div className="flex items-center gap-2">
                      <button
                        onClick={() => setEditingRule(rule)}
                        className="text-blue-600 hover:text-blue-900"
                      >
                        <Edit className="h-4 w-4" />
                      </button>
                      <button
                        onClick={() => deleteRule(rule.id)}
                        className="text-red-600 hover:text-red-900"
                      >
                        <Trash2 className="h-4 w-4" />
                      </button>
                    </div>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>

      {/* Alert Type Distribution */}
      {stats && (
        <div className="mt-6 grid gap-6 md:grid-cols-2">
          <div className="rounded-2xl border border-gray-200 bg-white p-4">
            <h4 className="text-sm font-semibold text-gray-900 mb-4">Alertas por Tipo</h4>
            <div className="space-y-2">
              {Object.entries(stats.alerts_by_type || {}).map(([type, count]) => (
                <div key={type} className="flex items-center justify-between">
                  <span className="text-sm text-gray-600">{getAlertTypeLabel(type)}</span>
                  <span className="text-sm font-medium text-gray-900">{count}</span>
                </div>
              ))}
            </div>
          </div>
          <div className="rounded-2xl border border-gray-200 bg-white p-4">
            <h4 className="text-sm font-semibold text-gray-900 mb-4">Alertas por Severidade</h4>
            <div className="space-y-2">
              {Object.entries(stats.alerts_by_severity || {}).map(([severity, count]) => (
                <div key={severity} className="flex items-center justify-between">
                  <span className={`text-sm font-medium ${getSeverityColor(severity)}`}>
                    {severity.toUpperCase()}
                  </span>
                  <span className="text-sm font-medium text-gray-900">{count}</span>
                </div>
              ))}
            </div>
          </div>
        </div>
      )}

      {loading && (
        <div className="mt-6 text-center text-sm text-gray-500">
          Carregando dados de alertas...
        </div>
      )}
    </ConsoleShell>
  );
}
