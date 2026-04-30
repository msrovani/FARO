"""
Project Context Processor
Processa contexto do projeto com token optimization
"""
import sys
from pathlib import Path

# Add brain_dev to path
sys.path.insert(0, str(Path(__file__).parent))

from token_optimization import create_enhanced_context_manager, File


def scan_project(project_path: str) -> list:
    """Scaneia projeto e coleta arquivos"""
    project = Path(project_path)
    files = []
    
    # Excluir .brain_dev, node_modules, __pycache__, .git
    exclude_dirs = {'.brain_dev', 'node_modules', '__pycache__', '.git', '.venv', 'venv', 'env'}
    
    for file_path in project.rglob("*"):
        if file_path.is_file():
            # Verificar se está em diretório excluído
            if any(excluded in file_path.parts for excluded in exclude_dirs):
                continue
            
            # Verificar extensão
            if file_path.suffix in ['.py', '.js', '.ts', '.jsx', '.tsx', '.java', '.go', '.rs', '.c', '.cpp', '.h', '.hpp', '.md', '.yml', '.yaml', '.json']:
                try:
                    with open(file_path, 'r', encoding='utf-8') as f:
                        content = f.read()
                    relative_path = file_path.relative_to(project)
                    files.append(File(str(relative_path), content, len(content)))
                except Exception as e:
                    print(f"Error reading {file_path}: {e}")
    
    return files


def main():
    """Função principal"""
    
    project_path = Path(__file__).parent.parent
    brain_dev_path = Path(__file__).parent
    
    print("=" * 60)
    print("Project Context Processor - Brain Dev")
    print("=" * 60)
    print(f"Project: {project_path}")
    print()
    
    # 1. Scaneia projeto
    print("Step 1: Scanning project...")
    files = scan_project(project_path)
    print(f"   Found {len(files)} files")
    
    # 2. Inicializa Enhanced Context Manager
    print("\nStep 2: Initializing Enhanced Context Manager...")
    context_manager = create_enhanced_context_manager(str(brain_dev_path))
    print("   ✓ Initialized")
    
    # 3. Carrega e organiza contexto
    print("\nStep 3: Loading and organizing context...")
    context = context_manager.load_context(files)
    print(f"   Total files: {context['total_files']}")
    print(f"   Clusters: {context['cluster_count']}")
    
    # 4. Exibe breakdown de clusters
    print("\nStep 4: Cluster breakdown:")
    for cluster_name, cluster_files in context['clusters'].items():
        total_size = sum(f.size for f in cluster_files)
        print(f"   {cluster_name}: {len(cluster_files)} files ({total_size} bytes)")
        if len(cluster_files) <= 5:
            for file in cluster_files:
                print(f"      - {file.path} ({file.size} bytes)")
        else:
            for file in cluster_files[:3]:
                print(f"      - {file.path} ({file.size} bytes)")
            print(f"      ... and {len(cluster_files) - 3} more")
    
    # 5. Estima tokens
    print("\nStep 5: Token estimation...")
    messages = [
        {"role": "system", "content": "You are a helpful assistant"},
        {"role": "user", "content": "Help me understand this codebase"}
    ]
    token_count = context_manager.estimate_tokens(messages)
    print(f"   Sample message tokens: {token_count}")
    
    # 6. Testa pruning
    print("\nStep 6: Testing context pruning...")
    target_capacity = 50000  # 50KB
    pruned_files = context_manager.prune_context(files, target_capacity)
    original_size = sum(f.size for f in files)
    pruned_size = sum(f.size for f in pruned_files)
    compression_ratio = pruned_size / original_size if original_size > 0 else 1.0
    print(f"   Original size: {original_size} bytes")
    print(f"   Pruned size: {pruned_size} bytes")
    print(f"   Compression ratio: {compression_ratio:.2%}")
    print(f"   Files kept: {len(pruned_files)}/{len(files)}")
    
    # 7. Cleanup
    print("\nStep 7: Cleanup...")
    context_manager.cleanup()
    print("   ✓ Cleanup complete")
    
    print("\n" + "=" * 60)
    print("Processing complete!")
    print("=" * 60)
    
    # Summary
    print("\nSummary:")
    print(f"- Total files scanned: {len(files)}")
    print(f"- Clusters identified: {context['cluster_count']}")
    print(f"- Compression ratio: {compression_ratio:.2%}")
    print(f"- Token optimization: Active")
    print()
    print("Your project is now ready for Brain Dev!")


if __name__ == "__main__":
    main()
