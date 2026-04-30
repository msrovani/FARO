"""
Brain Dev Initialization
Configura token optimization para o projeto específico
"""
import sys
from pathlib import Path

# Add brain_dev to path
sys.path.insert(0, str(Path(__file__).parent))

from token_optimization import create_enhanced_context_manager, File
import yaml


def init_project():
    """Inicializa configuração do projeto"""
    
    project_path = Path(__file__).parent.parent
    brain_dev_path = Path(__file__).parent
    
    print("=" * 60)
    print("Brain Dev Initialization")
    print("=" * 60)
    print(f"Project: {project_path}")
    print()
    
    # 1. Carregar configuração customizada
    print("Step 1: Loading custom configuration...")
    custom_config_path = brain_dev_path / "custom-config.yml"
    
    if custom_config_path.exists():
        with open(custom_config_path, 'r') as f:
            custom_config = yaml.safe_load(f)
        print("   ✓ Custom config loaded")
    else:
        custom_config = {}
        print("   ⚠️  No custom config, using defaults")
    
    # 2. Ajustar configurações baseadas no projeto
    print("\nStep 2: Adjusting configuration for project...")
    adjusted_config = adjust_config_for_project(project_path, custom_config)
    print("   ✓ Configuration adjusted")
    
    # 3. Salvar configuração ajustada
    print("\nStep 3: Saving adjusted configuration...")
    save_adjusted_config(adjusted_config, brain_dev_path)
    print("   ✓ Configuration saved")
    
    # 4. Testar inicialização
    print("\nStep 4: Testing initialization...")
    test_initialization(brain_dev_path)
    print("   ✓ Initialization successful")
    
    print("\n" + "=" * 60)
    print("✅ Brain Dev initialized successfully!")
    print("=" * 60)
    print("\nRun: python .brain_dev/process_project.py")


def adjust_config_for_project(project_path: Path, custom_config: dict) -> dict:
    """Ajusta configuração baseada no projeto"""
    
    # Detectar linguagem principal
    language = detect_language(project_path)
    
    # Ajustar clusters baseados na linguagem
    clusters = adjust_clusters_by_language(language)
    
    # Ajustar prioridades baseadas no tipo de projeto
    priorities = adjust_priorities_by_project_type(project_path)
    
    return {
        'language': language,
        'clusters': clusters,
        'priorities': priorities,
        'custom': custom_config
    }


def detect_language(project_path: Path) -> str:
    """Detecta linguagem principal do projeto"""
    
    # Contar arquivos por extensão
    extensions = {}
    
    for file in project_path.rglob("*"):
        if file.is_file():
            ext = file.suffix.lower()
            extensions[ext] = extensions.get(ext, 0) + 1
    
    # Determinar linguagem mais comum
    language_map = {
        '.py': 'python',
        '.js': 'javascript',
        '.ts': 'typescript',
        '.java': 'java',
        '.go': 'go',
        '.rs': 'rust',
        '.c': 'c',
        '.cpp': 'cpp',
        '.rb': 'ruby',
        '.php': 'php'
    }
    
    max_count = 0
    main_language = 'unknown'
    
    for ext, count in extensions.items():
        if ext in language_map and count > max_count:
            max_count = count
            main_language = language_map[ext]
    
    return main_language


def adjust_clusters_by_language(language: str) -> dict:
    """Ajusta clusters baseados na linguagem"""
    
    # Adicionar clusters específicos da linguagem
    language_clusters = {
        'python': {
            'name': 'python_modules',
            'patterns': [r'.*\.py$', r'.*__init__\.py$'],
            'description': 'Python modules'
        },
        'javascript': {
            'name': 'js_modules',
            'patterns': [r'.*\.js$', r'.*\.jsx$'],
            'description': 'JavaScript modules'
        },
        'typescript': {
            'name': 'ts_modules',
            'patterns': [r'.*\.ts$', r'.*\.tsx$'],
            'description': 'TypeScript modules'
        }
    }
    
    return language_clusters.get(language, {})


def adjust_priorities_by_project_type(project_path: Path) -> dict:
    """Ajusta prioridades baseadas no tipo de projeto"""
    
    # Detectar tipo de projeto
    has_tests = any('test' in f.name.lower() for f in project_path.rglob("*"))
    has_docs = any('doc' in f.name.lower() for f in project_path.rglob("*"))
    has_frontend = any(f.suffix in ['.html', '.css', '.js', '.jsx', '.ts', '.tsx'] for f in project_path.rglob("*"))
    
    priorities = {
        'testing_priority': 20 if has_tests else 15,
        'docs_priority': 10 if has_docs else 15,
        'frontend_priority': 5 if has_frontend else 15
    }
    
    return priorities


def save_adjusted_config(config: dict, brain_dev_path: Path):
    """Salva configuração ajustada"""
    
    config_path = brain_dev_path / "adjusted-config.yml"
    
    with open(config_path, 'w') as f:
        yaml.dump(config, f, default_flow_style=False)


def test_initialization(brain_dev_path: Path):
    """Testa inicialização"""
    
    try:
        from token_optimization import create_enhanced_context_manager
        context_manager = create_enhanced_context_manager(str(brain_dev_path))
        context_manager.cleanup()
        return True
    except Exception as e:
        print(f"   ⚠️  Initialization test failed: {e}")
        return False


if __name__ == "__main__":
    init_project()
