"""
MCP Protocol Server Implementation
Real Model Context Protocol server for SUPERDEV 2.0
"""
import asyncio
import json
import sys
from typing import Dict, List, Any, Optional, Callable
from dataclasses import dataclass, asdict
from pathlib import Path
import logging
import uuid
from datetime import datetime

# Import our memory system
try:
    from ..memory.hybrid_rag import HybridRAGMemory, MemoryQuery, MemoryData
    MEMORY_AVAILABLE = True
except ImportError:
    MEMORY_AVAILABLE = False
    print("Warning: Memory system not available, using fallback")

try:
    from ..context.token_optimization import EnhancedContextManager, File
    CONTEXT_AVAILABLE = True
except ImportError:
    CONTEXT_AVAILABLE = False
    print("Warning: Context optimization not available, using fallback")


@dataclass
class MCPRequest:
    """MCP Request structure"""
    jsonrpc: str = "2.0"
    id: str = ""
    method: str = ""
    params: Dict[str, Any] = None
    
    def __post_init__(self):
        if self.id == "":
            self.id = str(uuid.uuid4())
        if self.params is None:
            self.params = {}


@dataclass
class MCPResponse:
    """MCP Response structure"""
    jsonrpc: str = "2.0"
    id: str = ""
    result: Any = None
    error: Optional[Dict[str, Any]] = None


@dataclass
class MCPNotification:
    """MCP Notification structure"""
    jsonrpc: str = "2.0"
    method: str = ""
    params: Dict[str, Any] = None


