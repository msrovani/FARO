"use client";

import { FormEvent, useCallback, useEffect, useState } from "react";

import { ConsoleShell } from "@/app/components/console-shell";
import { intelligenceApi } from "@/app/services/api";
import { AnalystFeedbackTemplate, FeedbackRecipient, IntelligenceCase } from "@/app/types";
import { DragDropContext, Droppable, Draggable, DropResult } from "@hello-pangea/dnd";
import { LayoutGrid, ClipboardList, TrendingUp, CheckCircle2, ChevronRight, MessageSquareCode } from "lucide-react";

const statusOptions: IntelligenceCase["status"][] = ["open", "monitoring", "escalated", "closed"];

export default function CasesPage() {
  const [cases, setCases] = useState<IntelligenceCase[]>([]);
  const [selectedCaseId, setSelectedCaseId] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [statusFilter, setStatusFilter] = useState<IntelligenceCase["status"] | "all">("all");
  const [search, setSearch] = useState("");

  const [title, setTitle] = useState("");
  const [hypothesis, setHypothesis] = useState("");
  const [summary, setSummary] = useState("");
  const [status, setStatus] = useState<IntelligenceCase["status"]>("open");
  const [sensitivityLevel, setSensitivityLevel] = useState("reserved");
  const [reviewDueAt, setReviewDueAt] = useState("");
  const [priority, setPriority] = useState(50);
  const [submitting, setSubmitting] = useState(false);
  const [feedbackTemplates, setFeedbackTemplates] = useState<AnalystFeedbackTemplate[]>([]);
  const [recipientOptions, setRecipientOptions] = useState<FeedbackRecipient[]>([]);
  const [recipientQuery, setRecipientQuery] = useState("");
  const [recipientLoading, setRecipientLoading] = useState(false);
  const [feedbackTemplateId, setFeedbackTemplateId] = useState("");
  const [feedbackTargetUserId, setFeedbackTargetUserId] = useState("");
  const [feedbackTargetTeam, setFeedbackTargetTeam] = useState("");
  const [feedbackType, setFeedbackType] = useState("recommendation");
  const [feedbackSensitivity, setFeedbackSensitivity] = useState("operational");
  const [feedbackTitle, setFeedbackTitle] = useState("Retorno operacional de caso analitico");
  const [feedbackMessage, setFeedbackMessage] = useState("");
  const [sendingFeedback, setSendingFeedback] = useState(false);

  const loadCases = useCallback(async (params?: {
    status?: IntelligenceCase["status"] | "all";
    search?: string;
  }) => {
    const statusValue = params?.status ?? statusFilter;
    const searchValue = params?.search ?? "";
    try {
      setLoading(true);
      setError(null);
      const data = await intelligenceApi.listCases({
        status: statusValue === "all" ? undefined : statusValue,
        search: searchValue || undefined,
        page: 1,
        page_size: 50,
      });
      setCases(data);
    } catch (err) {
      console.error(err);
      setError("Falha ao carregar os casos analiticos.");
    } finally {
      setLoading(false);
    }
  }, [statusFilter]);

  const loadFeedbackTemplates = useCallback(async () => {
    try {
      const data = await intelligenceApi.listFeedbackTemplates(true);
      setFeedbackTemplates(data);
    } catch (err) {
      console.error(err);
      setError("Casos carregados, mas templates de feedback nao puderam ser consultados.");
    }
  }, []);

  useEffect(() => {
    void loadCases({ status: statusFilter, search: "" });
    void loadFeedbackTemplates();
  }, [loadCases, loadFeedbackTemplates, statusFilter]);

  async function searchRecipients() {
    if (recipientQuery.trim().length < 2) {
      setRecipientOptions([]);
      return;
    }
    try {
      setRecipientLoading(true);
      const data = await intelligenceApi.listFeedbackRecipients({ query: recipientQuery.trim(), limit: 20 });
      setRecipientOptions(data);
    } catch (err) {
      console.error(err);
      setError("Falha ao buscar destinatarios para feedback.");
    } finally {
      setRecipientLoading(false);
    }
  }

  function applyTemplate(templateId: string) {
    setFeedbackTemplateId(templateId);
    const template = feedbackTemplates.find((item) => item.id === templateId);
    if (!template) return;
    setFeedbackType(template.feedback_type);
    setFeedbackSensitivity(template.sensitivity_level);
    setFeedbackTitle(template.name);
    setFeedbackMessage(template.body_template);
  }

  function applyRecipient(value: string) {
    if (!value) {
      setFeedbackTargetUserId("");
      setFeedbackTargetTeam("");
      return;
    }
    const recipient = recipientOptions.find((item) => {
      if (item.recipient_type === "user") return item.user_id === value;
      return item.target_team_label === value;
    });
    if (!recipient) return;
    if (recipient.recipient_type === "user") {
      setFeedbackTargetUserId(recipient.user_id || "");
      setFeedbackTargetTeam(recipient.target_team_label || "");
      return;
    }
    setFeedbackTargetUserId("");
    setFeedbackTargetTeam(recipient.target_team_label || "");
  }

  async function sendCaseFeedback(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    if (!selectedCaseId || (!feedbackTargetUserId && !feedbackTargetTeam) || !feedbackTitle.trim() || sendingFeedback) {
      return;
    }
    try {
      setSendingFeedback(true);
      setError(null);
      await intelligenceApi.createFeedback({
        target_user_id: feedbackTargetUserId || undefined,
        target_team_label: feedbackTargetTeam || undefined,
        feedback_type: feedbackType,
        sensitivity_level: feedbackSensitivity,
        title: feedbackTitle.trim(),
        message: feedbackMessage.trim() || undefined,
        template_id: feedbackTemplateId || undefined,
      });
      setFeedbackTemplateId("");
      setFeedbackTargetUserId("");
      setFeedbackTargetTeam("");
      setRecipientQuery("");
      setRecipientOptions([]);
      setFeedbackType("recommendation");
      setFeedbackSensitivity("operational");
      setFeedbackTitle("Retorno operacional de caso analitico");
      setFeedbackMessage("");
    } catch (err) {
      console.error(err);
      setError("Falha ao enviar feedback do caso.");
    } finally {
      setSendingFeedback(false);
    }
  }

  async function submitCase(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    if (title.trim().length < 5 || submitting) return;

    try {
      setSubmitting(true);
      setError(null);
      const created = await intelligenceApi.createCase({
        title,
        hypothesis: hypothesis || undefined,
        summary: summary || undefined,
        status,
        sensitivity_level: sensitivityLevel,
        priority,
        review_due_at: reviewDueAt || undefined,
      });
      setCases((current) => [created, ...current]);
      setSelectedCaseId(created.id);
      setTitle("");
      setHypothesis("");
      setSummary("");
      setStatus("open");
      setSensitivityLevel("reserved");
      setReviewDueAt("");
      setPriority(50);
    } catch (err) {
      console.error(err);
      setError("Falha ao criar o caso analitico.");
    } finally {
      setSubmitting(false);
    }
  }

  function selectCase(caseItem: IntelligenceCase) {
    setSelectedCaseId(caseItem.id);
    setTitle(caseItem.title);
    setHypothesis(caseItem.hypothesis || "");
    setSummary(caseItem.summary || "");
    setStatus(caseItem.status);
    setSensitivityLevel(caseItem.sensitivity_level);
    setReviewDueAt(caseItem.review_due_at ? caseItem.review_due_at.slice(0, 16) : "");
    setPriority(caseItem.priority);
  }

  async function updateSelectedCase() {
    if (!selectedCaseId || title.trim().length < 5 || submitting) return;

    try {
      setSubmitting(true);
      setError(null);
      const updated = await intelligenceApi.updateCase(selectedCaseId, {
        title,
        hypothesis: hypothesis || undefined,
        summary: summary || undefined,
        status,
        sensitivity_level: sensitivityLevel,
        priority,
        review_due_at: reviewDueAt || undefined,
      });
      setCases((current) => current.map((item) => (item.id === selectedCaseId ? updated : item)));
    } catch (err) {
      console.error(err);
      setError("Falha ao atualizar o caso analitico.");
    } finally {
      setSubmitting(false);
    }
  }

  const onDragEnd = async (result: DropResult) => {
    const { destination, source, draggableId } = result;

    if (!destination) return;
    if (destination.droppableId === source.droppableId && destination.index === source.index) return;

    const newStatus = destination.droppableId as IntelligenceCase["status"];
    const draggedCase = cases.find((c) => c.id === draggableId);

    if (!draggedCase || draggedCase.status === newStatus) return;

    // Optimistic update
    const updatedCases = cases.map((c) => 
      c.id === draggableId ? { ...c, status: newStatus } : c
    );
    setCases(updatedCases);

    try {
      await intelligenceApi.updateCase(draggableId, { status: newStatus });
    } catch (err) {
      console.error("Failed to update case status via D&D", err);
      setError("Falha ao mover o caso. Sincronização interrompida.");
      // Rollback
      loadCases();
    }
  };

  const columns: { id: IntelligenceCase["status"]; label: string; icon: any; color: string }[] = [
    { id: "open", label: "Abertos", icon: ClipboardList, color: "text-sky-600 bg-sky-50 border-sky-200" },
    { id: "monitoring", label: "Monitoramento", icon: TrendingUp, color: "text-amber-600 bg-amber-50 border-amber-200" },
    { id: "escalated", label: "Escalonado", icon: MessageSquareCode, color: "text-red-600 bg-red-50 border-red-200" },
    { id: "closed", label: "Fechados", icon: CheckCircle2, color: "text-slate-600 bg-slate-50 border-slate-200" },
  ];

  return (
    <ConsoleShell
      title="Casos e Dossies"
      subtitle="Agrupa registros, hipoteses e acompanhamento para nao perder inteligencia em itens isolados."
    >
      {error ? (
        <div className="mb-6 rounded-3xl border border-red-200 bg-red-50 px-5 py-4 text-sm text-red-700">
          {error}
        </div>
      ) : null}

      <div className="grid gap-6 xl:grid-cols-[1fr_1.1fr]">
        <section className="rounded-3xl border border-slate-200 bg-white p-5 shadow-sm">
          <div className="mb-5">
            <h2 className="text-lg font-semibold text-slate-950">Novo caso</h2>
            <p className="mt-1 text-sm text-slate-500">
              Use para agrupar registros relacionados, consolidar hipotese e manter acompanhamento.
            </p>
          </div>

          <form className="space-y-4" onSubmit={submitCase}>
            <Field label="Titulo do caso">
              <input
                value={title}
                onChange={(event) => setTitle(event.target.value)}
                className="w-full rounded-2xl border border-slate-300 px-4 py-3 text-sm text-slate-900"
                placeholder="Ex.: Veiculo prata recorrente em corredor industrial"
              />
            </Field>
            <Field label="Hipotese analitica">
              <textarea
                value={hypothesis}
                onChange={(event) => setHypothesis(event.target.value)}
                className="min-h-24 w-full rounded-2xl border border-slate-300 px-4 py-3 text-sm text-slate-900"
                placeholder="Descreva a linha analitica central do caso."
              />
            </Field>
            <Field label="Sintese operacional">
              <textarea
                value={summary}
                onChange={(event) => setSummary(event.target.value)}
                className="min-h-24 w-full rounded-2xl border border-slate-300 px-4 py-3 text-sm text-slate-900"
                placeholder="Resumo curto para leitura rapida da mesa e da supervisao."
              />
            </Field>
            <div className="grid gap-4 md:grid-cols-2">
              <Field label="Status inicial">
                <select
                  value={status}
                  onChange={(event) => setStatus(event.target.value as IntelligenceCase["status"])}
                  className="w-full rounded-2xl border border-slate-300 px-4 py-3 text-sm text-slate-900"
                >
                  {statusOptions.map((option) => (
                    <option key={option} value={option}>
                      {humanize(option)}
                    </option>
                  ))}
                </select>
              </Field>
              <Field label="Prioridade">
                <input
                  type="number"
                  min={1}
                  max={100}
                  value={priority}
                  onChange={(event) => setPriority(Number(event.target.value))}
                  className="w-full rounded-2xl border border-slate-300 px-4 py-3 text-sm text-slate-900"
                />
              </Field>
            </div>
            <div className="grid gap-4 md:grid-cols-2">
              <Field label="Sensibilidade">
                <input
                  value={sensitivityLevel}
                  onChange={(event) => setSensitivityLevel(event.target.value)}
                  className="w-full rounded-2xl border border-slate-300 px-4 py-3 text-sm text-slate-900"
                />
              </Field>
              <Field label="Revisao obrigatoria">
                <input
                  type="datetime-local"
                  value={reviewDueAt}
                  onChange={(event) => setReviewDueAt(event.target.value)}
                  className="w-full rounded-2xl border border-slate-300 px-4 py-3 text-sm text-slate-900"
                />
              </Field>
            </div>
            <button
              type="submit"
              disabled={title.trim().length < 5 || submitting}
              className="w-full rounded-2xl bg-slate-900 px-4 py-3 text-sm font-semibold text-white disabled:cursor-not-allowed disabled:bg-slate-300"
            >
              {submitting ? "Processando caso..." : "Criar caso analitico"}
            </button>
            <button
              type="button"
              onClick={() => void updateSelectedCase()}
              disabled={!selectedCaseId || title.trim().length < 5 || submitting}
              className="w-full rounded-2xl border border-slate-300 bg-white px-4 py-3 text-sm font-semibold text-slate-900 disabled:cursor-not-allowed disabled:border-slate-200 disabled:text-slate-400"
            >
              {selectedCaseId ? "Atualizar caso selecionado" : "Selecione um caso para editar"}
            </button>
          </form>

          <form className="mt-6 space-y-4 rounded-2xl border border-slate-200 bg-slate-50 p-4" onSubmit={sendCaseFeedback}>
            <h3 className="text-sm font-semibold uppercase tracking-[0.2em] text-slate-600">Feedback de caso para campo</h3>
            <Field label="Template">
              <select
                value={feedbackTemplateId}
                onChange={(event) => applyTemplate(event.target.value)}
                className="w-full rounded-2xl border border-slate-300 px-4 py-3 text-sm text-slate-900"
              >
                <option value="">Sem template</option>
                {feedbackTemplates.map((template) => (
                  <option key={template.id} value={template.id}>
                    {template.name} - {template.feedback_type}
                  </option>
                ))}
              </select>
            </Field>
            <div className="grid gap-4 md:grid-cols-[1fr_auto]">
              <Field label="Buscar destinatario">
                <input
                  value={recipientQuery}
                  onChange={(event) => setRecipientQuery(event.target.value)}
                  className="w-full rounded-2xl border border-slate-300 px-4 py-3 text-sm text-slate-900"
                  placeholder="Nome, matricula, email, unidade ou codigo"
                />
              </Field>
              <button
                type="button"
                onClick={() => void searchRecipients()}
                disabled={recipientLoading || recipientQuery.trim().length < 2}
                className="mt-7 rounded-2xl border border-slate-300 bg-white px-4 py-3 text-sm font-semibold text-slate-900 disabled:cursor-not-allowed disabled:border-slate-200 disabled:text-slate-400"
              >
                {recipientLoading ? "Buscando..." : "Buscar"}
              </button>
            </div>
            <Field label="Destinatario sugerido">
              <select
                value={feedbackTargetUserId || feedbackTargetTeam}
                onChange={(event) => applyRecipient(event.target.value)}
                className="w-full rounded-2xl border border-slate-300 px-4 py-3 text-sm text-slate-900"
              >
                <option value="">Sem selecao</option>
                {recipientOptions.map((recipient) => (
                  <option
                    key={`${recipient.recipient_type}-${recipient.user_id || recipient.target_team_label}`}
                    value={recipient.recipient_type === "user" ? recipient.user_id : recipient.target_team_label}
                  >
                    {recipient.label}
                  </option>
                ))}
              </select>
            </Field>
            <div className="grid gap-4 md:grid-cols-3">
              <Field label="Tipo">
                <input
                  value={feedbackType}
                  onChange={(event) => setFeedbackType(event.target.value)}
                  className="w-full rounded-2xl border border-slate-300 px-4 py-3 text-sm text-slate-900"
                />
              </Field>
              <Field label="Sensibilidade">
                <input
                  value={feedbackSensitivity}
                  onChange={(event) => setFeedbackSensitivity(event.target.value)}
                  className="w-full rounded-2xl border border-slate-300 px-4 py-3 text-sm text-slate-900"
                />
              </Field>
              <Field label="Titulo">
                <input
                  value={feedbackTitle}
                  onChange={(event) => setFeedbackTitle(event.target.value)}
                  className="w-full rounded-2xl border border-slate-300 px-4 py-3 text-sm text-slate-900"
                />
              </Field>
            </div>
            <Field label="Mensagem">
              <textarea
                value={feedbackMessage}
                onChange={(event) => setFeedbackMessage(event.target.value)}
                className="min-h-24 w-full rounded-2xl border border-slate-300 px-4 py-3 text-sm text-slate-900"
              />
            </Field>
            <button
              type="submit"
              disabled={!selectedCaseId || (!feedbackTargetUserId && !feedbackTargetTeam) || !feedbackTitle.trim() || sendingFeedback}
              className="w-full rounded-2xl bg-slate-900 px-4 py-3 text-sm font-semibold text-white disabled:cursor-not-allowed disabled:bg-slate-300"
            >
              {sendingFeedback ? "Enviando..." : "Enviar feedback deste caso"}
            </button>
          </form>
        </section>

        <section className="rounded-3xl border border-slate-200 bg-white p-5 shadow-sm overflow-hidden flex flex-col">
          <div className="mb-5 flex flex-col gap-3 lg:flex-row lg:items-end lg:justify-between">
            <div>
              <h2 className="text-lg font-semibold text-slate-950">Mural de Investigação (Kanban)</h2>
              <p className="mt-1 text-sm text-slate-500">Mova os dossiês entre status para controle de fluxo ARI/DINT.</p>
            </div>
            <div className="flex gap-2">
               <button
                type="button"
                onClick={() => void loadCases({ status: statusFilter, search })}
                className="rounded-xl border border-slate-200 p-2 text-slate-600 hover:bg-slate-50"
              >
                <LayoutGrid size={20} />
              </button>
            </div>
          </div>

          <DragDropContext onDragEnd={onDragEnd}>
            <div className="flex-1 overflow-x-auto pb-4">
              <div className="flex gap-4 h-full min-w-[800px]">
                {columns.map((col) => (
                  <Droppable key={col.id} droppableId={col.id}>
                    {(provided, snapshot) => (
                      <div
                        className={`flex flex-col w-1/4 min-w-[200px] rounded-2xl border transition-colors ${
                          snapshot.isDraggingOver ? "bg-slate-50 border-slate-300" : "bg-transparent border-transparent"
                        }`}
                        {...provided.droppableProps}
                        ref={provided.innerRef}
                      >
                        <div className={`p-4 mb-2 rounded-t-2xl border-b flex items-center gap-2 ${col.color}`}>
                          <col.icon size={18} />
                          <h3 className="font-bold text-sm uppercase tracking-wider">{col.label}</h3>
                          <span className="ml-auto bg-white/50 px-2 rounded text-xs font-mono">
                            {cases.filter(c => c.status === col.id).length}
                          </span>
                        </div>
                        
                        <div className="flex-1 space-y-3 p-2 overflow-y-auto max-h-[700px]">
                          {cases
                            .filter((c) => c.status === col.id)
                            .map((caseItem, index) => (
                              <Draggable key={caseItem.id} draggableId={caseItem.id} index={index}>
                                {(provided, snapshot) => (
                                  <article
                                    ref={provided.innerRef}
                                    {...provided.draggableProps}
                                    {...provided.dragHandleProps}
                                    onClick={() => selectCase(caseItem)}
                                    className={`rounded-2xl border p-4 shadow-sm transition-all cursor-pointer ${
                                      snapshot.isDragging ? "shadow-xl ring-2 ring-slate-900 border-none scale-105 z-50" : 
                                      selectedCaseId === caseItem.id ? "border-amber-300 bg-amber-50" : "border-slate-200 bg-white hover:border-slate-400"
                                    }`}
                                  >
                                    <div className="flex justify-between items-start mb-2">
                                      <h4 className="font-bold text-sm text-slate-900 line-clamp-2">{caseItem.title}</h4>
                                      <ChevronRight size={14} className="text-slate-300" />
                                    </div>
                                    <p className="text-xs text-slate-500 line-clamp-2 mb-3">{caseItem.summary || caseItem.hypothesis || "Sem descrição"}</p>
                                    
                                    <div className="flex items-center justify-between">
                                      <div className="flex gap-1">
                                        <div className={`h-2 w-2 rounded-full ${caseItem.priority > 70 ? 'bg-red-500' : caseItem.priority > 30 ? 'bg-amber-500' : 'bg-emerald-500'}`} />
                                      </div>
                                      <span className="text-[10px] font-mono text-slate-400">#{caseItem.id.substring(0, 4)}</span>
                                    </div>
                                  </article>
                                )}
                              </Draggable>
                            ))}
                          {provided.placeholder}
                        </div>
                      </div>
                    )}
                  </Droppable>
                ))}
              </div>
            </div>
          </DragDropContext>
        </section>
      </div>
    </ConsoleShell>
  );
}

function Field({
  label,
  children,
}: {
  label: string;
  children: React.ReactNode;
}) {
  return (
    <label>
      <div className="mb-2 text-sm font-medium text-slate-700">{label}</div>
      {children}
    </label>
  );
}

function StatusBadge({ status }: { status: IntelligenceCase["status"] }) {
  const tone =
    status === "open"
      ? "bg-sky-100 text-sky-700"
      : status === "monitoring"
        ? "bg-amber-100 text-amber-700"
        : status === "escalated"
          ? "bg-red-100 text-red-700"
          : "bg-slate-200 text-slate-700";

  return <span className={`rounded-full px-2 py-1 text-[11px] font-semibold uppercase tracking-[0.2em] ${tone}`}>{humanize(status)}</span>;
}

function MiniTag({ text }: { text: string }) {
  return <span className="inline-flex items-center rounded-full bg-white px-2 py-1">{text}</span>;
}

function EmptyState({ text }: { text: string }) {
  return (
    <div className="rounded-2xl border border-dashed border-slate-200 bg-slate-50 px-5 py-10 text-center text-sm text-slate-500">
      {text}
    </div>
  );
}

function humanize(value: string) {
  return value.replaceAll("_", " ");
}
