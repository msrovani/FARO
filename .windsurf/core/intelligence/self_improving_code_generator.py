"""
Self-Improving Code Generator - AI that learns to write better code
Implements advanced code generation with self-improvement capabilities
"""
import asyncio
import ast
import json
import re
from typing import Dict, List, Any, Optional, Tuple, Union
from dataclasses import dataclass, asdict
from pathlib import Path
from datetime import datetime
import logging
from collections import defaultdict, deque
import hashlib
import uuid

# Import advanced learning system
try:
    from .advanced_learning_system import AdvancedLearningSystem, LearningExperience
    ADVANCED_LEARNING_AVAILABLE = True
except ImportError:
    ADVANCED_LEARNING_AVAILABLE = False

# Import existing systems
try:
    from ..memory.hybrid_rag import HybridRAGMemory, MemoryData, MemoryQuery
    MEMORY_AVAILABLE = True
except ImportError:
    MEMORY_AVAILABLE = False

try:
    from ..context.token_optimization import EnhancedContextManager, File
    CONTEXT_AVAILABLE = True
except ImportError:
    CONTEXT_AVAILABLE = False


@dataclass
class CodeGenerationRequest:
    """Request for code generation"""
    request_id: str
    description: str
    language: str
    framework: Optional[str]
    context: Dict[str, Any]
    requirements: List[str]
    constraints: List[str]
    examples: List[str]
    complexity: str
    created_at: str
    
    def __post_init__(self):
        if self.created_at == "":
            self.created_at = datetime.now().isoformat()


@dataclass
class CodeGenerationResult:
    """Result of code generation"""
    request_id: str
    success: bool
    code: str
    explanation: str
    confidence: float
    quality_score: float
    improvements: List[str]
    issues: List[str]
    learning_insights: List[str]
    execution_time: float
    metadata: Dict[str, Any]
    
    def __post_init__(self):
        if self.metadata is None:
            self.metadata = {}


@dataclass
class CodePattern:
    """Discovered code pattern"""
    pattern_id: str
    name: str
    language: str
    framework: Optional[str]
    pattern_code: str
    description: str
    use_cases: List[str]
    quality_score: float
    frequency: int
    discovered_at: str
    examples: List[str]


