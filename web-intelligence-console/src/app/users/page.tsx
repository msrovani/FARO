"use client";

import { useEffect, useState } from "react";
import { Plus, Search, Filter, UserPlus, Shield, User as UserIcon, Edit, Trash2 } from "lucide-react";

import { ConsoleShell } from "@/app/components/console-shell";
import { userApi, dashboardApi } from "@/app/services/api";
import { Agency } from "@/app/types";

interface User {
  id: string;
  email: string;
  full_name: string;
  cpf?: string;
  badge_number?: string;
  role: string;
  agency_id: string;
  agency_name?: string;
  unit_id?: string;
  unit_name?: string;
  is_active: boolean;
  is_verified: boolean;
  created_at: string;
}

export default function UsersPage() {
  const [users, setUsers] = useState<User[]>([]);
  const [agencies, setAgencies] = useState<Agency[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [selectedRole, setSelectedRole] = useState<string>("");
  const [selectedAgency, setSelectedAgency] = useState<string>("");
  const [searchTerm, setSearchTerm] = useState<string>("");
  const [page, setPage] = useState(1);
  const [total, setTotal] = useState(0);

  useEffect(() => {
    void loadUsers();
    void loadAgencies();
  }, [selectedRole, selectedAgency, page]);

  async function loadUsers() {
    try {
      setLoading(true);
      setError(null);
      const params: any = { page, page_size: 50 };
      if (selectedRole) params.role = selectedRole;
      if (selectedAgency) params.agency_id = selectedAgency;
      
      const response = await userApi.listUsers(params);
      setUsers(response.users);
      setTotal(response.total);
    } catch (err) {
      console.error(err);
      setError("Nao foi possivel carregar usuarios.");
    } finally {
      setLoading(false);
    }
  }

  async function loadAgencies() {
    try {
      const response = await dashboardApi.getAgencies();
      setAgencies(response.agencies);
    } catch (err) {
      console.error(err);
    }
  }

  return (
    <ConsoleShell
      title="Gestão de Usuários"
      subtitle="Cadastro e gerenciamento de analistas e agentes de campo por agência."
    >
      {/* Filters */}
      <div className="mb-6 flex flex-wrap items-center gap-4 rounded-2xl border border-gray-200 bg-white px-4 py-3">
        <div className="flex items-center gap-2 flex-1 min-w-[200px]">
          <Search className="h-5 w-5 text-gray-500" />
          <input
            type="text"
            placeholder="Buscar por nome ou email..."
            value={searchTerm}
            onChange={(e) => setSearchTerm(e.target.value)}
            className="flex-1 rounded-lg border-0 bg-transparent text-sm focus:ring-0"
          />
        </div>
        
        <select
          value={selectedRole}
          onChange={(e) => setSelectedRole(e.target.value)}
          className="rounded-lg border border-gray-200 bg-white px-3 py-2 text-sm font-medium text-gray-700 focus:ring-2 focus:ring-blue-500"
        >
          <option value="">Todos os perfis</option>
          <option value="intelligence">Analista de Inteligência</option>
          <option value="field_agent">Agente de Campo (PM)</option>
          <option value="supervisor">Supervisor</option>
          <option value="admin">Administrador</option>
        </select>

        <select
          value={selectedAgency}
          onChange={(e) => setSelectedAgency(e.target.value)}
          className="rounded-lg border border-gray-200 bg-white px-3 py-2 text-sm font-medium text-gray-700 focus:ring-2 focus:ring-blue-500"
        >
          <option value="">Todas as agências</option>
          {agencies.map((agency) => (
            <option key={agency.id} value={agency.id}>
              {agency.name} ({agency.type})
            </option>
          ))}
        </select>

        <button className="flex items-center gap-2 rounded-lg bg-blue-600 px-4 py-2 text-sm font-medium text-white hover:bg-blue-700">
          <UserPlus className="h-4 w-4" />
          Novo Usuário
        </button>
      </div>

      {error ? (
        <div className="mb-6 rounded-3xl border border-red-200 bg-red-50 px-5 py-4 text-sm text-red-700">
          {error}
        </div>
      ) : null}

      {/* Users Table */}
      <div className="rounded-2xl border border-gray-200 bg-white overflow-hidden">
        <table className="w-full">
          <thead className="bg-gray-50 border-b border-gray-200">
            <tr>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">
                Nome
              </th>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">
                Email
              </th>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">
                Perfil
              </th>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">
                Agência
              </th>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">
                Status
              </th>
              <th className="px-6 py-3 text-right text-xs font-medium text-gray-500 uppercase">
                Ações
              </th>
            </tr>
          </thead>
          <tbody className="divide-y divide-gray-200">
            {loading ? (
              <tr>
                <td colSpan={6} className="px-6 py-12 text-center text-sm text-gray-500">
                  Carregando...
                </td>
              </tr>
            ) : users.length === 0 ? (
              <tr>
                <td colSpan={6} className="px-6 py-12 text-center text-sm text-gray-500">
                  Nenhum usuário encontrado
                </td>
              </tr>
            ) : (
              users.map((user) => (
                <tr key={user.id} className="hover:bg-gray-50">
                  <td className="px-6 py-4 whitespace-nowrap">
                    <div className="flex items-center">
                      <div className="h-10 w-10 rounded-full bg-blue-100 flex items-center justify-center">
                        <UserIcon className="h-5 w-5 text-blue-600" />
                      </div>
                      <div className="ml-4">
                        <div className="text-sm font-medium text-gray-900">{user.full_name}</div>
                        {user.badge_number && (
                          <div className="text-xs text-gray-500">Crachá: {user.badge_number}</div>
                        )}
                      </div>
                    </div>
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                    {user.email}
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap">
                    <span className={`inline-flex rounded-full px-2 py-1 text-xs font-medium ${
                      user.role === 'intelligence' ? 'bg-purple-100 text-purple-800' :
                      user.role === 'field_agent' ? 'bg-green-100 text-green-800' :
                      user.role === 'supervisor' ? 'bg-blue-100 text-blue-800' :
                      'bg-gray-100 text-gray-800'
                    }`}>
                      {user.role === 'intelligence' ? 'Analista' :
                       user.role === 'field_agent' ? 'Agente' :
                       user.role === 'supervisor' ? 'Supervisor' : 'Admin'}
                    </span>
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                    {user.agency_name || user.agency_id}
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap">
                    <span className={`inline-flex rounded-full px-2 py-1 text-xs font-medium ${
                      user.is_active ? 'bg-green-100 text-green-800' : 'bg-red-100 text-red-800'
                    }`}>
                      {user.is_active ? 'Ativo' : 'Inativo'}
                    </span>
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap text-right text-sm font-medium">
                    <div className="flex items-center justify-end gap-2">
                      <button className="text-blue-600 hover:text-blue-900">
                        <Edit className="h-4 w-4" />
                      </button>
                      <button className="text-red-600 hover:text-red-900">
                        <Trash2 className="h-4 w-4" />
                      </button>
                    </div>
                  </td>
                </tr>
              ))
            )}
          </tbody>
        </table>
      </div>

      {/* Pagination */}
      {total > 50 && (
        <div className="mt-4 flex items-center justify-between">
          <div className="text-sm text-gray-500">
            Mostrando {((page - 1) * 50) + 1} a {Math.min(page * 50, total)} de {total} usuários
          </div>
          <div className="flex items-center gap-2">
            <button
              onClick={() => setPage(p => Math.max(1, p - 1))}
              disabled={page === 1}
              className="rounded-lg border border-gray-300 px-3 py-1 text-sm disabled:opacity-50"
            >
              Anterior
            </button>
            <span className="text-sm text-gray-500">Página {page}</span>
            <button
              onClick={() => setPage(p => p + 1)}
              disabled={page * 50 >= total}
              className="rounded-lg border border-gray-300 px-3 py-1 text-sm disabled:opacity-50"
            >
              Próxima
            </button>
          </div>
        </div>
      )}
    </ConsoleShell>
  );
}
