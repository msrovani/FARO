"use client";

import { ReactNode, useEffect, useState } from 'react';
import { X } from 'lucide-react';
import { Agency, UserRole } from '@/app/types';
import { userApi, dashboardApi } from '@/app/services/api';
import { useCurrentUser } from '@/app/hooks/use-current-user';
import { getAccessibleAgencies, getAllowedRoles, getRoleLabel, getAgencyTypeLabel } from '@/app/utils/agency-filter';

interface UserFormData {
  id?: string;
  email: string;
  full_name: string;
  cpf: string;
  badge_number: string;
  role: UserRole;
  agency_id: string;
  unit_id?: string;
  is_active: boolean;
  is_verified: boolean;
}

interface Props {
  isOpen: boolean;
  onClose: () => void;
  onSuccess: () => void;
  editUser?: UserFormData | null;
}

const defaultForm: UserFormData = {
  email: '',
  full_name: '',
  cpf: '',
  badge_number: '',
  role: 'field_agent',
  agency_id: '',
  is_active: true,
  is_verified: false,
};

export function UserFormModal({ isOpen, onClose, onSuccess, editUser }: Props) {
  const { user: currentUser } = useCurrentUser();
  const [loading, setLoading] = useState(false);
  const [saving, setSaving] = useState(false);
  const [agencies, setAgencies] = useState<Agency[]>([]);
  const [form, setForm] = useState<UserFormData>(defaultForm);
  const [errors, setErrors] = useState<Record<string, string>>({});

  useEffect(() => {
    if (!isOpen) {
      setForm(defaultForm);
      setErrors({});
      return;
    }
    loadAgencies();
  }, [isOpen]);

  useEffect(() => {
    if (editUser && isOpen) {
      setForm({
        id: editUser.id,
        email: editUser.email,
        full_name: editUser.full_name,
        cpf: editUser.cpf || '',
        badge_number: editUser.badge_number || '',
        role: editUser.role,
        agency_id: editUser.agency_id,
        unit_id: editUser.unit_id,
        is_active: editUser.is_active,
        is_verified: editUser.is_verified,
      });
    }
  }, [editUser, isOpen]);

  async function loadAgencies() {
    try {
      setLoading(true);
      const response = await dashboardApi.getAgencies();
      const filtered = getAccessibleAgencies(currentUser, response.agencies);
      setAgencies(filtered);
      
      if (!editUser && filtered.length > 0 && !form.agency_id) {
        const allowedRoles = getAllowedRoles(currentUser);
        setForm(prev => ({
          ...prev,
          agency_id: filtered[0].id,
          role: allowedRoles[0],
        }));
      }
    } catch (err) {
      console.error(err);
    } finally {
      setLoading(false);
    }
  }

  function validate(): boolean {
    const newErrors: Record<string, string> = {};

    if (!form.email.trim()) {
      newErrors.email = 'Email é obrigatório';
    } else if (!/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(form.email)) {
      newErrors.email = 'Email inválido';
    }

    if (!form.full_name.trim()) {
      newErrors.full_name = 'Nome completo é obrigatório';
    }

    if (form.cpf && !/^\d{11}$/.test(form.cpf.replace(/\D/g, ''))) {
      newErrors.cpf = 'CPF deve ter 11 dígitos';
    }

    if (!form.agency_id) {
      newErrors.agency_id = 'Agência é obrigatória';
    }

    if (!form.role) {
      newErrors.role = 'Perfil é obrigatório';
    }

    setErrors(newErrors);
    return Object.keys(newErrors).length === 0;
  }

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    if (!validate()) return;

    try {
      setSaving(true);
      const payload = {
        email: form.email.trim(),
        full_name: form.full_name.trim(),
        cpf: form.cpf.replace(/\D/g, '') || undefined,
        badge_number: form.badge_number || undefined,
        role: form.role,
        agency_id: form.agency_id,
        unit_id: form.unit_id || undefined,
        is_active: form.is_active,
        is_verified: form.is_verified,
      };

      if (editUser?.id) {
        await userApi.updateUser(editUser.id, payload);
      } else {
        await userApi.createUser(payload);
      }

      onSuccess();
      onClose();
    } catch (err) {
      console.error(err);
      setErrors({ submit: 'Falha ao salvar usuário' });
    } finally {
      setSaving(false);
    }
  }

  if (!isOpen) return null;

  const allowedRoles = getAllowedRoles(currentUser);

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-slate-900/60 backdrop-blur-sm p-4">
      <div className="w-full max-w-lg overflow-hidden rounded-3xl bg-white shadow-2xl ring-1 ring-slate-200">
        <div className="flex items-center justify-between bg-slate-900 px-6 py-4">
          <h3 className="text-lg font-bold text-white">
            {editUser ? 'Editar Usuário' : 'Novo Usuário'}
          </h3>
          <button
            onClick={onClose}
            className="rounded-lg p-1 text-slate-400 hover:bg-slate-800 hover:text-white"
          >
            <X size={20} />
          </button>
        </div>

        <form onSubmit={handleSubmit} className="max-h-[70vh] overflow-y-auto p-6">
          <div className="space-y-4">
            <Field
              label="Email *"
              error={errors.email}
            >
              <input
                type="email"
                value={form.email}
                onChange={e => setForm(prev => ({ ...prev, email: e.target.value }))}
                className="w-full rounded-2xl border border-slate-300 px-4 py-3 text-sm"
                placeholder="email@agencia.gov.br"
              />
            </Field>

            <Field
              label="Nome Completo *"
              error={errors.full_name}
            >
              <input
                type="text"
                value={form.full_name}
                onChange={e => setForm(prev => ({ ...prev, full_name: e.target.value }))}
                className="w-full rounded-2xl border border-slate-300 px-4 py-3 text-sm"
                placeholder="Nome completo"
              />
            </Field>

            <div className="grid gap-4 md:grid-cols-2">
              <Field label="CPF">
                <input
                  type="text"
                  value={form.cpf}
                  onChange={e => setForm(prev => ({ ...prev, cpf: e.target.value.replace(/\D/g, '').slice(0, 11) }))}
                  className="w-full rounded-2xl border border-slate-300 px-4 py-3 text-sm"
                  placeholder="Apenas dígitos"
                  maxLength={11}
                />
              </Field>

              <Field label="Crachá">
                <input
                  type="text"
                  value={form.badge_number}
                  onChange={e => setForm(prev => ({ ...prev, badge_number: e.target.value }))}
                  className="w-full rounded-2xl border border-slate-300 px-4 py-3 text-sm"
                  placeholder="Número do crachá"
                />
              </Field>
            </div>

            <Field
              label="Perfil *"
              error={errors.role}
            >
              <select
                value={form.role}
                onChange={e => setForm(prev => ({ ...prev, role: e.target.value as UserRole }))}
                className="w-full rounded-2xl border border-slate-300 px-4 py-3 text-sm"
              >
                {allowedRoles.map(role => (
                  <option key={role} value={role}>
                    {getRoleLabel(role)}
                  </option>
                ))}
              </select>
            </Field>

            <Field
              label="Agência *"
              error={errors.agency_id}
            >
              <select
                value={form.agency_id}
                onChange={e => setForm(prev => ({ ...prev, agency_id: e.target.value }))}
                className="w-full rounded-2xl border border-slate-300 px-4 py-3 text-sm"
                disabled={loading}
              >
                <option value="">Selecione...</option>
                {agencies.map(agency => (
                  <option key={agency.id} value={agency.id}>
                    {agency.name} ({getAgencyTypeLabel(agency.type)})
                  </option>
                ))}
              </select>
            </Field>

            <div className="flex gap-4">
              <label className="flex items-center gap-2 rounded-2xl border border-slate-200 bg-slate-50 px-4 py-3 text-sm">
                <input
                  type="checkbox"
                  checked={form.is_active}
                  onChange={e => setForm(prev => ({ ...prev, is_active: e.target.checked }))}
                  className="h-4 w-4 rounded border-slate-300"
                />
                Ativo
              </label>

              <label className="flex items-center gap-2 rounded-2xl border border-slate-200 bg-slate-50 px-4 py-3 text-sm">
                <input
                  type="checkbox"
                  checked={form.is_verified}
                  onChange={e => setForm(prev => ({ ...prev, is_verified: e.target.checked }))}
                  className="h-4 w-4 rounded border-slate-300"
                />
                Verificado
              </label>
            </div>
          </div>

          {errors.submit && (
            <div className="mt-4 rounded-xl border border-red-200 bg-red-50 px-4 py-3 text-sm text-red-700">
              {errors.submit}
            </div>
          )}

          <div className="mt-6 flex gap-3">
            <button
              type="button"
              onClick={onClose}
              className="flex-1 rounded-2xl border border-slate-200 bg-white py-3.5 text-sm font-bold text-slate-600 hover:bg-slate-50"
            >
              Cancelar
            </button>
            <button
              type="submit"
              disabled={saving}
              className="flex-1 rounded-2xl bg-slate-900 py-3.5 text-sm font-bold text-white disabled:cursor-not-allowed disabled:bg-slate-300"
            >
              {saving ? 'Salvando...' : editUser ? 'Atualizar' : 'Criar'}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
}

function Field({
  label,
  error,
  children,
}: {
  label: string;
  error?: string;
  children: ReactNode;
}) {
  return (
    <div>
      <label className="mb-2 block text-sm font-medium text-slate-700">{label}</label>
      {children}
      {error && <p className="mt-1 text-xs text-red-600">{error}</p>}
    </div>
  );
}