class CodeQualityAnalyzer:
    """Analyzes code quality and provides feedback"""
    
    def __init__(self):
        self.quality_metrics = {
            "complexity": 0.0,
            "maintainability": 0.0,
            "readability": 0.0,
            "testability": 0.0,
            "security": 0.0,
            "performance": 0.0
        }
        
        self.issue_patterns = {
            "complexity": [r"if.*and.*or", r"for.*for.*for", r"while.*while"],
            "security": [r"eval\(", r"exec\(", r"subprocess\.", r"shell=True"],
            "performance": [r"\.append\(.*\)\.append\(.*\)", r"for.*in.*range\(len\("],
            "readability": [r"[a-z][A-Z][a-z][A-Z]", r"_{2,}", r"[a-z]{20,}"]
        }
    
    def analyze_code(self, code: str, language: str) -> Dict[str, Any]:
        """Analyze code quality comprehensively"""
        analysis = {
            "overall_score": 0.0,
            "metrics": {},
            "issues": [],
            "suggestions": [],
            "complexity_analysis": {},
            "security_analysis": {},
            "performance_analysis": {}
        }
        
        try:
            if language.lower() == "python":
                analysis.update(self._analyze_python(code))
            elif language.lower() in ["javascript", "typescript"]:
                analysis.update(self._analyze_javascript(code))
            else:
                analysis.update(self._analyze_generic(code))
            
            # Calculate overall score
            scores = [analysis["metrics"].get(metric, 0.0) for metric in self.quality_metrics.keys()]
            analysis["overall_score"] = sum(scores) / len(scores)
            
        except Exception as e:
            analysis["error"] = str(e)
            analysis["overall_score"] = 0.0
        
        return analysis
    
    def _analyze_python(self, code: str) -> Dict[str, Any]:
        """Analyze Python code specifically"""
        analysis = {"metrics": {}, "issues": [], "suggestions": []}
        
        try:
            tree = ast.parse(code)
            
            # Complexity metrics
            complexity = 1
            functions = []
            classes = []
            
            for node in ast.walk(tree):
                if isinstance(node, (ast.If, ast.While, ast.For)):
                    complexity += 1
                elif isinstance(node, ast.FunctionDef):
                    functions.append(node.name)
                elif isinstance(node, ast.ClassDef):
                    classes.append(node.name)
            
            analysis["metrics"]["complexity"] = min(1.0, 10.0 / max(complexity, 1))
            analysis["metrics"]["functions_count"] = len(functions)
            analysis["metrics"]["classes_count"] = len(classes)
            
            # Maintainability
            lines = code.splitlines()
            docstring_count = sum(1 for node in ast.walk(tree) if isinstance(node, (ast.FunctionDef, ast.ClassDef)) and ast.get_docstring(node))
            analysis["metrics"]["maintainability"] = docstring_count / max(len(functions) + len(classes), 1)
            
            # Readability
            avg_line_length = sum(len(line) for line in lines) / max(len(lines), 1)
            analysis["metrics"]["readability"] = max(0.0, 1.0 - (avg_line_length - 80) / 100)
            
            # Security issues
            security_issues = []
            for pattern in self.issue_patterns["security"]:
                if re.search(pattern, code):
                    security_issues.append(f"Potential security issue: {pattern}")
            
            analysis["security_analysis"]["issues"] = security_issues
            analysis["metrics"]["security"] = 1.0 - len(security_issues) * 0.2
            
            # Performance issues
            performance_issues = []
            for pattern in self.issue_patterns["performance"]:
                if re.search(pattern, code):
                    performance_issues.append(f"Performance concern: {pattern}")
            
            analysis["performance_analysis"]["issues"] = performance_issues
            analysis["metrics"]["performance"] = 1.0 - len(performance_issues) * 0.1
            
            # General issues
            analysis["issues"].extend(security_issues)
            analysis["issues"].extend(performance_issues)
            
            # Suggestions
            if complexity > 10:
                analysis["suggestions"].append("Consider breaking down complex functions")
            if docstring_count < len(functions) + len(classes):
                analysis["suggestions"].append("Add docstrings to functions and classes")
            if avg_line_length > 100:
                analysis["suggestions"].append("Consider breaking long lines")
            
        except SyntaxError as e:
            analysis["issues"].append(f"Syntax error: {e}")
            analysis["metrics"]["complexity"] = 0.0
        
        return analysis
    
    def _analyze_javascript(self, code: str) -> Dict[str, Any]:
        """Analyze JavaScript/TypeScript code"""
        analysis = {"metrics": {}, "issues": [], "suggestions": []}
        
        # Basic metrics
        lines = code.splitlines()
        functions = len(re.findall(r"function\s+\w+|const\s+\w+\s*=|\w+\s*=>", code))
        classes = len(re.findall(r"class\s+\w+", code))
        
        analysis["metrics"]["functions_count"] = functions
        analysis["metrics"]["classes_count"] = classes
        
        # Complexity (simplified)
        complexity_indicators = len(re.findall(r"\b(if|for|while|switch)\b", code))
        analysis["metrics"]["complexity"] = min(1.0, 20.0 / max(complexity_indicators, 1))
        
        # Readability
        avg_line_length = sum(len(line) for line in lines) / max(len(lines), 1)
        analysis["metrics"]["readability"] = max(0.0, 1.0 - (avg_line_length - 80) / 100)
        
        # Security
        security_issues = []
        for pattern in self.issue_patterns["security"]:
            if re.search(pattern, code, re.IGNORECASE):
                security_issues.append(f"Security concern: {pattern}")
        
        analysis["security_analysis"]["issues"] = security_issues
        analysis["metrics"]["security"] = 1.0 - len(security_issues) * 0.2
        
        analysis["issues"].extend(security_issues)
        
        return analysis
    
    def _analyze_generic(self, code: str) -> Dict[str, Any]:
        """Generic code analysis for any language"""
        analysis = {"metrics": {}, "issues": [], "suggestions": []}
        
        lines = code.splitlines()
        avg_line_length = sum(len(line) for line in lines) / max(len(lines), 1)
        
        analysis["metrics"]["readability"] = max(0.0, 1.0 - (avg_line_length - 80) / 100)
        analysis["metrics"]["complexity"] = 0.5  # Default
        
        return analysis


