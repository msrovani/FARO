"use client";

import { FormEvent, useCallback, useEffect, useState } from "react";
import { BellRing, Eye, Map, TimerReset } from "lucide-react";

import { ConsoleShell } from "@/app/components/console-shell";
import { intelligenceApi } from "@/app/services/api";
import {
  AnalystFeedbackTemplate,
  FeedbackRecipient,
  WatchlistCategory,
  WatchlistEntry,
  WatchlistStatus,
} from "@/app/types";

const statusOptions: WatchlistStatus[] = ["active", "inactive", "archived"];
const categoryOptions: WatchlistCategory[] = [
  "stolen",
  "suspicious",
  "wanted",
  "monitoring",
];

export default function WatchlistPage() {
  const [entries, setEntries] = useState<WatchlistEntry[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [statusFilter, setStatusFilter] = useState<WatchlistStatus | "all">("all");

  const [category, setCategory] = useState<WatchlistCategory>("suspicious");
  const [plateNumber, setPlateNumber] = useState("");
  const [platePartial, setPlatePartial] = useState("");
  const [vehicleModel, setVehicleModel] = useState("");
  const [vehicleColor, setVehicleColor] = useState("");
  const [interestReason, setInterestReason] = useState("");
  const [priority, setPriority] = useState(50);
  const [recommendedAction, setRecommendedAction] = useState("");
  const [reviewDueAt, setReviewDueAt] = useState("");
  const [submitting, setSubmitting] = useState(false);
  const [feedbackTemplates, setFeedbackTemplates] = useState<AnalystFeedbackTemplate[]>([]);
  const [recipientOptions, setRecipientOptions] = useState<FeedbackRecipient[]>([]);
  const [recipientQuery, setRecipientQuery] = useState("");
  const [recipientLoading, setRecipientLoading] = useState(false);
  const [feedbackTemplateId, setFeedbackTemplateId] = useState("");
  const [feedbackTargetUserId, setFeedbackTargetUserId] = useState("");
  const [feedbackTargetTeam, setFeedbackTargetTeam] = useState("");
  const [feedbackType, setFeedbackType] = useState("monitoring");
  const [feedbackSensitivity, setFeedbackSensitivity] = useState("operational");
  const [feedbackTitle, setFeedbackTitle] = useState("Atualizacao de monitoramento de watchlist");
  const [feedbackMessage, setFeedbackMessage] = useState("");
  const [sendingFeedback, setSendingFeedback] = useState(false);

  const loadWatchlist = useCallback(async (statusValue?: WatchlistStatus | "all") => {
    const filter = statusValue ?? statusFilter;
    try {
      setLoading(true);
      setError(null);
      setEntries(await intelligenceApi.listWatchlist(filter === "all" ? undefined : filter));
    } catch (err) {
      console.error(err);
      setError("Nao foi possivel carregar a watchlist.");
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
      setError("Watchlist carregada, mas templates de feedback nao puderam ser consultados.");
    }
  }, []);

  useEffect(() => {
    void loadWatchlist(statusFilter);
    void loadFeedbackTemplates();
  }, [loadWatchlist, loadFeedbackTemplates, statusFilter]);

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

  async function sendWatchlistFeedback(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    if ((!feedbackTargetUserId && !feedbackTargetTeam) || !feedbackTitle.trim() || sendingFeedback) return;
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
      setFeedbackType("monitoring");
      setFeedbackSensitivity("operational");
      setFeedbackTitle("Atualizacao de monitoramento de watchlist");
      setFeedbackMessage("");
    } catch (err) {
      console.error(err);
      setError("Falha ao enviar feedback da watchlist.");
    } finally {
      setSendingFeedback(false);
    }
  }

  async function submit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    if (interestReason.trim().length < 5 || submitting) return;

    try {
      setSubmitting(true);
      setError(null);
      const created = await intelligenceApi.createWatchlistEntry({
        category,
        plate_number: plateNumber || undefined,
        plate_partial: platePartial || undefined,
        vehicle_model: vehicleModel || undefined,
        vehicle_color: vehicleColor || undefined,
        interest_reason: interestReason,
        priority,
        recommended_action: recommendedAction || undefined,
        review_due_at: reviewDueAt || undefined,
      });
      setEntries((current) => [created, ...current]);
      setPlateNumber("");
      setPlatePartial("");
      setVehicleModel("");
      setVehicleColor("");
      setInterestReason("");
      setPriority(50);
      setRecommendedAction("");
      setReviewDueAt("");
    } catch (err) {
      console.error(err);
      setError("Falha ao cadastrar item na watchlist.");
    } finally {
      setSubmitting(false);
    }
  }

  async function toggleStatus(entry: WatchlistEntry) {
    const nextStatus: WatchlistStatus = entry.status === "active" ? "inactive" : "active";
    try {
      const updated = await intelligenceApi.updateWatchlistEntry(entry.id, { status: nextStatus });
      setEntries((current) => current.map((item) => (item.id === entry.id ? updated : item)));
    } catch (err) {
      console.error(err);
      setError("Falha ao atualizar status da watchlist.");
    }
  }

  return (
    <ConsoleShell
      title="Watchlist e Cadastro Independente"
      subtitle="Monitoramento ativo, cadastro de interesse e controle de prioridade operacional."
    >
      {error ? (
        <div className="mb-6 rounded-3xl border border-red-200 bg-red-50 px-5 py-4 text-sm text-red-700">
          {error}
        </div>
      ) : null}

      <div className="grid gap-6 xl:grid-cols-[1.1fr_1fr]">
        <section className="rounded-3xl border border-slate-200 bg-white p-5 shadow-sm">
          <div className="mb-5 flex flex-col gap-3 lg:flex-row lg:items-end lg:justify-between">
            <div>
              <h2 className="text-lg font-semibold text-slate-950">Cadastro independente</h2>
              <p className="mt-1 text-sm text-slate-500">
                Use quando o veículo de interesse nao nasceu de um registro de campo.
              </p>
            </div>
            <div className="rounded-2xl border border-slate-200 bg-slate-50 px-4 py-3 text-sm text-slate-600">
              MVP funcional com persistencia real.
            </div>
          </div>

          <form className="grid gap-4 md:grid-cols-2" onSubmit={submit}>
            <Field label="Categoria">
              <select
                value={category}
                onChange={(event) => setCategory(event.target.value as WatchlistCategory)}
                className="w-full rounded-2xl border border-slate-300 px-4 py-3 text-sm text-slate-900"
              >
                {categoryOptions.map((option) => (
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
            <Field label="Placa exata">
              <input
                value={plateNumber}
                onChange={(event) => setPlateNumber(event.target.value.toUpperCase())}
                className="w-full rounded-2xl border border-slate-300 px-4 py-3 text-sm text-slate-900"
              />
            </Field>
            <Field label="Placa parcial">
              <input
                value={platePartial}
                onChange={(event) => setPlatePartial(event.target.value.toUpperCase())}
                className="w-full rounded-2xl border border-slate-300 px-4 py-3 text-sm text-slate-900"
              />
            </Field>
            <Field label="Modelo/descricao">
              <input
                value={vehicleModel}
                onChange={(event) => setVehicleModel(event.target.value)}
                className="w-full rounded-2xl border border-slate-300 px-4 py-3 text-sm text-slate-900"
              />
            </Field>
            <Field label="Cor">
              <input
                value={vehicleColor}
                onChange={(event) => setVehicleColor(event.target.value)}
                className="w-full rounded-2xl border border-slate-300 px-4 py-3 text-sm text-slate-900"
              />
            </Field>
            <Field className="md:col-span-2" label="Motivo do interesse">
              <textarea
                value={interestReason}
                onChange={(event) => setInterestReason(event.target.value)}
                className="min-h-28 w-full rounded-2xl border border-slate-300 px-4 py-3 text-sm text-slate-900"
                placeholder="Descreva a origem da informacao e por que este veiculo deve entrar em monitoramento."
              />
            </Field>
            <Field className="md:col-span-2" label="Recomendacao operacional">
              <input
                value={recommendedAction}
                onChange={(event) => setRecommendedAction(event.target.value)}
                className="w-full rounded-2xl border border-slate-300 px-4 py-3 text-sm text-slate-900"
                placeholder="Ex.: alertar apenas inteligencia e revisar em 72h."
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
            <div className="md:col-span-2">
              <button
                type="submit"
                disabled={interestReason.trim().length < 5 || submitting}
                className="w-full rounded-2xl bg-slate-900 px-4 py-3 text-sm font-semibold text-white disabled:cursor-not-allowed disabled:bg-slate-300"
              >
                {submitting ? "Salvando cadastro..." : "Cadastrar na watchlist"}
              </button>
            </div>
          </form>

          <form className="mt-6 space-y-4 rounded-2xl border border-slate-200 bg-slate-50 p-4" onSubmit={sendWatchlistFeedback}>
            <h3 className="text-sm font-semibold uppercase tracking-[0.2em] text-slate-600">Feedback de monitoramento</h3>
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
              disabled={(!feedbackTargetUserId && !feedbackTargetTeam) || !feedbackTitle.trim() || sendingFeedback}
              className="w-full rounded-2xl bg-slate-900 px-4 py-3 text-sm font-semibold text-white disabled:cursor-not-allowed disabled:bg-slate-300"
            >
              {sendingFeedback ? "Enviando..." : "Enviar feedback de watchlist"}
            </button>
          </form>
        </section>

        <section className="rounded-3xl border border-slate-200 bg-white p-5 shadow-sm">
          <div className="mb-5 flex flex-col gap-3 lg:flex-row lg:items-end lg:justify-between">
            <div>
              <h2 className="text-lg font-semibold text-slate-950">Monitoramento ativo</h2>
              <p className="mt-1 text-sm text-slate-500">Base atual de interesses cadastrados pela inteligencia.</p>
            </div>
            <select
              value={statusFilter}
              onChange={(event) => setStatusFilter(event.target.value as WatchlistStatus | "all")}
              className="rounded-2xl border border-slate-300 px-4 py-3 text-sm text-slate-900"
            >
              <option value="all">todos</option>
              {statusOptions.map((status) => (
                <option key={status} value={status}>
                  {humanize(status)}
                </option>
              ))}
            </select>
          </div>

          <div className="space-y-3">
            {loading ? (
              <EmptyState text="Carregando watchlist..." />
            ) : entries.length === 0 ? (
              <EmptyState text="Nenhum cadastro encontrado para o filtro atual." />
            ) : (
              entries.map((entry) => (
                <article key={entry.id} className="rounded-2xl border border-slate-200 bg-slate-50 p-4">
                  <div className="flex items-start justify-between gap-4">
                    <div>
                      <div className="flex flex-wrap items-center gap-2">
                        <span className="text-lg font-semibold tracking-widest text-slate-950">
                          {entry.plate_number || entry.plate_partial || "SEM PLACA DEFINIDA"}
                        </span>
                        <StatusBadge status={entry.status} />
                      </div>
                      <div className="mt-1 text-sm text-slate-600">
                        {humanize(entry.category)} • prioridade {entry.priority}
                      </div>
                      <div className="mt-2 text-sm text-slate-600">
                        {entry.vehicle_model || "Modelo nao informado"} {entry.vehicle_color ? `• ${entry.vehicle_color}` : ""}
                      </div>
                      <p className="mt-3 text-sm text-slate-600">{entry.interest_reason}</p>
                      <div className="mt-3 flex flex-wrap gap-2 text-xs text-slate-500">
                        <MiniTag icon={<Eye className="h-3.5 w-3.5" />} text={entry.created_by_name || "analista"} />
                        <MiniTag icon={<BellRing className="h-3.5 w-3.5" />} text={entry.recommended_action || "sem acao definida"} />
                        <MiniTag icon={<Map className="h-3.5 w-3.5" />} text={entry.geographic_scope || "sem area definida"} />
                        <MiniTag icon={<TimerReset className="h-3.5 w-3.5" />} text={entry.review_due_at ? new Date(entry.review_due_at).toLocaleString("pt-BR") : "sem revisao"} />
                      </div>
                    </div>
                    <button
                      type="button"
                      onClick={() => void toggleStatus(entry)}
                      className="rounded-2xl bg-slate-900 px-4 py-3 text-sm font-semibold text-white"
                    >
                      {entry.status === "active" ? "Suspender" : "Reativar"}
                    </button>
                  </div>
                </article>
              ))
            )}
          </div>
        </section>
      </div>
    </ConsoleShell>
  );
}

function Field({
  label,
  className,
  children,
}: {
  label: string;
  className?: string;
  children: React.ReactNode;
}) {
  return (
    <label className={className}>
      <div className="mb-2 text-sm font-medium text-slate-700">{label}</div>
      {children}
    </label>
  );
}

function StatusBadge({ status }: { status: WatchlistStatus }) {
  const tone =
    status === "active"
      ? "bg-emerald-100 text-emerald-700"
      : status === "inactive"
        ? "bg-amber-100 text-amber-700"
        : "bg-slate-200 text-slate-700";

  return <span className={`rounded-full px-2 py-1 text-[11px] font-semibold uppercase tracking-[0.2em] ${tone}`}>{humanize(status)}</span>;
}

function MiniTag({ icon, text }: { icon: React.ReactNode; text: string }) {
  return (
    <span className="inline-flex items-center gap-1 rounded-full bg-white px-2 py-1">
      {icon}
      {text}
    </span>
  );
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
