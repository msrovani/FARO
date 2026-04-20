"use client";

import { useEffect, useState } from "react";
import { Search, UserPlus, Edit, Trash2, ToggleLeft, ToggleRight } from "lucide-react";

import { ConsoleShell } from "@/app/components/console-shell";
import { UserFormModal } from "@/app/components/user-form-modal";
import { userApi, dashboardApi } from "@/app/services/api";
import { Agency, UserRole } from "@/app/types";
import { useCurrentUser } from "@/app/hooks/use-current-user";
import { getAccessibleAgencies, getAllowedRoles } from "@/app/utils/agency-filter";

interface User {
  id: string;
  email: string;
  full_name: string;
  cpf?: string;
  badge_number?: string;
  role: UserRole;
  agency_id: string;
  agency_name?: string;
  unit_id?: string;
  unit_name?: string;
  is_active: boolean;
  is_verified: boolean;
  created_at: string;
}

export default function UsersPage() {
  const { user: currentUser } = useCurrentUser();
  const [users, setUsers] = useState<User[]>([]);
  const [agencies, setAgencies] = useState<Agency[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [selectedRole, setSelectedRole] = useState<string>("");
  const [selectedAgency, setSelectedAgency] = useState<string>("");
  const [searchTerm, setSearchTerm] = useState<string>("");
  const [page, setPage] = useState(1);
  const [total, setTotal] = useState(0);

  const [isModalOpen, setIsModalOpen] = useState(false);
  const [editingUser, setEditingUser] = useState<User | null>(null);

  useEffect(() => {
    loadPageData();
  }, [selectedRole, selectedAgency, page]);

  useEffect(() => {
    if (currentUser) {
      loadAgencies();
    }
  }, [currentUser]);

  async function loadPageData() {
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
      const filtered = getAccessibleAgencies(currentUser, response.agencies);
      setAgencies(filtered);
    } catch (err) {
      console.error(err);
    }
  }

  function handleNewUser() {
    setEditingUser(null);
    setIsModalOpen(true);
  }

  function handleEditUser(user: User) {
    setEditingUser(user);
    setIsModalOpen(true);
  }

  async function handleToggleUser(user: User) {
    try {
      await userApi.toggleUserActive(user.id);
      setUsers(current =>
        current.map(u =>
          u.id === user.id ? { ...u, is_active: !u.is_active } : u
        )
      );
    } catch (err) {
      console.error(err);
      setError("Falha ao alterar status do usuario.");
    }
  }

  async function handleDeleteUser(user: User) {
    if (!confirm(`Desativar usuario ${user.full_name}?`)) return;
    try {
      await userApi.deleteUser(user.id);
      setUsers(current => current.filter(u => u.id !== user.id));
    } catch (err) {
      console.error(err);
      setError("Falha ao desativar usuario.");
    }
  }

  function handleModalSuccess() {
    loadPageData();
  }

  const allowedRoles = getAllowedRoles(currentUser);
  const filteredAgencies = getAccessibleAgencies(currentUser, agencies);

  return (
    <ConsoleShell
      title="Gestao de Usuarios"
      subtitle="Cadastro e gerenciamento de analistas e agentes de campo por agencia."
    >
      <div className="mb-6 flex flex-wrap items-center gap-4 rounded-2xl border border-slate-200 bg-white px-4 py-3">
        <div className="flex items-center gap-2 flex-1 min-w-[200px]">
          <Search className="h-5 w-5 text-slate-500" />
          <input
            type="text"
            placeholder="Buscar por nome ou email..."
            value={searchTerm}
            onChange={e => setSearchTerm(e.target.value)}
            className="flex-1 rounded-lg border-0 bg-transparent text-sm focus:ring-0"
          />
        </div>

        <select
          value={selectedRole}
          onChange={e => setSelectedRole(e.target.value)}
          className="rounded-lg border border-slate-200 bg-white px-3 py-2 text-sm font-medium text-slate-700 focus:ring-2 focus:ring-blue-500"
        >
          <option value="">Todos os perfis</option>
          {allowedRoles.map(role => (
            <option key={role} value={role}>
              {role === 'intelligence' ? 'Analista de Inteligencia' :
               role === 'field_agent' ? 'Agente de Campo' :
               role === 'supervisor' ? 'Supervisor' : 'Administrador'}
            </option>
          ))}
        </select>

        <select
          value={selectedAgency}
          onChange={e => setSelectedAgency(e.target.value)}
          className="rounded-lg border border-slate-200 bg-white px-3 py-2 text-sm font-medium text-slate-700 focus:ring-2 focus:ring-blue-500"
        >
          <option value="">Todas as agencias</option>
          {filteredAgencies.map(agency => (
            <option key={agency.id} value={agency.id}>
              {agency.name} ({agency.type})
            </option>
          ))}
        </select>

        <button
          onClick={handleNewUser}
          className="flex items-center gap-2 rounded-lg bg-blue-600 px-4 py-2 text-sm font-medium text-white hover:bg-blue-700"
        >
          <UserPlus className="h-4 w-4" />
          Novo Usuario
        </button>
      </div>

      {error ? (
        <div className="mb-6 rounded-3xl border border-red-200 bg-red-50 px-5 py-4 text-sm text-red-700">
          {error}
        </div>
      ) : null}

      <div className="rounded-2xl border border-slate-200 bg-white overflow-hidden">
        <table className="w-full">
          <thead className="bg-slate-50 border-b border-slate-200">
            <tr>
              <th className="px-6 py-3 text-left text-xs font-medium text-slate-500 uppercase">
                Nome
              </th>
              <th className="px-6 py-3 text-left text-xs font-medium text-slate-500 uppercase">
                Email
              </th>
              <th className="px-6 py-3 text-left text-xs font-medium text-slate-500 uppercase">
                Perfil
              </th>
              <th className="px-6 py-3 text-left text-xs font-medium text-slate-500 uppercase">
                Agencia
              </th>
              <th className="px-6 py-3 text-left text-xs font-medium text-slate-500 uppercase">
                Status
              </th>
              <th className="px-6 py-3 text-right text-xs font-medium text-slate-500 uppercase">
                Acoes
              </th>
            </tr>
          </thead>
          <tbody className="divide-y divide-slate-200">
            {loading ? (
              <tr>
                <td colSpan={6} className="px-6 py-12 text-center text-sm text-slate-500">
                  Carregando...
                </td>
              </tr>
            ) : users.length === 0 ? (
              <tr>
                <td colSpan={6} className="px-6 py-12 text-center text-sm text-slate-500">
                  Nenhum usuario encontrado
                </td>
              </tr>
            ) : (
              users.map(user => (
                <tr key={user.id} className="hover:bg-slate-50">
                  <td className="px-6 py-4 whitespace-nowrap">
                    <div className="flex items-center">
                      <div className="h-10 w-10 rounded-full bg-blue-100 flex items-center justify-center">
                        <span className="text-sm font-semibold text-blue-600">
                          {user.full_name.charAt(0).toUpperCase()}
                        </span>
                      </div>
                      <div className="ml-4">
                        <div className="text-sm font-medium text-slate-900">{user.full_name}</div>
                        {user.badge_number && (
                          <div className="text-xs text-slate-500">Cracha: {user.badge_number}</div>
                        )}
                      </div>
                    </div>
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap text-sm text-slate-500">
                    {user.email}
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap">
                    <span className={`inline-flex rounded-full px-2 py-1 text-xs font-medium ${
                      user.role === 'intelligence' ? 'bg-purple-100 text-purple-800' :
                      user.role === 'field_agent' ? 'bg-green-100 text-green-800' :
                      user.role === 'supervisor' ? 'bg-blue-100 text-blue-800' :
                      'bg-slate-100 text-slate-800'
                    }`}>
                      {user.role === 'intelligence' ? 'Analista' :
                       user.role === 'field_agent' ? 'Agente' :
                       user.role === 'supervisor' ? 'Supervisor' : 'Admin'}
                    </span>
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap text-sm text-slate-500">
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
                      <button
                        onClick={() => handleToggleUser(user)}
                        className={`p-1 rounded ${
                          user.is_active ? 'text-amber-600 hover:text-amber-800' : 'text-green-600 hover:text-green-800'
                        }`}
                        title={user.is_active ? 'Desativar' : 'Ativar'}
                      >
                        {user.is_active ? <ToggleRight className="h-5 w-5" /> : <ToggleLeft className="h-5 w-5" />}
                      </button>
                      <button
                        onClick={() => handleEditUser(user)}
                        className="text-blue-600 hover:text-blue-900"
                        title="Editar"
                      >
                        <Edit className="h-4 w-4" />
                      </button>
                      <button
                        onClick={() => handleDeleteUser(user)}
                        className="text-red-600 hover:text-red-900"
                        title="Excluir"
                      >
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

      {total > 50 && (
        <div className="mt-4 flex items-center justify-between">
          <div className="text-sm text-slate-500">
            Mostrando {((page - 1) * 50) + 1} a {Math.min(page * 50, total)} de {total} usuarios
          </div>
          <div className="flex items-center gap-2">
            <button
              onClick={() => setPage(p => Math.max(1, p - 1))}
              disabled={page === 1}
              className="rounded-lg border border-slate-300 px-3 py-1 text-sm disabled:opacity-50"
            >
              Anterior
            </button>
            <span className="text-sm text-slate-500">Pagina {page}</span>
            <button
              onClick={() => setPage(p => p + 1)}
              disabled={page * 50 >= total}
              className="rounded-lg border border-slate-300 px-3 py-1 text-sm disabled:opacity-50"
            >
              Proxima
            </button>
          </div>
        </div>
      )}

      <UserFormModal
        isOpen={isModalOpen}
        onClose={() => {
          setIsModalOpen(false);
          setEditingUser(null);
        }}
        onSuccess={handleModalSuccess}
        editUser={editingUser}
      />
    </ConsoleShell>
  );
}