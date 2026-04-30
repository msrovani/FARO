"use client";

import React, { useState, useCallback } from "react";
import { 
  AlertTriangle, 
  Shield, 
  Clock, 
  User, 
  MessageSquare, 
  TrendingUp,
  Eye,
  ThumbsUp,
  ThumbsDown,
  AlertCircle,
  CheckCircle,
  XCircle,
  FileText,
  Image,
  Mic
} from "lucide-react";

interface Evidence {
  id: string;
  type: "image" | "audio" | "document";
  url: string;
  description: string;
  timestamp: string;
}

interface ApproachHistory {
  id: string;
  agent_id: string;
  agent_name: string;
  approach_time: string;
  confirmed_suspicion: boolean;
  approach_level: number;
  has_incident: boolean;
  incident_type?: string;
  notes: string;
  evidence: Evidence[];
}

interface UnifiedSuspicionReport {
  id: string;
  observation_id: string;
  agent_id: string;
  
  // Initial suspicion (capture)
  initial_reason: string;
  initial_level: string;
  initial_urgency: string;
  initial_notes?: string;
  initial_evidence: Evidence[];
  
  // Approach confirmation
  was_approached: boolean;
  approach_confirmed_suspicion: boolean;
  approach_level: number;
  approach_notes?: string;
  approach_evidence: Evidence[];
  
  // Incident details
  has_incident: boolean;
  incident_type?: string;
  incident_report?: string;
  
  // System metadata
  status: string;
  priority: number;
  previous_approaches: ApproachHistory[];
  
  // Timestamps
  created_at: string;
  updated_at: string;
  approached_at?: string;
}

interface SuspicionContext {
  current_suspicion?: UnifiedSuspicionReport;
  suspicion_history: any[];
  agent_feedback: any[];
  recommendations: any[];
  plate_number: string;
  generated_at: string;
}

interface UnifiedSuspicionProps {
  suspicion?: UnifiedSuspicionReport;
  context?: SuspicionContext;
  showHistory?: boolean;
  showFeedback?: boolean;
  showRecommendations?: boolean;
  onFeedback?: (suspicionId: string, feedback: string) => void;
  onRefresh?: () => void;
  className?: string;
}

const SuspicionReasonLabels: Record<string, string> = {
  stolen_vehicle: "Veículo Roubado",
  suspicious_behavior: "Comportamento Suspeito",
  wanted_plate: "Placa Procurada",
  unusual_hours: "Horário Incomum",
  known_associate: "Associado Conhecido",
  drug_trafficking: "Tráfico de Drogas",
  weapons: "Armas",
  gang_activity: "Atividade de Gangue",
  other: "Outro"
};

const SuspicionLevelLabels: Record<string, string> = {
  low: "Baixo",
  medium: "Médio",
  high: "Alto"
};

const UrgencyLevelLabels: Record<string, string> = {
  monitor: "Monitorar",
  intelligence: "Inteligência",
  approach: "Abordar"
};

const SuspicionStatusLabels: Record<string, string> = {
  pending_approach: "Pendente de Abordagem",
  approached: "Abordado",
  confirmed: "Confirmado",
  false_positive: "Falso Positivo",
  resolved: "Resolvido"
};

