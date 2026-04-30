"""
Hybrid RAG Memory System - Vector Database + Graph RAG + MOM Integration
Real implementation of SUPERDEV 2.0 memory system
"""
import json
import sqlite3
import hashlib
import uuid
from datetime import datetime
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass, asdict
from pathlib import Path
import re
import numpy as np
from collections import defaultdict, deque

try:
    import faiss
    FAISS_AVAILABLE = True
except ImportError:
    FAISS_AVAILABLE = False
    print("Warning: FAISS not available, using fallback vector store")

try:
    import networkx as nx
    NETWORKX_AVAILABLE = True
except ImportError:
    NETWORKX_AVAILABLE = False
    print("Warning: NetworkX not available, using fallback graph store")


@dataclass
class MemoryData:
    """Memory data structure with citation tracking"""
    id: str
    content: str
    mom_type: str  # decision, pattern, fact, learning, constraint
    category: str
    importance: float
    source_id: Optional[str] = None
    session_id: Optional[str] = None
    timestamp: str = ""
    tags: List[str] = None
    embedding: Optional[List[float]] = None
    
    def __post_init__(self):
        if self.timestamp == "":
            self.timestamp = datetime.now().isoformat()
        if self.tags is None:
            self.tags = []


@dataclass
class MemoryQuery:
    """Query structure for memory retrieval"""
    text: str
    mom_type: Optional[str] = None
    category: Optional[str] = None
    session_id: Optional[str] = None
    limit: int = 10
    min_importance: float = 0.0


class VectorStore:
    """Vector database implementation using FAISS or fallback"""
    
    def __init__(self, dimension: int = 768):
        self.dimension = dimension
        self.index = None
        self.id_to_memory = {}
        self._init_index()
    
    def _init_index(self):
        """Initialize FAISS index or fallback"""
        if FAISS_AVAILABLE:
            self.index = faiss.IndexFlatL2(self.dimension)
        else:
            # Fallback: simple numpy-based search
            self.vectors = []
            self.memory_ids = []
    
    def add_memory(self, memory: MemoryData):
        """Add memory to vector store"""
        if memory.embedding is None:
            return
        
        if FAISS_AVAILABLE:
            vector = np.array([memory.embedding]).astype('float32')
            self.index.add(vector)
            self.id_to_memory[len(self.id_to_memory)] = memory.id
        else:
            self.vectors.append(memory.embedding)
            self.memory_ids.append(memory.id)
    
    def search(self, query_embedding: List[float], k: int = 10) -> List[Tuple[str, float]]:
        """Search for similar memories"""
        if FAISS_AVAILABLE:
            query_vector = np.array([query_embedding]).astype('float32')
            distances, indices = self.index.search(query_vector, k)
            
            results = []
            for i, (dist, idx) in enumerate(zip(distances[0], indices[0])):
                if idx >= 0 and idx < len(self.id_to_memory):
                    memory_id = self.id_to_memory[idx]
                    results.append((memory_id, float(dist)))
            return results
        else:
            # Fallback: simple cosine similarity
            if not self.vectors:
                return []
            
            query_vec = np.array(query_embedding)
            similarities = []
            
            for i, stored_vec in enumerate(self.vectors):
                stored_vec = np.array(stored_vec)
                similarity = np.dot(query_vec, stored_vec) / (
                    np.linalg.norm(query_vec) * np.linalg.norm(stored_vec)
                )
                similarities.append((self.memory_ids[i], float(similarity)))
            
            # Sort by similarity (descending)
            similarities.sort(key=lambda x: x[1], reverse=True)
            return similarities[:k]


