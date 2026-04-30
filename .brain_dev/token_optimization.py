"""
Token Optimization Components for SUPERDEV 2.0
Implements insights from TabNews article (Nexor tool)
"""
import re
import gzip
import base64
import yaml
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Any
from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import dataclass

try:
    import tiktoken
    TIKTOKEN_AVAILABLE = True
except ImportError:
    TIKTOKEN_AVAILABLE = False


@dataclass
class File:
    """Represents a file in the codebase"""
    path: str
    content: str
    size: int = 0


class SemanticClusterer:
    """Groups files by functionality/domain for better LLM understanding"""
    
    def __init__(self, config_path: str):
        self.config = self._load_config(config_path)
    
    def _load_config(self, config_path: str) -> Dict[str, Any]:
        """Load semantic clusters configuration from YAML"""
        with open(config_path, 'r', encoding='utf-8') as f:
            config = yaml.safe_load(f)
        return config['semantic_clusters']
    
    def cluster(self, files: List[File]) -> Dict[str, List[File]]:
        """Group files by semantic cluster"""
        clusters: Dict[str, List[File]] = {}
        
        for file in files:
            cluster_name = self._assign_cluster(file)
            if cluster_name not in clusters:
                clusters[cluster_name] = []
            clusters[cluster_name].append(file)
        
        return clusters
    
    def cluster_async(self, files: List[File], max_workers: int = 4) -> Dict[str, List[File]]:
        """Group files by semantic cluster using parallel processing"""
        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            futures = {executor.submit(self._assign_cluster, file): file for file in files}
            
            clusters: Dict[str, List[File]] = {}
            for future in as_completed(futures):
                file = futures[future]
                cluster_name = future.result()
                if cluster_name not in clusters:
                    clusters[cluster_name] = []
                clusters[cluster_name].append(file)
        
        return clusters
    
    def _assign_cluster(self, file: File) -> str:
        """Assign a file to a cluster based on patterns"""
        # Normalize path separators to forward slashes
        normalized_path = file.path.replace('\\', '/')
        
        for cluster_name, cluster_config in self.config.items():
            for pattern in cluster_config['patterns']:
                if re.match(pattern, normalized_path, re.IGNORECASE):
                    return cluster_name
        return 'default'


class PriorityManager:
    """Orders files by importance for intelligent context truncation"""
    
    def __init__(self, config_path: str):
        self.config = self._load_config(config_path)
        self._build_priority_map()
    
    def _load_config(self, config_path: str) -> Dict[str, Any]:
        """Load priority hierarchy configuration from YAML"""
        with open(config_path, 'r', encoding='utf-8') as f:
            config = yaml.safe_load(f)
        return config['priority_hierarchy']
    
    def _build_priority_map(self):
        """Build a priority map for quick lookup"""
        self.priority_map = {}
        for level_name, level_config in self.config.items():
            order = level_config['order']
            for pattern in level_config['patterns']:
                self.priority_map[pattern] = order
    
    def prioritize(self, files: List[File]) -> List[File]:
        """Sort files by priority (lower order = higher priority)"""
        return sorted(files, key=lambda f: self._get_priority(f))
    
    def _get_priority(self, file: File) -> int:
        """Get priority for a file"""
        # Normalize path separators to forward slashes
        normalized_path = file.path.replace('\\', '/')
        
        for pattern, order in self.priority_map.items():
            if re.match(pattern, normalized_path, re.IGNORECASE):
                return order
        return self.config.get('default', {}).get('order', 999)


