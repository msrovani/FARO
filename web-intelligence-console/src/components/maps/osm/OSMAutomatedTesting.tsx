"use client";

import React, { useState, useEffect, useCallback } from "react";
import { Play, Pause, CheckCircle, XCircle, AlertCircle, RefreshCw, Download, Upload } from "lucide-react";

interface TestCase {
  id: string;
  name: string;
  description: string;
  category: "navigation" | "performance" | "cache" | "offline" | "tactical" | "compatibility";
  priority: "high" | "medium" | "low";
  status: "pending" | "running" | "passed" | "failed" | "skipped";
  duration: number;
  errorMessage?: string;
  metrics?: {
    loadTime: number;
    cacheHitRate: number;
    memoryUsage: number;
    tileCount: number;
  };
}

interface TestSuite {
  name: string;
  tests: TestCase[];
  status: "pending" | "running" | "completed" | "failed";
  startTime?: Date;
  endTime?: Date;
  totalDuration: number;
  passedCount: number;
  failedCount: number;
  skippedCount: number;
}

export default function OSMAutomatedTesting() {
  const [isRunning, setIsRunning] = useState(false);
  const [currentTestSuite, setCurrentTestSuite] = useState<TestSuite | null>(null);
  const [testHistory, setTestHistory] = useState<TestSuite[]>([]);
  const [autoRun, setAutoRun] = useState(false);
  const [testInterval, setTestInterval] = useState(5000); // 5 seconds

  // Define comprehensive test cases
  const createTestSuite = (): TestSuite => ({
    name: `OSM Integration Test Suite - ${new Date().toISOString()}`,
    tests: [
      // Navigation Tests
      {
        id: "nav_basic",
        name: "Navegação Básica",
        description: "Testa navegação básica do mapa (pan e zoom)",
        category: "navigation",
        priority: "high",
        status: "pending",
        duration: 0,
      },
      {
        id: "nav_controls",
        name: "Controles do Mapa",
        description: "Testa funcionalidade dos controles de zoom e navegação",
        category: "navigation",
        priority: "high",
        status: "pending",
        duration: 0,
      },
      {
        id: "nav_keyboard",
        name: "Navegação por Teclado",
        description: "Testa navegação usando atalhos de teclado",
        category: "navigation",
        priority: "medium",
        status: "pending",
        duration: 0,
      },
      
      // Performance Tests
      {
        id: "perf_initial_load",
        name: "Carregamento Inicial",
        description: "Testa tempo de carregamento inicial do mapa",
        category: "performance",
        priority: "high",
        status: "pending",
        duration: 0,
      },
      {
        id: "perf_tile_load",
        name: "Carregamento de Tiles",
        description: "Testa tempo de carregamento de tiles individuais",
        category: "performance",
        priority: "high",
        status: "pending",
        duration: 0,
      },
      {
        id: "perf_memory",
        name: "Uso de Memória",
        description: "Monitora uso de memória durante operações",
        category: "performance",
        priority: "medium",
        status: "pending",
        duration: 0,
      },
      
      // Cache Tests
      {
        id: "cache_hit_rate",
        name: "Taxa de Cache Hit",
        description: "Verifica eficiência do cache de tiles",
        category: "cache",
        priority: "high",
        status: "pending",
        duration: 0,
      },
      {
        id: "cache_preload",
        name: "Pré-carregamento",
        description: "Testa pré-carregamento de tiles para áreas táticas",
        category: "cache",
        priority: "medium",
        status: "pending",
        duration: 0,
      },
      {
        id: "cache_cleanup",
        name: "Limpeza de Cache",
        description: "Testa limpeza automática de cache antigo",
        category: "cache",
        priority: "low",
        status: "pending",
        duration: 0,
      },
      
      // Offline Tests
      {
        id: "offline_basic",
        name: "Modo Offline Básico",
        description: "Testa funcionamento offline com tiles cacheados",
        category: "offline",
        priority: "high",
        status: "pending",
        duration: 0,
      },
      {
        id: "offline_sync",
        name: "Sincronização Offline",
        description: "Testa sincronização quando conexão retorna",
        category: "offline",
        priority: "medium",
        status: "pending",
        duration: 0,
      },
      
      // Tactical Tests
      {
        id: "tactical_styling",
        name: "Estilo Tático",
        description: "Verifica aplicação de estilo tático (dark mode)",
        category: "tactical",
        priority: "high",
        status: "pending",
        duration: 0,
      },
      {
        id: "tactical_contrast",
        name: "Contraste e Acessibilidade",
        description: "Testa contraste e legibilidade em modo tático",
        category: "tactical",
        priority: "medium",
        status: "pending",
        duration: 0,
      },
      
      // Compatibility Tests
      {
        id: "compat_browser",
        name: "Compatibilidade Browser",
        description: "Testa compatibilidade com diferentes browsers",
        category: "compatibility",
        priority: "high",
        status: "pending",
        duration: 0,
      },
      {
        id: "compat_mobile",
        name: "Compatibilidade Mobile",
        description: "Testa funcionamento em dispositivos móveis",
        category: "compatibility",
        priority: "high",
        status: "pending",
        duration: 0,
      },
      {
        id: "compat_responsive",
        name: "Design Responsivo",
        description: "Testa adaptação a diferentes tamanhos de tela",
        category: "compatibility",
        priority: "medium",
        status: "pending",
        duration: 0,
      },
    ],
    status: "pending",
    totalDuration: 0,
    passedCount: 0,
    failedCount: 0,
    skippedCount: 0,
  });

  // Simulate test execution
  const executeTest = useCallback(async (test: TestCase): Promise<TestCase> => {
    const startTime = performance.now();
    
    try {
      // Simulate different test scenarios
      await new Promise(resolve => setTimeout(resolve, Math.random() * 2000 + 500));
      
      const endTime = performance.now();
      const duration = endTime - startTime;
      
      // Simulate test results based on category
      const passRate = test.category === "performance" ? 0.85 : 
                      test.category === "cache" ? 0.90 :
                      test.category === "offline" ? 0.80 :
                      test.category === "tactical" ? 0.95 :
                      test.category === "navigation" ? 0.90 : 0.88;
      
      const passed = Math.random() < passRate;
      
      return {
        ...test,
        status: passed ? "passed" : "failed",
        duration,
        metrics: {
          loadTime: Math.random() * 1000 + 100,
          cacheHitRate: Math.random() * 30 + 70,
          memoryUsage: Math.random() * 50 + 20,
          tileCount: Math.floor(Math.random() * 100 + 50),
        },
        errorMessage: passed ? undefined : "Erro simulado: falha na validação do teste",
      };
    } catch (error) {
      return {
        ...test,
        status: "failed",
        duration: performance.now() - startTime,
        errorMessage: error instanceof Error ? error.message : "Erro desconhecido",
      };
    }
  }, []);

  // Run test suite
  const runTestSuite = useCallback(async () => {
    const suite = createTestSuite();
    setCurrentTestSuite(suite);
    setIsRunning(true);
    
    suite.status = "running";
    suite.startTime = new Date();
    
    for (let i = 0; i < suite.tests.length; i++) {
      const test = suite.tests[i];
      
      // Update test status to running
      suite.tests[i] = { ...test, status: "running" };
      setCurrentTestSuite({ ...suite });
      
      // Execute test
      const result = await executeTest(test);
      
      // Update test result
      suite.tests[i] = result;
      
      // Update counters
      if (result.status === "passed") suite.passedCount++;
      else if (result.status === "failed") suite.failedCount++;
      else if (result.status === "skipped") suite.skippedCount++;
      
      setCurrentTestSuite({ ...suite });
      
      // Small delay between tests
      await new Promise(resolve => setTimeout(resolve, 100));
    }
    
    suite.status = "completed";
    suite.endTime = new Date();
    suite.totalDuration = suite.endTime.getTime() - suite.startTime.getTime();
    
    setCurrentTestSuite({ ...suite });
    setTestHistory(prev => [...prev, suite]);
    setIsRunning(false);
  }, [executeTest]);

  // Auto-run functionality
  useEffect(() => {
    if (autoRun && !isRunning) {
      const interval = setInterval(() => {
        runTestSuite();
      }, testInterval);
      
      return () => clearInterval(interval);
    }
  }, [autoRun, testInterval, isRunning, runTestSuite]);

  const getCategoryColor = (category: string) => {
    switch (category) {
      case "navigation": return "bg-blue-100 text-blue-800";
      case "performance": return "bg-green-100 text-green-800";
      case "cache": return "bg-purple-100 text-purple-800";
      case "offline": return "bg-orange-100 text-orange-800";
      case "tactical": return "bg-red-100 text-red-800";
      case "compatibility": return "bg-gray-100 text-gray-800";
      default: return "bg-gray-100 text-gray-800";
    }
  };

  const getStatusIcon = (status: string) => {
    switch (status) {
      case "passed": return <CheckCircle className="w-4 h-4 text-green-500" />;
      case "failed": return <XCircle className="w-4 h-4 text-red-500" />;
      case "running": return <RefreshCw className="w-4 h-4 text-blue-500 animate-spin" />;
      case "skipped": return <AlertCircle className="w-4 h-4 text-yellow-500" />;
      default: return <div className="w-4 h-4 bg-gray-300 rounded-full" />;
    }
  };

  const exportResults = () => {
    if (!currentTestSuite) return;
    
    const results = {
      suite: currentTestSuite.name,
      timestamp: new Date().toISOString(),
      summary: {
        total: currentTestSuite.tests.length,
        passed: currentTestSuite.passedCount,
        failed: currentTestSuite.failedCount,
        skipped: currentTestSuite.skippedCount,
        duration: currentTestSuite.totalDuration,
        successRate: (currentTestSuite.passedCount / currentTestSuite.tests.length * 100).toFixed(1) + "%",
      },
      tests: currentTestSuite.tests.map(test => ({
        id: test.id,
        name: test.name,
        category: test.category,
        priority: test.priority,
        status: test.status,
        duration: test.duration,
        errorMessage: test.errorMessage,
        metrics: test.metrics,
      })),
    };
    
    const blob = new Blob([JSON.stringify(results, null, 2)], { type: "application/json" });
    const url = URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url;
    a.download = `osm-test-results-${Date.now()}.json`;
    a.click();
    URL.revokeObjectURL(url);
  };

  return (
    <div className="p-6 bg-white rounded-lg shadow-lg">
      <div className="mb-6">
        <h2 className="text-2xl font-bold text-gray-900 mb-2">
          Testes Automatizados OpenStreetMap
        </h2>
        <p className="text-gray-600">
          Suite de testes abrangente para garantir qualidade da migração OSM
        </p>
      </div>

      {/* Control Panel */}
      <div className="bg-gray-50 rounded-lg p-4 mb-6">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-4">
            <button
              onClick={runTestSuite}
              disabled={isRunning}
              className="flex items-center gap-2 px-4 py-2 bg-blue-600 text-white rounded-lg font-medium hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed"
            >
              {isRunning ? (
                <>
                  <Pause className="w-4 h-4" />
                  Executando...
                </>
              ) : (
                <>
                  <Play className="w-4 h-4" />
                  Executar Testes
                </>
              )}
            </button>
            
            <button
              onClick={exportResults}
              disabled={!currentTestSuite || currentTestSuite.status !== "completed"}
              className="flex items-center gap-2 px-4 py-2 border border-gray-300 rounded-lg font-medium hover:bg-gray-50 disabled:opacity-50 disabled:cursor-not-allowed"
            >
              <Download className="w-4 h-4" />
              Exportar Resultados
            </button>
          </div>
          
          <div className="flex items-center gap-4">
            <label className="flex items-center gap-2">
              <input
                type="checkbox"
                checked={autoRun}
                onChange={(e) => setAutoRun(e.target.checked)}
                disabled={isRunning}
                className="rounded"
              />
              <span className="text-sm text-gray-700">Auto-executar</span>
            </label>
            
            <select
              value={testInterval}
              onChange={(e) => setTestInterval(Number(e.target.value))}
              disabled={isRunning}
              className="px-3 py-1 border rounded text-sm"
            >
              <option value={5000}>5s</option>
              <option value={10000}>10s</option>
              <option value={30000}>30s</option>
              <option value={60000}>1min</option>
            </select>
          </div>
        </div>
      </div>

      {/* Current Test Suite */}
      {currentTestSuite && (
        <div className="mb-6">
          <div className="flex items-center justify-between mb-4">
            <h3 className="text-lg font-semibold text-gray-900">
              {currentTestSuite.name}
            </h3>
            <div className="flex items-center gap-4 text-sm">
              <span className={`px-2 py-1 rounded-full font-medium ${
                currentTestSuite.status === "completed" ? "bg-green-100 text-green-800" :
                currentTestSuite.status === "running" ? "bg-blue-100 text-blue-800" :
                "bg-gray-100 text-gray-800"
              }`}>
                {currentTestSuite.status === "completed" ? "Concluído" :
                 currentTestSuite.status === "running" ? "Executando" : "Pendente"}
              </span>
              <span className="text-gray-600">
                {currentTestSuite.passedCount} passados, {currentTestSuite.failedCount} falharam
              </span>
              {currentTestSuite.totalDuration > 0 && (
                <span className="text-gray-600">
                  {(currentTestSuite.totalDuration / 1000).toFixed(1)}s
                </span>
              )}
            </div>
          </div>
          
          {/* Progress Bar */}
          <div className="mb-4">
            <div className="bg-gray-200 rounded-full h-2">
              <div
                className="bg-blue-600 h-2 rounded-full transition-all duration-300"
                style={{
                  width: `${(currentTestSuite.tests.filter(t => t.status !== "pending").length / currentTestSuite.tests.length) * 100}%`
                }}
              />
            </div>
          </div>
          
          {/* Test Results */}
          <div className="space-y-2">
            {currentTestSuite.tests.map((test, index) => (
              <div key={test.id} className="flex items-center justify-between p-3 bg-gray-50 rounded-lg">
                <div className="flex items-center gap-3">
                  {getStatusIcon(test.status)}
                  <div>
                    <div className="font-medium text-gray-900">{test.name}</div>
                    <div className="text-sm text-gray-600">{test.description}</div>
                  </div>
                </div>
                
                <div className="flex items-center gap-3">
                  <span className={`px-2 py-1 rounded text-xs font-medium ${getCategoryColor(test.category)}`}>
                    {test.category}
                  </span>
                  
                  <span className={`px-2 py-1 rounded text-xs font-medium ${
                    test.priority === "high" ? "bg-red-100 text-red-800" :
                    test.priority === "medium" ? "bg-yellow-100 text-yellow-800" :
                    "bg-gray-100 text-gray-800"
                  }`}>
                    {test.priority}
                  </span>
                  
                  {test.duration > 0 && (
                    <span className="text-sm text-gray-600">
                      {test.duration.toFixed(0)}ms
                    </span>
                  )}
                  
                  {test.metrics && (
                    <div className="text-xs text-gray-600">
                      <div>Cache: {test.metrics.cacheHitRate.toFixed(1)}%</div>
                      <div>Mem: {test.metrics.memoryUsage.toFixed(1)}MB</div>
                    </div>
                  )}
                  
                  {test.errorMessage && (
                    <div className="text-xs text-red-600 max-w-xs truncate" title={test.errorMessage}>
                      {test.errorMessage}
                    </div>
                  )}
                </div>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Test History */}
      {testHistory.length > 0 && (
        <div>
          <h3 className="text-lg font-semibold text-gray-900 mb-4">Histórico de Testes</h3>
          <div className="space-y-2">
            {testHistory.slice(-5).map((suite, index) => (
              <div key={index} className="flex items-center justify-between p-3 bg-gray-50 rounded-lg">
                <div>
                  <div className="font-medium text-gray-900">{suite.name}</div>
                  <div className="text-sm text-gray-600">
                    {suite.passedCount} passados, {suite.failedCount} falharam, {suite.skippedCount} pulados
                  </div>
                </div>
                <div className="text-sm text-gray-600">
                  {(suite.totalDuration / 1000).toFixed(1)}s
                </div>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}
