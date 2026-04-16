"use client";

import { FormEvent, ReactNode, Suspense, useCallback, useEffect, useMemo, useState, useTransition, useRef } from "react";
import { useSearchParams } from "next/navigation";
import { Clock3, MapPinned, ShieldAlert, Waypoints, Navigation2, Car, PaintBucket, Smartphone, WifiRouter, ShieldClose, TriangleAlert, ShieldCheck } from "lucide-react";
import { Marker } from "react-map-gl";
import MapBase from "@/app/components/map/MapBase";

import { ConsoleShell } from "@/app/components/console-shell";
import { intelligenceApi } from "@/app/services/api";
import {
  AnalystConclusion,
  AnalystDecision,
  AnalystFeedbackTemplate,
  AnalystReviewStatus,
  IntelligenceCase,
  IntelligenceQueueItem,
  ObservationDetail,
} from "@/app/types";

const statusOptions: Array<{ value: AnalystReviewStatus; label: string }> = [
  { value: "final", label: "Finalizar analise" },
  { value: "draft", label: "Salvar rascunho" },
  { value: "supervisor_review", label: "Encaminhar supervisor" },
];

const conclusionOptions: Array<{ value: AnalystConclusion; label: string }> = [
  { value: "improcedente", label: "Improcedente" },
  { value: "fraca", label: "Fraca" },
  { value: "moderada", label: "Moderada" },
  { value: "relevante", label: "Relevante" },
  { value: "critica", label: "Critica" },
];

const decisionOptions: Array<{ value: AnalystDecision; label: string }> = [
  { value: "in_analysis", label: "Manter em analise" },
  { value: "discarded", label: "Descartar" },
  { value: "confirmed_monitoring", label: "Confirmar monitoramento" },
  { value: "confirmed_approach", label: "Recomendar abordagem" },
  { value: "linked_to_case", label: "Vincular a caso" },
  { value: "escalated", label: "Escalonar" },
];

export default function QueuePage() {
  return (
    <Suspense fallback={<QueueFallback />}>
      <QueueContent />
    </Suspense>
  );
}

