"use client";

import Link from "next/link";
import { useEffect, useMemo, useState } from "react";
import { AlertTriangle, ArrowRight, Clock3, Eye, Radar, ShieldAlert, Siren, TimerReset, Waypoints } from "lucide-react";

import { ConsoleShell } from "@/app/components/console-shell";
import { dashboardApi, intelligenceApi } from "@/app/services/api";
import { DashboardPriorityBucket, DashboardStats, FeedbackForAgent, IntelligenceQueueItem } from "@/app/types";

export default function DashboardPage() {
  const [stats, setStats] = useState<DashboardStats | null>(null);
  const [queue, setQueue] = useState<IntelligenceQueueItem[]>([]);
  const [feedbacks, setFeedbacks] = useState<FeedbackForAgent[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    void loadConsole();
  }, []);

  async function loadConsole() {
    try {
      setLoading(true);
      setError(null);
      const [statsData, queueData, feedbackData] = await Promise.all([
        dashboardApi.getStats(),
        intelligenceApi.getQueue(undefined, { page: 1, page_size: 12 }),
        intelligenceApi.getPendingFeedback(),
      ]);

      setStats(statsData);
      setQueue(queueData);
      setFeedbacks(feedbackData);
    } catch (err) {
      console.error(err);
      setError("Nao foi possivel carregar a mesa analitica.");
    } finally {
      setLoading(false);
    }
  }

  const priorityBuckets = useMemo<DashboardPriorityBucket[]>(() => {
    const critical = queue.filter((item) => item.urgency === "approach").length;
    const high = queue.filter((item) => item.urgency === "intelligence").length;
    const moderate = queue.filter((item) => item.urgency === "monitor").length;

    return [
      {
        label: "Resposta imediata",
        description: "Itens com indicacao forte de abordagem qualificada ou escalonamento.",
        count: critical,
        tone: "critical",
      },
      {
        label: "Triagem qualificada",
        description: "Suspeicoes que merecem leitura completa, correlacao e decisao formal.",
        count: high,
        tone: "high",
      },
      {
        label: "Monitoramento",
        description: "Informes que devem permanecer acompanhados pela inteligencia.",
        count: moderate,
        tone: "moderate",
      },
      {
        label: "Retroalimentacao",
        description: "Feedbacks pendentes e retornos que precisam chegar ao campo.",
        count: feedbacks.length,
        tone: "info",
      },
    ];
  }, [feedbacks.length, queue]);

  const queueLead = queue.slice(0, 5);
  const recurringItems = [...queue]
    .sort((a, b) => b.previous_observations_count - a.previous_observations_count)
    .slice(0, 4);

  return (
    <ConsoleShell
      title="Mesa Analítica"
      subtitle="Central de triagem, priorização, revisão e retorno ao campo."
    >
      {error ? (
        <div className="mb-6 rounded-3xl border border-red-200 bg-red-50 px-5 py-4 text-sm text-red-700">
          {error}
        </div>
      ) : null}

      <section className="grid gap-4 xl:grid-cols-4">
        <MetricCard
          loading={loading}
          label="Pendentes de análise"
          value={stats?.pending_reviews ?? 0}
          hint="Fila não concluída"
          icon={<Eye className="h-5 w-5" />}
        />
        <MetricCard
          loading={loading}
          label="Alertas ativos"
          value={stats?.active_alerts ?? 0}
          hint="Feedbacks e sinais acionáveis"
          icon={<Siren className="h-5 w-5" />}
          tone="critical"
        />
        <MetricCard
          loading={loading}
          label="Tempo médio de resposta"
          value={stats ? `${stats.avg_response_time_hours.toFixed(1)}h` : "0h"}
          hint="Do registro até a revisão"
          icon={<TimerReset className="h-5 w-5" />}
        />
        <MetricCard
          loading={loading}
          label="OCR corrigido"
          value={stats ? `${(stats.ocr_correction_rate * 100).toFixed(1)}%` : "0%"}
          hint="Indicador de confiança operacional"
          icon={<ShieldAlert className="h-5 w-5" />}
        />
      </section>

      <section className="mt-6 grid gap-6 xl:grid-cols-[1.4fr_1fr]">
        <div className="space-y-6">
          <Panel
            title="Fila priorizada"
            subtitle="Os itens abaixo representam a frente de trabalho da inteligencia nesta mesa."
            actionHref="/queue"
            actionLabel="Abrir fila completa"
          >
            <div className="grid gap-3 md:grid-cols-2">
              {priorityBuckets.map((bucket) => (
                <PriorityCard key={bucket.label} bucket={bucket} />
              ))}
            </div>
          </Panel>

          <Panel
            title="Entrada de informes"
            subtitle="Itens mais recentes ou mais criticos para assumir, redistribuir ou abrir ficha completa."
            actionHref="/queue"
            actionLabel="Assumir análise"
          >
            {loading ? (
              <EmptyState text="Carregando mesa..." />
            ) : queueLead.length === 0 ? (
              <EmptyState text="Nao ha informes pendentes para a fila atual." />
            ) : (
              <div className="space-y-3">
                {queueLead.map((item) => (
                  <Link
                    key={item.observation_id}
                    href={`/queue?highlight=${item.observation_id}`}
                    className="block rounded-2xl border border-slate-200 bg-slate-50 px-4 py-4 transition hover:border-slate-300 hover:bg-white"
                  >
                    <div className="flex items-start justify-between gap-4">
                      <div>
                        <div className="flex items-center gap-2">
                          <span className="text-lg font-semibold tracking-widest">{item.plate_number}</span>
                          <SeverityBadge urgency={item.urgency} />
                        </div>
                        <p className="mt-1 text-sm text-slate-600">{humanizeReason(item.suspicion_reason)}</p>
                        <div className="mt-2 flex flex-wrap gap-2 text-xs text-slate-500">
                          <Tag icon={<Clock3 className="h-3.5 w-3.5" />} text={new Date(item.observed_at).toLocaleString("pt-BR")} />
                          <Tag icon={<Radar className="h-3.5 w-3.5" />} text={`${item.previous_observations_count} passagens`} />
                          <Tag icon={<Waypoints className="h-3.5 w-3.5" />} text={item.unit_name || "Unidade sem identificação"} />
                        </div>
                      </div>
                      <ArrowRight className="mt-1 h-4 w-4 text-slate-400" />
                    </div>
                  </Link>
                ))}
              </div>
            )}
          </Panel>
        </div>

        <div className="space-y-6">
          <Panel
            title="Retorno ao campo"
            subtitle="Feedbacks que ainda demandam leitura, conferência ou reforço tático."
            actionHref="/feedback"
            actionLabel="Abrir central"
          >
            {loading ? (
              <EmptyState text="Carregando feedbacks..." />
            ) : feedbacks.length === 0 ? (
              <EmptyState text="Sem feedbacks pendentes para o usuario autenticado." />
            ) : (
              <div className="space-y-3">
                {feedbacks.slice(0, 4).map((feedback) => (
                  <div key={feedback.feedback_id} className="rounded-2xl border border-slate-200 bg-slate-50 px-4 py-4">
                    <div className="flex items-center justify-between gap-3">
                      <div className="text-sm font-semibold text-slate-900">{feedback.title}</div>
                      <span className="rounded-full bg-slate-900 px-2 py-1 text-[11px] uppercase tracking-[0.2em] text-white">
                        {feedback.feedback_type}
                      </span>
                    </div>
                    <p className="mt-2 text-sm text-slate-600">{feedback.message}</p>
                    <div className="mt-3 text-xs text-slate-500">
                      {feedback.plate_number} • {feedback.reviewer_name}
                    </div>
                  </div>
                ))}
              </div>
            )}
          </Panel>

          <Panel
            title="Recorrência e contexto"
            subtitle="Sinais objetivos que ajudam o analista a não perder padrão no meio da fila."
          >
            {loading ? (
              <EmptyState text="Calculando recorrência..." />
            ) : recurringItems.length === 0 ? (
              <EmptyState text="Sem amostra suficiente para destacar recorrências." />
            ) : (
              <div className="space-y-3">
                {recurringItems.map((item) => (
                  <div key={item.observation_id} className="rounded-2xl bg-slate-950 px-4 py-4 text-white">
                    <div className="flex items-center justify-between gap-4">
                      <div>
                        <div className="text-lg font-semibold tracking-[0.2em]">{item.plate_number}</div>
                        <div className="mt-1 text-sm text-slate-300">{humanizeReason(item.suspicion_reason)}</div>
                      </div>
                      <div className="text-right">
                        <div className="text-2xl font-semibold">{item.previous_observations_count}</div>
                        <div className="text-xs uppercase tracking-[0.25em] text-slate-400">passagens</div>
                      </div>
                    </div>
                  </div>
                ))}
              </div>
            )}
          </Panel>

          <Panel
            title="Módulos estratégicos"
            subtitle="Blocos já previstos no frontend, aguardando contratos de backend para sair do estado de modelagem."
          >
            <div className="grid gap-3">
              <RoadmapItem
                title="Cadastro independente de veículo suspeito"
                description="Precisa de CRUD com sigilo, validade, prioridade e vínculo com watchlist."
              />
              <RoadmapItem
                title="Watchlist operacional"
                description="Depende de regras editáveis, janela temporal, área geográfica e orientação de abordagem."
              />
              <RoadmapItem
                title="Casos e dossiês"
                description="Precisa agrupar veículos, pessoas, ocorrências, anexos e evolução analítica."
              />
            </div>
          </Panel>
        </div>
      </section>
    </ConsoleShell>
  );
}

