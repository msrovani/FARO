"use client";

import React, { useState, useEffect } from "react";
import { ConsoleShell } from "@/app/components/console-shell";
import { 
  Users, 
  Search, 
  Filter, 
  Plus, 
  Edit, 
  Eye, 
  MapPin, 
  Phone,
  Mail,
  Shield,
  Calendar,
  Activity,
  RefreshCw
} from "lucide-react";
import { agentsApi } from "@/app/services/api";
import { User, PaginatedResponse } from "@/app/types";

export default function AgentsPage() {
  const [agents, setAgents] = useState<User[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [selectedAgent, setSelectedAgent] = useState<User | null>(null);
  const [filters, setFilters] = useState({
    agency_id: "",
    unit_id: "",
    role: "",
    status: ""
  });
  const [pagination, setPagination] = useState({
    page: 1,
    page_size: 20
  });

  useEffect(() => {
    loadAgents();
  }, [filters, pagination.page]);

  const loadAgents = async () => {
    try {
      setLoading(true);
      const response = await agentsApi.listAgents({
        ...filters,
        ...pagination
      });
      setAgents(response.items || []);
    } catch (err) {
      console.error("Failed to load agents:", err);
      setError("Falha ao carregar agentes.");
    } finally {
      setLoading(false);
    }
  };

  const handleUpdateStatus = async (agent: User, status: string) => {
    try {
      await agentsApi.updateAgentStatus(agent.id, { status });
      setAgents(agents.map(a => 
        a.id === agent.id ? { ...a, is_active: status === 'active' } : a
      ));
    } catch (err) {
      console.error("Failed to update agent status:", err);
      setError("Falha ao atualizar status do agente.");
    }
  };

  const handleUpdateLocation = async (agent: User, location: { latitude: number; longitude: number }) => {
    try {
      await agentsApi.updateAgentLocation(agent.id, location);
      // Update local state or reload
      loadAgents();
    } catch (err) {
      console.error("Failed to update agent location:", err);
      setError("Falha ao atualizar localização do agente.");
    }
  };

  const getStatusColor = (isActive: boolean) => {
    return isActive ? "text-green-600 bg-green-50" : "text-red-600 bg-red-50";
  };

  const getStatusIcon = (isActive: boolean) => {
    return isActive ? <Activity size={16} /> : <Phone size={16} />;
  };

  const getRoleColor = (role: string) => {
    switch (role) {
      case "admin": return "text-purple-600 bg-purple-50";
      case "supervisor": return "text-blue-600 bg-blue-50";
      case "intelligence": return "text-yellow-600 bg-yellow-50";
      case "field_agent": return "text-green-600 bg-green-50";
      default: return "text-gray-600 bg-gray-50";
    }
  };

  return (
    <ConsoleShell
      title="Gestão de Agentes"
      subtitle="Gerenciamento completo de agentes de campo e suas localizações."
    >
      <div className="space-y-6">
        {/* Filters and Actions */}
        <div className="bg-white rounded-lg shadow-sm p-6">
          <div className="flex flex-col lg:flex-row gap-4 items-start lg:items-end">
            {/* Filters */}
            <div className="flex-1 grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">Agência</label>
                <select
                  value={filters.agency_id}
                  onChange={(e) => setFilters({ ...filters, agency_id: e.target.value })}
                  className="w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-blue-500 focus:border-blue-500 sm:text-sm"
                >
                  <option value="">Todas</option>
                  {/* TODO: Load agencies dynamically */}
                </select>
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">Unidade</label>
                <select
                  value={filters.unit_id}
                  onChange={(e) => setFilters({ ...filters, unit_id: e.target.value })}
                  className="w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-blue-500 focus:border-blue-500 sm:text-sm"
                >
                  <option value="">Todas</option>
                  {/* TODO: Load units dynamically */}
                </select>
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">Função</label>
                <select
                  value={filters.role}
                  onChange={(e) => setFilters({ ...filters, role: e.target.value })}
                  className="w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-blue-500 focus:border-blue-500 sm:text-sm"
                >
                  <option value="">Todas</option>
                  <option value="field_agent">Agente de Campo</option>
                  <option value="intelligence">Inteligência</option>
                  <option value="supervisor">Supervisor</option>
                  <option value="admin">Administrador</option>
                </select>
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">Status</label>
                <select
                  value={filters.status}
                  onChange={(e) => setFilters({ ...filters, status: e.target.value })}
                  className="w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-blue-500 focus:border-blue-500 sm:text-sm"
                >
                  <option value="">Todos</option>
                  <option value="active">Ativo</option>
                  <option value="inactive">Inativo</option>
                </select>
              </div>
            </div>

            {/* Actions */}
            <div className="flex gap-2">
              <button
                onClick={() => console.log("Navigate to create agent")}
                className="inline-flex items-center px-4 py-2 border border-transparent rounded-md shadow-sm text-sm font-medium text-white bg-blue-600 hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500"
              >
                <Plus size={16} className="mr-2" />
                Novo Agente
              </button>

              <button
                onClick={loadAgents}
                className="inline-flex items-center px-4 py-2 border border-gray-300 rounded-md shadow-sm text-sm font-medium text-gray-700 bg-white hover:bg-gray-50 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500"
              >
                <RefreshCw size={16} className="mr-2" />
                Atualizar
              </button>
            </div>
          </div>
        </div>

        {/* Summary Stats */}
        <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
          <div className="bg-white rounded-lg shadow-sm p-6">
            <div className="flex items-center">
              <Users className="h-8 w-8 text-blue-600" />
              <div className="ml-3">
                <p className="text-sm font-medium text-gray-500">Total</p>
                <p className="text-2xl font-semibold text-gray-900">{agents.length}</p>
              </div>
            </div>
          </div>

          <div className="bg-white rounded-lg shadow-sm p-6">
            <div className="flex items-center">
              <Activity className="h-8 w-8 text-green-600" />
              <div className="ml-3">
                <p className="text-sm font-medium text-gray-500">Ativos</p>
                <p className="text-2xl font-semibold text-gray-900">
                  {agents.filter(a => a.is_active).length}
                </p>
              </div>
            </div>
          </div>

          <div className="bg-white rounded-lg shadow-sm p-6">
            <div className="flex items-center">
              <Phone className="h-8 w-8 text-red-600" />
              <div className="ml-3">
                <p className="text-sm font-medium text-gray-500">Inativos</p>
                <p className="text-2xl font-semibold text-gray-900">
                  {agents.filter(a => !a.is_active).length}
                </p>
              </div>
            </div>
          </div>

          <div className="bg-white rounded-lg shadow-sm p-6">
            <div className="flex items-center">
              <Shield className="h-8 w-8 text-purple-600" />
              <div className="ml-3">
                <p className="text-sm font-medium text-gray-500">Campo</p>
                <p className="text-2xl font-semibold text-gray-900">
                  {agents.filter(a => a.role === 'field_agent').length}
                </p>
              </div>
            </div>
          </div>
        </div>

        {/* Loading and Error States */}
        {loading && (
          <div className="bg-white rounded-lg shadow-sm p-8 text-center">
            <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600 mx-auto"></div>
            <p className="mt-4 text-gray-600">Carregando agentes...</p>
          </div>
        )}

        {error && (
          <div className="bg-red-50 border border-red-200 rounded-md p-4">
            <div className="flex">
              <Phone className="h-5 w-5 text-red-400" />
              <div className="ml-3">
                <h3 className="text-sm font-medium text-red-800">Erro</h3>
                <p className="mt-2 text-sm text-red-700">{error}</p>
              </div>
            </div>
          </div>
        )}

        {/* Agents Table */}
        {!loading && !error && (
          <div className="bg-white rounded-lg shadow-sm overflow-hidden">
            <div className="overflow-x-auto">
              <table className="min-w-full divide-y divide-gray-200">
                <thead className="bg-gray-50">
                  <tr>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                      Nome
                    </th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                      Email
                    </th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                      Função
                    </th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                      Status
                    </th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                      Agência
                    </th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                      Último Login
                    </th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                      Ações
                    </th>
                  </tr>
                </thead>
                <tbody className="bg-white divide-y divide-gray-200">
                  {agents.map((agent) => (
                    <tr key={agent.id} className="hover:bg-gray-50">
                      <td className="px-6 py-4 whitespace-nowrap text-sm font-medium text-gray-900">
                        <div className="flex items-center">
                          <Users size={16} className="mr-2 text-gray-400" />
                          {agent.full_name}
                        </div>
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                        <div className="flex items-center">
                          <Mail size={16} className="mr-2 text-gray-400" />
                          {agent.email}
                        </div>
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap">
                        <span className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium ${getRoleColor(agent.role)}`}>
                          {agent.role}
                        </span>
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap">
                        <span className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium ${getStatusColor(agent.is_active)}`}>
                          {getStatusIcon(agent.is_active)}
                          <span className="ml-2">{agent.is_active ? 'Ativo' : 'Inativo'}</span>
                        </span>
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                        {agent.agency_name || 'N/A'}
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                        <div className="flex items-center">
                          <Calendar size={16} className="mr-2 text-gray-400" />
                          {agent.last_login ? new Date(agent.last_login).toLocaleString() : 'Nunca'}
                        </div>
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap text-sm font-medium">
                        <div className="flex items-center gap-2">
                          <button
                            onClick={() => setSelectedAgent(agent)}
                            className="text-blue-600 hover:text-blue-900"
                          >
                            <Eye size={16} />
                          </button>
                          <button
                            onClick={() => console.log("Navigate to edit agent:", agent.id)}
                            className="text-green-600 hover:text-green-900"
                          >
                            <Edit size={16} />
                          </button>
                          <button
                            onClick={() => handleUpdateStatus(agent, agent.is_active ? 'inactive' : 'active')}
                            className="text-yellow-600 hover:text-yellow-900"
                          >
                            {agent.is_active ? <Phone size={16} /> : <Activity size={16} />}
                          </button>
                        </div>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>

            {/* Pagination */}
            <div className="bg-white px-4 py-3 flex items-center justify-between border-t border-gray-200 sm:px-6">
              <div className="flex-1 flex justify-between sm:hidden">
                <button
                  onClick={() => setPagination({ ...pagination, page: Math.max(1, pagination.page - 1) })}
                  disabled={pagination.page === 1}
                  className="relative inline-flex items-center px-4 py-2 border border-gray-300 text-sm font-medium rounded-md text-gray-700 bg-white hover:bg-gray-50 disabled:opacity-50"
                >
                  Anterior
                </button>
                <button
                  onClick={() => setPagination({ ...pagination, page: pagination.page + 1 })}
                  className="relative ml-3 inline-flex items-center px-4 py-2 border border-gray-300 text-sm font-medium rounded-md text-gray-700 bg-white hover:bg-gray-50"
                >
                  Próximo
                </button>
              </div>
              <div className="hidden sm:flex-1 sm:justify-between">
                <p className="text-sm text-gray-700">
                  Página <span className="font-medium">{pagination.page}</span> de{' '}
                  <span className="font-medium">{Math.ceil(agents.length / pagination.page_size)}</span>
                </p>
                <nav className="relative z-0 inline-flex rounded-md shadow-sm -space-x-px">
                  <button
                    onClick={() => setPagination({ ...pagination, page: Math.max(1, pagination.page - 1) })}
                    disabled={pagination.page === 1}
                    className="relative inline-flex items-center px-2 py-2 rounded-l-md border border-gray-300 bg-white text-sm font-medium text-gray-500 hover:bg-gray-50 disabled:opacity-50"
                  >
                    Anterior
                  </button>
                  <button
                    onClick={() => setPagination({ ...pagination, page: pagination.page + 1 })}
                    disabled={pagination.page >= Math.ceil(agents.length / pagination.page_size)}
                    className="relative ml-3 inline-flex items-center px-4 py-2 border border-gray-300 bg-white text-sm font-medium text-gray-700 hover:bg-gray-50"
                  >
                    Próximo
                  </button>
                </nav>
              </div>
            </div>
          </div>
        )}

        {/* Selected Agent Details Modal */}
        {selectedAgent && (
          <div className="fixed inset-0 bg-gray-600 bg-opacity-50 overflow-y-auto h-full w-full z-50">
            <div className="relative min-h-screen flex items-center justify-center p-4">
              <div className="relative bg-white rounded-lg overflow-hidden shadow-xl max-w-4xl w-full max-h-[90vh] overflow-y-auto">
                <div className="px-6 py-4">
                  <div className="flex items-start justify-between">
                    <h3 className="text-lg font-medium text-gray-900">Detalhes do Agente</h3>
                    <button
                      onClick={() => setSelectedAgent(null)}
                      className="text-gray-400 hover:text-gray-600"
                    >
                      <Phone size={24} />
                    </button>
                  </div>

                  <div className="mt-6 space-y-6">
                    {/* Agent Info */}
                    <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                      <div>
                        <h4 className="text-sm font-medium text-gray-900 mb-2">Informações Pessoais</h4>
                        <dl className="space-y-2">
                          <div className="flex justify-between">
                            <dt className="text-sm text-gray-500">ID:</dt>
                            <dd className="text-sm font-medium text-gray-900">{selectedAgent.id}</dd>
                          </div>
                          <div className="flex justify-between">
                            <dt className="text-sm text-gray-500">Nome:</dt>
                            <dd className="text-sm font-medium text-gray-900">{selectedAgent.full_name}</dd>
                          </div>
                          <div className="flex justify-between">
                            <dt className="text-sm text-gray-500">Email:</dt>
                            <dd className="text-sm font-medium text-gray-900">{selectedAgent.email}</dd>
                          </div>
                          <div className="flex justify-between">
                            <dt className="text-sm text-gray-500">CPF:</dt>
                            <dd className="text-sm font-medium text-gray-900">{selectedAgent.cpf || 'N/A'}</dd>
                          </div>
                          <div className="flex justify-between">
                            <dt className="text-sm text-gray-500">Crachá:</dt>
                            <dd className="text-sm font-medium text-gray-900">{selectedAgent.badge_number || 'N/A'}</dd>
                          </div>
                        </dl>
                      </div>

                      <div>
                        <h4 className="text-sm font-medium text-gray-900 mb-2">Informações Profissionais</h4>
                        <dl className="space-y-2">
                          <div className="flex justify-between">
                            <dt className="text-sm text-gray-500">Função:</dt>
                            <dd className="text-sm font-medium">
                              <span className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium ${getRoleColor(selectedAgent.role)}`}>
                                {selectedAgent.role}
                              </span>
                            </dd>
                          </div>
                          <div className="flex justify-between">
                            <dt className="text-sm text-gray-500">Status:</dt>
                            <dd className="text-sm font-medium">
                              <span className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium ${getStatusColor(selectedAgent.is_active)}`}>
                                {getStatusIcon(selectedAgent.is_active)}
                                <span className="ml-2">{selectedAgent.is_active ? 'Ativo' : 'Inativo'}</span>
                              </span>
                            </dd>
                          </div>
                          <div className="flex justify-between">
                            <dt className="text-sm text-gray-500">Agência:</dt>
                            <dd className="text-sm font-medium text-gray-900">{selectedAgent.agency_name || 'N/A'}</dd>
                          </div>
                          <div className="flex justify-between">
                            <dt className="text-sm text-gray-500">Unidade:</dt>
                            <dd className="text-sm font-medium text-gray-900">{selectedAgent.unit_name || 'N/A'}</dd>
                          </div>
                          <div className="flex justify-between">
                            <dt className="text-sm text-gray-500">Verificado:</dt>
                            <dd className="text-sm font-medium text-gray-900">{selectedAgent.is_verified ? 'Sim' : 'Não'}</dd>
                          </div>
                          <div className="flex justify-between">
                            <dt className="text-sm text-gray-500">Último Login:</dt>
                            <dd className="text-sm font-medium text-gray-900">
                              {selectedAgent.last_login ? new Date(selectedAgent.last_login).toLocaleString() : 'Nunca'}
                            </dd>
                          </div>
                        </dl>
                      </div>
                    </div>

                    {/* Actions */}
                    <div className="flex gap-3 pt-4 border-t border-gray-200">
                      <button
                        onClick={() => console.log("Navigate to edit agent:", selectedAgent.id)}
                        className="flex-1 inline-flex justify-center items-center px-4 py-2 border border-transparent rounded-md shadow-sm text-sm font-medium text-white bg-blue-600 hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500"
                      >
                        <Edit size={16} className="mr-2" />
                        Editar
                      </button>
                      <button
                        onClick={() => handleUpdateStatus(selectedAgent, selectedAgent.is_active ? 'inactive' : 'active')}
                        className="flex-1 inline-flex justify-center items-center px-4 py-2 border border-gray-300 rounded-md shadow-sm text-sm font-medium text-gray-700 bg-white hover:bg-gray-50 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500"
                      >
                        {selectedAgent.is_active ? <Phone size={16} className="mr-2" /> : <Activity size={16} className="mr-2" />}
                        {selectedAgent.is_active ? 'Desativar' : 'Ativar'}
                      </button>
                      <button
                        onClick={() => setSelectedAgent(null)}
                        className="flex-1 inline-flex justify-center items-center px-4 py-2 border border-gray-300 rounded-md shadow-sm text-sm font-medium text-gray-700 bg-white hover:bg-gray-50 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500"
                      >
                        Fechar
                      </button>
                    </div>
                  </div>
                </div>
              </div>
            </div>
          </div>
        )}
      </div>
    </ConsoleShell>
  );
}