class CodeMinifier:
    """Removes comments, docstrings, and whitespace that are noise for AI"""
    
    def __init__(self, config_path: str):
        self.config = self._load_config(config_path)
        self._compile_preserve_patterns()
    
    def _load_config(self, config_path: str) -> Dict[str, Any]:
        """Load minification configuration from YAML"""
        with open(config_path, 'r', encoding='utf-8') as f:
            config = yaml.safe_load(f)
        return config['minification']
    
    def _compile_preserve_patterns(self):
        """Compile regex patterns for important comments"""
        self.preserve_patterns = [
            re.compile(pattern, re.IGNORECASE)
            for pattern in self.config.get('preserve_patterns', [])
        ]
    
    def minify(self, content: str, file_path: str = "") -> str:
        """Minify code content"""
        if not self.config.get('enabled', True):
            return content
        
        # Check file extension
        if not self._should_minify(file_path):
            return content
        
        result = content
        
        if self.config.get('remove_docstrings', True):
            result = self._remove_docstrings(result)
        
        if self.config.get('remove_comments', True):
            result = self._remove_comments(result)
        
        if self.config.get('remove_whitespace', True):
            result = self._remove_whitespace(result)
        
        return result
    
    def _should_minify(self, file_path: str) -> bool:
        """Check if file should be minified based on extension"""
        if not file_path:
            return True
        
        target_extensions = self.config.get('target_extensions', [])
        return any(file_path.endswith(ext) for ext in target_extensions)
    
    def _remove_docstrings(self, content: str) -> str:
        """Remove triple-quoted strings (docstrings)"""
        # Remove both """ and ''' docstrings
        content = re.sub(r'"""[\s\S]*?"""', '', content)
        content = re.sub(r"'''[\s\S]*?'''", '', content)
        return content
    
    def _remove_comments(self, content: str) -> str:
        """Remove comments while preserving important ones"""
        lines = content.split('\n')
        result = []
        
        for line in lines:
            processed = self._remove_comment_from_line(line)
            if processed.strip():  # Don't add empty lines
                result.append(processed)
        
        return '\n'.join(result)
    
    def _remove_comment_from_line(self, line: str) -> str:
        """Remove comment from a single line, preserving important comments"""
        in_string = False
        string_char = ''
        escape = False
        comment_pos = -1
        
        for i, char in enumerate(line):
            if not escape and char in ('"', "'"):
                if not in_string:
                    in_string = True
                    string_char = char
                elif char == string_char:
                    in_string = False
            elif not in_string and char == '#':
                comment_pos = i
                break
            
            escape = not escape and char == '\\'
        
        if comment_pos >= 0:
            comment = line[comment_pos + 1:]
            if self._is_important_comment(comment):
                return line  # Keep important comments
            return line[:comment_pos].rstrip()
        
        return line
    
    def _is_important_comment(self, comment: str) -> bool:
        """Check if comment is important and should be preserved"""
        for pattern in self.preserve_patterns:
            if pattern.search(comment):
                return True
        return False
    
    def _remove_whitespace(self, content: str) -> str:
        """Remove excessive whitespace"""
        # Replace multiple spaces with single space
        content = re.sub(r' +', ' ', content)
        # Replace multiple newlines with single newline
        content = re.sub(r'\n+', '\n', content)
        return content.strip()


class TokenCounter:
    """Precise token counting using tiktoken"""
    
    def __init__(self, encoding: str = "cl100k_base"):
        if not TIKTOKEN_AVAILABLE:
            print("Warning: tiktoken not available, using approximation")
            self.encoding = None
        else:
            self.encoding = tiktoken.get_encoding(encoding)
    
    def count(self, text: str) -> int:
        """Count tokens in text"""
        if self.encoding:
            return len(self.encoding.encode(text))
        else:
            # Fallback: approximate (4 chars per token)
            return len(text) // 4
    
    def count_messages(self, messages: List[Dict[str, str]]) -> int:
        """Count tokens in list of messages"""
        total = 0
        for message in messages:
            total += self.count(message.get('content', ''))
        return total
    
    def free(self):
        """Free encoding resources"""
        if self.encoding and hasattr(self.encoding, 'free'):
            self.encoding.free()


class ParallelProcessor:
    """Parallel processing for large codebases"""
    
    def __init__(self, max_workers: int = 4):
        self.max_workers = max_workers
    
    def process_files(self, files: List[File], processor) -> List[Any]:
        """Process files in parallel"""
        with ThreadPoolExecutor(max_workers=self.max_workers) as executor:
            futures = {executor.submit(processor, file): file for file in files}
            
            results = []
            for future in as_completed(futures):
                try:
                    result = future.result()
                    results.append(result)
                except Exception as e:
                    print(f"Error processing file: {e}")
        
        return results


class ConditionalCompressor:
    """Compresses files conditionally when it's worth it"""
    
    def __init__(self, threshold_bytes: int = 10 * 1024):
        self.threshold = threshold_bytes
    
    def compress(self, content: str) -> Tuple[str, bool]:
        """Compress content if it's above threshold"""
        content_bytes = content.encode('utf-8')
        
        if len(content_bytes) <= self.threshold:
            return content, False
        
        try:
            compressed = gzip.compress(content_bytes, compresslevel=6)
            compressed_b64 = base64.b64encode(compressed).decode('ascii')
            return compressed_b64, True
        except Exception as e:
            print(f"Compression error: {e}")
            return content, False
    
    def decompress(self, content: str, compressed: bool) -> str:
        """Decompress content if it was compressed"""
        if not compressed:
            return content
        
        try:
            compressed_bytes = base64.b64decode(content)
            decompressed = gzip.decompress(compressed_bytes)
            return decompressed.decode('utf-8')
        except Exception as e:
            print(f"Decompression error: {e}")
            return content


