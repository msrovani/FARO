"use client";

import React, { useState, useEffect } from "react";
import { X, Info, CheckCircle, AlertCircle, Play, Pause } from "lucide-react";

interface TrainingStep {
  id: string;
  title: string;
  description: string;
  action: string;
  expected: string;
  icon: React.ReactNode;
  difficulty: "easy" | "medium" | "hard";
}

interface UserTrainingProps {
  onComplete: () => void;
  onSkip: () => void;
}

export default function OSMUserTraining({ onComplete, onSkip }: UserTrainingProps) {
  const [currentStep, setCurrentStep] = useState(0);
  const [isPlaying, setIsPlaying] = useState(false);
  const [completedSteps, setCompletedSteps] = useState<Set<string>>(new Set());
  const [showHint, setShowHint] = useState(false);
  const [trainingProgress, setTrainingProgress] = useState(0);

  const trainingSteps: TrainingStep[] = [
    {
      id: "welcome",
      title: "Bem-vindo ao OpenStreetMap",
      description: "O F.A.R.O. agora usa OpenStreetMap, um sistema de mapas de código aberto e gratuito.",
      action: "Clique em 'Próximo' para continuar",
      expected: "Usuário avança para o próximo passo",
      icon: <Info className="w-6 h-6 text-blue-500" />,
      difficulty: "easy"
    },
    {
      id: "navigation",
      title: "Navegação Básica",
      description: "Use o mouse para navegar: clique e arraste para mover, scroll para zoom.",
      action: "Tente mover o mapa e dar zoom",
      expected: "Usuário consegue navegar no mapa",
      icon: <Play className="w-6 h-6 text-green-500" />,
      difficulty: "easy"
    },
    {
      id: "controls",
      title: "Controles do Mapa",
      description: "Use os controles no canto superior direito para zoom preciso e o controle de escala no canto inferior esquerdo.",
      action: "Experimente os controles de zoom e escala",
      expected: "Usuário usa os controles do mapa",
      icon: <CheckCircle className="w-6 h-6 text-green-500" />,
      difficulty: "easy"
    },
    {
      id: "layers",
      title: "Camadas do Mapa",
      description: "OpenStreetMap oferece dados de ruas, edifícios e pontos de interesse atualizados pela comunidade.",
      action: "Explore diferentes áreas do mapa para ver os detalhes",
      expected: "Usuário explora o mapa",
      icon: <Info className="w-6 h-6 text-blue-500" />,
      difficulty: "medium"
    },
    {
      id: "performance",
      title: "Otimização de Performance",
      description: "O sistema usa cache agressivo para carregamento rápido. Tiles são pré-carregados para áreas táticas.",
      action: "Navegue para áreas diferentes e note a velocidade",
      expected: "Usuário percebe o carregamento rápido",
      icon: <CheckCircle className="w-6 h-6 text-green-500" />,
      difficulty: "medium"
    },
    {
      id: "tactical",
      title: "Modo Tático",
      description: "O mapa está otimizado para uso operacional com cores de alto contraste e interface limpa.",
      action: "Observe o estilo escuro e controles visíveis",
      expected: "Usuário reconhece o modo tático",
      icon: <AlertCircle className="w-6 h-6 text-orange-500" />,
      difficulty: "medium"
    },
    {
      id: "offline",
      title: "Modo Offline",
      description: "Tiles são cacheados para uso offline, essencial para operações em áreas sem conexão.",
      action: "Desconecte da internet e tente usar o mapa",
      expected: "Usuário entende o modo offline",
      icon: <CheckCircle className="w-6 h-6 text-green-500" />,
      difficulty: "hard"
    },
    {
      id: "comparison",
      title: "Comparação com Anterior",
      description: "Compare a velocidade e funcionalidade com o sistema anterior.",
      action: "Use o mapa e avalie a experiência",
      expected: "Usuário faz a comparação",
      icon: <Info className="w-6 h-6 text-blue-500" />,
      difficulty: "medium"
    },
    {
      id: "troubleshooting",
      title: "Solução de Problemas",
      description: "Se o mapa não carregar, verifique a conexão ou limpe o cache com F5.",
      action: "Memorize as soluções de problemas comuns",
      expected: "Usuário sabe resolver problemas",
      icon: <AlertCircle className="w-6 h-6 text-orange-500" />,
      difficulty: "medium"
    },
    {
      id: "completion",
      title: "Treinamento Concluído",
      description: "Parabéns! Você agora está familiarizado com o novo sistema de mapas OpenStreetMap.",
      action: "Clique em 'Concluir' para finalizar",
      expected: "Usuário finaliza o treinamento",
      icon: <CheckCircle className="w-6 h-6 text-green-500" />,
      difficulty: "easy"
    }
  ];

  const currentStepData = trainingSteps[currentStep];

  useEffect(() => {
    const progress = (completedSteps.size / trainingSteps.length) * 100;
    setTrainingProgress(progress);
  }, [completedSteps]);

  const handleNext = () => {
    if (currentStep < trainingSteps.length - 1) {
      setCurrentStep(currentStep + 1);
      setShowHint(false);
    } else {
      onComplete();
    }
  };

  const handlePrevious = () => {
    if (currentStep > 0) {
      setCurrentStep(currentStep - 1);
      setShowHint(false);
    }
  };

  const handleCompleteStep = () => {
    setCompletedSteps(prev => new Set(prev).add(currentStepData.id));
  };

  const getDifficultyColor = (difficulty: string) => {
    switch (difficulty) {
      case "easy": return "text-green-600 bg-green-100";
      case "medium": return "text-yellow-600 bg-yellow-100";
      case "hard": return "text-red-600 bg-red-100";
      default: return "text-gray-600 bg-gray-100";
    }
  };

  const getDifficultyText = (difficulty: string) => {
    switch (difficulty) {
      case "easy": return "Fácil";
      case "medium": return "Médio";
      case "hard": return "Difícil";
      default: return "Desconhecido";
    }
  };

  if (!isPlaying) {
    return (
      <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
        <div className="bg-white rounded-lg p-8 max-w-md w-full mx-4">
          <div className="text-center">
            <div className="mb-6">
              <div className="w-16 h-16 bg-blue-100 rounded-full flex items-center justify-center mx-auto mb-4">
                <Info className="w-8 h-8 text-blue-600" />
              </div>
              <h2 className="text-2xl font-bold text-gray-900 mb-2">
                Treinamento OpenStreetMap
              </h2>
              <p className="text-gray-600">
                Aprenda a usar o novo sistema de mapas do F.A.R.O.
              </p>
            </div>
            
            <div className="mb-6">
              <div className="bg-blue-50 rounded-lg p-4">
                <h3 className="font-semibold text-blue-900 mb-2">O que você aprenderá:</h3>
                <ul className="text-sm text-blue-800 space-y-1">
                  <li>• Navegação básica e avançada</li>
                  <li>• Uso dos controles do mapa</li>
                  <li>• Funcionalidades táticas</li>
                  <li>• Modo offline e cache</li>
                  <li>• Solução de problemas</li>
                </ul>
              </div>
            </div>
            
            <div className="mb-6">
              <div className="bg-gray-100 rounded-lg p-4">
                <div className="flex justify-between text-sm text-gray-600 mb-2">
                  <span>Duração estimada:</span>
                  <span>5-10 minutos</span>
                </div>
                <div className="flex justify-between text-sm text-gray-600">
                  <span>Nível de dificuldade:</span>
                  <span>Iniciante</span>
                </div>
              </div>
            </div>
            
            <div className="flex gap-3">
              <button
                onClick={() => setIsPlaying(true)}
                className="flex-1 bg-blue-600 text-white py-3 px-4 rounded-lg font-medium hover:bg-blue-700 transition-colors"
              >
                Começar Treinamento
              </button>
              <button
                onClick={onSkip}
                className="px-4 py-3 border border-gray-300 rounded-lg font-medium hover:bg-gray-50 transition-colors"
              >
                Pular
              </button>
            </div>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
      <div className="bg-white rounded-lg p-6 max-w-2xl w-full mx-4 max-h-[90vh] overflow-y-auto">
        {/* Header */}
        <div className="flex justify-between items-start mb-6">
          <div className="flex-1">
            <h2 className="text-2xl font-bold text-gray-900 mb-2">
              Treinamento OpenStreetMap
            </h2>
            <div className="flex items-center gap-4 text-sm text-gray-600">
              <span>Passo {currentStep + 1} de {trainingSteps.length}</span>
              <span className={`px-2 py-1 rounded-full text-xs font-medium ${getDifficultyColor(currentStepData.difficulty)}`}>
                {getDifficultyText(currentStepData.difficulty)}
              </span>
            </div>
          </div>
          <button
            onClick={onSkip}
            className="text-gray-400 hover:text-gray-600"
          >
            <X className="w-6 h-6" />
          </button>
        </div>

        {/* Progress Bar */}
        <div className="mb-6">
          <div className="bg-gray-200 rounded-full h-2">
            <div
              className="bg-blue-600 h-2 rounded-full transition-all duration-300"
              style={{ width: `${trainingProgress}%` }}
            />
          </div>
          <div className="flex justify-between text-xs text-gray-600 mt-1">
            <span>{Math.round(trainingProgress)}% completo</span>
            <span>{completedSteps.size} de {trainingSteps.length} passos concluídos</span>
          </div>
        </div>

        {/* Step Content */}
        <div className="mb-6">
          <div className="flex items-start gap-4 mb-4">
            <div className="flex-shrink-0">
              {currentStepData.icon}
            </div>
            <div className="flex-1">
              <h3 className="text-lg font-semibold text-gray-900 mb-2">
                {currentStepData.title}
              </h3>
              <p className="text-gray-600 mb-4">
                {currentStepData.description}
              </p>
              
              <div className="bg-blue-50 border border-blue-200 rounded-lg p-4">
                <h4 className="font-medium text-blue-900 mb-1">Ação necessária:</h4>
                <p className="text-blue-800">{currentStepData.action}</p>
                <p className="text-blue-600 text-sm mt-1">Esperado: {currentStepData.expected}</p>
              </div>
            </div>
          </div>
        </div>

        {/* Hint Section */}
        {showHint && (
          <div className="mb-6">
            <div className="bg-yellow-50 border border-yellow-200 rounded-lg p-4">
              <div className="flex items-start gap-2">
                <AlertCircle className="w-5 h-5 text-yellow-600 flex-shrink-0 mt-0.5" />
                <div>
                  <h4 className="font-medium text-yellow-900 mb-1">Dica:</h4>
                  <p className="text-yellow-800 text-sm">
                    {currentStepData.id === "navigation" && "Use o botão esquerdo do mouse para clicar e arrastar. Use o scroll do mouse para dar zoom."}
                    {currentStepData.id === "controls" && "Os controles estão nos cantos do mapa. Experimente clicar nos botões de + e -."}
                    {currentStepData.id === "layers" && "Tente navegar para diferentes cidades ou áreas para ver os detalhes do mapa."}
                    {currentStepData.id === "performance" && "Navegue rapidamente entre diferentes áreas e note como os tiles carregam instantaneamente."}
                    {currentStepData.id === "tactical" && "Observe as cores escuras e o contraste elevado, ideais para uso em ambientes operacionais."}
                    {currentStepData.id === "offline" && "Desconecte da internet e navegue para áreas que você já visitou."}
                    {currentStepData.id === "comparison" && "Compare a velocidade, clareza e funcionalidades com o sistema anterior."}
                    {currentStepData.id === "troubleshooting" && "Se o mapa não carregar, tente recarregar a página (F5) ou verificar a conexão."}
                    {currentStepData.id === "completion" && "Você concluiu o treinamento! Está pronto para usar o novo sistema."}
                  </p>
                </div>
              </div>
            </div>
          </div>
        )}

        {/* Action Buttons */}
        <div className="flex gap-3 mb-4">
          <button
            onClick={handlePrevious}
            disabled={currentStep === 0}
            className="px-4 py-2 border border-gray-300 rounded-lg font-medium hover:bg-gray-50 transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
          >
            Anterior
          </button>
          
          <button
            onClick={() => setShowHint(!showHint)}
            className="px-4 py-2 border border-yellow-300 bg-yellow-50 text-yellow-700 rounded-lg font-medium hover:bg-yellow-100 transition-colors"
          >
            {showHint ? "Ocultar Dica" : "Mostrar Dica"}
          </button>
          
          <button
            onClick={handleCompleteStep}
            disabled={completedSteps.has(currentStepData.id)}
            className="px-4 py-2 border border-green-300 bg-green-50 text-green-700 rounded-lg font-medium hover:bg-green-100 transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
          >
            {completedSteps.has(currentStepData.id) ? "Concluído" : "Marcar como Concluído"}
          </button>
          
          <button
            onClick={handleNext}
            className="flex-1 bg-blue-600 text-white py-2 px-4 rounded-lg font-medium hover:bg-blue-700 transition-colors"
          >
            {currentStep === trainingSteps.length - 1 ? "Concluir" : "Próximo"}
          </button>
        </div>

        {/* Skip Option */}
        <div className="text-center">
          <button
            onClick={onSkip}
            className="text-sm text-gray-500 hover:text-gray-700"
          >
            Pular treinamento
          </button>
        </div>
      </div>
    </div>
  );
}
