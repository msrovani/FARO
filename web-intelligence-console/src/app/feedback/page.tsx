"use client";

import { FormEvent, ReactNode, useEffect, useState } from "react";
import { CheckCheck, MessageSquareReply, Plus, ShieldAlert } from "lucide-react";

import { ConsoleShell } from "@/app/components/console-shell";
import { intelligenceApi } from "@/app/services/api";
import { AnalystFeedbackTemplate, FeedbackForAgent, FeedbackRecipient } from "@/app/types";

const defaultTemplate = {
  name: "",
  feedback_type: "pedagogical",
  sensitivity_level: "operational",
  body_template: "",
  is_active: true,
};

export default function FeedbackPage() {
  const [feedbacks, setFeedbacks] = useState<FeedbackForAgent[]>([]);
  const [templates, setTemplates] = useState<AnalystFeedbackTemplate[]>([]);
  const [form, setForm] = useState(defaultTemplate);
  const [dispatchObservationId, setDispatchObservationId] = useState("");
  const [dispatchTargetUserId, setDispatchTargetUserId] = useState("");
  const [dispatchTargetTeam, setDispatchTargetTeam] = useState("");
  const [recipientQuery, setRecipientQuery] = useState("");
  const [recipientOptions, setRecipientOptions] = useState<FeedbackRecipient[]>([]);
  const [recipientLoading, setRecipientLoading] = useState(false);
  const [dispatchTitle, setDispatchTitle] = useState("Retorno operacional da inteligencia");
  const [dispatchType, setDispatchType] = useState("confirmation");
  const [dispatchSensitivity, setDispatchSensitivity] = useState("operational");
  const [dispatchTemplateId, setDispatchTemplateId] = useState("");
  const [dispatchMessage, setDispatchMessage] = useState("");
  const [loading, setLoading] = useState(true);
  const [savingTemplate, setSavingTemplate] = useState(false);
  const [sendingFeedback, setSendingFeedback] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    void loadPageData();
  }, []);

  async function loadPageData() {
    try {
      setLoading(true);
      setError(null);
      const [pendingFeedbacks, activeTemplates] = await Promise.all([
        intelligenceApi.getPendingFeedback(),
        intelligenceApi.listFeedbackTemplates(true),
      ]);
      setFeedbacks(pendingFeedbacks);
      setTemplates(activeTemplates);
    } catch (err) {
      console.error(err);
      setError("Nao foi possivel carregar o centro de feedback.");
    } finally {
      setLoading(false);
    }
  }

  async function markAsRead(feedbackId: string) {
    try {
      await intelligenceApi.markFeedbackRead(feedbackId);
      setFeedbacks((current) => current.filter((item) => item.feedback_id !== feedbackId));
    } catch (err) {
      console.error(err);
      setError("Falha ao atualizar o status de leitura.");
    }
  }

  async function createTemplate(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    if (savingTemplate || form.name.trim().length < 3 || form.body_template.trim().length < 5) {
      return;
    }

    try {
      setSavingTemplate(true);
      setError(null);
      const created = await intelligenceApi.createFeedbackTemplate({
        name: form.name.trim(),
        feedback_type: form.feedback_type.trim(),
        sensitivity_level: form.sensitivity_level.trim(),
        body_template: form.body_template.trim(),
        is_active: form.is_active,
      });
      setTemplates((current) => [created, ...current]);
      setForm(defaultTemplate);
    } catch (err) {
      console.error(err);
      setError("Falha ao criar template de feedback.");
    } finally {
      setSavingTemplate(false);
    }
  }

  function applyDispatchTemplate(templateId: string) {
    setDispatchTemplateId(templateId);
    const template = templates.find((item) => item.id === templateId);
    if (!template) {
      return;
    }
    setDispatchTitle(template.name);
    setDispatchType(template.feedback_type);
    setDispatchSensitivity(template.sensitivity_level);
    setDispatchMessage(template.body_template);
  }

  async function searchRecipients() {
    if (recipientQuery.trim().length < 2) {
      setRecipientOptions([]);
      return;
    }
    try {
      setRecipientLoading(true);
      const recipients = await intelligenceApi.listFeedbackRecipients({
        query: recipientQuery.trim(),
        limit: 20,
      });
      setRecipientOptions(recipients);
    } catch (err) {
      console.error(err);
      setError("Falha ao buscar destinatarios.");
    } finally {
      setRecipientLoading(false);
    }
  }

  function applyRecipientSelection(value: string) {
    if (!value) {
      setDispatchTargetUserId("");
      setDispatchTargetTeam("");
      return;
    }
    const recipient = recipientOptions.find((item) => {
      if (item.recipient_type === "user") return item.user_id === value;
      return item.target_team_label === value;
    });
    if (!recipient) return;
    if (recipient.recipient_type === "user") {
      setDispatchTargetUserId(recipient.user_id || "");
      setDispatchTargetTeam(recipient.target_team_label || "");
      return;
    }
    setDispatchTargetUserId("");
    setDispatchTargetTeam(recipient.target_team_label || "");
  }

  async function sendFeedback(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    if (
      sendingFeedback
      || (!dispatchObservationId && !dispatchTargetTeam && !dispatchTargetUserId)
      || !dispatchTitle.trim()
    ) {
      return;
    }

    try {
      setSendingFeedback(true);
      setError(null);
      await intelligenceApi.createFeedback({
        observation_id: dispatchObservationId || undefined,
        target_user_id: dispatchTargetUserId || undefined,
        target_team_label: dispatchTargetTeam || undefined,
        feedback_type: dispatchType,
        sensitivity_level: dispatchSensitivity,
        title: dispatchTitle.trim(),
        message: dispatchMessage.trim() || undefined,
        template_id: dispatchTemplateId || undefined,
      });
      setDispatchObservationId("");
      setDispatchTargetUserId("");
      setDispatchTargetTeam("");
      setRecipientQuery("");
      setRecipientOptions([]);
      setDispatchTitle("Retorno operacional da inteligencia");
      setDispatchType("confirmation");
      setDispatchSensitivity("operational");
      setDispatchTemplateId("");
      setDispatchMessage("");
      await loadPageData();
    } catch (err) {
      console.error(err);
      setError("Falha ao enviar feedback operacional.");
    } finally {
      setSendingFeedback(false);
    }
  }

  return (
    <ConsoleShell
      title="Centro de Feedback"
      subtitle="Retorno ao campo, leitura pendente e padronizacao de mensagens operacionais."
    >
      {error ? (
        <div className="mb-6 rounded-3xl border border-red-200 bg-red-50 px-5 py-4 text-sm text-red-700">
          {error}
        </div>
      ) : null}

      <div className="grid gap-6 xl:grid-cols-[1.2fr_0.8fr]">
        <section className="space-y-6">
          <div className="rounded-3xl border border-slate-200 bg-white p-5 shadow-sm">
            <div className="flex items-end justify-between gap-4">
              <div>
                <h2 className="text-lg font-semibold text-slate-950">Feedbacks pendentes</h2>
                <p className="mt-1 text-sm text-slate-500">
                  Historico imediato de retornos que ainda precisam ser confirmados como lidos.
                </p>
              </div>
              <div className="rounded-2xl bg-slate-950 px-4 py-2 text-sm font-semibold text-white">
                {feedbacks.length} pendentes
              </div>
            </div>

            <div className="mt-5 space-y-3">
              {loading ? (
                <EmptyPanel text="Carregando feedbacks..." />
              ) : feedbacks.length === 0 ? (
                <EmptyPanel text="Nao ha feedback pendente para o usuario autenticado." />
              ) : (
                feedbacks.map((feedback) => (
                  <article key={feedback.feedback_id} className="rounded-2xl border border-slate-200 bg-slate-50 p-4">
                    <div className="flex flex-col gap-3 lg:flex-row lg:items-start lg:justify-between">
                      <div>
                        <div className="flex items-center gap-2">
                          <span className="text-sm font-semibold uppercase tracking-[0.25em] text-slate-500">
                            {feedback.feedback_type}
                          </span>
                          <span className="rounded-full bg-slate-900 px-2 py-1 text-[11px] uppercase tracking-[0.2em] text-white">
                            {feedback.plate_number}
                          </span>
                        </div>
                        <h3 className="mt-2 text-lg font-semibold text-slate-950">{feedback.title}</h3>
                        <p className="mt-2 text-sm text-slate-600">{feedback.message}</p>
                        {feedback.recommended_action ? (
                          <div className="mt-3 rounded-2xl border border-amber-200 bg-amber-50 px-3 py-3 text-sm text-amber-900">
                            Acao recomendada: {feedback.recommended_action}
                          </div>
                        ) : null}
                        <div className="mt-3 text-xs text-slate-500">
                          {feedback.reviewer_name} • {new Date(feedback.sent_at).toLocaleString("pt-BR")}
                        </div>
                      </div>
                      <button
                        type="button"
                        onClick={() => void markAsRead(feedback.feedback_id)}
                        className="inline-flex items-center gap-2 rounded-2xl bg-slate-900 px-4 py-3 text-sm font-semibold text-white"
                      >
                        <CheckCheck className="h-4 w-4" />
                        Marcar como lido
                      </button>
                    </div>
                  </article>
                ))
              )}
            </div>
          </div>

          <div className="rounded-3xl border border-slate-200 bg-white p-5 shadow-sm">
            <h2 className="text-lg font-semibold text-slate-950">Templates ativos</h2>
            <p className="mt-1 text-sm text-slate-500">
              Modelos reutilizaveis para acelerar retorno qualificado sem perder padronizacao.
            </p>

            <div className="mt-5 space-y-3">
              {loading ? (
                <EmptyPanel text="Carregando templates..." />
              ) : templates.length === 0 ? (
                <EmptyPanel text="Nenhum template ativo cadastrado." />
              ) : (
                templates.map((template) => (
                  <article key={template.id} className="rounded-2xl border border-slate-200 bg-slate-50 p-4">
                    <div className="flex items-start justify-between gap-4">
                      <div>
                        <div className="flex flex-wrap items-center gap-2">
                          <h3 className="text-base font-semibold text-slate-950">{template.name}</h3>
                          <span className="rounded-full bg-white px-2 py-1 text-[11px] font-semibold uppercase tracking-[0.2em] text-slate-600">
                            {template.feedback_type}
                          </span>
                          <span className="rounded-full bg-slate-900 px-2 py-1 text-[11px] font-semibold uppercase tracking-[0.2em] text-white">
                            {template.sensitivity_level}
                          </span>
                        </div>
                        <p className="mt-2 text-sm text-slate-600">{template.body_template}</p>
                      </div>
                      <div className="text-right text-xs text-slate-500">
                        <div>{template.created_by_name || "Analista"}</div>
                        <div>{new Date(template.updated_at).toLocaleString("pt-BR")}</div>
                      </div>
                    </div>
                  </article>
                ))
              )}
            </div>
          </div>
        </section>

        <section className="space-y-6">
          <div className="rounded-3xl border border-slate-200 bg-white p-5 shadow-sm">
            <h2 className="text-lg font-semibold text-slate-950">Disparo avulso ao campo</h2>
            <p className="mt-1 text-sm text-slate-500">
              Use para retorno por observacao especifica ou para envio por equipe/unidade quando o contexto exigir.
            </p>

            <form className="mt-5 space-y-4" onSubmit={sendFeedback}>
              <Field label="Template aplicado">
                <select
                  value={dispatchTemplateId}
                  onChange={(event) => applyDispatchTemplate(event.target.value)}
                  className="w-full rounded-2xl border border-slate-300 px-4 py-3 text-sm text-slate-900"
                >
                  <option value="">Sem template</option>
                  {templates.map((template) => (
                    <option key={template.id} value={template.id}>
                      {template.name} - {template.feedback_type}
                    </option>
                  ))}
                </select>
              </Field>
              <div className="grid gap-4 md:grid-cols-2">
                <Field label="Observacao de origem">
                  <input
                    value={dispatchObservationId}
                    onChange={(event) => setDispatchObservationId(event.target.value)}
                    className="w-full rounded-2xl border border-slate-300 px-4 py-3 text-sm text-slate-900"
                    placeholder="UUID da observacao"
                  />
                </Field>
                <Field label="Equipe / unidade destinataria">
                  <input
                    value={dispatchTargetTeam}
                    onChange={(event) => setDispatchTargetTeam(event.target.value)}
                    className="w-full rounded-2xl border border-slate-300 px-4 py-3 text-sm text-slate-900"
                    placeholder="Ex.: 1CIA-TATICO"
                  />
                </Field>
              </div>
              <div className="grid gap-4 md:grid-cols-[1fr_auto]">
                <Field label="Busca assistida de destinatario">
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
              <Field label="Selecionar destinatario sugerido">
                <select
                  value={dispatchTargetUserId || dispatchTargetTeam}
                  onChange={(event) => applyRecipientSelection(event.target.value)}
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
                    value={dispatchType}
                    onChange={(event) => setDispatchType(event.target.value)}
                    className="w-full rounded-2xl border border-slate-300 px-4 py-3 text-sm text-slate-900"
                  />
                </Field>
                <Field label="Sensibilidade">
                  <input
                    value={dispatchSensitivity}
                    onChange={(event) => setDispatchSensitivity(event.target.value)}
                    className="w-full rounded-2xl border border-slate-300 px-4 py-3 text-sm text-slate-900"
                  />
                </Field>
                <Field label="Titulo">
                  <input
                    value={dispatchTitle}
                    onChange={(event) => setDispatchTitle(event.target.value)}
                    className="w-full rounded-2xl border border-slate-300 px-4 py-3 text-sm text-slate-900"
                  />
                </Field>
              </div>
              <Field label="Mensagem operacional">
                <textarea
                  value={dispatchMessage}
                  onChange={(event) => setDispatchMessage(event.target.value)}
                  className="min-h-28 w-full rounded-2xl border border-slate-300 px-4 py-3 text-sm text-slate-900"
                  placeholder="Retorno objetivo, proporcional e acionavel."
                />
              </Field>
              <button
                type="submit"
                disabled={
                  sendingFeedback
                  || (!dispatchObservationId && !dispatchTargetTeam && !dispatchTargetUserId)
                  || !dispatchTitle.trim()
                }
                className="w-full rounded-2xl bg-slate-900 px-4 py-3 text-sm font-semibold text-white disabled:cursor-not-allowed disabled:bg-slate-300"
              >
                {sendingFeedback ? "Enviando feedback..." : "Enviar feedback ao campo"}
              </button>
            </form>
          </div>

          <div className="rounded-3xl border border-slate-200 bg-white p-5 shadow-sm">
            <h2 className="text-lg font-semibold text-slate-950">Novo template</h2>
            <p className="mt-1 text-sm text-slate-500">
              Cadastre modelos curtos, claros e proporcionais para reduzir digitacao e padronizar retorno.
            </p>

            <form className="mt-5 space-y-4" onSubmit={createTemplate}>
              <Field label="Nome do template">
                <input
                  value={form.name}
                  onChange={(event) => setForm((current) => ({ ...current, name: event.target.value }))}
                  className="w-full rounded-2xl border border-slate-300 px-4 py-3 text-sm text-slate-900"
                  placeholder="Confirmacao de monitoramento"
                />
              </Field>
              <div className="grid gap-4 md:grid-cols-2">
                <Field label="Tipo de feedback">
                  <input
                    value={form.feedback_type}
                    onChange={(event) => setForm((current) => ({ ...current, feedback_type: event.target.value }))}
                    className="w-full rounded-2xl border border-slate-300 px-4 py-3 text-sm text-slate-900"
                    placeholder="confirmation"
                  />
                </Field>
                <Field label="Sensibilidade">
                  <input
                    value={form.sensitivity_level}
                    onChange={(event) => setForm((current) => ({ ...current, sensitivity_level: event.target.value }))}
                    className="w-full rounded-2xl border border-slate-300 px-4 py-3 text-sm text-slate-900"
                    placeholder="operational"
                  />
                </Field>
              </div>
              <Field label="Corpo do template">
                <textarea
                  value={form.body_template}
                  onChange={(event) => setForm((current) => ({ ...current, body_template: event.target.value }))}
                  className="min-h-32 w-full rounded-2xl border border-slate-300 px-4 py-3 text-sm text-slate-900"
                  placeholder="Seu informe foi confirmado e permanece relevante para monitoramento futuro."
                />
              </Field>
              <label className="flex items-center gap-3 rounded-2xl border border-slate-200 bg-slate-50 px-4 py-3 text-sm text-slate-700">
                <input
                  type="checkbox"
                  checked={form.is_active}
                  onChange={(event) => setForm((current) => ({ ...current, is_active: event.target.checked }))}
                  className="h-4 w-4 rounded border-slate-300"
                />
                Publicar template como ativo imediatamente
              </label>
              <button
                type="submit"
                disabled={savingTemplate || form.name.trim().length < 3 || form.body_template.trim().length < 5}
                className="inline-flex w-full items-center justify-center gap-2 rounded-2xl bg-slate-900 px-4 py-3 text-sm font-semibold text-white disabled:cursor-not-allowed disabled:bg-slate-300"
              >
                <Plus className="h-4 w-4" />
                {savingTemplate ? "Salvando template..." : "Criar template"}
              </button>
            </form>
          </div>

          <div className="rounded-3xl border border-slate-200 bg-white p-5 shadow-sm">
            <h2 className="text-lg font-semibold text-slate-950">Boas praticas de retorno</h2>
            <div className="mt-4 space-y-3 text-sm text-slate-600">
              <Tip icon={<MessageSquareReply className="h-4 w-4" />} text="Feedback deve ser claro, curto e operacionalmente acionavel." />
              <Tip icon={<ShieldAlert className="h-4 w-4" />} text="Nao exponha toda a inteligencia. Devolva apenas o necessario para o campo." />
              <Tip icon={<CheckCheck className="h-4 w-4" />} text="Priorize retorno que valida o informe, orienta abordagem futura ou corrige qualidade do dado." />
            </div>
          </div>
        </section>
      </div>
    </ConsoleShell>
  );
}

function Field({ label, children }: { label: string; children: ReactNode }) {
  return (
    <div>
      <label className="mb-2 block text-sm font-medium text-slate-700">{label}</label>
      {children}
    </div>
  );
}

function EmptyPanel({ text }: { text: string }) {
  return (
    <div className="rounded-2xl border border-dashed border-slate-200 bg-slate-50 px-5 py-10 text-center text-sm text-slate-500">
      {text}
    </div>
  );
}

function Tip({ icon, text }: { icon: ReactNode; text: string }) {
  return (
    <div className="flex items-start gap-3 rounded-2xl bg-slate-50 px-4 py-3">
      <div className="mt-0.5 text-slate-900">{icon}</div>
      <p>{text}</p>
    </div>
  );
}