class GraphStore:
    """Graph database implementation using NetworkX or fallback"""
    
    def __init__(self):
        self.graph = None
        self.node_data = {}
        self._init_graph()
    
    def _init_graph(self):
        """Initialize NetworkX graph or fallback"""
        if NETWORKX_AVAILABLE:
            self.graph = nx.Graph()
        else:
            # Fallback: simple adjacency list
            self.adjacency = defaultdict(list)
    
    def add_memory(self, memory: MemoryData):
        """Add memory as node in graph"""
        self.node_data[memory.id] = memory
        
        if NETWORKX_AVAILABLE:
            self.graph.add_node(memory.id, **asdict(memory))
        else:
            self.adjacency[memory.id] = []
    
    def add_relation(self, from_id: str, to_id: str, relation_type: str = "related"):
        """Add relationship between memories"""
        if NETWORKX_AVAILABLE:
            self.graph.add_edge(from_id, to_id, relation=relation_type)
        else:
            self.adjacency[from_id].append((to_id, relation_type))
            self.adjacency[to_id].append((from_id, relation_type))
    
    def get_related(self, memory_id: str, max_depth: int = 2) -> List[str]:
        """Get related memories using graph traversal"""
        if NETWORKX_AVAILABLE:
            # Use NetworkX for graph traversal
            related = set()
            for node in self.graph.neighbors(memory_id):
                related.add(node)
                # Add neighbors of neighbors (depth 2)
                for neighbor in self.graph.neighbors(node):
                    if neighbor != memory_id:
                        related.add(neighbor)
            return list(related)
        else:
            # Fallback: simple adjacency list traversal
            visited = set()
            queue = deque([(memory_id, 0)])
            related = set()
            
            while queue:
                current_id, depth = queue.popleft()
                if depth >= max_depth or current_id in visited:
                    continue
                
                visited.add(current_id)
                
                for neighbor, _ in self.adjacency.get(current_id, []):
                    if neighbor not in visited and depth < max_depth:
                        related.add(neighbor)
                        queue.append((neighbor, depth + 1))
            
            return list(related)


class SimpleEmbedder:
    """Simple embedding implementation (fallback when no model available)"""
    
    def __init__(self):
        self.word_cache = {}
    
    def embed(self, text: str) -> List[float]:
        """Generate simple embedding using TF-IDF like approach"""
        # Simple word frequency embedding
        words = re.findall(r'\w+', text.lower())
        word_freq = defaultdict(int)
        
        for word in words:
            word_freq[word] += 1
        
        # Create fixed-size embedding (768 dimensions)
        embedding = [0.0] * 768
        
        for i, (word, freq) in enumerate(word_freq.items()):
            if i >= 768:
                break
            # Simple hash-based positioning
            hash_val = int(hashlib.md5(word.encode()).hexdigest(), 16)
            pos = hash_val % 768
            embedding[pos] = freq / len(words)
        
        # Normalize
        norm = sum(x**2 for x in embedding) ** 0.5
        if norm > 0:
            embedding = [x / norm for x in embedding]
        
        return embedding


