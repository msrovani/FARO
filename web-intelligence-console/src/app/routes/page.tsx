"use client";

import { useCallback, useEffect, useMemo, useState } from "react";

import { ConsoleShell } from "@/app/components/console-shell";
import { intelligenceApi } from "@/app/services/api";
import { AlgorithmResult } from "@/app/types";

export default function RoutesPage() {
  const [plateFilter, setPlateFilter] = useState("");
  const [routes, setRoutes] = useState<AlgorithmResult[]>([]);
  const [convoys, setConvoys] = useState<AlgorithmResult[]>([]);
  const [roaming, setRoaming] = useState<AlgorithmResult[]>([]);
  const [sensitive, setSensitive] = useState<AlgorithmResult[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const loadData = useCallback(async (plate?: string) => {
    try {
      setLoading(true);
      setError(null);
      const [routeData, convoyData, roamingData, sensitiveData] = await Promise.all([
        intelligenceApi.listRoutes(plate || undefined),
        intelligenceApi.listConvoys(plate || undefined),
        intelligenceApi.listRoaming(plate || undefined),
        intelligenceApi.listSensitiveAssets(plate ? { plate_number: plate } : undefined),
      ]);
      setRoutes(routeData);
      setConvoys(convoyData);
      setRoaming(roamingData);
      setSensitive(sensitiveData);
    } catch (err) {
      console.error(err);
      setError("Falha ao carregar os modulos geoespaciais e de recorrencia.");
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    void loadData();
  }, [loadData]);

  const summary = useMemo(
    () => ({
      routes: routes.length,
      convoys: convoys.length,
      roaming: roaming.length,
      sensitive: sensitive.length,
    }),
    [convoys.length, roaming.length, routes.length, sensitive.length]
  );

  return (
    <ConsoleShell
      title="Rotas, Recorrencia e Coocorrencia"
      subtitle="Consolida os eventos dos algoritmos espaciais para leitura tatico-analitica."
    >
      {error ? (
        <div className="mb-6 rounded-3xl border border-red-200 bg-red-50 px-5 py-4 text-sm text-red-700">
          {error}
        </div>
      ) : null}

      <div className="mb-6 flex flex-col gap-3 rounded-3xl border border-slate-200 bg-white p-4 shadow-sm lg:flex-row lg:items-end lg:justify-between">
        <div>
          <h2 className="text-lg font-semibold text-slate-900">Filtro operacional</h2>
          <p className="text-sm text-slate-500">Filtre por placa para reduzir ruído e consolidar leitura de padrao.</p>
        </div>
        <form
          className="flex flex-col gap-3 sm:flex-row"
          onSubmit={(event) => {
            event.preventDefault();
            void loadData(plateFilter);
          }}
        >
          <input
            value={plateFilter}
            onChange={(event) => setPlateFilter(event.target.value.toUpperCase())}
            placeholder="Placa"
            className="rounded-2xl border border-slate-300 bg-white px-4 py-3 text-sm text-slate-900"
          />
          <button type="submit" className="rounded-2xl bg-slate-900 px-4 py-3 text-sm font-semibold text-white">
            Atualizar
          </button>
        </form>
      </div>

      <section className="mb-6 grid gap-4 md:grid-cols-4">
        <SummaryCard label="Rotas anomalas" value={summary.routes} />
        <SummaryCard label="Comboios / coocorrencia" value={summary.convoys} tone="warning" />
        <SummaryCard label="Roaming / loitering" value={summary.roaming} tone="info" />
        <SummaryCard label="Ativo sensivel" value={summary.sensitive} tone="critical" />
      </section>

      {loading ? (
        <EmptyState text="Carregando eventos analiticos..." />
      ) : (
        <div className="grid gap-6 xl:grid-cols-2">
          <EventColumn title="Rota anomala" subtitle="Desvios relevantes entre regioes de interesse." items={routes} />
          <EventColumn title="Comboio / coocorrencia" subtitle="Placas que reaparecem juntas em janelas curtas." items={convoys} />
          <EventColumn title="Roaming / loitering" subtitle="Aproximacoes repetidas e circulacao pendular." items={roaming} />
          <EventColumn title="Ativo sensivel" subtitle="Recorrencia em zonas ou ativos protegidos." items={sensitive} />
        </div>
      )}
    </ConsoleShell>
  );
}

function EventColumn({
  title,
  subtitle,
  items,
}: {
  title: string;
  subtitle: string;
  items: AlgorithmResult[];
}) {
  return (
    <section className="rounded-3xl border border-slate-200 bg-white p-4 shadow-sm">
      <div className="mb-4">
        <h2 className="text-lg font-semibold text-slate-900">{title}</h2>
        <p className="text-sm text-slate-500">{subtitle}</p>
      </div>

      {items.length === 0 ? (
        <EmptyState text="Nenhum evento para os filtros atuais." />
      ) : (
        <div className="space-y-3">
          {items.slice(0, 12).map((item) => (
            <article key={item.id} className="rounded-2xl border border-slate-200 bg-slate-50 p-4">
              <div className="flex items-center justify-between gap-3">
                <div>
                  <div className="text-sm font-semibold text-slate-900">
                    {item.plate_number || "sem placa principal"}
                  </div>
                  <div className="text-xs uppercase tracking-[0.18em] text-slate-500">
                    {item.decision}
                  </div>
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

function SummaryCard({
  label,
  value,
  tone = "default",
}: {
  label: string;
  value: number;
  tone?: "default" | "critical" | "warning" | "info";
}) {
  const styles = {
    default: "border-slate-200 bg-white text-slate-900",
    critical: "border-red-200 bg-red-50 text-red-700",
    warning: "border-amber-200 bg-amber-50 text-amber-700",
    info: "border-sky-200 bg-sky-50 text-sky-700",
  } as const;

  return (
    <div className={`rounded-3xl border px-5 py-4 shadow-sm ${styles[tone]}`}>
      <div className="text-sm font-medium">{label}</div>
      <div className="mt-2 text-3xl font-semibold">{value}</div>
    </div>
  );
}

function EmptyState({ text }: { text: string }) {
  return (
    <div className="rounded-2xl border border-dashed border-slate-200 bg-slate-50 px-6 py-10 text-center text-sm text-slate-500">
      {text}
    </div>
  );
}
