"use client";

import React, { useState, useEffect } from "react";
import { Users, MapPin, Phone, Mail, Shield, Search, Filter, Plus, Edit, Trash2, RefreshCw, Clock, CheckCircle, XCircle, AlertCircle, Eye } from "lucide-react";
import { ConsoleShell } from "@/app/components/console-shell";
import { agentsApi } from "@/app/services/api";

interface Agent {
  id: string;
  name: string;
  email: string;
  phone: string;
  badge_number: string;
  role: string;
  status: string;
  agency_id: string;
  agency_name: string;
  unit_id?: string;
  unit_name?: string;
  last_login?: string;
  is_active: boolean;
  created_at: string;
  updated_at: string;
}

export default function AgentsManagementPage() {
  const [agents, setAgents] = useState<Agent[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [searchTerm, setSearchTerm] = useState("");
  const [filters, setFilters] = useState({
    agency_id: "",
    unit_id: "",
    status: "",
  });
  const [selectedAgent, setSelectedAgent] = useState<Agent | null>(null);
  const [showCreateForm, setShowCreateForm] = useState(false);
  const [showLocationModal, setShowLocationModal] = useState(false);

  useEffect(() => {
    void loadAgents();
  }, [filters]);

  async function loadAgents() {
    try {
      setLoading(true);
      setError(null);
      
      const response = await agentsApi.listAgents(filters);
      setAgents(response.agents);
    } catch (err) {
      console.error(err);
      setError("Não foi possível carregar agentes.");
    } finally {
      setLoading(false);
    }
  }

  async function handleUpdateStatus(agentId: string, status: string, reason?: string) {
    try {
      await agentsApi.updateAgentStatus(agentId, { status, reason });
      await loadAgents();
      setSelectedAgent(null);
    } catch (err) {
      console.error(err);
      setError("Falha ao atualizar status do agente.");
    }
  }

  async function handleUpdateLocation(agentId: string, location: {
    latitude: number;
    longitude: number;
    accuracy?: number;
    heading?: number;
    speed?: number;
  }) {
    try {
      await agentsApi.updateAgentLocation(agentId, location);
      await loadAgents();
      setShowLocationModal(false);
    } catch (err) {
      console.error(err);
      setError("Falha ao atualizar localização do agente.");
    }
  }

  const filteredAgents = agents.filter(agent =>
    agent.name.toLowerCase().includes(searchTerm.toLowerCase()) ||
    agent.email.toLowerCase().includes(searchTerm.toLowerCase()) ||
    agent.badge_number.toLowerCase().includes(searchTerm.toLowerCase()) ||
    agent.phone.toLowerCase().includes(searchTerm.toLowerCase())
  );

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'active': return 'text-green-600 bg-green-50 border-green-200';
      case 'inactive': return 'text-gray-600 bg-gray-50 border-gray-200';
      case 'suspended': return 'text-red-600 bg-red-50 border-red-200';
      case 'on_duty': return 'text-blue-600 bg-blue-50 border-blue-200';
      case 'off_duty': return 'text-yellow-600 bg-yellow-50 border-yellow-200';
      default: return 'text-gray-600 bg-gray-50 border-gray-200';
    }
  };

  const getRoleColor = (role: string) => {
    switch (role) {
      case 'field_agent': return 'text-blue-600 bg-blue-50 border-blue-200';
      case 'intelligence': return 'text-purple-600 bg-purple-50 border-purple-200';
      case 'supervisor': return 'text-orange-600 bg-orange-50 border-orange-200';
      case 'admin': return 'text-red-600 bg-red-50 border-red-200';
      default: return 'text-gray-600 bg-gray-50 border-gray-200';
    }
  };

  const getRoleLabel = (role: string) => {
    const labels: Record<string, string> = {
      'field_agent': 'Agente de Campo',
      'intelligence': 'Inteligência',
      'supervisor': 'Supervisor',
      'admin': 'Administrador',
    };
    return labels[role] || role;
  };

  const getStatusLabel = (status: string) => {
    const labels: Record<string, string> = {
      'active': 'Ativo',
      'inactive': 'Inativo',
      'suspended': 'Suspenso',
      'on_duty': 'Em Serviço',
      'off_duty': 'Fora de Serviço',
    };
    return labels[status] || status;
  };

  return (
    <ConsoleShell
      title="Gestão de Agentes"
      subtitle="Cadastro, status e localização em tempo real dos agentes."
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
              <p className="text-sm text-gray-600">Total Agentes</p>
              <p className="text-2xl font-semibold text-gray-900">{agents.length}</p>
            </div>
            <Users className="h-8 w-8 text-blue-600" />
          </div>
        </div>
        <div className="rounded-2xl border border-gray-200 bg-white p-4">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm text-gray-600">Ativos</p>
              <p className="text-2xl font-semibold text-green-600">
                {agents.filter(a => a.status === 'active' || a.status === 'on_duty').length}
              </p>
            </div>
            <CheckCircle className="h-8 w-8 text-green-600" />
          </div>
        </div>
        <div className="rounded-2xl border border-gray-200 bg-white p-4">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm text-gray-600">Em Serviço</p>
              <p className="text-2xl font-semibold text-blue-600">
                {agents.filter(a => a.status === 'on_duty').length}
              </p>
            </div>
            <Shield className="h-8 w-8 text-blue-600" />
          </div>
        </div>
        <div className="rounded-2xl border border-gray-200 bg-white p-4">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm text-gray-600">Suspenso</p>
              <p className="text-2xl font-semibold text-red-600">
                {agents.filter(a => a.status === 'suspended').length}
              </p>
            </div>
            <XCircle className="h-8 w-8 text-red-600" />
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
                placeholder="Buscar agente..."
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
              <option value="active">Ativo</option>
              <option value="inactive">Inativo</option>
              <option value="suspended">Suspenso</option>
              <option value="on_duty">Em Serviço</option>
              <option value="off_duty">Fora de Serviço</option>
            </select>
            <button
              onClick={loadAgents}
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
              Novo Agente
            </button>
          </div>
        </div>
      </div>

      {/* Agents Table */}
      <div className="rounded-2xl border border-gray-200 bg-white overflow-hidden">
        <div className="px-6 py-4 border-b border-gray-200">
          <h3 className="text-lg font-semibold text-gray-900">Agentes</h3>
        </div>
        <div className="overflow-x-auto">
          <table className="w-full">
            <thead className="bg-gray-50">
              <tr>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Agente
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Contato
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Função
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Status
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Agência/Unidade
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Último Login
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Ações
                </th>
              </tr>
            </thead>
            <tbody className="divide-y divide-gray-200">
              {filteredAgents.map((agent) => (
                <tr key={agent.id} className="hover:bg-gray-50">
                  <td className="px-6 py-4 whitespace-nowrap">
                    <div>
                      <div className="text-sm font-medium text-gray-900">{agent.name}</div>
                      <div className="text-xs text-gray-500">Crachá: {agent.badge_number}</div>
                      <div className="text-xs text-gray-500">ID: {agent.id.slice(0, 8)}...</div>
                    </div>
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap">
                    <div className="space-y-1">
                      <div className="flex items-center text-sm text-gray-900">
                        <Mail className="mr-2 h-3 w-3 text-gray-400" />
                        {agent.email}
                      </div>
                      <div className="flex items-center text-sm text-gray-900">
                        <Phone className="mr-2 h-3 w-3 text-gray-400" />
                        {agent.phone}
                      </div>
                    </div>
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap">
                    <span className={`inline-flex px-2 py-1 text-xs font-semibold rounded-full border ${getRoleColor(agent.role)}`}>
                      {getRoleLabel(agent.role)}
                    </span>
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap">
                    <span className={`inline-flex px-2 py-1 text-xs font-semibold rounded-full border ${getStatusColor(agent.status)}`}>
                      {getStatusLabel(agent.status)}
                    </span>
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap">
                    <div>
                      <div className="text-sm text-gray-900">{agent.agency_name}</div>
                      {agent.unit_name && (
                        <div className="text-xs text-gray-500">{agent.unit_name}</div>
                      )}
                    </div>
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                    {agent.last_login 
                      ? new Date(agent.last_login).toLocaleString('pt-BR', {
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
                        onClick={() => setSelectedAgent(agent)}
                        className="text-blue-600 hover:text-blue-900"
                      >
                        <Eye className="h-4 w-4" />
                      </button>
                      <button
                        onClick={() => setShowLocationModal(true)}
                        className="text-green-600 hover:text-green-900"
                      >
                        <MapPin className="h-4 w-4" />
                      </button>
                      <button
                        onClick={() => handleUpdateStatus(agent.id, 
                          agent.status === 'active' ? 'inactive' : 'active'
                        )}
                        className="text-orange-600 hover:text-orange-900"
                      >
                        <AlertCircle className="h-4 w-4" />
                      </button>
                    </div>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>

      {/* Status Distribution */}
      <div className="mt-6 rounded-2xl border border-gray-200 bg-white p-4">
        <h4 className="text-sm font-semibold text-gray-900 mb-4">Distribuição por Status</h4>
        <div className="grid gap-4 md:grid-cols-5">
          {['active', 'inactive', 'suspended', 'on_duty', 'off_duty'].map((status) => {
            const count = agents.filter(a => a.status === status).length;
            const percentage = agents.length > 0 ? (count / agents.length) * 100 : 0;
            return (
              <div key={status} className="text-center">
                <div className={`inline-flex px-3 py-2 text-sm font-semibold rounded-full border ${getStatusColor(status)}`}>
                  {getStatusLabel(status)}
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

      {loading && (
        <div className="mt-6 text-center text-sm text-gray-500">
          Carregando agentes...
        </div>
      )}
    </ConsoleShell>
  );
}
