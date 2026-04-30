"use client";

import { AlgorithmResult } from "@/app/types";

export function AlgorithmEventList({
  title,
  subtitle,
  items,
  loading,
}: {
  title: string;
  subtitle: string;
  items: AlgorithmResult[];
  loading: boolean;
}) {
  return (
    <section className="rounded-3xl border border-slate-200 bg-white p-4 shadow-sm">
      <div className="mb-4">
        <h2 className="text-lg font-semibold text-slate-900">{title}</h2>
        <p className="text-sm text-slate-500">{subtitle}</p>
      </div>

      {loading ? (
        <EmptyState text="Carregando eventos..." />
      ) : items.length === 0 ? (
        <EmptyState text="Nenhum evento encontrado para os filtros aplicados." />
      ) : (
        <div className="space-y-3">
          {items.slice(0, 20).map((item) => (
            <article key={item.id} className="rounded-2xl border border-slate-200 bg-slate-50 p-4">
              <div className="flex items-center justify-between gap-3">
                <div>
                  <div className="text-sm font-semibold text-slate-900">
                    {item.plate_number || "placa nao informada"}
                  </div>
                  <div className="text-xs uppercase tracking-[0.18em] text-slate-500">{item.decision}</div>
                </div>
                <div className="rounded-full bg-slate-900 px-3 py-1 text-xs font-semibold text-white">
                  conf. {Math.round(item.confidence * 100)}%
                </div>
              </div>
              <p className="mt-3 text-sm text-slate-600">{item.explanation}</p>
              <div className="mt-3 flex flex-wrap gap-2 text-xs text-slate-500">
                {Object.entries(item.metrics || {}).map(([key, value]) => (
                  <span key={key} className="rounded-full bg-white px-2 py-1">
                    {key}: {String(value)}
                  </span>
                ))}
              </div>
            </article>
          ))}
        </div>
      )}
    </section>
  );
}

function EmptyState({ text }: { text: string }) {
  return (
    <div className="rounded-2xl border border-dashed border-slate-200 bg-slate-50 px-6 py-10 text-center text-sm text-slate-500">
      {text}
    </div>
  );
}