function MetricCard({
  label,
  value,
  hint,
  icon,
  loading,
  tone = "default",
}: {
  label: string;
  value: number | string;
  hint: string;
  icon: React.ReactNode;
  loading: boolean;
  tone?: "default" | "critical";
}) {
  return (
    <div className={`rounded-3xl border p-5 shadow-sm ${tone === "critical" ? "border-red-200 bg-red-50" : "border-slate-200 bg-white"}`}>
      <div className="flex items-start justify-between gap-4">
        <div>
          <div className="text-sm font-medium text-slate-500">{label}</div>
          <div className="mt-3 text-3xl font-semibold text-slate-950">{loading ? "..." : value}</div>
          <div className="mt-2 text-sm text-slate-500">{hint}</div>
        </div>
        <div className={`rounded-2xl p-3 ${tone === "critical" ? "bg-red-100 text-red-700" : "bg-slate-100 text-slate-700"}`}>
          {icon}
        </div>
      </div>
    </div>
  );
}

function Panel({
  title,
  subtitle,
  actionHref,
  actionLabel,
  children,
}: {
  title: string;
  subtitle: string;
  actionHref?: string;
  actionLabel?: string;
  children: React.ReactNode;
}) {
  return (
    <section className="rounded-3xl border border-slate-200 bg-white p-5 shadow-sm">
      <div className="mb-4 flex flex-col gap-3 lg:flex-row lg:items-end lg:justify-between">
        <div>
          <h2 className="text-lg font-semibold text-slate-950">{title}</h2>
          <p className="mt-1 text-sm text-slate-500">{subtitle}</p>
        </div>
        {actionHref && actionLabel ? (
          <Link href={actionHref} className="text-sm font-semibold text-slate-900 hover:text-amber-600">
            {actionLabel}
          </Link>
        ) : null}
      </div>
      {children}
    </section>
  );
}