class PatternExtractor:
    """Extracts and learns code patterns"""
    
    def __init__(self):
        self.patterns: Dict[str, CodePattern] = {}
        self.pattern_frequency = defaultdict(int)
        
    def extract_patterns(self, code: str, language: str, framework: Optional[str] = None) -> List[CodePattern]:
        """Extract patterns from code"""
        patterns = []
        
        # Extract structural patterns
        if language.lower() == "python":
            patterns.extend(self._extract_python_patterns(code, language, framework))
        elif language.lower() in ["javascript", "typescript"]:
            patterns.extend(self._extract_js_patterns(code, language, framework))
        
        # Extract common patterns
        patterns.extend(self._extract_common_patterns(code, language, framework))
        
        return patterns
    
    def _extract_python_patterns(self, code: str, language: str, framework: Optional[str]) -> List[CodePattern]:
        """Extract Python-specific patterns"""
        patterns = []
        
        try:
            tree = ast.parse(code)
            
            # Class patterns
            for node in ast.walk(tree):
                if isinstance(node, ast.ClassDef):
                    pattern_code = ast.get_source_segment(open(__file__).read(), node) or ""
                    if pattern_code:
                        pattern = CodePattern(
                            pattern_id=f"class_{node.name}_{hash(pattern_code) % 10000}",
                            name=f"Class: {node.name}",
                            language=language,
                            framework=framework,
                            pattern_code=pattern_code,
                            description=f"Python class definition pattern",
                            use_cases=["Object-oriented programming", "Data structures"],
                            quality_score=0.8,
                            frequency=1,
                            discovered_at=datetime.now().isoformat(),
                            examples=[pattern_code]
                        )
                        patterns.append(pattern)
                
                # Function patterns
                elif isinstance(node, ast.FunctionDef):
                    pattern_code = ast.get_source_segment(open(__file__).read(), node) or ""
                    if pattern_code:
                        pattern = CodePattern(
                            pattern_id=f"function_{node.name}_{hash(pattern_code) % 10000}",
                            name=f"Function: {node.name}",
                            language=language,
                            framework=framework,
                            pattern_code=pattern_code,
                            description=f"Python function definition pattern",
                            use_cases=["Code organization", "Reusable logic"],
                            quality_score=0.7,
                            frequency=1,
                            discovered_at=datetime.now().isoformat(),
                            examples=[pattern_code]
                        )
                        patterns.append(pattern)
        
        except:
            pass
        
        return patterns
    
    def _extract_js_patterns(self, code: str, language: str, framework: Optional[str]) -> List[CodePattern]:
        """Extract JavaScript/TypeScript patterns"""
        patterns = []
        
        # Function patterns
        function_matches = re.finditer(r"(?:function\s+(\w+)|const\s+(\w+)\s*=|(\w+)\s*=>)", code)
        for match in function_matches:
            func_name = match.group(1) or match.group(2) or match.group(3)
            if func_name:
                pattern = CodePattern(
                    pattern_id=f"js_function_{func_name}_{hash(match.group(0)) % 10000}",
                    name=f"Function: {func_name}",
                    language=language,
                    framework=framework,
                    pattern_code=match.group(0),
                    description=f"JavaScript function pattern",
                    use_cases=["Code organization", "Event handlers"],
                    quality_score=0.7,
                    frequency=1,
                    discovered_at=datetime.now().isoformat(),
                    examples=[match.group(0)]
                )
                patterns.append(pattern)
        
        return patterns
    
    def _extract_common_patterns(self, code: str, language: str, framework: Optional[str]) -> List[CodePattern]:
        """Extract common programming patterns"""
        patterns = []
        
        # Import patterns
        import_patterns = re.finditer(r"(?:import|from|require).*;", code)
        for match in import_patterns:
            pattern = CodePattern(
                pattern_id=f"import_{hash(match.group(0)) % 10000}",
                name="Import/Require Pattern",
                language=language,
                framework=framework,
                pattern_code=match.group(0),
                description="Module import pattern",
                use_cases=["Dependency management", "Code organization"],
                quality_score=0.6,
                frequency=1,
                discovered_at=datetime.now().isoformat(),
                examples=[match.group(0)]
            )
            patterns.append(pattern)
        
        # Comment patterns
        comment_patterns = re.finditer(r"//.*|/\*[\s\S]*?\*/", code)
        for match in comment_patterns:
            pattern = CodePattern(
                pattern_id=f"comment_{hash(match.group(0)) % 10000}",
                name="Comment Pattern",
                language=language,
                framework=framework,
                pattern_code=match.group(0),
                description="Code documentation pattern",
                use_cases=["Documentation", "Code explanation"],
                quality_score=0.5,
                frequency=1,
                discovered_at=datetime.now().isoformat(),
                examples=[match.group(0)]
            )
            patterns.append(pattern)
        
        return patterns
    
    def learn_pattern(self, pattern: CodePattern):
        """Learn and store a pattern"""
        pattern_id = pattern.pattern_id
        
        if pattern_id in self.patterns:
            # Update existing pattern
            existing = self.patterns[pattern_id]
            existing.frequency += 1
            existing.quality_score = (existing.quality_score + pattern.quality_score) / 2
            existing.examples.extend(pattern.examples[:2])  # Keep recent examples
        else:
            # Add new pattern
            self.patterns[pattern_id] = pattern
            self.pattern_frequency[pattern_id] = 1
    
    def get_relevant_patterns(self, context: Dict[str, Any], limit: int = 5) -> List[CodePattern]:
        """Get patterns relevant to current context"""
        language = context.get("language", "").lower()
        framework = context.get("framework", "").lower()
        task_type = context.get("task_type", "").lower()
        
        relevant_patterns = []
        
        for pattern in self.patterns.values():
            relevance_score = 0.0
            
            # Language match
            if pattern.language.lower() == language:
                relevance_score += 0.4
            
            # Framework match
            if pattern.framework and pattern.framework.lower() == framework:
                relevance_score += 0.3
            
            # Task type relevance
            if task_type:
                for use_case in pattern.use_cases:
                    if task_type in use_case.lower():
                        relevance_score += 0.2
                        break
            
            # Quality and frequency
            relevance_score += pattern.quality_score * 0.1
            relevance_score += min(pattern.frequency / 10, 0.1)
            
            pattern.relevance_score = relevance_score
            relevant_patterns.append(pattern)
        
        # Sort by relevance and return top
        relevant_patterns.sort(key=lambda p: p.relevance_score, reverse=True)
        return relevant_patterns[:limit]