class EnhancedContextManager:
    """Enhanced Context Manager with all token optimization components"""
    
    def __init__(self, config_dir: str):
        config_dir_path = Path(config_dir)
        
        # Initialize components
        self.clusterer = SemanticClusterer(str(config_dir_path / "semantic-clusters.yml"))
        self.priority_manager = PriorityManager(str(config_dir_path / "priority-hierarchy.yml"))
        self.minifier = CodeMinifier(str(config_dir_path / "minification-config.yml"))
        self.token_counter = TokenCounter()
        self.parallel_processor = ParallelProcessor(max_workers=4)
        self.compressor = ConditionalCompressor()
    
    def load_context(self, files: List[File]) -> Dict[str, Any]:
        """Load and organize context with all optimizations"""
        # Step 1: Cluster files by functionality
        clusters = self.clusterer.cluster(files)
        
        # Step 2: Prioritize files within each cluster
        prioritized_clusters = {}
        for cluster_name, cluster_files in clusters.items():
            prioritized_clusters[cluster_name] = self.priority_manager.prioritize(cluster_files)
        
        # Step 3: Minify content
        for cluster_name, cluster_files in prioritized_clusters.items():
            for file in cluster_files:
                file.content = self.minifier.minify(file.content, file.path)
                file.size = len(file.content)
        
        return {
            'clusters': prioritized_clusters,
            'total_files': len(files),
            'cluster_count': len(clusters)
        }
    
    def estimate_tokens(self, messages: List[Dict[str, str]]) -> int:
        """Estimate token count precisely"""
        return self.token_counter.count_messages(messages)
    
    def prune_context(self, files: List[File], target_capacity: int) -> List[File]:
        """Prune context using priority hierarchy"""
        # Prioritize files
        prioritized = self.priority_manager.prioritize(files)
        
        # Keep files until capacity is reached
        result = []
        current_size = 0
        
        for file in prioritized:
            if current_size + file.size <= target_capacity:
                result.append(file)
                current_size += file.size
            else:
                break
        
        return result
    
    def cleanup(self):
        """Cleanup resources"""
        self.token_counter.free()


# Convenience function for quick usage
def create_enhanced_context_manager(config_dir: str = ".windsurf/core/context") -> EnhancedContextManager:
    """Create an enhanced context manager with default configuration"""
    return EnhancedContextManager(config_dir)


if __name__ == "__main__":
    # Test the components
    print("Token Optimization Components Test")
    print("=" * 50)
    
    # Test SemanticClusterer
    print("\n1. Testing SemanticClusterer...")
    files = [
        File("core/orchestration/orchestration-engine.md", "content1"),
        File("flavors/self-evolution/workflows/auto-update.md", "content2"),
        File("detection/flavor-detection.md", "content3"),
        File("unknown/file.txt", "content4")
    ]
    
    clusterer = SemanticClusterer(".windsurf/core/context/semantic-clusters.yml")
    clusters = clusterer.cluster(files)
    print(f"   Found {len(clusters)} clusters:")
    for name, cluster_files in clusters.items():
        print(f"   - {name}: {len(cluster_files)} files")
    
    # Test PriorityManager
    print("\n2. Testing PriorityManager...")
    priority_manager = PriorityManager(".windsurf/core/context/priority-hierarchy.yml")
    prioritized = priority_manager.prioritize(files)
    print(f"   Files prioritized:")
    for file in prioritized:
        print(f"   - {file.path}")
    
    # Test CodeMinifier
    print("\n3. Testing CodeMinifier...")
    minifier = CodeMinifier(".windsurf/core/context/minification-config.yml")
    code = '''
    def hello():
        """This is a docstring"""
        # This is a comment
        print("Hello")  # TODO: implement
    '''
    minified = minifier.minify(code, "test.py")
    print(f"   Original length: {len(code)}")
    print(f"   Minified length: {len(minified)}")
    
    # Test TokenCounter
    print("\n4. Testing TokenCounter...")
    token_counter = TokenCounter()
    text = "Hello, world! This is a test."
    tokens = token_counter.count(text)
    print(f"   Text: {text}")
    print(f"   Tokens: {tokens}")
    token_counter.free()
    
    # Test ConditionalCompressor
    print("\n5. Testing ConditionalCompressor...")
    compressor = ConditionalCompressor(threshold_bytes=100)
    small_content = "Small content"
    large_content = "Large content " * 1000
    small_compressed, small_was_compressed = compressor.compress(small_content)
    large_compressed, large_was_compressed = compressor.compress(large_content)
    print(f"   Small content compressed: {small_was_compressed}")
    print(f"   Large content compressed: {large_was_compressed}")
    print(f"   Large content original size: {len(large_content)}")
    print(f"   Large content compressed size: {len(large_compressed)}")
    
    print("\n" + "=" * 50)
    print("All tests completed!")