class MCPServer:
    """MCP Protocol Server implementation"""
    
    def __init__(self, name: str, version: str = "1.0.0"):
        self.name = name
        self.version = version
        self.tools: Dict[str, Callable] = {}
        self.resources: Dict[str, Callable] = {}
        self.prompts: Dict[str, Callable] = {}
        self.memory_system = None
        self.context_manager = None
        self.logger = logging.getLogger(name)
        
        # Initialize components if available
        if MEMORY_AVAILABLE:
            self.memory_system = HybridRAGMemory()
        if CONTEXT_AVAILABLE:
            self.context_manager = EnhancedContextManager()
        
        # Register default handlers
        self._register_default_handlers()
    
    def _register_default_handlers(self):
        """Register default MCP handlers"""
        self.register_tool("list_tools", self._list_tools)
        self.register_tool("call_tool", self._call_tool)
        self.register_resource("list_resources", self._list_resources)
        self.register_resource("read_resource", self._read_resource)
        self.register_prompt("list_prompts", self._list_prompts)
        self.register_prompt("get_prompt", self._get_prompt)
    
    def register_tool(self, name: str, handler: Callable):
        """Register a tool handler"""
        self.tools[name] = handler
    
    def register_resource(self, name: str, handler: Callable):
        """Register a resource handler"""
        self.resources[name] = handler
    
    def register_prompt(self, name: str, handler: Callable):
        """Register a prompt handler"""
        self.prompts[name] = handler
    
    async def handle_request(self, request_data: str) -> str:
        """Handle incoming MCP request"""
        try:
            request = json.loads(request_data)
            
            if "method" not in request:
                return self._create_error_response(request.get("id", ""), -32600, "Invalid Request")
            
            method = request["method"]
            params = request.get("params", {})
            request_id = request.get("id", "")
            
            # Handle different method types
            if method.startswith("tools/"):
                return await self._handle_tools_method(method, params, request_id)
            elif method.startswith("resources/"):
                return await self._handle_resources_method(method, params, request_id)
            elif method.startswith("prompts/"):
                return await self._handle_prompts_method(method, params, request_id)
            else:
                return self._create_error_response(request_id, -32601, "Method not found")
                
        except json.JSONDecodeError:
            return self._create_error_response("", -32700, "Parse error")
        except Exception as e:
            return self._create_error_response("", -32603, f"Internal error: {str(e)}")
    
    async def _handle_tools_method(self, method: str, params: Dict, request_id: str) -> str:
        """Handle tools/* methods"""
        if method == "tools/list":
            return await self._list_tools(params, request_id)
        elif method == "tools/call":
            return await self._call_tool(params, request_id)
        else:
            return self._create_error_response(request_id, -32601, "Method not found")
    
    async def _handle_resources_method(self, method: str, params: Dict, request_id: str) -> str:
        """Handle resources/* methods"""
        if method == "resources/list":
            return await self._list_resources(params, request_id)
        elif method == "resources/read":
            return await self._read_resource(params, request_id)
        else:
            return self._create_error_response(request_id, -32601, "Method not found")
    
    async def _handle_prompts_method(self, method: str, params: Dict, request_id: str) -> str:
        """Handle prompts/* methods"""
        if method == "prompts/list":
            return await self._list_prompts(params, request_id)
        elif method == "prompts/get":
            return await self._get_prompt(params, request_id)
        else:
            return self._create_error_response(request_id, -32601, "Method not found")
    
    async def _list_tools(self, params: Dict, request_id: str) -> str:
        """List available tools"""
        tools = []
        
        # Memory tools
        if self.memory_system:
            tools.extend([
                {
                    "name": "memory_store",
                    "description": "Store information in memory with citation tracking",
                    "inputSchema": {
                        "type": "object",
                        "properties": {
                            "content": {"type": "string"},
                            "mom_type": {"type": "string", "enum": ["decision", "pattern", "fact", "learning", "constraint"]},
                            "category": {"type": "string"},
                            "importance": {"type": "number"},
                            "tags": {"type": "array", "items": {"type": "string"}}
                        },
                        "required": ["content", "mom_type"]
                    }
                },
                {
                    "name": "memory_recall",
                    "description": "Recall information from memory with citation",
                    "inputSchema": {
                        "type": "object",
                        "properties": {
                            "query": {"type": "string"},
                            "mom_type": {"type": "string"},
                            "category": {"type": "string"},
                            "limit": {"type": "number"}
                        },
                        "required": ["query"]
                    }
                },
                {
                    "name": "memory_search",
                    "description": "Search memories by content",
                    "inputSchema": {
                        "type": "object",
                        "properties": {
                            "query_text": {"type": "string"},
                            "limit": {"type": "number"}
                        },
                        "required": ["query_text"]
                    }
                }
            ])
        
        # Context tools
        if self.context_manager:
            tools.extend([
                {
                    "name": "context_optimize",
                    "description": "Optimize context for token efficiency",
                    "inputSchema": {
                        "type": "object",
                        "properties": {
                            "files": {"type": "array"},
                            "target_capacity": {"type": "number"}
                        },
                        "required": ["files"]
                    }
                },
                {
                    "name": "context_cluster",
                    "description": "Cluster files by semantic similarity",
                    "inputSchema": {
                        "type": "object",
                        "properties": {
                            "files": {"type": "array"}
                        },
                        "required": ["files"]
                    }
                }
            ])
        
        response = MCPResponse(id=request_id, result={"tools": tools})
        return json.dumps(asdict(response))
    
    async def _call_tool(self, params: Dict, request_id: str) -> str:
        """Execute a tool call"""
        tool_name = params.get("name")
        arguments = params.get("arguments", {})
        
        if not tool_name:
            return self._create_error_response(request_id, -32602, "Tool name required")
        
        try:
            if tool_name == "memory_store" and self.memory_system:
                return await self._tool_memory_store(arguments, request_id)
            elif tool_name == "memory_recall" and self.memory_system:
                return await self._tool_memory_recall(arguments, request_id)
            elif tool_name == "memory_search" and self.memory_system:
                return await self._tool_memory_search(arguments, request_id)
            elif tool_name == "context_optimize" and self.context_manager:
                return await self._tool_context_optimize(arguments, request_id)
            elif tool_name == "context_cluster" and self.context_manager:
                return await self._tool_context_cluster(arguments, request_id)
            else:
                return self._create_error_response(request_id, -32601, f"Tool '{tool_name}' not found")
                
        except Exception as e:
            return self._create_error_response(request_id, -32603, f"Tool execution error: {str(e)}")
    
    async def _tool_memory_store(self, args: Dict, request_id: str) -> str:
        """Store memory tool implementation"""
        content = args["content"]
        mom_type = args["mom_type"]
        category = args.get("category", "general")
        importance = args.get("importance", 0.5)
        tags = args.get("tags", [])
        
        memory_data = MemoryData(
            id=f"mem_{uuid.uuid4().hex[:8]}",
            content=content,
            mom_type=mom_type,
            category=category,
            importance=importance,
            tags=tags
        )
        
        memory_id = self.memory_system.store_with_citation(memory_data)
        
        response = MCPResponse(
            id=request_id,
            result={
                "success": True,
                "memory_id": memory_id,
                "citation": f"Source: {memory_id} (session: {memory_data.session_id or 'unknown'})"
            }
        )
        return json.dumps(asdict(response))
    
    async def _tool_memory_recall(self, args: Dict, request_id: str) -> str:
        """Recall memory tool implementation"""
        query_text = args["query"]
        mom_type = args.get("mom_type")
        category = args.get("category")
        limit = args.get("limit", 10)
        
        query = MemoryQuery(
            text=query_text,
            mom_type=mom_type,
            category=category,
            limit=limit
        )
        
        results = self.memory_system.recall_with_citation(query)
        
        formatted_results = []
        for result in results:
            memory = result["memory"]
            formatted_results.append({
                "content": memory["content"],
                "mom_type": memory["mom_type"],
                "category": memory["category"],
                "importance": memory["importance"],
                "citation": result["citation"],
                "similarity_score": result["similarity_score"],
                "related_memories": result["related_memories"][:2]  # Limit related memories
            })
        
        response = MCPResponse(
            id=request_id,
            result={
                "memories": formatted_results,
                "total_found": len(formatted_results)
            }
        )
        return json.dumps(asdict(response))
    
    async def _tool_memory_search(self, args: Dict, request_id: str) -> str:
        """Search memory tool implementation"""
        query_text = args["query_text"]
        limit = args.get("limit", 10)
        
        memories = self.memory_system.search_full_text(query_text, limit)
        
        formatted_memories = []
        for memory in memories:
            formatted_memories.append({
                "id": memory.id,
                "content": memory.content,
                "mom_type": memory.mom_type,
                "category": memory.category,
                "importance": memory.importance,
                "timestamp": memory.timestamp,
                "session_id": memory.session_id
            })
        
        response = MCPResponse(
            id=request_id,
            result={
                "memories": formatted_memories,
                "total_found": len(formatted_memories)
            }
        )
        return json.dumps(asdict(response))
    
    async def _tool_context_optimize(self, args: Dict, request_id: str) -> str:
        """Context optimization tool implementation"""
        files_data = args["files"]
        target_capacity = args.get("target_capacity", 50000)
        
        # Convert to File objects
        files = []
        for file_data in files_data:
            files.append(File(
                path=file_data["path"],
                content=file_data["content"],
                size=len(file_data["content"])
            ))
        
        # Optimize context
        pruned_files = self.context_manager.prune_context(files, target_capacity)
        
        # Convert back to dict
        result_files = []
        for file in pruned_files:
            result_files.append({
                "path": file.path,
                "content": file.content,
                "size": file.size
            })
        
        response = MCPResponse(
            id=request_id,
            result={
                "optimized_files": result_files,
                "original_count": len(files),
                "optimized_count": len(result_files),
                "compression_ratio": len(result_files) / len(files) if files else 0
            }
        )
        return json.dumps(asdict(response))
    
    async def _tool_context_cluster(self, args: Dict, request_id: str) -> str:
        """Context clustering tool implementation"""
        files_data = args["files"]
        
        # Convert to File objects
        files = []
        for file_data in files_data:
            files.append(File(
                path=file_data["path"],
                content=file_data["content"],
                size=len(file_data["content"])
            ))
        
        # Load context to get clusters
        context = self.context_manager.load_context(files)
        
        # Format clusters
        formatted_clusters = {}
        for cluster_name, cluster_files in context["clusters"].items():
            formatted_clusters[cluster_name] = [
                {
                    "path": file.path,
                    "size": file.size
                }
                for file in cluster_files
            ]
        
        response = MCPResponse(
            id=request_id,
            result={
                "clusters": formatted_clusters,
                "total_files": context["total_files"],
                "cluster_count": context["cluster_count"]
            }
        )
        return json.dumps(asdict(response))
    
    async def _list_resources(self, params: Dict, request_id: str) -> str:
        """List available resources"""
        resources = []
        
        if self.memory_system:
            resources.extend([
                {
                    "uri": "memory://statistics",
                    "name": "Memory Statistics",
                    "description": "Current memory system statistics",
                    "mimeType": "application/json"
                },
                {
                    "uri": "memory://export",
                    "name": "Memory Export",
                    "description": "Export all memories",
                    "mimeType": "application/json"
                }
            ])
        
        response = MCPResponse(id=request_id, result={"resources": resources})
        return json.dumps(asdict(response))
    
    async def _read_resource(self, params: Dict, request_id: str) -> str:
        """Read a resource"""
        uri = params.get("uri")
        
        if not uri:
            return self._create_error_response(request_id, -32602, "URI required")
        
        try:
            if uri == "memory://statistics" and self.memory_system:
                stats = self.memory_system.get_statistics()
                response = MCPResponse(id=request_id, result={
                    "contents": [
                        {
                            "uri": uri,
                            "mimeType": "application/json",
                            "text": json.dumps(stats, indent=2)
                        }
                    ]
                })
                return json.dumps(asdict(response))
            elif uri == "memory://export" and self.memory_system:
                # Export all memories
                all_memories = []
                for mom_type in ["decision", "pattern", "fact", "learning", "constraint"]:
                    memories = self.memory_system.get_by_mom_type(mom_type, limit=100)
                    for memory in memories:
                        all_memories.append({
                            "id": memory.id,
                            "content": memory.content,
                            "mom_type": memory.mom_type,
                            "category": memory.category,
                            "importance": memory.importance,
                            "timestamp": memory.timestamp,
                            "session_id": memory.session_id,
                            "tags": memory.tags
                        })
                
                export_data = {
                    "export_timestamp": datetime.now().isoformat(),
                    "total_memories": len(all_memories),
                    "memories": all_memories
                }
                
                response = MCPResponse(id=request_id, result={
                    "contents": [
                        {
                            "uri": uri,
                            "mimeType": "application/json",
                            "text": json.dumps(export_data, indent=2)
                        }
                    ]
                })
                return json.dumps(asdict(response))
            else:
                return self._create_error_response(request_id, -32601, f"Resource '{uri}' not found")
                
        except Exception as e:
            return self._create_error_response(request_id, -32603, f"Resource read error: {str(e)}")
    
    async def _list_prompts(self, params: Dict, request_id: str) -> str:
        """List available prompts"""
        prompts = [
            {
                "name": "memory_context",
                "description": "Load relevant memories as context",
                "arguments": [
                    {
                        "name": "query",
                        "description": "Query to search for relevant memories",
                        "required": True
                    },
                    {
                        "name": "limit",
                        "description": "Maximum number of memories to include",
                        "required": False
                    }
                ]
            },
            {
                "name": "project_summary",
                "description": "Generate project summary from memories",
                "arguments": [
                    {
                        "name": "session_id",
                        "description": "Session ID to focus on",
                        "required": False
                    }
                ]
            }
        ]
        
        response = MCPResponse(id=request_id, result={"prompts": prompts})
        return json.dumps(asdict(response))
    
    async def _get_prompt(self, params: Dict, request_id: str) -> str:
        """Get a specific prompt"""
        name = params.get("name")
        arguments = params.get("arguments", {})
        
        if not name:
            return self._create_error_response(request_id, -32602, "Prompt name required")
        
        try:
            if name == "memory_context" and self.memory_system:
                query = arguments.get("query", "")
                limit = arguments.get("limit", 5)
                
                memory_query = MemoryQuery(text=query, limit=limit)
                results = self.memory_system.recall_with_citation(memory_query)
                
                # Build prompt context
                context_lines = [f"# Relevant Memories for: {query}"]
                for result in results:
                    memory = result["memory"]
                    context_lines.append(f"## {memory['mom_type'].title()}: {memory['category']}")
                    context_lines.append(f"{memory['content']}")
                    context_lines.append(f"*{result['citation']}*")
                    context_lines.append("")
                
                prompt_content = "\n".join(context_lines)
                
                response = MCPResponse(id=request_id, result={
                    "description": f"Context from {len(results)} relevant memories",
                    "messages": [
                        {
                            "role": "system",
                            "content": {
                                "type": "text",
                                "text": "Use the following memories as context for your response:"
                            }
                        },
                        {
                            "role": "user", 
                            "content": {
                                "type": "text",
                                "text": prompt_content
                            }
                        }
                    ]
                })
                return json.dumps(asdict(response))
                
            elif name == "project_summary" and self.memory_system:
                session_id = arguments.get("session_id")
                
                if session_id:
                    memories = self.memory_system.get_session_memories(session_id)
                else:
                    # Get recent memories across all sessions
                    memories = []
                    for mom_type in ["decision", "pattern", "fact", "learning", "constraint"]:
                        memories.extend(self.memory_system.get_by_mom_type(mom_type, limit=5))
                
                # Group by type
                by_type = {}
                for memory in memories:
                    if memory.mom_type not in by_type:
                        by_type[memory.mom_type] = []
                    by_type[memory.mom_type].append(memory)
                
                # Build summary
                summary_lines = ["# Project Summary"]
                summary_lines.append(f"Generated on: {datetime.now().isoformat()}")
                summary_lines.append("")
                
                for mom_type, type_memories in by_type.items():
                    summary_lines.append(f"## {mom_type.title()}s ({len(type_memories)})")
                    for memory in type_memories[:3]:  # Limit to 3 per type
                        summary_lines.append(f"- {memory.content}")
                    summary_lines.append("")
                
                prompt_content = "\n".join(summary_lines)
                
                response = MCPResponse(id=request_id, result={
                    "description": "Project summary from memory",
                    "messages": [
                        {
                            "role": "system",
                            "content": {
                                "type": "text",
                                "text": "Based on the project summary:"
                            }
                        },
                        {
                            "role": "user",
                            "content": {
                                "type": "text", 
                                "text": prompt_content
                            }
                        }
                    ]
                })
                return json.dumps(asdict(response))
            else:
                return self._create_error_response(request_id, -32601, f"Prompt '{name}' not found")
                
        except Exception as e:
            return self._create_error_response(request_id, -32603, f"Prompt generation error: {str(e)}")
    
    def _create_error_response(self, request_id: str, code: int, message: str) -> str:
        """Create an error response"""
        response = MCPResponse(
            id=request_id,
            error={
                "code": code,
                "message": message
            }
        )
        return json.dumps(asdict(response))
    
    async def run_stdio(self):
        """Run the MCP server over stdio"""
        self.logger.info(f"Starting MCP server: {self.name} v{self.version}")
        
        while True:
            try:
                # Read request from stdin
                line = await asyncio.get_event_loop().run_in_executor(
                    None, sys.stdin.readline
                )
                
                if not line:
                    break
                
                line = line.strip()
                if not line:
                    continue
                
                # Handle request
                response = await self.handle_request(line)
                
                # Send response to stdout
                print(response, flush=True)
                
            except KeyboardInterrupt:
                break
            except Exception as e:
                self.logger.error(f"Error handling request: {e}")
                error_response = self._create_error_response("", -32603, f"Server error: {str(e)}")
                print(error_response, flush=True)
        
        self.logger.info("MCP server stopped")
    
    def cleanup(self):
        """Cleanup resources"""
        if self.memory_system:
            self.memory_system.cleanup()


# Factory functions for different server types
def create_memory_server() -> MCPServer:
    """Create MCP server focused on memory operations"""
    server = MCPServer("superdev-memory", "1.0.0")
    return server


def create_context_server() -> MCPServer:
    """Create MCP server focused on context optimization"""
    server = MCPServer("superdev-context", "1.0.0")
    return server


def create_full_server() -> MCPServer:
    """Create full-featured MCP server"""
    server = MCPServer("superdev-full", "1.0.0")
    return server


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="SUPERDEV MCP Server")
    parser.add_argument("--server-type", choices=["memory", "context", "full"], 
                       default="full", help="Type of MCP server to run")
    parser.add_argument("--log-level", choices=["DEBUG", "INFO", "WARNING", "ERROR"], 
                       default="INFO", help="Log level")
    
    args = parser.parse_args()
    
    # Setup logging
    logging.basicConfig(
        level=getattr(logging, args.log_level),
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    # Create server
    if args.server_type == "memory":
        server = create_memory_server()
    elif args.server_type == "context":
        server = create_context_server()
    else:
        server = create_full_server()
    
    # Run server
    try:
        asyncio.run(server.run_stdio())
    except KeyboardInterrupt:
        print("\nShutting down server...")
    finally:
        server.cleanup()