function QueueContent() {
  const searchParams = useSearchParams();
  const highlightedId = searchParams.get("highlight");

  const [items, setItems] = useState<IntelligenceQueueItem[]>([]);
  const [selectedId, setSelectedId] = useState<string | null>(highlightedId);
  const [selectedObservation, setSelectedObservation] = useState<ObservationDetail | null>(null);
  const [cases, setCases] = useState<IntelligenceCase[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [plateFilter, setPlateFilter] = useState("");
  const [status, setStatus] = useState<AnalystReviewStatus>("final");
  const [conclusion, setConclusion] = useState<AnalystConclusion>("relevante");
  const [decision, setDecision] = useState<AnalystDecision>("confirmed_monitoring");
  const [recommendation, setRecommendation] = useState("Manter monitoramento silencioso e retornar ao campo quando houver nova coincidencia.");
  const [feedbackTemplates, setFeedbackTemplates] = useState<AnalystFeedbackTemplate[]>([]);
  const [linkedCaseId, setLinkedCaseId] = useState("");
  const [reviewDueAt, setReviewDueAt] = useState("");
  const [sensitivityLevel, setSensitivityLevel] = useState("reserved");
  const [selectedTemplateId, setSelectedTemplateId] = useState("");
  const [feedbackTitle, setFeedbackTitle] = useState("Retorno qualificado da inteligencia");
  const [feedbackType, setFeedbackType] = useState("recommendation");
  const [feedbackSensitivity, setFeedbackSensitivity] = useState("operational");
  const [justification, setJustification] = useState("");
  const [feedbackMessage, setFeedbackMessage] = useState("");
  const [submitting, setSubmitting] = useState(false);
  const [isPending, startTransition] = useTransition();
  const mapRef = useRef<any>(null);

  useEffect(() => {
    function handleKeyDown(e: KeyboardEvent) {
      if (document.activeElement?.tagName === "TEXTAREA" || document.activeElement?.tagName === "INPUT") {
        return;
      }
      
      if (e.key === "ArrowDown") {
        e.preventDefault();
        const idx = items.findIndex((i) => i.observation_id === selectedId);
        if (idx >= 0 && idx < items.length - 1) {
          setSelectedId(items[idx + 1].observation_id);
        }
      } else if (e.key === "ArrowUp") {
        e.preventDefault();
        const idx = items.findIndex((i) => i.observation_id === selectedId);
        if (idx > 0) {
          setSelectedId(items[idx - 1].observation_id);
        }
      } else if (e.key === "Enter" && e.shiftKey) {
        e.preventDefault();
        const form = document.getElementById('review-form') as HTMLFormElement;
        if (form) form.requestSubmit();
      }
    }
    
    window.addEventListener("keydown", handleKeyDown);
    return () => window.removeEventListener("keydown", handleKeyDown);
  }, [items, selectedId]);

  useEffect(() => {
    if (highlightedId) {
      setSelectedId(highlightedId);
    }
  }, [highlightedId]);

  useEffect(() => {
    if (!selectedId) {
      setSelectedObservation(null);
      return;
    }

    startTransition(() => {
      void intelligenceApi
        .getObservationDetail(selectedId)
        .then((data) => {
          setSelectedObservation(data);
          if (mapRef.current) {
            mapRef.current.flyTo({
              center: [data.location.longitude, data.location.latitude],
              duration: 1200,
              zoom: 16
            });
          }
        })
        .catch((err) => {
          console.error(err);
          setError("Falha ao abrir o detalhe da observacao.");
        });
    });
  }, [selectedId]);

  const loadQueue = useCallback(async (options?: { plate?: string; preferredId?: string | null }) => {
    const plate = options?.plate ?? "";
    const preferredId = options?.preferredId ?? highlightedId;
    try {
      setLoading(true);
      setError(null);
      const data = await intelligenceApi.getQueue(
        plate ? { plate_number: plate } : undefined,
        { page: 1, page_size: 50 }
      );
      setItems(data);

      if (data.length === 0) {
        setSelectedId(null);
        setSelectedObservation(null);
        return;
      }

      if (!preferredId || !data.some((item) => item.observation_id === preferredId)) {
        setSelectedId(data[0].observation_id);
      }
    } catch (err) {
      console.error(err);
      setError("Nao foi possivel carregar a fila analitica.");
    } finally {
      setLoading(false);
    }
  }, [highlightedId]);

  const loadFeedbackTemplates = useCallback(async () => {
    try {
      const data = await intelligenceApi.listFeedbackTemplates(true);
      setFeedbackTemplates(data);
    } catch (err) {
      console.error(err);
      setError("A fila carregou, mas os templates de feedback nao puderam ser consultados.");
    }
  }, []);

  const loadCases = useCallback(async () => {
    try {
      const data = await intelligenceApi.listCases({ page: 1, page_size: 100 });
      setCases(data);
    } catch (err) {
      console.error(err);
      setError("A fila carregou, mas os casos analiticos nao puderam ser consultados.");
    }
  }, []);

  useEffect(() => {
    void loadQueue({ plate: plateFilter, preferredId: highlightedId });
    void loadFeedbackTemplates();
    void loadCases();
  }, [highlightedId, loadCases, loadFeedbackTemplates, loadQueue, plateFilter]);

  function applyFeedbackTemplate(templateId: string) {
    setSelectedTemplateId(templateId);
    const template = feedbackTemplates.find((item) => item.id === templateId);
    if (!template) {
      return;
    }
    setFeedbackType(template.feedback_type);
    setFeedbackSensitivity(template.sensitivity_level);
    setFeedbackTitle(template.name);
    setFeedbackMessage(template.body_template);
  }

  async function submitReview(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    if (!selectedId || justification.trim().length < 10 || submitting) return;

    try {
      setSubmitting(true);
      setError(null);
      await intelligenceApi.createReview({
        observation_id: selectedId,
        status,
        conclusion,
        decision,
        source_quality: selectedObservation?.plate_reads[0] ? "supported" : "partial",
        data_reliability: selectedObservation?.instant_feedback?.has_alert ? "high" : "medium",
        reinforcing_factors: {
          score_label: selectedObservation?.suspicion_score?.final_label,
          active_algorithms: selectedObservation?.algorithm_results.map((item) => item.algorithm_type),
        },
        weakening_factors: {
          false_positive_risks: selectedObservation?.algorithm_results.map((item) => item.false_positive_risk),
        },
        recommendation,
        justification,
        linked_case_id: linkedCaseId || undefined,
        review_due_at: reviewDueAt || undefined,
        sensitivity_level: sensitivityLevel,
      });

      if (feedbackMessage.trim().length > 0) {
        await intelligenceApi.createFeedback({
          observation_id: selectedId,
          feedback_type: feedbackType,
          sensitivity_level: feedbackSensitivity,
          title: feedbackTitle,
          message: feedbackMessage,
          template_id: selectedTemplateId || undefined,
        });
      }

      setJustification("");
      setLinkedCaseId("");
      setReviewDueAt("");
      setSensitivityLevel("reserved");
      setSelectedTemplateId("");
      setFeedbackTitle("Retorno qualificado da inteligencia");
      setFeedbackType("recommendation");
      setFeedbackSensitivity("operational");
      setFeedbackMessage("");
      await loadQueue({ plate: plateFilter, preferredId: selectedId });
      if (selectedId) {
        const refreshed = await intelligenceApi.getObservationDetail(selectedId);
        setSelectedObservation(refreshed);
      }
    } catch (err) {
      console.error(err);
      setError("Falha ao concluir a revisao. Revise os campos estruturados e tente novamente.");
    } finally {
      setSubmitting(false);
    }
  }

  const summary = useMemo(() => {
    const approach = items.filter((item) => item.urgency === "approach").length;
    const intelligence = items.filter((item) => item.urgency === "intelligence").length;
    const monitor = items.filter((item) => item.urgency === "monitor").length;
    const scored = items.filter((item) => (item.score_value ?? 0) >= 60).length;
    return { approach, intelligence, monitor, scored };
  }, [items]);

  return (
    <ConsoleShell
      title="Fila Analitica de Suspeicoes"
      subtitle="Triagem, leitura de contexto, score composto e avaliacao estruturada do analista."
    >
      {error ? (
        <div className="mb-6 rounded-3xl border border-red-200 bg-red-50 px-5 py-4 text-sm text-red-700">
          {error}
        </div>
      ) : null}

      <section className="mb-6 grid gap-4 md:grid-cols-4">
        <SummaryCard label="Itens na mesa" value={items.length} />
        <SummaryCard label="Score elevado" value={summary.scored} tone="critical" />
        <SummaryCard label="Abordagem recomendada" value={summary.approach} tone="warning" />
        <SummaryCard label="Monitoramento" value={summary.monitor} tone="info" />
      </section>

      <div className="grid gap-6 xl:grid-cols-[1.05fr_1fr]">
        <section className="rounded-3xl border border-slate-200 bg-white p-4 shadow-sm">
          <div className="mb-4 flex flex-col gap-3 lg:flex-row lg:items-end lg:justify-between">
            <div>
              <h2 className="text-lg font-semibold text-slate-900">Entrada de informes</h2>
              <p className="text-sm text-slate-500">Prioridade por urgencia do campo e score composto.</p>
            </div>
            <form
              className="flex flex-col gap-3 sm:flex-row"
              onSubmit={(event) => {
                event.preventDefault();
                void loadQueue({ plate: plateFilter, preferredId: selectedId });
              }}
            >
              <input
                value={plateFilter}
                onChange={(event) => setPlateFilter(event.target.value.toUpperCase())}
                placeholder="Filtrar placa"
                className="rounded-2xl border border-slate-300 bg-white px-4 py-3 text-sm text-slate-900"
              />
              <button
                type="submit"
                className="rounded-2xl bg-slate-900 px-4 py-3 text-sm font-semibold text-white"
              >
                Atualizar fila
              </button>
            </form>
          </div>

          {loading ? (
            <EmptyState text="Carregando fila..." />
          ) : items.length === 0 ? (
            <EmptyState text="Nenhum informe pendente para os filtros atuais." />
          ) : (
            <div className="space-y-3">
              {items.map((item) => {
                const selected = item.observation_id === selectedId;
                return (
                  <button
                    key={item.observation_id}
                    type="button"
                    onClick={() => setSelectedId(item.observation_id)}
                    className={`w-full rounded-2xl border p-4 text-left transition ${
                      selected
                        ? "border-amber-400 bg-amber-50 shadow-sm"
                        : "border-slate-200 bg-white hover:border-slate-300 hover:bg-slate-50"
                    }`}
                  >
                    <div className="flex items-start justify-between gap-4">
                      <div>
                        <div className="flex items-center gap-2">
                          <span className="text-lg font-semibold tracking-widest text-slate-900">
                            {item.plate_number}
                          </span>
                          <UrgencyBadge urgency={item.urgency} />
                        </div>
                        <p className="mt-1 text-sm text-slate-600">{labelReason(item.suspicion_reason)}</p>
                      </div>
                      <div className="text-right text-xs text-slate-500">
                        <div>{new Date(item.observed_at).toLocaleString("pt-BR")}</div>
                        <div>{item.agent_name}</div>
                      </div>
                    </div>
                    <div className="mt-3 flex flex-wrap gap-2 text-xs text-slate-600">
                      <Badge icon={<ShieldAlert className="h-3.5 w-3.5" />} label={`Nivel ${item.suspicion_level}`} />
                      <Badge icon={<Clock3 className="h-3.5 w-3.5" />} label={`${item.previous_observations_count} passagens`} />
                      <Badge icon={<MapPinned className="h-3.5 w-3.5" />} label={item.unit_name || "Unidade nao informada"} />
                      {item.score_value ? (
                        <Badge icon={<Waypoints className="h-3.5 w-3.5" />} label={`Score ${Math.round(item.score_value)} / ${item.score_label}`} />
                      ) : null}
                    </div>
                  </button>
                );
              })}
            </div>
          )}
        </section>

        <section className="rounded-3xl border border-slate-200 bg-white p-4 shadow-sm">
          <div className="mb-4">
            <h2 className="text-lg font-semibold text-slate-900">Ficha analitica do registro</h2>
            <p className="text-sm text-slate-500">Contexto operacional, algoritmos e decisao formal.</p>
          </div>

          {!selectedId ? (
            <EmptyState text="Selecione um item da fila para revisar." />
          ) : isPending || !selectedObservation ? (
            <EmptyState text="Carregando detalhe..." />
          ) : (
            <>
              <div className="rounded-2xl bg-slate-950 p-5 text-white">
                <div className="flex items-center justify-between gap-4">
                  <div>
                    <div className="text-xs uppercase tracking-[0.3em] text-slate-400">placa confirmada</div>
                    <div className="mt-1 text-3xl font-semibold tracking-[0.3em]">
                      {selectedObservation.plate_number}
                    </div>
                  </div>
                  <div className="text-right text-sm text-slate-300">
                    <div>{selectedObservation.agent_name}</div>
                    <div>{new Date(selectedObservation.observed_at_local).toLocaleString("pt-BR")}</div>
                  </div>
                </div>
                <div className="mt-4 grid gap-3 text-sm sm:grid-cols-2">
                  <InfoRow label="Latitude" value={selectedObservation.location.latitude.toFixed(6)} />
                  <InfoRow label="Longitude" value={selectedObservation.location.longitude.toFixed(6)} />
                  <InfoRow label="Precisao GPS" value={`${selectedObservation.location.accuracy ?? 0} m`} />
                  <InfoRow
                    label="OCR"
                    value={
                      selectedObservation.plate_reads[0]
                        ? `${selectedObservation.plate_reads[0].ocr_raw_text} (${Math.round(
                            selectedObservation.plate_reads[0].ocr_confidence * 100
                          )}%)`
                        : "Sem OCR vinculado"
                    }
                  />
                </div>
              </div>

              {/* SECTION: Kinematic Map */}
              <div className="mt-4 overflow-hidden rounded-2xl border border-slate-200">
                <div className="h-48 w-full bg-slate-100 relative">
                  <MapBase
                    mapRef={mapRef}
                    initialView={{
                      latitude: selectedObservation.location.latitude,
                      longitude: selectedObservation.location.longitude,
                      zoom: 16,
                    }}
                  >
                    <Marker
                      latitude={selectedObservation.location.latitude}
                      longitude={selectedObservation.location.longitude}
                    >
                      <div
                        className="flex h-8 w-8 items-center justify-center rounded-full bg-slate-900 text-white shadow-xl ring-4 ring-white/50"
                        style={{
                          transform: `rotate(${selectedObservation.heading ?? 0}deg)`,
                          transition: "transform 0.3s ease-out",
                        }}
                      >
                        <Navigation2 className="h-5 w-5 fill-white" />
                      </div>
                    </Marker>
                  </MapBase>
                </div>
                <div className="grid grid-cols-2 divide-x divide-slate-100 bg-white sm:grid-cols-4">
                  <div className="flex items-center gap-2 p-3">
                    <Navigation2 className="hidden h-4 w-4 text-slate-400 sm:block" />
                    <div>
                      <div className="text-[10px] font-semibold uppercase tracking-wider text-slate-500">Rumo Direcional</div>
                      <div className="text-sm font-medium text-slate-900">{selectedObservation.heading ? `${selectedObservation.heading}°` : "N/D"}</div>
                    </div>
                  </div>
                  <div className="flex items-center gap-2 p-3">
                    <Waypoints className="hidden h-4 w-4 text-slate-400 sm:block" />
                    <div>
                      <div className="text-[10px] font-semibold uppercase tracking-wider text-slate-500">Velocidade (Est.)</div>
                      <div className="text-sm font-medium text-slate-900">{selectedObservation.speed ? `${selectedObservation.speed} km/h` : "N/D"}</div>
                    </div>
                  </div>
                  <div className="flex items-center gap-2 p-3">
                    <Car className="hidden h-4 w-4 text-slate-400 sm:block" />
                    <div>
                      <div className="text-[10px] font-semibold uppercase tracking-wider text-slate-500">Tipo / Marca</div>
                      <div className="text-sm font-medium text-slate-900">{selectedObservation.vehicle_type || selectedObservation.vehicle_model || "--"}</div>
                    </div>
                  </div>
                  <div className="flex items-center gap-2 p-3">
                    <PaintBucket className="hidden h-4 w-4 text-slate-400 sm:block" />
                    <div>
                      <div className="text-[10px] font-semibold uppercase tracking-wider text-slate-500">Cor Identificada</div>
                      <div className="text-sm font-medium text-slate-900">{selectedObservation.vehicle_color || "--"}</div>
                    </div>
                  </div>
                </div>
              </div>

              {/* SECTION: Diagnostic Health */}
              {(selectedObservation.metadata_snapshot || selectedObservation.sync_status === "failed") && (
                <div className="mt-4 flex flex-wrap items-center gap-4 rounded-xl border border-dashed border-slate-200 bg-slate-50/50 p-3 text-xs text-slate-500">
                  <div className="flex items-center gap-1.5 flex-1 min-w-[200px]">
                    <Smartphone className="h-4 w-4" />
                    Versão App: <span className="font-medium text-slate-900">{(selectedObservation.metadata_snapshot as any)?.app_version || "N/A"}</span>
                  </div>
                  <div className="flex items-center gap-1.5 flex-1 min-w-[200px]">
                    <WifiRouter className="h-4 w-4" />
                    Rede: <span className="font-medium text-slate-900">{(selectedObservation.metadata_snapshot as any)?.network_type || "N/A"}</span>
                  </div>
                  <div className="flex items-center gap-1.5 flex-1 min-w-[200px]">
                    <Clock3 className="h-4 w-4" />
                    Sync: <span className={`font-medium ${selectedObservation.sync_status === 'failed' ? 'text-red-600' : 'text-emerald-600'}`}>{selectedObservation.sync_status}</span>
                  </div>
                </div>
              )}

              {/* SECTION: Intel Debrief (Approach Confirmation) */}
              {selectedObservation.suspicion_report && (
                <div className="mt-6 rounded-2xl border-l-4 border-l-slate-900 bg-slate-50 p-5 shadow-sm">
                  <div className="flex items-start justify-between gap-4">
                    <div>
                      <h3 className="text-sm font-bold uppercase tracking-wider text-slate-900 flex items-center gap-2">
                        <ShieldAlert className="h-4 w-4 text-slate-900" />
                        Intel Debrief (Retorno de Campo)
                      </h3>
                      <p className="mt-1 text-sm text-slate-600">
                        {selectedObservation.suspicion_report.reason} • Urgência: {selectedObservation.suspicion_report.urgency}
                      </p>
                    </div>
                    {selectedObservation.suspicion_report.abordado !== undefined && (
                      <div className={`px-3 py-1 text-xs font-bold uppercase tracking-wider rounded-full ${selectedObservation.suspicion_report.abordado ? 'bg-emerald-100 text-emerald-800' : 'bg-red-100 text-red-800'}`}>
                        {selectedObservation.suspicion_report.abordado ? 'Abordado' : 'Não Abordado'}
                      </div>
                    )}
                  </div>
                  
                  {selectedObservation.suspicion_report.abordado && (
                    <div className="mt-5 grid gap-4 sm:grid-cols-[1fr_2fr]">
                      <div>
                         <div className="text-xs font-semibold text-slate-500 uppercase tracking-widest mb-2">Termômetro Tático</div>
                         <div className="flex items-center gap-3">
                           <div className="text-3xl font-black text-slate-900">{selectedObservation.suspicion_report.nivel_abordagem ?? '?'}</div>
                           <div className="text-xs space-y-1 text-slate-500 font-medium">
                              <div>/ 100 de Perigo</div>
                              {selectedObservation.suspicion_report.ocorrencia_registrada ? (
                                <div className="text-amber-600 font-bold flex items-center gap-1"><TriangleAlert className="h-3 w-3" /> Gerou Ocorrência</div>
                              ) : (
                                <div className="text-slate-400 font-bold flex items-center gap-1"><ShieldCheck className="h-3 w-3" /> Nada Consta</div>
                              )}
                           </div>
                         </div>
                      </div>
                      <div className="bg-white border border-slate-200 rounded-xl p-3 text-sm text-slate-700 italic">
                        "{selectedObservation.suspicion_report.notes || selectedObservation.suspicion_report.texto_ocorrencia || "Sem relato descritivo do agente."}"
                      </div>
                    </div>
                  )}
                </div>
              )}

              {selectedObservation.suspicion_score ? (
                <div className="mt-4 rounded-2xl border border-slate-200 bg-slate-50 p-4">
                  <div className="flex items-center justify-between gap-4">
                    <div>
                      <div className="text-xs uppercase tracking-[0.25em] text-slate-500">score composto</div>
                      <div className="mt-1 text-2xl font-semibold text-slate-900">
                        {Math.round(selectedObservation.suspicion_score.final_score)} / 100
                      </div>
                    </div>
                    <div className="rounded-full bg-slate-900 px-3 py-2 text-xs font-semibold uppercase tracking-[0.2em] text-white">
                      {selectedObservation.suspicion_score.final_label}
                    </div>
                  </div>
                  <p className="mt-3 text-sm text-slate-600">{selectedObservation.suspicion_score.explanation}</p>
                </div>
              ) : null}

              <div className="mt-4 grid gap-3">
                {selectedObservation.algorithm_results.slice(0, 4).map((result) => (
                  <div key={result.id} className="rounded-2xl border border-slate-200 bg-white p-3">
                    <div className="flex items-center justify-between gap-3">
                      <div className="text-sm font-semibold text-slate-900">{formatAlgorithm(result.algorithm_type)}</div>
                      <span className="rounded-full bg-slate-100 px-2 py-1 text-xs font-medium text-slate-700">
                        {result.decision}
                      </span>
                    </div>
                    <p className="mt-2 text-sm text-slate-600">{result.explanation}</p>
                  </div>
                ))}
              </div>

              <form id="review-form" className="mt-4 space-y-4" onSubmit={submitReview}>
                <div className="grid gap-3 md:grid-cols-3">
                  <SelectField label="Status" value={status} onChange={setStatus} options={statusOptions} />
                  <SelectField label="Conclusao" value={conclusion} onChange={setConclusion} options={conclusionOptions} />
                  <SelectField label="Decisao" value={decision} onChange={setDecision} options={decisionOptions} />
                </div>
                <div className="grid gap-3 md:grid-cols-3">
                  <div>
                    <label className="mb-2 block text-sm font-medium text-slate-700">Caso vinculado</label>
                    <select
                      value={linkedCaseId}
                      onChange={(event) => setLinkedCaseId(event.target.value)}
                      className="w-full rounded-2xl border border-slate-300 px-4 py-3 text-sm text-slate-900"
                    >
                      <option value="">Sem vinculo</option>
                      {cases.map((caseItem) => (
                        <option key={caseItem.id} value={caseItem.id}>
                          {caseItem.title}
                        </option>
                      ))}
                    </select>
                  </div>
                  <div>
                    <label className="mb-2 block text-sm font-medium text-slate-700">Prazo de revisao</label>
                    <input
                      type="datetime-local"
                      value={reviewDueAt}
                      onChange={(event) => setReviewDueAt(event.target.value)}
                      className="w-full rounded-2xl border border-slate-300 px-4 py-3 text-sm text-slate-900"
                    />
                  </div>
                  <div>
                    <label className="mb-2 block text-sm font-medium text-slate-700">Sensibilidade</label>
                    <input
                      value={sensitivityLevel}
                      onChange={(event) => setSensitivityLevel(event.target.value)}
                      className="w-full rounded-2xl border border-slate-300 px-4 py-3 text-sm text-slate-900"
                    />
                  </div>
                </div>
                <div>
                  <label className="mb-2 block text-sm font-medium text-slate-700">Recomendacao operacional</label>
                  <input
                    value={recommendation}
                    onChange={(event) => setRecommendation(event.target.value)}
                    className="w-full rounded-2xl border border-slate-300 px-4 py-3 text-sm text-slate-900"
                  />
                </div>
                <div>
                  <label className="mb-2 block text-sm font-medium text-slate-700">Fundamentacao analitica</label>
                  <textarea
                    value={justification}
                    onChange={(event) => setJustification(event.target.value)}
                    className="min-h-32 w-full rounded-2xl border border-slate-300 px-4 py-3 text-sm text-slate-900"
                    placeholder="Explique fatores de reforco, fatores de enfraquecimento, conclusao e destino do item."
                  />
                </div>
                <div>
                  <label className="mb-2 block text-sm font-medium text-slate-700">Template de feedback</label>
                  <select
                    value={selectedTemplateId}
                    onChange={(event) => applyFeedbackTemplate(event.target.value)}
                    className="w-full rounded-2xl border border-slate-300 px-4 py-3 text-sm text-slate-900"
                  >
                    <option value="">Sem template</option>
                    {feedbackTemplates.map((template) => (
                      <option key={template.id} value={template.id}>
                        {template.name} - {template.feedback_type}
                      </option>
                    ))}
                  </select>
                </div>
                <div className="grid gap-3 md:grid-cols-3">
                  <div>
                    <label className="mb-2 block text-sm font-medium text-slate-700">Tipo de feedback</label>
                    <input
                      value={feedbackType}
                      onChange={(event) => setFeedbackType(event.target.value)}
                      className="w-full rounded-2xl border border-slate-300 px-4 py-3 text-sm text-slate-900"
                    />
                  </div>
                  <div>
                    <label className="mb-2 block text-sm font-medium text-slate-700">Sensibilidade</label>
                    <input
                      value={feedbackSensitivity}
                      onChange={(event) => setFeedbackSensitivity(event.target.value)}
                      className="w-full rounded-2xl border border-slate-300 px-4 py-3 text-sm text-slate-900"
                    />
                  </div>
                  <div>
                    <label className="mb-2 block text-sm font-medium text-slate-700">Titulo do retorno</label>
                    <input
                      value={feedbackTitle}
                      onChange={(event) => setFeedbackTitle(event.target.value)}
                      className="w-full rounded-2xl border border-slate-300 px-4 py-3 text-sm text-slate-900"
                    />
                  </div>
                </div>
                <div>
                  <label className="mb-2 block text-sm font-medium text-slate-700">Feedback ao campo</label>
                  <textarea
                    value={feedbackMessage}
                    onChange={(event) => setFeedbackMessage(event.target.value)}
                    className="min-h-24 w-full rounded-2xl border border-slate-300 px-4 py-3 text-sm text-slate-900"
                    placeholder="Opcional. Use quando houver retorno claro, proporcional e operacional."
                  />
                </div>
                <button
                  type="submit"
                  disabled={justification.trim().length < 10 || submitting}
                  className="w-full rounded-2xl bg-slate-900 px-4 py-3 text-sm font-semibold text-white disabled:cursor-not-allowed disabled:bg-slate-300"
                >
                  {submitting ? "Registrando analise..." : "Registrar analise estruturada"}
                </button>
              </form>
            </>
          )}
        </section>
      </div>
    </ConsoleShell>
  );
}

function QueueFallback() {
  return (
    <ConsoleShell
      title="Fila Analitica de Suspeicoes"
      subtitle="Triagem, leitura de contexto, score composto e avaliacao estruturada do analista."
    >
      <EmptyState text="Preparando a mesa analitica..." />
    </ConsoleShell>
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

function SelectField<T extends string>({
  label,
  value,
  onChange,
  options,
}: {
  label: string;
  value: T;
  onChange: (value: T) => void;
  options: Array<{ value: T; label: string }>;
}) {
  return (
    <div>
      <label className="mb-2 block text-sm font-medium text-slate-700">{label}</label>
      <select
        value={value}
        onChange={(event) => onChange(event.target.value as T)}
        className="w-full rounded-2xl border border-slate-300 px-4 py-3 text-sm text-slate-900"
      >
        {options.map((option) => (
          <option key={option.value} value={option.value}>
            {option.label}
          </option>
        ))}
      </select>
    </div>
  );
}

function labelReason(reason: IntelligenceQueueItem["suspicion_reason"]) {
  return reason.replaceAll("_", " ");
}

function formatAlgorithm(value: string) {
  return value.replaceAll("_", " ");
}

function UrgencyBadge({ urgency }: { urgency: IntelligenceQueueItem["urgency"] }) {
  const tone =
    urgency === "approach"
      ? "bg-red-100 text-red-700"
      : urgency === "intelligence"
        ? "bg-amber-100 text-amber-700"
        : "bg-sky-100 text-sky-700";

  return <span className={`rounded-full px-2 py-1 text-xs font-semibold ${tone}`}>{urgency}</span>;
}

function Badge({ icon, label }: { icon: ReactNode; label: string }) {
  return (
    <span className="inline-flex items-center gap-1 rounded-full bg-slate-100 px-2 py-1">
      {icon}
      {label}
    </span>
  );
}

function InfoRow({ label, value }: { label: string; value: string }) {
  return (
    <div className="rounded-2xl bg-white/10 px-3 py-2">
      <div className="text-xs uppercase tracking-[0.2em] text-slate-400">{label}</div>
      <div className="mt-1 font-medium text-white">{value}</div>
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
