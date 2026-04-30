"use client";

import { useCallback, useEffect, useState } from "react";

import { AlgorithmEventList } from "@/app/components/algorithm-event-list";
import { ConsoleShell } from "@/app/components/console-shell";
import { intelligenceApi } from "@/app/services/api";
import { AlgorithmResult } from "@/app/types";

export default function SensitiveAssetsPage() {
  const [plateFilter, setPlateFilter] = useState("");
  const [zoneFilter, setZoneFilter] = useState("");
  const [items, setItems] = useState<AlgorithmResult[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const loadData = useCallback(async (plate?: string, zone?: string) => {
    try {
      setLoading(true);
      setError(null);
      const data = await intelligenceApi.listSensitiveAssets({
        plate_number: plate || undefined,
        zone_id: zone || undefined,
      });
      setItems(data);
    } catch (err) {
      console.error(err);
      setError("Falha ao carregar eventos de recorrencia em ativo sensivel.");
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    void loadData();
  }, [loadData]);

  return (
    <ConsoleShell
      title="Modulo de Ativo Sensivel"
      subtitle="Foco em protecao do ativo: recorrencia por zona, reaparicao e monitoramento recomendado."
    >
      {error ? (
        <div className="mb-6 rounded-3xl border border-red-200 bg-red-50 px-5 py-4 text-sm text-red-700">
          {error}
        </div>
      ) : null}

      <div className="mb-6 flex flex-col gap-3 rounded-3xl border border-slate-200 bg-white p-4 shadow-sm">
        <div>
          <h2 className="text-lg font-semibold text-slate-900">Filtro operacional</h2>
          <p className="text-sm text-slate-500">Filtre por placa e zona para priorizar risco em perimetros protegidos.</p>
        </div>
        <form
          className="grid gap-3 sm:grid-cols-3"
          onSubmit={(event) => {
            event.preventDefault();
            void loadData(plateFilter, zoneFilter);
          }}
        >
          <input
            value={plateFilter}
            onChange={(event) => setPlateFilter(event.target.value.toUpperCase())}
            placeholder="Placa"
            className="rounded-2xl border border-slate-300 bg-white px-4 py-3 text-sm text-slate-900"
          />
          <input
            value={zoneFilter}
            onChange={(event) => setZoneFilter(event.target.value)}
            placeholder="Zone ID (UUID)"
            className="rounded-2xl border border-slate-300 bg-white px-4 py-3 text-sm text-slate-900"
          />
          <button type="submit" className="rounded-2xl bg-slate-900 px-4 py-3 text-sm font-semibold text-white">
            Atualizar
          </button>
        </form>
      </div>

      <AlgorithmEventList
        title="Recorrencia em ativo sensivel"
        subtitle="Eventos com decisao, confianca e explicacao para priorizacao da inteligencia."
        items={items}
        loading={loading}
      />
    </ConsoleShell>
  );
}