export function UnifiedSuspicion({
  suspicion,
  context,
  showHistory = false,
  showFeedback = false,
  showRecommendations = false,
  onFeedback,
  onRefresh,
  className = ""
}: UnifiedSuspicionProps) {
  const [activeTab, setActiveTab] = useState<"details" | "history" | "feedback" | "recommendations">("details");
  const [feedbackText, setFeedbackText] = useState("");
  const [isSubmittingFeedback, setIsSubmittingFeedback] = useState(false);

  const currentSuspicion = suspicion || context?.current_suspicion;

  const handleFeedbackSubmit = useCallback(async () => {
    if (!feedbackText.trim() || !currentSuspicion || !onFeedback) return;

    setIsSubmittingFeedback(true);
    try {
      await onFeedback(currentSuspicion.id, feedbackText);
      setFeedbackText("");
      onRefresh?.();
    } catch (error) {
      console.error("Failed to submit feedback:", error);
    } finally {
      setIsSubmittingFeedback(false);
    }
  }, [feedbackText, currentSuspicion, onFeedback, onRefresh]);

  const getPriorityColor = (priority: number) => {
    if (priority >= 80) return "text-red-600 bg-red-100";
    if (priority >= 60) return "text-orange-600 bg-orange-100";
    if (priority >= 40) return "text-yellow-600 bg-yellow-100";
    return "text-green-600 bg-green-100";
  };

  const getStatusColor = (status: string) => {
    switch (status) {
      case "confirmed": return "text-green-600 bg-green-100";
      case "false_positive": return "text-red-600 bg-red-100";
      case "approached": return "text-blue-600 bg-blue-100";
      case "pending_approach": return "text-yellow-600 bg-yellow-100";
      default: return "text-gray-600 bg-gray-100";
    }
  };

  const getLevelColor = (level: string) => {
    switch (level) {
      case "high": return "text-red-600";
      case "medium": return "text-orange-600";
      case "low": return "text-green-600";
      default: return "text-gray-600";
    }
  };

  if (!currentSuspicion) {
    return (
      <div className={`p-6 text-center text-gray-500 ${className}`}>
        <AlertCircle className="h-12 w-12 mx-auto mb-4 text-gray-400" />
        <p>Nenhuma suspeição encontrada</p>
      </div>
    );
  }

  return (
    <div className={`bg-white rounded-lg shadow-lg ${className}`}>
      {/* Header */}
      <div className="border-b border-gray-200 p-6">
        <div className="flex items-start justify-between">
          <div>
            <h3 className="text-lg font-semibold text-gray-900">Relatório de Suspeição</h3>
            <p className="text-sm text-gray-500 mt-1">
              ID: {currentSuspicion.id} • Observação: {currentSuspicion.observation_id}
            </p>
          </div>
          <div className="flex items-center space-x-2">
            <span className={`px-3 py-1 rounded-full text-xs font-medium ${getPriorityColor(currentSuspicion.priority)}`}>
              Prioridade: {currentSuspicion.priority}/100
            </span>
            <span className={`px-3 py-1 rounded-full text-xs font-medium ${getStatusColor(currentSuspicion.status)}`}>
              {SuspicionStatusLabels[currentSuspicion.status] || currentSuspicion.status}
            </span>
          </div>
        </div>
      </div>

      {/* Tabs */}
      <div className="border-b border-gray-200">
        <nav className="flex space-x-8 px-6">
          <button
            onClick={() => setActiveTab("details")}
            className={`py-3 px-1 border-b-2 font-medium text-sm ${
              activeTab === "details"
                ? "border-blue-500 text-blue-600"
                : "border-transparent text-gray-500 hover:text-gray-700"
            }`}
          >
            Detalhes
          </button>
          {showHistory && (
            <button
              onClick={() => setActiveTab("history")}
              className={`py-3 px-1 border-b-2 font-medium text-sm ${
                activeTab === "history"
                  ? "border-blue-500 text-blue-600"
                  : "border-transparent text-gray-500 hover:text-gray-700"
              }`}
            >
              Histórico ({currentSuspicion.previous_approaches.length})
            </button>
          )}
          {showFeedback && (
            <button
              onClick={() => setActiveTab("feedback")}
              className={`py-3 px-1 border-b-2 font-medium text-sm ${
                activeTab === "feedback"
                  ? "border-blue-500 text-blue-600"
                  : "border-transparent text-gray-500 hover:text-gray-700"
              }`}
            >
              Feedback
            </button>
          )}
          {showRecommendations && context?.recommendations && (
            <button
              onClick={() => setActiveTab("recommendations")}
              className={`py-3 px-1 border-b-2 font-medium text-sm ${
                activeTab === "recommendations"
                  ? "border-blue-500 text-blue-600"
                  : "border-transparent text-gray-500 hover:text-gray-700"
              }`}
            >
              Recomendações ({context.recommendations.length})
            </button>
          )}
        </nav>
      </div>

      {/* Tab Content */}
      <div className="p-6">
        {activeTab === "details" && (
          <div className="space-y-6">
            {/* Initial Suspicion */}
            <div>
              <h4 className="text-md font-medium text-gray-900 mb-3">Suspeição Inicial</h4>
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                <div>
                  <label className="text-sm font-medium text-gray-500">Motivo</label>
                  <p className="text-sm text-gray-900">
                    {SuspicionReasonLabels[currentSuspicion.initial_reason] || currentSuspicion.initial_reason}
                  </p>
                </div>
                <div>
                  <label className="text-sm font-medium text-gray-500">Nível</label>
                  <p className={`text-sm font-medium ${getLevelColor(currentSuspicion.initial_level)}`}>
                    {SuspicionLevelLabels[currentSuspicion.initial_level] || currentSuspicion.initial_level}
                  </p>
                </div>
                <div>
                  <label className="text-sm font-medium text-gray-500">Urgência</label>
                  <p className="text-sm text-gray-900">
                    {UrgencyLevelLabels[currentSuspicion.initial_urgency] || currentSuspicion.initial_urgency}
                  </p>
                </div>
                <div>
                  <label className="text-sm font-medium text-gray-500">Agente</label>
                  <p className="text-sm text-gray-900">{currentSuspicion.agent_id}</p>
                </div>
              </div>
              {currentSuspicion.initial_notes && (
                <div className="mt-4">
                  <label className="text-sm font-medium text-gray-500">Notas Iniciais</label>
                  <p className="text-sm text-gray-900 mt-1 bg-gray-50 p-3 rounded">
                    {currentSuspicion.initial_notes}
                  </p>
                </div>
              )}
            </div>

            {/* Approach Details */}
            {currentSuspicion.was_approached && (
              <div>
                <h4 className="text-md font-medium text-gray-900 mb-3">Detalhes da Abordagem</h4>
                <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                  <div>
                    <label className="text-sm font-medium text-gray-500">Suspeição Confirmada</label>
                    <div className="flex items-center mt-1">
                      {currentSuspicion.approach_confirmed_suspicion ? (
                        <CheckCircle className="h-5 w-5 text-green-600 mr-2" />
                      ) : (
                        <XCircle className="h-5 w-5 text-red-600 mr-2" />
                      )}
                      <span className="text-sm text-gray-900">
                        {currentSuspicion.approach_confirmed_suspicion ? "Sim" : "Não"}
                      </span>
                    </div>
                  </div>
                  <div>
                    <label className="text-sm font-medium text-gray-500">Nível de Confiança</label>
                    <div className="flex items-center mt-1">
                      <div className="flex-1 bg-gray-200 rounded-full h-2 mr-2">
                        <div
                          className={`h-2 rounded-full ${
                            currentSuspicion.approach_level >= 70
                              ? "bg-red-500"
                              : currentSuspicion.approach_level >= 40
                              ? "bg-yellow-500"
                              : "bg-green-500"
                          }`}
                          style={{ width: `${currentSuspicion.approach_level}%` }}
                        />
                      </div>
                      <span className="text-sm font-medium">{currentSuspicion.approach_level}%</span>
                    </div>
                  </div>
                  <div>
                    <label className="text-sm font-medium text-gray-500">Ocorrência Registrada</label>
                    <div className="flex items-center mt-1">
                      {currentSuspicion.has_incident ? (
                        <AlertTriangle className="h-5 w-5 text-orange-600 mr-2" />
                      ) : (
                        <Shield className="h-5 w-5 text-green-600 mr-2" />
                      )}
                      <span className="text-sm text-gray-900">
                        {currentSuspicion.has_incident ? "Sim" : "Não"}
                      </span>
                    </div>
                  </div>
                  {currentSuspicion.approached_at && (
                    <div>
                      <label className="text-sm font-medium text-gray-500">Data da Abordagem</label>
                      <p className="text-sm text-gray-900">
                        {new Date(currentSuspicion.approached_at).toLocaleString("pt-BR")}
                      </p>
                    </div>
                  )}
                </div>
                {currentSuspicion.approach_notes && (
                  <div className="mt-4">
                    <label className="text-sm font-medium text-gray-500">Notas da Abordagem</label>
                    <p className="text-sm text-gray-900 mt-1 bg-gray-50 p-3 rounded">
                      {currentSuspicion.approach_notes}
                    </p>
                  </div>
                )}
              </div>
            )}

            {/* Evidence */}
            {(currentSuspicion.initial_evidence.length > 0 || currentSuspicion.approach_evidence.length > 0) && (
              <div>
                <h4 className="text-md font-medium text-gray-900 mb-3">Evidências</h4>
                <div className="space-y-4">
                  {currentSuspicion.initial_evidence.length > 0 && (
                    <div>
                      <label className="text-sm font-medium text-gray-500">Evidências Iniciais</label>
                      <div className="mt-2 grid grid-cols-2 md:grid-cols-4 gap-2">
                        {currentSuspicion.initial_evidence.map((evidence) => (
                          <div key={evidence.id} className="border rounded p-2">
                            <div className="flex items-center justify-center mb-1">
                              {evidence.type === "image" && <Image className="h-6 w-6 text-gray-400" />}
                              {evidence.type === "audio" && <Mic className="h-6 w-6 text-gray-400" />}
                              {evidence.type === "document" && <FileText className="h-6 w-6 text-gray-400" />}
                            </div>
                            <p className="text-xs text-gray-500 truncate">{evidence.description}</p>
                          </div>
                        ))}
                      </div>
                    </div>
                  )}
                  {currentSuspicion.approach_evidence.length > 0 && (
                    <div>
                      <label className="text-sm font-medium text-gray-500">Evidências da Abordagem</label>
                      <div className="mt-2 grid grid-cols-2 md:grid-cols-4 gap-2">
                        {currentSuspicion.approach_evidence.map((evidence) => (
                          <div key={evidence.id} className="border rounded p-2">
                            <div className="flex items-center justify-center mb-1">
                              {evidence.type === "image" && <Image className="h-6 w-6 text-gray-400" />}
                              {evidence.type === "audio" && <Mic className="h-6 w-6 text-gray-400" />}
                              {evidence.type === "document" && <FileText className="h-6 w-6 text-gray-400" />}
                            </div>
                            <p className="text-xs text-gray-500 truncate">{evidence.description}</p>
                          </div>
                        ))}
                      </div>
                    </div>
                  )}
                </div>
              </div>
            )}
          </div>
        )}

        {activeTab === "history" && (
          <div className="space-y-4">
            {currentSuspicion.previous_approaches.length === 0 ? (
              <p className="text-gray-500 text-center py-8">Nenhuma abordagem anterior registrada</p>
            ) : (
              currentSuspicion.previous_approaches.map((approach) => (
                <div key={approach.id} className="border rounded-lg p-4">
                  <div className="flex items-start justify-between">
                    <div>
                      <div className="flex items-center">
                        <User className="h-4 w-4 text-gray-400 mr-2" />
                        <span className="text-sm font-medium text-gray-900">{approach.agent_name}</span>
                      </div>
                      <div className="flex items-center mt-1">
                        <Clock className="h-4 w-4 text-gray-400 mr-2" />
                        <span className="text-sm text-gray-500">
                          {new Date(approach.approach_time).toLocaleString("pt-BR")}
                        </span>
                      </div>
                    </div>
                    <div className="flex items-center">
                      {approach.confirmed_suspicion ? (
                        <ThumbsUp className="h-5 w-5 text-green-600" />
                      ) : (
                        <ThumbsDown className="h-5 w-5 text-red-600" />
                      )}
                    </div>
                  </div>
                  <div className="mt-3 grid grid-cols-1 md:grid-cols-3 gap-4">
                    <div>
                      <label className="text-xs font-medium text-gray-500">Nível de Confiança</label>
                      <div className="flex items-center mt-1">
                        <div className="flex-1 bg-gray-200 rounded-full h-2 mr-2">
                          <div
                            className={`h-2 rounded-full ${
                              approach.approach_level >= 70
                                ? "bg-red-500"
                                : approach.approach_level >= 40
                                ? "bg-yellow-500"
                                : "bg-green-500"
                            }`}
                            style={{ width: `${approach.approach_level}%` }}
                          />
                        </div>
                        <span className="text-sm font-medium">{approach.approach_level}%</span>
                      </div>
                    </div>
                    <div>
                      <label className="text-xs font-medium text-gray-500">Ocorrência</label>
                      <p className="text-sm text-gray-900">
                        {approach.has_incident ? (approach.incident_type || "Sim") : "Não"}
                      </p>
                    </div>
                    <div>
                      <label className="text-xs font-medium text-gray-500">Evidências</label>
                      <p className="text-sm text-gray-900">{approach.evidence.length}</p>
                    </div>
                  </div>
                  {approach.notes && (
                    <div className="mt-3">
                      <label className="text-xs font-medium text-gray-500">Notas</label>
                      <p className="text-sm text-gray-900 mt-1 bg-gray-50 p-2 rounded">
                        {approach.notes}
                      </p>
                    </div>
                  )}
                </div>
              ))
            )}
          </div>
        )}

        {activeTab === "feedback" && (
          <div className="space-y-4">
            {/* Feedback Form */}
            <div>
              <label className="text-sm font-medium text-gray-900">Adicionar Feedback</label>
              <div className="mt-2">
                <textarea
                  value={feedbackText}
                  onChange={(e) => setFeedbackText(e.target.value)}
                  placeholder="Digite seu feedback sobre esta suspeição..."
                  className="w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-blue-500 focus:border-blue-500"
                  rows={4}
                />
              </div>
              <div className="mt-2">
                <button
                  onClick={handleFeedbackSubmit}
                  disabled={!feedbackText.trim() || isSubmittingFeedback}
                  className="px-4 py-2 bg-blue-600 text-white text-sm font-medium rounded-md hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed"
                >
                  {isSubmittingFeedback ? "Enviando..." : "Enviar Feedback"}
                </button>
              </div>
            </div>

            {/* Existing Feedback */}
            {context?.agent_feedback && context.agent_feedback.length > 0 && (
              <div>
                <h4 className="text-md font-medium text-gray-900 mb-3">Feedback Anterior</h4>
                <div className="space-y-3">
                  {context.agent_feedback.map((feedback, index) => (
                    <div key={index} className="border rounded-lg p-4">
                      <div className="flex items-start justify-between">
                        <div className="flex items-center">
                          <MessageSquare className="h-4 w-4 text-gray-400 mr-2" />
                          <span className="text-sm font-medium text-gray-900">Analista</span>
                        </div>
                        <span className="text-xs text-gray-500">
                          {new Date(feedback.created_at).toLocaleString("pt-BR")}
                        </span>
                      </div>
                      <p className="text-sm text-gray-900 mt-2">{feedback.feedback_content}</p>
                    </div>
                  ))}
                </div>
              </div>
            )}
          </div>
        )}

        {activeTab === "recommendations" && context?.recommendations && (
          <div className="space-y-4">
            {context.recommendations.length === 0 ? (
              <p className="text-gray-500 text-center py-8">Nenhuma recomendação disponível</p>
            ) : (
              context.recommendations.map((recommendation, index) => (
                <div key={index} className="border rounded-lg p-4">
                  <div className="flex items-start">
                    <TrendingUp className="h-5 w-5 text-blue-600 mr-3 mt-0.5" />
                    <div>
                      <div className="flex items-center">
                        <span className="text-sm font-medium text-gray-900">
                          {recommendation.type.replace("_", " ").toUpperCase()}
                        </span>
                        <span className={`ml-2 px-2 py-1 rounded text-xs font-medium ${
                          recommendation.priority === "high"
                            ? "bg-red-100 text-red-800"
                            : recommendation.priority === "medium"
                            ? "bg-yellow-100 text-yellow-800"
                            : "bg-green-100 text-green-800"
                        }`}>
                          {recommendation.priority}
                        </span>
                      </div>
                      <p className="text-sm text-gray-600 mt-1">{recommendation.reason}</p>
                      <div className="mt-2">
                        <div className="flex items-center">
                          <span className="text-xs text-gray-500 mr-2">Confiança:</span>
                          <div className="flex-1 bg-gray-200 rounded-full h-2 max-w-xs">
                            <div
                              className="bg-blue-500 h-2 rounded-full"
                              style={{ width: `${(recommendation.confidence || 0) * 100}%` }}
                            />
                          </div>
                          <span className="text-xs text-gray-500 ml-2">
                            {Math.round((recommendation.confidence || 0) * 100)}%
                          </span>
                        </div>
                      </div>
                    </div>
                  </div>
                </div>
              ))
            )}
          </div>
        )}
      </div>
    </div>
  );
}