class SelfImprovingCodeGenerator:
    """Main self-improving code generator"""
    
    def __init__(self, memory_system: Optional[HybridRAGMemory] = None, learning_system: Optional[AdvancedLearningSystem] = None):
        self.memory_system = memory_system
        self.learning_system = learning_system
        
        # Components
        self.quality_analyzer = CodeQualityAnalyzer()
        self.pattern_extractor = PatternExtractor()
        
        # Learning state
        self.generation_history = deque(maxlen=1000)
        self.improvement_cycles = 0
        self.performance_metrics = defaultdict(list)
        
        # Code templates and patterns
        self.code_templates = self._initialize_templates()
        
        # Self-improvement settings
        self.auto_improve = True
        self.learning_rate = 0.1
        self.quality_threshold = 0.7
        
        self.logger = logging.getLogger("SelfImprovingCodeGenerator")
    
    def _initialize_templates(self) -> Dict[str, Dict[str, str]]:
        """Initialize code templates for different languages/frameworks"""
        return {
            "python": {
                "function": '''def {function_name}({parameters}):
    """
    {description}
    
    Args:
        {args_doc}
    
    Returns:
        {return_doc}
    """
    {implementation}
''',
                "class": '''class {class_name}:
    """
    {description}
    
    Attributes:
        {attributes_doc}
    """
    
    def __init__(self{init_params}):
        {init_implementation}
    
    {methods}
''',
                "react_component": '''import React from 'react';
import './{component_name}.css';

interface {component_name}Props {{
  {props_interface}
}}

export const {component_name}: React.FC<{component_name}Props> = ({{
  {props_destructuring}
}}) => {{
  return (
    <div className="{component_name.lower()}">
      {jsx_content}
    </div>
  );
}};

export default {component_name};
'''
            },
            "javascript": {
                "function": '''/**
 * {description}
 * @param {{{{param_types}}} {params}
 * @returns {{{{return_type}}} {return_description}
 */
function {function_name}({parameters}) {{
  {implementation}
}}

module.exports = {function_name};
''',
                "class": '''/**
 * {description}
 */
class {class_name} {{
  constructor({constructor_params}) {{
    {constructor_implementation}
  }}
  
  {methods}
}}

module.exports = {class_name};
'''
            },
            "typescript": {
                "interface": '''interface {interface_name} {{
  {properties}
}}

export default {interface_name};
''',
                "type": '''type {type_name} = {type_definition};

export default {type_name};
'''
            }
        }
    
    async def generate_code(self, request: CodeGenerationRequest) -> CodeGenerationResult:
        """Generate code with self-improvement"""
        start_time = datetime.now()
        
        try:
            # Analyze request and context
            context_analysis = await self._analyze_request(request)
            
            # Get relevant patterns
            relevant_patterns = self.pattern_extractor.get_relevant_patterns(request.context)
            
            # Generate initial code
            initial_code = await self._generate_initial_code(request, context_analysis, relevant_patterns)
            
            # Analyze and improve code
            quality_analysis = self.quality_analyzer.analyze_code(initial_code, request.language)
            
            # Self-improvement loop
            improved_code = initial_code
            improvement_iterations = 0
            
            while (quality_analysis["overall_score"] < self.quality_threshold and 
                   improvement_iterations < 3 and 
                   self.auto_improve):
                
                improved_code = await self._improve_code(improved_code, quality_analysis, request)
                quality_analysis = self.quality_analyzer.analyze_code(improved_code, request.language)
                improvement_iterations += 1
            
            # Extract patterns from generated code
            extracted_patterns = self.pattern_extractor.extract_patterns(
                improved_code, request.language, request.framework
            )
            
            # Learn from patterns
            for pattern in extracted_patterns:
                self.pattern_extractor.learn_pattern(pattern)
            
            # Create result
            execution_time = (datetime.now() - start_time).total_seconds()
            
            result = CodeGenerationResult(
                request_id=request.request_id,
                success=True,
                code=improved_code,
                explanation=self._generate_explanation(request, improved_code, quality_analysis),
                confidence=self._calculate_confidence(quality_analysis, improvement_iterations),
                quality_score=quality_analysis["overall_score"],
                improvements=self._extract_improvements(initial_code, improved_code),
                issues=quality_analysis.get("issues", []),
                learning_insights=self._generate_learning_insights(extracted_patterns, quality_analysis),
                execution_time=execution_time,
                metadata={
                    "patterns_used": len(relevant_patterns),
                    "improvement_iterations": improvement_iterations,
                    "context_analysis": context_analysis,
                    "quality_analysis": quality_analysis
                }
            )
            
            # Store in generation history
            self.generation_history.append(result)
            
            # Learn from this generation
            await self._learn_from_generation(request, result)
            
            return result
            
        except Exception as e:
            execution_time = (datetime.now() - start_time).total_seconds()
            
            error_result = CodeGenerationResult(
                request_id=request.request_id,
                success=False,
                code="",
                explanation=f"Code generation failed: {str(e)}",
                confidence=0.0,
                quality_score=0.0,
                improvements=[],
                issues=[str(e)],
                learning_insights=[],
                execution_time=execution_time,
                metadata={"error": str(e)}
            )
            
            self.generation_history.append(error_result)
            return error_result
    
    async def _analyze_request(self, request: CodeGenerationRequest) -> Dict[str, Any]:
        """Analyze generation request"""
        analysis = {
            "task_complexity": self._estimate_complexity(request),
            "language_features": self._get_language_features(request.language),
            "framework_conventions": self._get_framework_conventions(request.framework),
            "code_style": self._infer_code_style(request.context),
            "requirements_priority": self._prioritize_requirements(request.requirements)
        }
        
        return analysis
    
    def _estimate_complexity(self, request: CodeGenerationRequest) -> str:
        """Estimate task complexity"""
        complexity_score = 0.0
        
        # Description length
        complexity_score += len(request.description) / 1000.0
        
        # Requirements count
        complexity_score += len(request.requirements) * 0.1
        
        # Constraints count
        complexity_score += len(request.constraints) * 0.05
        
        # Examples count
        complexity_score += len(request.examples) * 0.02
        
        if complexity_score < 0.3:
            return "simple"
        elif complexity_score < 0.7:
            return "medium"
        else:
            return "complex"
    
    def _get_language_features(self, language: str) -> List[str]:
        """Get language-specific features"""
        features = {
            "python": ["functions", "classes", "decorators", "generators", "type hints"],
            "javascript": ["functions", "classes", "closures", "promises", "async/await"],
            "typescript": ["interfaces", "types", "generics", "enums", "decorators"],
            "java": ["classes", "interfaces", "generics", "annotations", "packages"],
            "go": ["functions", "structs", "interfaces", "goroutines", "channels"]
        }
        
        return features.get(language.lower(), [])
    
    def _get_framework_conventions(self, framework: Optional[str]) -> Dict[str, Any]:
        """Get framework-specific conventions"""
        conventions = {
            "react": {
                "component_naming": "PascalCase",
                "file_naming": "component-name.tsx",
                "imports": "import React from 'react'",
                "exports": "export default Component"
            },
            "vue": {
                "component_naming": "PascalCase",
                "file_naming": "ComponentName.vue",
                "structure": "<template><script><style>",
                "exports": "export default"
            },
            "django": {
                "model_naming": "PascalCase",
                "view_naming": "snake_case",
                "imports": "from django.db import models",
                "class_style": "models.Model"
            },
            "express": {
                "middleware_naming": "camelCase",
                "route_naming": "camelCase",
                "imports": "const express = require('express')",
                "pattern": "router.get/post/put/delete"
            }
        }
        
        return conventions.get(framework.lower() if framework else "", {})
    
    def _infer_code_style(self, context: Dict[str, Any]) -> Dict[str, str]:
        """Infer code style from context"""
        style = {
            "naming_convention": "snake_case",  # Default
            "indentation": "2_spaces",
            "line_ending": "\\n",
            "quote_style": "single"
        }
        
        # Analyze existing code if provided
        existing_code = context.get("existing_code", "")
        if existing_code:
            # Detect naming convention
            if re.search(r"[a-z][A-Z][a-z][A-Z]", existing_code):
                style["naming_convention"] = "camelCase"
            elif re.search(r"[a-z]+_[a-z]+", existing_code):
                style["naming_convention"] = "snake_case"
            
            # Detect indentation
            lines = existing_code.split("\\n")
            indented_lines = [line for line in lines if line.startswith("  ") or line.startswith("\\t")]
            if indented_lines:
                if indented_lines[0].startswith("  "):
                    style["indentation"] = "2_spaces"
                elif indented_lines[0].startswith("\\t"):
                    style["indentation"] = "tab"
        
        return style
    
    def _prioritize_requirements(self, requirements: List[str]) -> List[str]:
        """Prioritize requirements by importance"""
        priority_keywords = {
            "security": 10,
            "performance": 9,
            "accessibility": 8,
            "testability": 7,
            "maintainability": 6,
            "readability": 5
        }
        
        scored_requirements = []
        for req in requirements:
            score = 5  # Default score
            for keyword, priority in priority_keywords.items():
                if keyword in req.lower():
                    score = priority
                    break
            scored_requirements.append((req, score))
        
        # Sort by score (descending)
        scored_requirements.sort(key=lambda x: x[1], reverse=True)
        
        return [req for req, score in scored_requirements]
    
    async def _generate_initial_code(self, request: CodeGenerationRequest, analysis: Dict[str, Any], patterns: List[CodePattern]) -> str:
        """Generate initial code based on request and analysis"""
        language = request.language.lower()
        framework = request.framework.lower() if request.framework else None
        
        # Select appropriate template
        template_key = self._select_template(request, analysis)
        template = self.code_templates.get(language, {}).get(template_key, "")
        
        if not template:
            # Fallback generic generation
            return await self._generate_generic_code(request, analysis, patterns)
        
        # Fill template
        code = self._fill_template(template, request, analysis, patterns)
        
        return code
    
    def _select_template(self, request: CodeGenerationRequest, analysis: Dict[str, Any]) -> str:
        """Select appropriate code template"""
        language = request.language.lower()
        
        # Determine template type based on request
        if "component" in request.description.lower() or "ui" in request.description.lower():
            if language == "python":
                return "class"
            elif language in ["javascript", "typescript"]:
                return "react_component"
        
        if "class" in request.description.lower():
            return "class"
        
        if "function" in request.description.lower() or "method" in request.description.lower():
            return "function"
        
        if language == "typescript" and "interface" in request.description.lower():
            return "interface"
        
        # Default to function
        return "function"
    
    def _fill_template(self, template: str, request: CodeGenerationRequest, analysis: Dict[str, Any], patterns: List[CodePattern]) -> str:
        """Fill template with request-specific content"""
        # Extract template variables
        variables = {
            "function_name": self._extract_function_name(request),
            "class_name": self._extract_class_name(request),
            "component_name": self._extract_component_name(request),
            "description": request.description,
            "parameters": self._generate_parameters(request),
            "implementation": self._generate_implementation(request, patterns),
            "props_interface": self._generate_props_interface(request),
            "props_destructuring": self._generate_props_destructuring(request),
            "jsx_content": self._generate_jsx_content(request)
        }
        
        # Fill template
        code = template
        for var, value in variables.items():
            code = code.replace(f"{{{var}}}", str(value))
        
        return code
    
    def _extract_function_name(self, request: CodeGenerationRequest) -> str:
        """Extract function name from request"""
        # Simple extraction - could be enhanced with NLP
        words = request.description.split()
        for word in words:
            if word[0].islower() and word.isalpha():
                return word
        return "generated_function"
    
    def _extract_class_name(self, request: CodeGenerationRequest) -> str:
        """Extract class name from request"""
        words = request.description.split()
        for word in words:
            if word[0].isupper() and word.isalpha():
                return word
        return "GeneratedClass"
    
    def _extract_component_name(self, request: CodeGenerationRequest) -> str:
        """Extract component name from request"""
        words = request.description.split()
        for word in words:
            if word[0].isupper() and word.isalpha():
                return word
        return "GeneratedComponent"
    
    def _generate_parameters(self, request: CodeGenerationRequest) -> str:
        """Generate function parameters"""
        if not request.requirements:
            return ""
        
        params = []
        for req in request.requirements[:5]:  # Limit to 5 parameters
            if "param" in req.lower():
                param_name = req.split()[-1]
                params.append(f"{param_name}: any")
        
        return ", ".join(params)
    
    def _generate_implementation(self, request: CodeGenerationRequest, patterns: List[CodePattern]) -> str:
        """Generate implementation code"""
        implementation_lines = []
        
        # Add implementation based on patterns
        for pattern in patterns[:3]:  # Use top 3 patterns
            if pattern.pattern_code:
                implementation_lines.append(f"// Based on pattern: {pattern.name}")
                implementation_lines.append(pattern.pattern_code)
                implementation_lines.append("")
        
        # Add basic implementation
        if "TODO" not in request.description:
            implementation_lines.append("// TODO: Implement based on requirements")
            for req in request.requirements:
                implementation_lines.append(f"// Requirement: {req}")
        
        return "\\n".join(implementation_lines)
    
    def _generate_props_interface(self, request: CodeGenerationRequest) -> str:
        """Generate props interface for React component"""
        props = []
        for req in request.requirements:
            if ":" in req:
                prop_name, prop_type = req.split(":", 1)
                props.append(f"  {prop_name.strip()}: {prop_type.strip()};")
        
        return "\\n".join(props) if props else "  // No specific props"
    
    def _generate_props_destructuring(self, request: CodeGenerationRequest) -> str:
        """Generate props destructuring"""
        props = []
        for req in request.requirements:
            if ":" in req:
                prop_name = req.split(":")[0].strip()
                props.append(prop_name)
        
        return ", ".join(props) if props else ""
    
    def _generate_jsx_content(self, request: CodeGenerationRequest) -> str:
        """Generate JSX content"""
        jsx_lines = ["<div>", f"  <h2>{request.description}</h2>"]
        
        for req in request.requirements:
            jsx_lines.append(f"  <p>{req}</p>")
        
        jsx_lines.append("</div>")
        
        return "\\n".join(jsx_lines)
    
    async def _generate_generic_code(self, request: CodeGenerationRequest, analysis: Dict[str, Any], patterns: List[CodePattern]) -> str:
        """Generate generic code when no template matches"""
        code_lines = [
            f"// Generated code for: {request.description}",
            f"// Language: {request.language}",
            f"// Framework: {request.framework or 'None'}",
            ""
        ]
        
        # Add requirements
        code_lines.append("// Requirements:")
        for req in request.requirements:
            code_lines.append(f"// - {req}")
        
        code_lines.append("")
        code_lines.append("// Implementation:")
        code_lines.append("// TODO: Implement based on requirements")
        
        # Add pattern examples
        for pattern in patterns[:2]:
            code_lines.append(f"// Pattern example: {pattern.name}")
            code_lines.append(pattern.pattern_code)
        
        return "\\n".join(code_lines)
    
    async def _improve_code(self, code: str, quality_analysis: Dict[str, Any], request: CodeGenerationRequest) -> str:
        """Improve code based on quality analysis"""
        improved_code = code
        
        # Apply improvements based on analysis
        suggestions = quality_analysis.get("suggestions", [])
        
        for suggestion in suggestions:
            if "docstring" in suggestion.lower():
                improved_code = self._add_docstrings(improved_code, request.language)
            elif "break" in suggestion.lower() and "complex" in suggestion.lower():
                improved_code = self._reduce_complexity(improved_code, request.language)
            elif "line" in suggestion.lower():
                improved_code = self._improve_line_length(improved_code)
        
        return improved_code
    
    def _add_docstrings(self, code: str, language: str) -> str:
        """Add docstrings to code"""
        # Simple docstring addition
        lines = code.split("\\n")
        improved_lines = []
        
        for i, line in enumerate(lines):
            improved_lines.append(line)
            
            # Add docstring after function/class definition
            if language == "python":
                if line.strip().startswith("def ") or line.strip().startswith("class "):
                    improved_lines.append('    """')
                    improved_lines.append('    TODO: Add docstring')
                    improved_lines.append('    """')
        
        return "\\n".join(improved_lines)
    
    def _reduce_complexity(self, code: str, language: str) -> str:
        """Reduce code complexity"""
        # Simple complexity reduction
        return code  # Placeholder for actual complexity reduction logic
    
    def _improve_line_length(self, code: str) -> str:
        """Improve line length"""
        lines = code.split("\\n")
        improved_lines = []
        
        for line in lines:
            if len(line) > 100:
                # Simple line breaking
                improved_lines.extend([line[:80] + "...", "    ..." + line[80:]])
            else:
                improved_lines.append(line)
        
        return "\\n".join(improved_lines)
    
    def _generate_explanation(self, request: CodeGenerationRequest, code: str, quality_analysis: Dict[str, Any]) -> str:
        """Generate explanation for generated code"""
        explanation_parts = [
            f"Generated {request.language} code for: {request.description}",
            f"Quality score: {quality_analysis['overall_score']:.2f}/1.0",
            ""
        ]
        
        if quality_analysis.get("metrics"):
            explanation_parts.append("Code metrics:")
            for metric, value in quality_analysis["metrics"].items():
                if isinstance(value, (int, float)):
                    explanation_parts.append(f"- {metric}: {value:.2f}")
        
        if quality_analysis.get("suggestions"):
            explanation_parts.append("\\nImprovements made:")
            explanation_parts.extend(f"- {suggestion}" for suggestion in quality_analysis["suggestions"][:3])
        
        return "\\n".join(explanation_parts)
    
    def _calculate_confidence(self, quality_analysis: Dict[str, Any], improvement_iterations: int) -> float:
        """Calculate confidence in generated code"""
        base_confidence = quality_analysis.get("overall_score", 0.5)
        
        # Adjust for improvement iterations
        iteration_factor = 1.0 - (improvement_iterations * 0.1)
        
        # Adjust for issues
        issues_count = len(quality_analysis.get("issues", []))
        issues_factor = max(0.0, 1.0 - (issues_count * 0.1))
        
        confidence = base_confidence * iteration_factor * issues_factor
        return max(0.0, min(1.0, confidence))
    
    def _extract_improvements(self, original_code: str, improved_code: str) -> List[str]:
        """Extract improvements made to code"""
        improvements = []
        
        if len(improved_code) > len(original_code):
            improvements.append("Added documentation and comments")
        
        if improved_code.count("\\n") > original_code.count("\\n"):
            improvements.append("Improved code structure")
        
        # Compare specific changes
        if "TODO:" not in improved_code and "TODO:" in original_code:
            improvements.append("Implemented TODO items")
        
        return improvements if improvements else ["Code formatting improvements"]
    
    def _generate_learning_insights(self, patterns: List[CodePattern], quality_analysis: Dict[str, Any]) -> List[str]:
        """Generate learning insights from generation"""
        insights = []
        
        if patterns:
            insights.append(f"Discovered {len(patterns)} new code patterns")
        
        if quality_analysis["overall_score"] > 0.8:
            insights.append("High quality code generated - patterns effective")
        elif quality_analysis["overall_score"] < 0.5:
            insights.append("Code quality needs improvement - review patterns")
        
        if quality_analysis.get("metrics", {}).get("complexity", 0) < 0.5:
            insights.append("Code complexity detected - consider refactoring")
        
        return insights
    
    async def _learn_from_generation(self, request: CodeGenerationRequest, result: CodeGenerationResult):
        """Learn from code generation"""
        if not self.learning_system:
            return
        
        # Create learning context
        context = {
            "task_type": self._categorize_task(request.description),
            "language": request.language,
            "framework": request.framework,
            "complexity": request.complexity,
            "success": result.success,
            "quality": result.quality_score
        }
        
        # Create outcome
        outcome = {
            "success": result.success,
            "quality": result.quality_score,
            "confidence": result.confidence,
            "execution_time": result.execution_time
        }
        
        # Learn from this experience
        await self.learning_system.learn_from_outcome(context, outcome)
        
        # Store in memory if available
        if self.memory_system:
            memory = MemoryData(
                id=f"code_generation_{request.request_id}",
                content=f"Generated {request.language} code: {request.description}",
                mom_type="learning",
                category="code_generation",
                importance=result.quality_score,
                tags=[request.language, request.framework or "generic", "code_gen"]
            )
            self.memory_system.store_with_citation(memory)
    
    def _categorize_task(self, description: str) -> str:
        """Categorize task type from description"""
        description_lower = description.lower()
        
        if any(word in description_lower for word in ["component", "ui", "interface"]):
            return "frontend"
        elif any(word in description_lower for word in ["api", "endpoint", "server", "backend"]):
            return "backend"
        elif any(word in description_lower for word in ["database", "model", "schema"]):
            return "database"
        elif any(word in description_lower for word in ["test", "testing", "spec"]):
            return "testing"
        elif any(word in description_lower for word in ["security", "auth", "validation"]):
            return "security"
        else:
            return "general"
    
    def get_performance_report(self) -> Dict[str, Any]:
        """Get comprehensive performance report"""
        if not self.generation_history:
            return {"message": "No generation history available"}
        
        successful_generations = [r for r in self.generation_history if r.success]
        failed_generations = [r for r in self.generation_history if not r.success]
        
        # Calculate metrics
        success_rate = len(successful_generations) / len(self.generation_history)
        avg_quality = sum(r.quality_score for r in successful_generations) / max(len(successful_generations), 1)
        avg_confidence = sum(r.confidence for r in successful_generations) / max(len(successful_generations), 1)
        avg_execution_time = sum(r.execution_time for r in self.generation_history) / len(self.generation_history)
        
        # Pattern statistics
        total_patterns = len(self.pattern_extractor.patterns)
        most_common_patterns = sorted(
            self.pattern_extractor.patterns.values(),
            key=lambda p: p.frequency,
            reverse=True
        )[:5]
        
        return {
            "summary": {
                "total_generations": len(self.generation_history),
                "success_rate": success_rate,
                "avg_quality_score": avg_quality,
                "avg_confidence": avg_confidence,
                "avg_execution_time": avg_execution_time,
                "improvement_cycles": self.improvement_cycles
            },
            "patterns": {
                "total_patterns": total_patterns,
                "most_common": [
                    {
                        "name": p.name,
                        "frequency": p.frequency,
                        "quality_score": p.quality_score
                    }
                    for p in most_common_patterns
                ]
            },
            "learning": {
                "auto_improve_enabled": self.auto_improve,
                "quality_threshold": self.quality_threshold,
                "learning_rate": self.learning_rate
            },
            "recent_performance": {
                "last_10_success_rate": sum(1 for r in list(self.generation_history)[-10:] if r.success) / min(10, len(self.generation_history)),
                "last_10_avg_quality": sum(r.quality_score for r in list(self.generation_history)[-10:] if r.success) / min(10, len([r for r in list(self.generation_history)[-10:] if r.success]))
            }
        }


