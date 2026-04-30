"use client";

import React, { useState, useEffect } from "react";
import { MessageCircle, CheckCircle, XCircle, Clock, User, AlertTriangle } from "lucide-react";
import { mobileApi } from "@/app/services/mobileApi";
import { FeedbackForAgent } from "@/app/types";

interface ObservationFeedbackProps {
  observationId: string;
  plateNumber: string;
}

export default function ObservationFeedback({ observationId, plateNumber }: ObservationFeedbackProps) {
  const [feedbacks, setFeedbacks] = useState<FeedbackForAgent[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const loadFeedbacks = async () => {
      try {
        setLoading(true);
        setError(null);
        const data = await mobileApi.getFeedback(observationId);
        setFeedbacks(data);
      } catch (err) {
        console.error("Failed to load feedbacks:", err);
        setError("Não foi possível carregar feedbacks.");
      } finally {
        setLoading(false);
      }
    };

    if (observationId) {
      loadFeedbacks();
    }
  }, [observationId]);

  const getFeedbackIcon = (feedbackType: string) => {
    switch (feedbackType) {
      case "confirmation":
        return <CheckCircle className="text-green-500" size={16} />;
      case "rejection":
        return <XCircle className="text-red-500" size={16} />;
      case "information":
        return <AlertTriangle className="text-yellow-500" size={16} />;
      default:
        return <MessageCircle className="text-blue-500" size={16} />;
    }
  };

  const getFeedbackColor = (feedbackType: string) => {
    switch (feedbackType) {
      case "confirmation":
        return "border-green-500 bg-green-50";
      case "rejection":
        return "border-red-500 bg-red-50";
      case "information":
        return "border-yellow-500 bg-yellow-50";
      default:
        return "border-blue-500 bg-blue-50";
    }
  };

  if (loading) {
    return (
      <div className="bg-white rounded-lg p-4 shadow-sm">
        <div className="animate-pulse">
          <div className="h-4 bg-gray-200 rounded w-3/4 mb-2"></div>
          <div className="h-4 bg-gray-200 rounded w-1/2 mb-2"></div>
          <div className="h-4 bg-gray-200 rounded w-2/3"></div>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="bg-white rounded-lg p-4 shadow-sm border border-red-200">
        <div className="flex items-center gap-2 text-red-600">
          <XCircle size={16} />
          <span className="text-sm">{error}</span>
        </div>
      </div>
    );
  }

  if (feedbacks.length === 0) {
    return (
      <div className="bg-white rounded-lg p-4 shadow-sm">
        <div className="flex items-center gap-2 text-gray-500">
          <MessageCircle size={16} />
          <span className="text-sm">Nenhum feedback recebido para esta observação</span>
        </div>
      </div>
    );
  }

  return (
    <div className="bg-white rounded-lg shadow-sm">
      <div className="p-4 border-b border-gray-200">
        <h3 className="text-lg font-semibold text-gray-900 flex items-center gap-2">
          <MessageCircle className="text-blue-600" size={20} />
          Feedback da Inteligência
        </h3>
        <p className="text-sm text-gray-600 mt-1">
          Placa: <span className="font-mono font-semibold">{plateNumber}</span>
        </p>
      </div>

      <div className="divide-y divide-gray-200">
        {feedbacks.map((feedback, index) => (
          <div key={feedback.feedback_id} className="p-4">
            <div className="flex items-start gap-3">
              <div className={`p-2 rounded-full border ${getFeedbackColor(feedback.feedback_type)}`}>
                {getFeedbackIcon(feedback.feedback_type)}
              </div>
              
              <div className="flex-1 min-w-0">
                <div className="flex items-center justify-between mb-2">
                  <h4 className="font-medium text-gray-900">
                    {feedback.title}
                  </h4>
                  <div className="flex items-center gap-1 text-xs text-gray-500">
                    <Clock size={12} />
                    {new Date(feedback.sent_at).toLocaleString()}
                  </div>
                </div>

                <p className="text-sm text-gray-700 mb-3">
                  {feedback.message}
                </p>

                {feedback.recommended_action && (
                  <div className="bg-blue-50 border border-blue-200 rounded-lg p-3 mb-3">
                    <h5 className="font-medium text-blue-900 mb-1 text-sm">
                      Ação Recomendada:
                    </h5>
                    <p className="text-sm text-blue-800">
                      {feedback.recommended_action}
                    </p>
                  </div>
                )}

                <div className="flex items-center justify-between text-xs text-gray-500">
                  <div className="flex items-center gap-1">
                    <User size={12} />
                    <span>Analista: {feedback.reviewer_name}</span>
                  </div>
                  
                  <div className="flex items-center gap-2">
                    <span>Status: {feedback.is_read ? "Lido" : "Não lido"}</span>
                    {feedback.read_at && (
                      <span>em {new Date(feedback.read_at).toLocaleString()}</span>
                    )}
                  </div>
                </div>
              </div>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}