class HybridRAGMemory:
    """Hybrid RAG Memory System implementation"""
    
    def __init__(self, db_path: str = "memory.db"):
        self.db_path = db_path
        self.vector_store = VectorStore()
        self.graph_store = GraphStore()
        self.embedder = SimpleEmbedder()
        self._init_database()
    
    def _init_database(self):
        """Initialize SQLite database for metadata"""
        self.conn = sqlite3.connect(self.db_path)
        self.conn.execute("""
            CREATE TABLE IF NOT EXISTS memories (
                id TEXT PRIMARY KEY,
                content TEXT NOT NULL,
                mom_type TEXT NOT NULL,
                category TEXT,
                importance REAL,
                source_id TEXT,
                session_id TEXT,
                timestamp TEXT,
                tags TEXT,
                embedding BLOB
            )
        """)
        
        self.conn.execute("""
            CREATE TABLE IF NOT EXISTS relations (
                from_id TEXT,
                to_id TEXT,
                relation_type TEXT,
                PRIMARY KEY (from_id, to_id)
            )
        """)
        
        self.conn.commit()
    
    def store_with_citation(self, data: MemoryData, session_id: str = None) -> str:
        """Store memory with citation tracking"""
        if session_id:
            data.session_id = session_id
        
        # Generate embedding
        data.embedding = self.embedder.embed(data.content)
        
        # Store in SQLite
        tags_json = json.dumps(data.tags)
        embedding_blob = json.dumps(data.embedding).encode()
        
        self.conn.execute("""
            INSERT OR REPLACE INTO memories 
            (id, content, mom_type, category, importance, source_id, session_id, timestamp, tags, embedding)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            data.id, data.content, data.mom_type, data.category,
            data.importance, data.source_id, data.session_id,
            data.timestamp, tags_json, embedding_blob
        ))
        
        # Store in vector store
        self.vector_store.add_memory(data)
        
        # Store in graph
        self.graph_store.add_memory(data)
        
        # Auto-relate similar memories
        self._auto_relate_memory(data)
        
        self.conn.commit()
        return data.id
    
    def _auto_relate_memory(self, new_memory: MemoryData):
        """Automatically relate new memory to existing ones"""
        # Find similar memories using vector search
        similar = self.vector_store.search(new_memory.embedding, k=5)
        
        for memory_id, score in similar:
            if memory_id != new_memory.id and score < 0.8:  # Similarity threshold
                self.add_relation(new_memory.id, memory_id, "similar")
    
    def add_relation(self, from_id: str, to_id: str, relation_type: str = "related"):
        """Add relationship between memories"""
        self.conn.execute("""
            INSERT OR REPLACE INTO relations (from_id, to_id, relation_type)
            VALUES (?, ?, ?)
        """, (from_id, to_id, relation_type))
        
        self.graph_store.add_relation(from_id, to_id, relation_type)
        self.conn.commit()
    
    def recall_with_citation(self, query: MemoryQuery) -> List[Dict[str, Any]]:
        """Recall memories with citation information"""
        # Generate query embedding
        query_embedding = self.embedder.embed(query.text)
        
        # Vector search
        vector_results = self.vector_store.search(query_embedding, k=query.limit * 2)
        
        # Filter by criteria
        filtered_results = []
        for memory_id, score in vector_results:
            memory = self._get_memory_by_id(memory_id)
            if not memory:
                continue
            
            # Apply filters
            if query.mom_type and memory.mom_type != query.mom_type:
                continue
            if query.category and memory.category != query.category:
                continue
            if query.session_id and memory.session_id != query.session_id:
                continue
            if memory.importance < query.min_importance:
                continue
            
            # Get related memories for context
            related_ids = self.graph_store.get_related(memory_id, max_depth=2)
            related_memories = [self._get_memory_by_id(rid) for rid in related_ids[:3]]
            
            result = {
                "memory": asdict(memory),
                "similarity_score": score,
                "citation": f"Source: {memory.id} (session: {memory.session_id or 'unknown'})",
                "related_memories": [asdict(rm) for rm in related_memories if rm]
            }
            filtered_results.append(result)
        
        # Sort by importance and similarity
        filtered_results.sort(key=lambda x: (x["memory"]["importance"], -x["similarity_score"]), reverse=True)
        
        return filtered_results[:query.limit]
    
    def _get_memory_by_id(self, memory_id: str) -> Optional[MemoryData]:
        """Get memory by ID from database"""
        cursor = self.conn.execute("""
            SELECT id, content, mom_type, category, importance, source_id, session_id, timestamp, tags, embedding
            FROM memories WHERE id = ?
        """, (memory_id,))
        
        row = cursor.fetchone()
        if not row:
            return None
        
        tags = json.loads(row[8]) if row[8] else []
        embedding = json.loads(row[9].decode()) if row[9] else None
        
        return MemoryData(
            id=row[0], content=row[1], mom_type=row[2], category=row[3],
            importance=row[4], source_id=row[5], session_id=row[6],
            timestamp=row[7], tags=tags, embedding=embedding
        )
    
    def get_by_mom_type(self, mom_type: str, limit: int = 10) -> List[MemoryData]:
        """Get memories by MOM type"""
        cursor = self.conn.execute("""
            SELECT id, content, mom_type, category, importance, source_id, session_id, timestamp, tags, embedding
            FROM memories WHERE mom_type = ?
            ORDER BY importance DESC, timestamp DESC
            LIMIT ?
        """, (mom_type, limit))
        
        memories = []
        for row in cursor.fetchall():
            tags = json.loads(row[8]) if row[8] else []
            embedding = json.loads(row[9].decode()) if row[9] else None
            
            memories.append(MemoryData(
                id=row[0], content=row[1], mom_type=row[2], category=row[3],
                importance=row[4], source_id=row[5], session_id=row[6],
                timestamp=row[7], tags=tags, embedding=embedding
            ))
        
        return memories
    
    def get_session_memories(self, session_id: str) -> List[MemoryData]:
        """Get all memories from a specific session"""
        cursor = self.conn.execute("""
            SELECT id, content, mom_type, category, importance, source_id, session_id, timestamp, tags, embedding
            FROM memories WHERE session_id = ?
            ORDER BY timestamp DESC
        """, (session_id,))
        
        memories = []
        for row in cursor.fetchall():
            tags = json.loads(row[8]) if row[8] else []
            embedding = json.loads(row[9].decode()) if row[9] else None
            
            memories.append(MemoryData(
                id=row[0], content=row[1], mom_type=row[2], category=row[3],
                importance=row[4], source_id=row[5], session_id=row[6],
                timestamp=row[7], tags=tags, embedding=embedding
            ))
        
        return memories
    
    def search_full_text(self, query_text: str, limit: int = 10) -> List[MemoryData]:
        """Full-text search across memories"""
        cursor = self.conn.execute("""
            SELECT id, content, mom_type, category, importance, source_id, session_id, timestamp, tags, embedding
            FROM memories 
            WHERE content LIKE ?
            ORDER BY importance DESC, timestamp DESC
            LIMIT ?
        """, (f"%{query_text}%", limit))
        
        memories = []
        for row in cursor.fetchall():
            tags = json.loads(row[8]) if row[8] else []
            embedding = json.loads(row[9].decode()) if row[9] else None
            
            memories.append(MemoryData(
                id=row[0], content=row[1], mom_type=row[2], category=row[3],
                importance=row[4], source_id=row[5], session_id=row[6],
                timestamp=row[7], tags=tags, embedding=embedding
            ))
        
        return memories
    
    def get_statistics(self) -> Dict[str, Any]:
        """Get memory system statistics"""
        cursor = self.conn.execute("SELECT COUNT(*) FROM memories")
        total_memories = cursor.fetchone()[0]
        
        cursor = self.conn.execute("SELECT mom_type, COUNT(*) FROM memories GROUP BY mom_type")
        mom_type_counts = dict(cursor.fetchall())
        
        cursor = self.conn.execute("SELECT COUNT(*) FROM relations")
        total_relations = cursor.fetchone()[0]
        
        return {
            "total_memories": total_memories,
            "mom_type_distribution": mom_type_counts,
            "total_relations": total_relations,
            "vector_store_size": len(self.vector_store.id_to_memory) if FAISS_AVAILABLE else len(self.vector_store.vectors),
            "graph_nodes": len(self.graph_store.node_data)
        }
    
    def cleanup(self):
        """Cleanup resources"""
        self.conn.close()


# Factory function for easy usage
def create_hybrid_rag_memory(db_path: str = "memory.db") -> HybridRAGMemory:
    """Create a Hybrid RAG Memory system with default configuration"""
    return HybridRAGMemory(db_path)


if __name__ == "__main__":
    # Test the Hybrid RAG Memory System
    print("Testing Hybrid RAG Memory System")
    print("=" * 50)
    
    memory_system = create_hybrid_rag_memory("test_memory.db")
    
    # Test storing memories
    print("\n1. Testing memory storage...")
    
    decision_memory = MemoryData(
        id="decision_001",
        content="Use PostgreSQL for user data storage",
        mom_type="decision",
        category="database",
        importance=0.9,
        source_id="team_discussion",
        session_id="session_001"
    )
    
    pattern_memory = MemoryData(
        id="pattern_001",
        content="React components use PascalCase naming",
        mom_type="pattern",
        category="frontend",
        importance=0.8,
        source_id="code_review",
        session_id="session_001"
    )
    
    memory_system.store_with_citation(decision_memory, "session_001")
    memory_system.store_with_citation(pattern_memory, "session_001")
    
    print(f"   Stored decision memory: {decision_memory.id}")
    print(f"   Stored pattern memory: {pattern_memory.id}")
    
    # Test recall
    print("\n2. Testing memory recall...")
    
    query = MemoryQuery(
        text="database",
        mom_type="decision",
        limit=5
    )
    
    results = memory_system.recall_with_citation(query)
    print(f"   Found {len(results)} memories:")
    for result in results:
        memory = result["memory"]
        print(f"   - {memory['content']} (score: {result['similarity_score']:.3f})")
        print(f"     Citation: {result['citation']}")
    
    # Test MOM type retrieval
    print("\n3. Testing MOM type retrieval...")
    
    decisions = memory_system.get_by_mom_type("decision")
    print(f"   Found {len(decisions)} decision memories")
    
    patterns = memory_system.get_by_mom_type("pattern")
    print(f"   Found {len(patterns)} pattern memories")
    
    # Test statistics
    print("\n4. Testing statistics...")
    
    stats = memory_system.get_statistics()
    print(f"   Total memories: {stats['total_memories']}")
    print(f"   MOM types: {stats['mom_type_distribution']}")
    print(f"   Relations: {stats['total_relations']}")
    
    # Test full-text search
    print("\n5. Testing full-text search...")
    
    search_results = memory_system.search_full_text("React")
    print(f"   Found {len(search_results)} memories with 'React'")
    
    memory_system.cleanup()
    
    print("\n" + "=" * 50)
    print("Hybrid RAG Memory System test completed!")
