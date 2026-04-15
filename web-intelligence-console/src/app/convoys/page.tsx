"use client";

import { useCallback, useEffect, useState } from "react";

import { AlgorithmEventList } from "@/app/components/algorithm-event-list";
import { ConsoleShell } from "@/app/components/console-shell";
import { intelligenceApi } from "@/app/services/api";
import { AlgorithmResult } from "@/app/types";

export default function ConvoysPage() {
  const [plateFilter, setPlateFilter] = useState("");
  const [items, setItems] = useState<AlgorithmResult[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const loadData = useCallback(async (plate?: string) => {
    try {
      setLoading(true);
      setError(null);
      const data = await intelligenceApi.listConvoys(plate || undefined);
      setItems(data);
    } catch (err) {
      console.error(err);
      setError("Falha ao carregar eventos de comboio/coocorrencia.");
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    void loadData();
  }, [loadData]);

  return (
    <ConsoleShell
      title="Modulo de Comboio / Coocorrencia"
      subtitle="Identifica placas que reaparecem juntas, com explicacao auditavel e leitura de forca do vinculo."
    >
      {error ? (
        <div className="mb-6 rounded-3xl border border-red-200 bg-red-50 px-5 py-4 text-sm text-red-700">
          {error}
        </div>
      ) : null}

      <div className="mb-6 flex flex-col gap-3 rounded-3xl border border-slate-200 bg-white p-4 shadow-sm lg:flex-row lg:items-end lg:justify-between">
        <div>
          <h2 className="text-lg font-semibold text-slate-900">Filtro operacional</h2>
          <p className="text-sm text-slate-500">Use placa principal ou correlata para focar a analise.</p>
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

      <AlgorithmEventList
        title="Eventos de comboio / coocorrencia"
        subtitle="Evidencia temporal de deslocamento conjunto e repeticao de pareamento."
        items={items}
        loading={loading}
      />
    </ConsoleShell>
  );
}