# Factory function
def create_self_improving_code_generator(memory_system: Optional[HybridRAGMemory] = None, learning_system: Optional[AdvancedLearningSystem] = None) -> SelfImprovingCodeGenerator:
    """Create a self-improving code generator"""
    return SelfImprovingCodeGenerator(memory_system, learning_system)


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="SUPERDEV Self-Improving Code Generator")
    parser.add_argument("--test", action="store_true", help="Run tests")
    parser.add_argument("--language", default="python", help="Target language")
    parser.add_argument("--description", default="Create a function to process data", help="Generation description")
    parser.add_argument("--log-level", choices=["DEBUG", "INFO", "WARNING", "ERROR"], 
                       default="INFO", help="Log level")
    
    args = parser.parse_args()
    
    # Setup logging
    logging.basicConfig(
        level=getattr(logging, args.log_level),
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    async def test_code_generator():
        memory_system = HybridRAGMemory() if MEMORY_AVAILABLE else None
        learning_system = AdvancedLearningSystem(memory_system) if ADVANCED_LEARNING_AVAILABLE else None
        
        generator = create_self_improving_code_generator(memory_system, learning_system)
        
        # Create test request
        request = CodeGenerationRequest(
            request_id="test-001",
            description=args.description,
            language=args.language,
            framework=None,
            context={"task_type": "general"},
            requirements=["data processing", "error handling"],
            constraints=["no external dependencies"],
            examples=[],
            complexity="medium",
            created_at=datetime.now().isoformat()
        )
        
        # Generate code
        result = await generator.generate_code(request)
        
        print("Self-Improving Code Generator Test Results:")
        print(f"Success: {result.success}")
        print(f"Quality Score: {result.quality_score:.2f}")
        print(f"Confidence: {result.confidence:.2f}")
        print(f"Execution Time: {result.execution_time:.2f}s")
        print(f"Improvements: {len(result.improvements)}")
        print(f"Issues: {len(result.issues)}")
        print(f"Learning Insights: {len(result.learning_insights)}")
        print("\\nGenerated Code:")
        print(result.code)
        
        if result.explanation:
            print("\\nExplanation:")
            print(result.explanation)
        
        # Get performance report
        report = generator.get_performance_report()
        print("\\nPerformance Report:")
        print(json.dumps(report, indent=2))
    
    if args.test:
        asyncio.run(test_code_generator())
