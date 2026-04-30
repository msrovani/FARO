"use client";

import { useCallback, useEffect, useState } from "react";

import { ConsoleShell } from "@/app/components/console-shell";
import { intelligenceApi } from "@/app/services/api";
import { AuditLogEntry } from "@/app/types";

export default function AuditPage() {
  const [logs, setLogs] = useState<AuditLogEntry[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [actionFilter, setActionFilter] = useState("");

  const loadLogs = useCallback(async (action: string = actionFilter) => {
    try {
      setLoading(true);
      setError(null);
      const data = await intelligenceApi.listAuditLogs(
        action ? { action, page: 1, page_size: 50 } : { page: 1, page_size: 50 }
      );
      setLogs(data);
    } catch (err) {
      console.error(err);
      setError("Falha ao carregar a trilha de auditoria.");
    } finally {
      setLoading(false);
    }
  }, [actionFilter]);

  useEffect(() => {
    void loadLogs();
  }, [loadLogs]);

  return (
    <ConsoleShell
      title="Auditoria e Governanca"
      subtitle="Reconstrucao cronologica de decisoes, alteracoes e retornos sensiveis."
    >
      {error ? (
        <div className="mb-6 rounded-3xl border border-red-200 bg-red-50 px-5 py-4 text-sm text-red-700">
          {error}
        </div>
      ) : null}

      <div className="mb-6 flex flex-col gap-3 rounded-3xl border border-slate-200 bg-white p-4 shadow-sm lg:flex-row lg:items-end lg:justify-between">
        <div>
          <h2 className="text-lg font-semibold text-slate-900">Filtro de auditoria</h2>
          <p className="text-sm text-slate-500">Permite rastrear revisao, watchlist, casos e feedbacks.</p>
        </div>
        <form
          className="flex flex-col gap-3 sm:flex-row"
          onSubmit={(event) => {
            event.preventDefault();
            void loadLogs(actionFilter);
          }}
        >
          <input
            value={actionFilter}
            onChange={(event) => setActionFilter(event.target.value)}
            placeholder="Acao, ex.: analyst_review_created"
            className="rounded-2xl border border-slate-300 bg-white px-4 py-3 text-sm text-slate-900"
          />
          <button type="submit" className="rounded-2xl bg-slate-900 px-4 py-3 text-sm font-semibold text-white">
            Atualizar
          </button>
        </form>
      </div>

      <section className="rounded-3xl border border-slate-200 bg-white p-4 shadow-sm">
        <div className="mb-4">
          <h2 className="text-lg font-semibold text-slate-900">Eventos auditaveis</h2>
          <p className="text-sm text-slate-500">Ultimos 50 registros conforme os filtros aplicados.</p>
        </div>

        {loading ? (
          <EmptyState text="Carregando auditoria..." />
        ) : logs.length === 0 ? (
          <EmptyState text="Nenhum evento para os filtros atuais." />
        ) : (
          <div className="space-y-3">
            {logs.map((log) => (
              <article key={log.id} className="rounded-2xl border border-slate-200 bg-slate-50 p-4">
                <div className="flex flex-col gap-2 lg:flex-row lg:items-start lg:justify-between">
                  <div>
                    <div className="text-sm font-semibold text-slate-900">{log.action}</div>
                    <div className="text-xs uppercase tracking-[0.18em] text-slate-500">
                      {log.entity_type}
                    </div>
                  </div>
                  <div className="text-right text-xs text-slate-500">
                    <div>{new Date(log.created_at).toLocaleString("pt-BR")}</div>
                    <div>{log.actor_name || "ator nao identificado"}</div>
                  </div>
                </div>
                {log.justification ? (
                  <p className="mt-3 text-sm text-slate-600">{log.justification}</p>
                ) : null}
                {log.details ? (
                  <div className="mt-3 flex flex-wrap gap-2 text-xs text-slate-500">
                    {Object.entries(log.details).map(([key, value]) => (
                      <span key={key} className="rounded-full bg-white px-2 py-1">
                        {key}: {String(value)}
                      </span>
                    ))}
                  </div>
                ) : null}
              </article>
            ))}
          </div>
        )}
      </section>
    </ConsoleShell>
  );
}

function EmptyState({ text }: { text: string }) {
  return (
    <div className="rounded-2xl border border-dashed border-slate-200 bg-slate-50 px-6 py-10 text-center text-sm text-slate-500">
      {text}
    </div>
  );
}
