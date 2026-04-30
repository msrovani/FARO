# Brain Dev - SUPERDEV 2.0 Token Optimization

Sistema de otimização de contexto para LLMs baseado em insights do artigo TabNews (Nexor tool).

## O que é Brain Dev?

Brain Dev é o "cérebro de desenvolvimento" do seu projeto. Ele otimiza o contexto enviado aos LLMs para:

- **Reduzir tokens em 20-30%** além do baseline
- **Melhorar entendimento** via semantic clusters
- **Truncar inteligentemente** com priority hierarchy
- **Processar mais rápido** com parallel processing
- **Economizar custos** em 15-25%

## Instalação

```bash
# 1. Instalar dependências
pip install -r .brain_dev/requirements.txt

# 2. Inicializar para seu projeto
python .brain_dev/init_brain_dev.py

# 3. Processar seu projeto
python .brain_dev/process_project.py
```

## Configuração

### Configuração Padrão

Os arquivos de configuração padrão estão em:
- `semantic-clusters.yml` - Agrupamento de arquivos por funcionalidade
- `priority-hierarchy.yml` - Ordem de importância dos arquivos
- `minification-config.yml` - Configuração de minificação

### Configuração Customizada

Crie `custom-config.yml` para ajustar ao seu projeto:

```yaml
# Configurações específicas do seu projeto
custom_clusters:
  - name: "api_routes"
    patterns: ["routes/.*", "api/.*"]
    description: "API routes"

custom_priorities:
  - name: "api"
    patterns: ["routes/.*", "api/.*"]
    order: 2  # Alta prioridade

minification:
  preserve_patterns:
    - "TODO"
    - "FIXME"
    - "IMPORTANT"
```

## Uso

### Processar Contexto

```python
from .brain_dev.token_optimization import create_enhanced_context_manager, File
from pathlib import Path

# Criar context manager
context_manager = create_enhanced_context_manager(".brain_dev")

# Scaneia arquivos
files = []
for file_path in Path(".").rglob("*.py"):
    with open(file_path) as f:
        content = f.read()
    files.append(File(str(file_path), content))

# Otimiza contexto
context = context_manager.load_context(files)

# Pruna se necessário
pruned = context_manager.prune_context(files, 50000)

# Cleanup
context_manager.cleanup()
```

### Integrar com seu Workflow

Adicione ao seu script de desenvolvimento:

```python
# Antes de enviar ao LLM
from .brain_dev.token_optimization import create_enhanced_context_manager

context_manager = create_enhanced_context_manager(".brain_dev")
optimized_context = context_manager.load_context(your_files)
# Envie optimized_context ao LLM
```

## Componentes

1. **Semantic Clusters** - Agrupa arquivos por funcionalidade
2. **Priority Hierarchy** - Ordena por importância
3. **Code Minification** - Remove ruído (comentários, docstrings)
4. **Token Counter** - Contagem precisa com tiktoken
5. **Parallel Processing** - Processamento paralelo
6. **Conditional Compression** - Compressão gzip+base64

## Métricas Esperadas

- Token Reduction: 20-30%
- Processing Time: 50-70% mais rápido
- Cost Reduction: 15-25%

## Suporte

Para mais informações, veja:
- TabNews Article: https://www.tabnews.com.br/claudiosilvadev/a-ilusao-do-contexto-infinito-por-que-seu-llm-esquece-seu-codigo-e-como-parei-de-jogar-dinheiro-fora-com-token-inutil
- SUPERDEV 2.0: https://github.com/msrovani/OpenDEV