function PriorityCard({ bucket }: { bucket: DashboardPriorityBucket }) {
  const tones = {
    critical: "border-red-200 bg-red-50 text-red-700",
    high: "border-amber-200 bg-amber-50 text-amber-700",
    moderate: "border-sky-200 bg-sky-50 text-sky-700",
    info: "border-slate-200 bg-slate-50 text-slate-700",
  } as const;

  return (
    <div className={`rounded-2xl border p-4 ${tones[bucket.tone]}`}>
      <div className="text-sm font-semibold uppercase tracking-[0.2em]">{bucket.label}</div>
      <div className="mt-3 text-3xl font-semibold">{bucket.count}</div>
      <div className="mt-2 text-sm opacity-90">{bucket.description}</div>
    </div>
  );
}

function SeverityBadge({ urgency }: { urgency: IntelligenceQueueItem["urgency"] }) {
  const style =
    urgency === "approach"
      ? "bg-red-100 text-red-700"
      : urgency === "intelligence"
        ? "bg-amber-100 text-amber-700"
        : "bg-sky-100 text-sky-700";

  return <span className={`rounded-full px-2 py-1 text-[11px] font-semibold uppercase tracking-[0.2em] ${style}`}>{urgency}</span>;
}

function Tag({ icon, text }: { icon: React.ReactNode; text: string }) {
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

function RoadmapItem({ title, description }: { title: string; description: string }) {
  return (
    <div className="rounded-2xl border border-slate-200 bg-slate-50 px-4 py-4">
      <div className="flex items-center gap-2 text-sm font-semibold text-slate-900">
        <AlertTriangle className="h-4 w-4 text-amber-600" />
        {title}
      </div>
      <p className="mt-2 text-sm text-slate-600">{description}</p>
    </div>
  );
}

function humanizeReason(reason: IntelligenceQueueItem["suspicion_reason"]) {
  return reason.replaceAll("_", " ");
}
