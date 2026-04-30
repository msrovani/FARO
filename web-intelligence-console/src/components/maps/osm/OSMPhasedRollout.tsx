"use client";

import React, { useState, useEffect } from "react";
import { CheckCircle, AlertCircle, Users, Settings, Activity, Shield } from "lucide-react";

interface RolloutPhase {
  id: string;
  name: string;
  description: string;
  percentage: number;
  users: number;
  features: string[];
  status: "pending" | "active" | "completed";
  requirements: string[];
  risks: string[];
  benefits: string[];
}

interface RolloutConfig {
  currentPhase: string;
  totalUsers: number;
  rolloutSpeed: "slow" | "medium" | "fast";
  monitoringEnabled: boolean;
  rollbackEnabled: boolean;
}

export default function OSMPhasedRollout() {
  const [config, setConfig] = useState<RolloutConfig>({
    currentPhase: "beta",
    totalUsers: 1000,
    rolloutSpeed: "medium",
    monitoringEnabled: true,
    rollbackEnabled: true,
  });

  const [phases, setPhases] = useState<RolloutPhase[]>([
    {
      id: "alpha",
      name: "Alpha Test",
      description: "Teste interno com equipe de desenvolvimento",
      percentage: 5,
      users: 50,
      features: [
        "Mapa OpenStreetMap básico",
        "Navegação e zoom",
        "Cache de tiles",
        "Controles básicos",
      ],
      status: "completed",
      requirements: [
        "Equipe de desenvolvimento",
        "Ambiente de teste isolado",
        "Monitoramento de performance",
      ],
      risks: [
        "Bugs críticos",
        "Instabilidade",
        "Performance issues",
      ],
      benefits: [
        "Feedback rápido",
        "Correções imediatas",
        "Risco controlado",
      ],
    },
    {
      id: "beta",
      name: "Beta Test",
      description: "Teste com usuários selecionados (agentes de campo)",
      percentage: 15,
      users: 150,
      features: [
        "Mapa OpenStreetMap completo",
        "Modo tático",
        "Cache agressivo",
        "Modo offline básico",
        "Treinamento integrado",
      ],
      status: "active",
      requirements: [
        "Usuários voluntários",
        "Sistema de feedback",
        "Monitoramento em tempo real",
        "Plano de rollback",
      ],
      risks: [
        "Problemas de usabilidade",
        "Performance em campo",
        "Adoção inicial",
      ],
      benefits: [
        "Feedback real de campo",
        "Validação operacional",
        "Identificação de edge cases",
      ],
    },
    {
      id: "gamma",
      name: "Gamma Release",
      description: "Lançamento para todos os agentes de campo",
      percentage: 40,
      users: 400,
      features: [
        "Todas as funcionalidades beta",
        "Modo offline completo",
        "Sincronização avançada",
        "Alertas contextuais",
      ],
      status: "pending",
      requirements: [
        "Sucesso validado em beta",
        "Documentação completa",
        "Suporte técnico preparado",
        "Capacidade de servidor",
      ],
      risks: [
        "Sobrecarga de servidor",
        "Problemas de escalabilidade",
        "Resistência à mudança",
      ],
      benefits: [
        "Cobertura ampliada",
        "Feedback em escala",
        "Otimização de performance",
      ],
    },
    {
      id: "production",
      name: "Production Release",
      description: "Lançamento completo para todos os usuários",
      percentage: 100,
      users: 1000,
      features: [
        "Sistema completo",
        "Personalização avançada",
        "Integração total",
        "Analytics completo",
      ],
      status: "pending",
      requirements: [
        "Validação completa",
        "Performance estável",
        "Documentação final",
        "Treinamento completo",
      ],
      risks: [
        "Problemas em produção",
        "Impacto operacional",
        "Rejeição do sistema",
      ],
      benefits: [
        "Adoção completa",
        "Economia de custos",
        "Independência de vendor",
        "Sistema estável",
      ],
    },
  ]);

  const [metrics, setMetrics] = useState({
    userSatisfaction: 0,
    performanceScore: 0,
    bugReports: 0,
    featureRequests: 0,
    systemUptime: 100,
  });

  // Simulate metrics updates
  useEffect(() => {
    const interval = setInterval(() => {
      setMetrics(prev => ({
        ...prev,
        userSatisfaction: Math.min(100, prev.userSatisfaction + Math.random() * 5),
        performanceScore: Math.min(100, prev.performanceScore + Math.random() * 3),
        bugReports: Math.max(0, prev.bugReports + Math.floor(Math.random() * 3 - 1)),
        systemUptime: Math.max(95, prev.systemUptime + (Math.random() * 2 - 1)),
      }));
    }, 3000);

    return () => clearInterval(interval);
  }, []);

  const getCurrentPhase = () => {
    return phases.find(phase => phase.id === config.currentPhase) || phases[0];
  };

  const canAdvanceToNextPhase = (phaseId: string) => {
    const phaseIndex = phases.findIndex(phase => phase.id === phaseId);
    return phaseIndex < phases.length - 1;
  };

  const advancePhase = () => {
    const currentPhaseIndex = phases.findIndex(phase => phase.id === config.currentPhase);
    if (currentPhaseIndex < phases.length - 1) {
      const nextPhase = phases[currentPhaseIndex + 1];
      
      // Update current phase status to completed
      setPhases(prev => prev.map(phase => 
        phase.id === config.currentPhase 
          ? { ...phase, status: "completed" as const }
          : phase
      ));
      
      // Set next phase as active
      setPhases(prev => prev.map(phase => 
        phase.id === nextPhase.id 
          ? { ...phase, status: "active" as const }
          : phase
      ));
      
      setConfig(prev => ({ ...prev, currentPhase: nextPhase.id }));
    }
  };

  const rollbackPhase = () => {
    const currentPhaseIndex = phases.findIndex(phase => phase.id === config.currentPhase);
    if (currentPhaseIndex > 0) {
      const previousPhase = phases[currentPhaseIndex - 1];
      
      setPhases(prev => prev.map(phase => 
        phase.id === config.currentPhase 
          ? { ...phase, status: "pending" as const }
          : phase.id === previousPhase.id 
          ? { ...phase, status: "active" as const }
          : phase
      ));
      
      setConfig(prev => ({ ...prev, currentPhase: previousPhase.id }));
    }
  };

  const getStatusColor = (status: string) => {
    switch (status) {
      case "completed": return "text-green-600 bg-green-100";
      case "active": return "text-blue-600 bg-blue-100";
      case "pending": return "text-gray-600 bg-gray-100";
      default: return "text-gray-600 bg-gray-100";
    }
  };

  const getStatusText = (status: string) => {
    switch (status) {
      case "completed": return "Concluído";
      case "active": return "Ativo";
      case "pending": return "Pendente";
      default: return "Desconhecido";
    }
  };

  const getSpeedMultiplier = () => {
    switch (config.rolloutSpeed) {
      case "slow": return 0.5;
      case "medium": return 1;
      case "fast": return 2;
      default: return 1;
    }
  };

  const currentPhase = getCurrentPhase();

  return (
    <div className="p-6 bg-white rounded-lg shadow-lg">
      <div className="mb-6">
        <h2 className="text-2xl font-bold text-gray-900 mb-2">
          Migração OpenStreetMap - Rollout Controlado
        </h2>
        <p className="text-gray-600">
          Gerenciamento de migração faseada para minimizar impacto operacional
        </p>
      </div>

      {/* Current Configuration */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mb-6">
        <div className="bg-blue-50 rounded-lg p-4">
          <div className="flex items-center gap-2 mb-2">
            <Settings className="w-5 h-5 text-blue-600" />
            <h3 className="font-medium text-blue-900">Configuração Atual</h3>
          </div>
          <div className="space-y-1 text-sm">
            <div className="flex justify-between">
              <span className="text-blue-700">Fase Atual:</span>
              <span className="font-medium">{currentPhase.name}</span>
            </div>
            <div className="flex justify-between">
              <span className="text-blue-700">Usuários:</span>
              <span className="font-medium">{currentPhase.users}</span>
            </div>
            <div className="flex justify-between">
              <span className="text-blue-700">Velocidade:</span>
              <span className="font-medium capitalize">{config.rolloutSpeed}</span>
            </div>
          </div>
        </div>

        <div className="bg-green-50 rounded-lg p-4">
          <div className="flex items-center gap-2 mb-2">
            <Activity className="w-5 h-5 text-green-600" />
            <h3 className="font-medium text-green-900">Métricas</h3>
          </div>
          <div className="space-y-1 text-sm">
            <div className="flex justify-between">
              <span className="text-green-700">Satisfação:</span>
              <span className="font-medium">{metrics.userSatisfaction.toFixed(1)}%</span>
            </div>
            <div className="flex justify-between">
              <span className="text-green-700">Performance:</span>
              <span className="font-medium">{metrics.performanceScore.toFixed(1)}%</span>
            </div>
            <div className="flex justify-between">
              <span className="text-green-700">Uptime:</span>
              <span className="font-medium">{metrics.systemUptime.toFixed(1)}%</span>
            </div>
          </div>
        </div>

        <div className="bg-orange-50 rounded-lg p-4">
          <div className="flex items-center gap-2 mb-2">
            <AlertCircle className="w-5 h-5 text-orange-600" />
            <h3 className="font-medium text-orange-900">Alertas</h3>
          </div>
          <div className="space-y-1 text-sm">
            <div className="flex justify-between">
              <span className="text-orange-700">Bug Reports:</span>
              <span className="font-medium">{metrics.bugReports}</span>
            </div>
            <div className="flex justify-between">
              <span className="text-orange-700">Feature Requests:</span>
              <span className="font-medium">{metrics.featureRequests}</span>
            </div>
            <div className="flex justify-between">
              <span className="text-orange-700">Rollback:</span>
              <span className="font-medium">{config.rollbackEnabled ? "Ativo" : "Inativo"}</span>
            </div>
          </div>
        </div>
      </div>

      {/* Phase Timeline */}
      <div className="mb-6">
        <h3 className="text-lg font-semibold text-gray-900 mb-4">Timeline de Fases</h3>
        <div className="relative">
          <div className="absolute left-8 top-0 bottom-0 w-0.5 bg-gray-300"></div>
          
          {phases.map((phase, index) => (
            <div key={phase.id} className="relative flex items-start mb-6">
              <div className={`w-16 h-16 rounded-full flex items-center justify-center z-10 ${
                phase.status === "completed" ? "bg-green-500" :
                phase.status === "active" ? "bg-blue-500" : "bg-gray-300"
              }`}>
                {phase.status === "completed" ? (
                  <CheckCircle className="w-8 h-8 text-white" />
                ) : phase.status === "active" ? (
                  <Activity className="w-8 h-8 text-white" />
                ) : (
                  <Users className="w-8 h-8 text-gray-500" />
                )}
              </div>
              
              <div className="ml-6 flex-1">
                <div className="bg-white border rounded-lg p-4">
                  <div className="flex justify-between items-start mb-2">
                    <div>
                      <h4 className="font-semibold text-gray-900">{phase.name}</h4>
                      <p className="text-sm text-gray-600">{phase.description}</p>
                    </div>
                    <span className={`px-2 py-1 rounded-full text-xs font-medium ${getStatusColor(phase.status)}`}>
                      {getStatusText(phase.status)}
                    </span>
                  </div>
                  
                  <div className="grid grid-cols-1 md:grid-cols-3 gap-4 text-sm">
                    <div>
                      <span className="font-medium text-gray-700">Usuários:</span>
                      <span className="ml-2">{phase.users} ({phase.percentage}%)</span>
                    </div>
                    <div>
                      <span className="font-medium text-gray-700">Features:</span>
                      <span className="ml-2">{phase.features.length}</span>
                    </div>
                    <div>
                      <span className="font-medium text-gray-700">Riscos:</span>
                      <span className="ml-2">{phase.risks.length}</span>
                    </div>
                  </div>
                  
                  {phase.status === "active" && (
                    <div className="mt-3 pt-3 border-t">
                      <div className="flex flex-wrap gap-1">
                        {phase.features.map((feature, idx) => (
                          <span key={idx} className="px-2 py-1 bg-blue-100 text-blue-700 text-xs rounded">
                            {feature}
                          </span>
                        ))}
                      </div>
                    </div>
                  )}
                </div>
              </div>
            </div>
          ))}
        </div>
      </div>

      {/* Current Phase Details */}
      <div className="mb-6">
        <h3 className="text-lg font-semibold text-gray-900 mb-4">
          Detalhes da Fase Atual: {currentPhase.name}
        </h3>
        
        <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
          <div>
            <h4 className="font-medium text-gray-900 mb-3">Features Implementados</h4>
            <div className="space-y-2">
              {currentPhase.features.map((feature, idx) => (
                <div key={idx} className="flex items-center gap-2">
                  <CheckCircle className="w-4 h-4 text-green-500" />
                  <span className="text-sm text-gray-700">{feature}</span>
                </div>
              ))}
            </div>
          </div>
          
          <div>
            <h4 className="font-medium text-gray-900 mb-3">Riscos e Mitigações</h4>
            <div className="space-y-2">
              {currentPhase.risks.map((risk, idx) => (
                <div key={idx} className="flex items-start gap-2">
                  <AlertCircle className="w-4 h-4 text-orange-500 flex-shrink-0 mt-0.5" />
                  <span className="text-sm text-gray-700">{risk}</span>
                </div>
              ))}
            </div>
          </div>
        </div>
      </div>

      {/* Control Actions */}
      <div className="flex gap-3">
        {config.rollbackEnabled && (
          <button
            onClick={rollbackPhase}
            disabled={currentPhase.id === "alpha"}
            className="px-4 py-2 border border-red-300 bg-red-50 text-red-700 rounded-lg font-medium hover:bg-red-100 transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
          >
            Rollback
          </button>
        )}
        
        <button
          onClick={advancePhase}
          disabled={!canAdvanceToNextPhase(config.currentPhase)}
          className="px-4 py-2 bg-blue-600 text-white rounded-lg font-medium hover:bg-blue-700 transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
        >
          Avançar Fase
        </button>
        
        <div className="flex-1 flex items-center justify-end gap-4">
          <label className="flex items-center gap-2">
            <input
              type="checkbox"
              checked={config.monitoringEnabled}
              onChange={(e) => setConfig(prev => ({ ...prev, monitoringEnabled: e.target.checked }))}
              className="rounded"
            />
            <span className="text-sm text-gray-700">Monitoramento</span>
          </label>
          
          <label className="flex items-center gap-2">
            <input
              type="checkbox"
              checked={config.rollbackEnabled}
              onChange={(e) => setConfig(prev => ({ ...prev, rollbackEnabled: e.target.checked }))}
              className="rounded"
            />
            <span className="text-sm text-gray-700">Rollback</span>
          </label>
          
          <select
            value={config.rolloutSpeed}
            onChange={(e) => setConfig(prev => ({ ...prev, rolloutSpeed: e.target.value as any }))}
            className="px-3 py-1 border rounded text-sm"
          >
            <option value="slow">Lento</option>
            <option value="medium">Médio</option>
            <option value="fast">Rápido</option>
          </select>
        </div>
      </div>
    </div>
  );
}
