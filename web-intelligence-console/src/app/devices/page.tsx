"use client";

import { useEffect, useState } from "react";
import { ServerCrash, Smartphone, ShieldCheck, ShieldAlert, Cpu } from "lucide-react";
import { ConsoleShell } from "@/app/components/console-shell";
import { devicesApi } from "@/app/services/api";
import { Device } from "@/app/types";

export default function DevicesPage() {
  const [devices, setDevices] = useState<Device[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [isModalOpen, setIsModalOpen] = useState(false);
  const [selectedDeviceId, setSelectedDeviceId] = useState<string | null>(null);
  const [justification, setJustification] = useState("");
  const [isSubmitting, setIsSubmitting] = useState(false);

  const fetchDevices = async () => {
    try {
      const data = await devicesApi.listDevices();
      setDevices(data);
    } catch (err) {
      console.error("Erro ao carregar dispositivos", err);
    } finally {
      setIsLoading(false);
    }
  };

  useEffect(() => {
    fetchDevices();
  }, []);

  const handleOpenModal = (deviceId: string) => {
    setSelectedDeviceId(deviceId);
    setJustification("");
    setIsModalOpen(true);
  };

  const handleConfirmToggle = async () => {
    if (!selectedDeviceId || justification.trim().length < 10 || isSubmitting) return;
    
    try {
      setIsSubmitting(true);
      const updated = await devicesApi.suspendDevice(selectedDeviceId, justification);
      setDevices((prev) => prev.map((d) => (d.id === updated.id ? updated : d)));
      setIsModalOpen(false);
    } catch (error) {
      console.error(error);
      alert("Falha ao atualizar o acesso do dispositivo.");
    } finally {
      setIsSubmitting(false);
    }
  };

  return (
    <ConsoleShell activePath="/devices">
      <div className="flex h-full flex-col">
        <header className="border-b border-slate-200 bg-white px-6 py-5">
          <h1 className="text-xl font-semibold tracking-tight text-slate-900">Gerenciamento de Dispositivos (Mobiles)</h1>
          <p className="mt-1 text-sm text-slate-500">Supervisão de frota de borda, saúde do aplicativo e revogação de acessos autorizados.</p>
        </header>

        <div className="flex-1 overflow-auto bg-slate-50 p-6 object-center">
          {isLoading ? (
            <div className="flex h-32 items-center justify-center text-sm font-semibold text-slate-500">Carregando dispositivos autorizados...</div>
          ) : devices.length === 0 ? (
            <div className="rounded-xl border border-dashed border-slate-300 p-12 text-center text-slate-400">
              <ServerCrash className="mx-auto h-12 w-12 text-slate-300" />
              <p className="mt-4 font-medium uppercase tracking-widest text-slate-500">Nenhum dispositivo encontrado</p>
            </div>
          ) : (
            <div className="grid gap-6 md:grid-cols-2 lg:grid-cols-3">
              {devices.map((device) => (
                <div key={device.id} className="relative overflow-hidden rounded-2xl border border-slate-200 bg-white shadow-sm ring-1 ring-slate-200/50 transition-all hover:shadow-md">
                  <div className={`absolute top-0 left-0 w-full h-1 ${device.is_active ? 'bg-emerald-500' : 'bg-red-500'}`} />
                  <div className="p-5">
                    <div className="flex items-start justify-between">
                      <div className="flex items-center gap-3">
                        <div className={`rounded-xl p-2.5 ${device.is_active ? 'bg-emerald-50 text-emerald-600' : 'bg-red-50 text-red-600'}`}>
                           <Smartphone className="h-6 w-6" />
                        </div>
                        <div>
                          <p className="font-semibold text-slate-900 line-clamp-1" title={device.device_id}>
                            {device.device_model || 'Dispositivo N/D'}
                          </p>
                          <p className="text-xs uppercase tracking-wider text-slate-500">Edge ID: {device.device_id.substring(0, 8)}...</p>
                        </div>
                      </div>
                      
                      <button
                        onClick={() => handleOpenModal(device.id)}
                        className={`group relative flex h-8 items-center gap-1.5 overflow-hidden rounded-full border px-3 text-xs font-semibold uppercase tracking-wider transition-colors ${
                          device.is_active 
                            ? 'border-emerald-200 bg-emerald-50 text-emerald-700 hover:border-red-200 hover:bg-red-50 hover:text-red-700'
                            : 'border-red-200 bg-red-50 text-red-700 hover:border-emerald-200 hover:bg-emerald-50 hover:text-emerald-700'
                        }`}
                      >
                         {device.is_active ? (
                            <>
                              <ShieldCheck className="h-4 w-4 shrink-0 transition-transform group-hover:-translate-y-full" />
                              <ShieldAlert className="absolute left-[11px] h-4 w-4 shrink-0 translate-y-full transition-transform group-hover:translate-y-0" />
                              <span className="relative">Ativo</span>
                            </>
                         ) : (
                           <>
                             <ShieldAlert className="h-4 w-4 shrink-0 transition-transform group-hover:-translate-y-full" />
                             <ShieldCheck className="absolute left-[11px] h-4 w-4 shrink-0 translate-y-full transition-transform group-hover:translate-y-0" />
                             <span className="relative">Revogado</span>
                           </>
                         )}
                      </button>
                    </div>

                    <div className="mt-5 grid grid-cols-2 gap-4 rounded-xl bg-slate-50 p-4">
                      <div>
                        <p className="text-[10px] font-semibold uppercase tracking-widest text-slate-500">Versão O.S.</p>
                        <p className="mt-1 font-mono text-sm font-medium text-slate-900">{device.os_version || '?'}</p>
                      </div>
                      <div>
                        <p className="text-[10px] font-semibold uppercase tracking-widest text-slate-500">App FaroMobile</p>
                        <p className="mt-1 font-mono text-sm font-medium text-slate-900">{device.app_version || '?'}</p>
                      </div>
                      <div className="col-span-2">
                        <p className="text-[10px] font-semibold uppercase tracking-widest text-slate-500">Última Ref. Rede</p>
                        <p className="mt-1 flex items-center gap-2 text-sm font-medium text-slate-900">
                           <Cpu className="h-3 w-3" />
                           {new Date(device.last_seen).toLocaleString("pt-BR")}
                        </p>
                      </div>
                    </div>
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>

        {/* Audit Justification Modal Overlay */}
        {isModalOpen && (
          <div className="fixed inset-0 z-50 flex items-center justify-center bg-slate-900/60 backdrop-blur-sm p-4">
            <div className="w-full max-w-md overflow-hidden rounded-3xl bg-white shadow-2xl ring-1 ring-slate-200">
              <div className="bg-slate-900 px-6 py-5 text-white">
                <h3 className="text-lg font-bold">Justificativa de Auditoria</h3>
                <p className="text-xs uppercase tracking-widest text-slate-400">Controle de Ativos DINT/ARI</p>
              </div>
              <div className="p-6">
                <p className="text-sm text-slate-600 mb-4">
                  Para alterar o acesso deste dispositivo móvel, é obrigatório registrar a justificativa operacional fundamentada.
                </p>
                <textarea
                  autoFocus
                  value={justification}
                  onChange={(e) => setJustification(e.target.value)}
                  className="w-full min-h-[120px] rounded-2xl border border-slate-300 bg-slate-50 p-4 text-sm text-slate-900 focus:border-slate-900 focus:ring-0 transition-all font-medium"
                  placeholder="Ex: Oficial em licença, extravio relatado, fim da missão estratégica..."
                />
                <div className="mt-2 flex justify-between px-1">
                  <span className={`text-[10px] font-bold uppercase tracking-wider ${justification.trim().length >= 10 ? 'text-emerald-600' : 'text-slate-400'}`}>
                    Mínimo: 10 caracteres
                  </span>
                  <span className="text-[10px] font-bold text-slate-400 uppercase tracking-wider">
                    {justification.length} caracteres
                  </span>
                </div>
                
                <div className="mt-8 flex gap-3">
                  <button
                    onClick={() => setIsModalOpen(false)}
                    className="flex-1 rounded-2xl border border-slate-200 bg-white py-3.5 text-sm font-bold text-slate-600 hover:bg-slate-50 transition-colors"
                  >
                    Cancelar
                  </button>
                  <button
                    disabled={justification.trim().length < 10 || isSubmitting}
                    onClick={handleConfirmToggle}
                    className="flex-1 rounded-2xl bg-slate-900 py-3.5 text-sm font-bold text-white shadow-lg shadow-slate-900/20 disabled:cursor-not-allowed disabled:bg-slate-300 transition-all hover:bg-slate-800"
                  >
                    {isSubmitting ? 'Processando...' : 'Confirmar Alteração'}
                  </button>
                </div>
              </div>
            </div>
          </div>
        )}
      </div>
    </ConsoleShell>
  );
}