// Hook for unified suspicion management
export function useUnifiedSuspicion() {
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const captureSuspicion = useCallback(async (data: any) => {
    setLoading(true);
    setError(null);

    try {
      const response = await fetch('/api/v1/suspicion/capture', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(data),
      });

      if (!response.ok) {
        throw new Error(`Failed to capture suspicion: ${response.statusText}`);
      }

      const result = await response.json();
      return result;
    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : 'Unknown error';
      setError(errorMessage);
      throw err;
    } finally {
      setLoading(false);
    }
  }, []);

  const confirmApproach = useCallback(async (data: any) => {
    setLoading(true);
    setError(null);

    try {
      const response = await fetch('/api/v1/suspicion/approach', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(data),
      });

      if (!response.ok) {
        throw new Error(`Failed to confirm approach: ${response.statusText}`);
      }

      const result = await response.json();
      return result;
    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : 'Unknown error';
      setError(errorMessage);
      throw err;
    } finally {
      setLoading(false);
    }
  }, []);

  const addFeedback = useCallback(async (suspicionId: string, feedback: string) => {
    setLoading(true);
    setError(null);

    try {
      const response = await fetch('/api/v1/suspicion/feedback', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          suspicion_id: suspicionId,
          feedback_type: "analyst_review",
          feedback_content: feedback,
        }),
      });

      if (!response.ok) {
        throw new Error(`Failed to add feedback: ${response.statusText}`);
      }

      const result = await response.json();
      return result;
    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : 'Unknown error';
      setError(errorMessage);
      throw err;
    } finally {
      setLoading(false);
    }
  }, []);

  return {
    captureSuspicion,
    confirmApproach,
    addFeedback,
    loading,
    error,
  };
}
