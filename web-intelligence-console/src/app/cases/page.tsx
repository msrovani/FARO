"use client";

import { FormEvent, useCallback, useEffect, useState } from "react";

import { ConsoleShell } from "@/app/components/console-shell";
import { intelligenceApi } from "@/app/services/api";
import { AnalystFeedbackTemplate, FeedbackRecipient, IntelligenceCase } from "@/app/types";

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

        <section className="rounded-3xl border border-slate-200 bg-white p-5 shadow-sm">
          <div className="mb-5 flex flex-col gap-3 lg:flex-row lg:items-end lg:justify-between">
            <div>
              <h2 className="text-lg font-semibold text-slate-950">Dossies ativos</h2>
              <p className="mt-1 text-sm text-slate-500">Lista priorizada para acompanhamento, reabertura e escalonamento.</p>
            </div>
            <div className="flex flex-col gap-3 sm:flex-row">
              <input
                value={search}
                onChange={(event) => setSearch(event.target.value)}
                placeholder="Buscar por titulo ou hipotese"
                className="rounded-2xl border border-slate-300 px-4 py-3 text-sm text-slate-900"
              />
              <select
                value={statusFilter}
                onChange={(event) => setStatusFilter(event.target.value as IntelligenceCase["status"] | "all")}
                className="rounded-2xl border border-slate-300 px-4 py-3 text-sm text-slate-900"
              >
                <option value="all">todos</option>
                {statusOptions.map((option) => (
                  <option key={option} value={option}>
                    {humanize(option)}
                  </option>
                ))}
              </select>
              <button
                type="button"
                onClick={() => void loadCases({ status: statusFilter, search })}
                className="rounded-2xl bg-slate-900 px-4 py-3 text-sm font-semibold text-white"
              >
                Atualizar
              </button>
            </div>
          </div>

          {loading ? (
            <EmptyState text="Carregando casos..." />
          ) : cases.length === 0 ? (
            <EmptyState text="Nenhum caso encontrado para o filtro atual." />
          ) : (
            <div className="space-y-3">
              {cases.map((caseItem) => (
                <article
                  key={caseItem.id}
                  className={`rounded-2xl border p-4 ${selectedCaseId === caseItem.id ? "border-amber-300 bg-amber-50" : "border-slate-200 bg-slate-50"}`}
                >
                  <div className="flex items-start justify-between gap-4">
                    <div>
                      <div className="flex flex-wrap items-center gap-2">
                        <h3 className="text-lg font-semibold text-slate-950">{caseItem.title}</h3>
                        <StatusBadge status={caseItem.status} />
                      </div>
                      {caseItem.hypothesis ? (
                        <p className="mt-2 text-sm text-slate-600">{caseItem.hypothesis}</p>
                      ) : null}
                      {caseItem.summary ? (
                        <p className="mt-2 text-sm text-slate-500">{caseItem.summary}</p>
                      ) : null}
                      <div className="mt-3 flex flex-wrap gap-2 text-xs text-slate-500">
                        <MiniTag text={`prioridade ${caseItem.priority}`} />
                        <MiniTag text={caseItem.sensitivity_level} />
                        <MiniTag text={caseItem.created_by_name || "analista"} />
                        <MiniTag text={new Date(caseItem.created_at).toLocaleString("pt-BR")} />
                      </div>
                    </div>
                    <button
                      type="button"
                      onClick={() => selectCase(caseItem)}
                      className="rounded-2xl bg-slate-900 px-4 py-3 text-sm font-semibold text-white"
                    >
                      Editar
                    </button>
                  </div>
                </article>
              ))}
            </div>
          )}
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
