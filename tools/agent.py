"""
NOVA Agent & Task Planner (Phase 4)
====================================
Enterprise multi-step task execution with planning
"""

import json
from loguru import logger
from typing import List, Dict, Any, Optional
from enum import Enum


class TaskStatus(Enum):
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class Task:
    """Represents a single task step"""
    
    def __init__(self, tool_name: str, parameters: Dict[str, Any], 
                 description: str = "", dependencies: List[str] = None):
        self.tool_name = tool_name
        self.parameters = parameters
        self.description = description
        self.dependencies = dependencies or []
        self.status = TaskStatus.PENDING
        self.result = None
        self.error = None
    
    def to_dict(self) -> Dict:
        return {
            "tool": self.tool_name,
            "parameters": self.parameters,
            "description": self.description,
            "status": self.status.value,
            "result": self.result,
            "error": self.error
        }


class TaskPlanner:
    """
    AI-powered task planner
    Breaks down complex requests into steps
    """
    
    def __init__(self, llm):
        self.llm = llm
        logger.info("Task planner initialized")
    
    def plan_task(self, user_request: str, available_tools: List[str]) -> List[Task]:
        """
        Create execution plan from user request
        """
        # Detailed tool definitions to prevent hallucinations
        tool_definitions = """
- open_app(app_name: str): Open application (e.g., 'chrome', 'notepad', 'calc')
- search_web(query: str): Search Google for a query
- create_file(path: str, content: str): Create a file with content
- read_file(path: str): Read file content
- list_apps(): List running applications
- run_command(command: str): Run shell command (use sparingly)
- get_system_info(): Get CPU/Memory usage
        """

        # Simplified Prompt - Focus on getting VALID JSON
        planning_prompt = f"""You are an AI assistant. User says: "{user_request}"

TOOLS AVAILABLE:
{tool_definitions}

INSTRUCTION:
Return a JSON list with the steps to fulfill this request.
Use ONLY the tools listed above. Use EXACT parameter names.

FORMAT:
[
  {{
    "tool": "tool_name",
    "parameters": {{ "param_name": "value" }},
    "description": "Short description"
  }}
]

Strict JSON only. No text before or after."""
        
        # Get plan from LLM
        response = self.llm.get_quick_response(planning_prompt)
        logger.debug(f"LLM Response: {response}")
        
        try:
            import re
            import json
            
            # 1. Try to find [ ... ]
            match = re.search(r'\[.*\]', response, re.DOTALL)
            if match:
                json_str = match.group(0)
            else:
                # 2. Try to find { ... } and wrap in list
                match = re.search(r'\{.*\}', response, re.DOTALL)
                if match:
                    json_str = f"[{match.group(0)}]"
                else:
                    logger.error("No JSON found in response")
                    return []
            
            # Clean up potential markdown code blocks if regex missed them
            json_str = json_str.replace("```json", "").replace("```", "")
            
            steps = json.loads(json_str)
            
            # Validate steps
            tasks = []
            for i, step in enumerate(steps):
                if 'tool' in step and 'parameters' in step:
                    task = Task(
                        tool_name=step['tool'],
                        parameters=step['parameters'],
                        description=step.get('description', f'Step {i+1}')
                    )
                    tasks.append(task)
            
            if tasks:
                return tasks
            else:
                logger.warning("JSON parsed but contained no valid tasks")
                return []
                
        except Exception as e:
            logger.error(f"Plan parsing failed: {e}")
            return []


class AgentExecutor:
    """
    Enterprise agent executor
    Executes multi-step plans with error recovery
    """
    
    def __init__(self, tool_executor, llm, voice_output=None):
        self.tool_executor = tool_executor
        self.llm = llm
        self.voice_output = voice_output
        self.planner = TaskPlanner(llm)
        
        logger.info("Agent executor initialized")
    
    def execute_request(self, user_request: str) -> Dict[str, Any]:
        """
        Execute a complex user request
        
        Returns:
            Execution summary
        """
        logger.info(f"Agent executing: {user_request}")
        
        # Get available tools
        available_tools = list(self.tool_executor.tools.keys())
        
        # Create plan
        tasks = self.planner.plan_task(user_request, available_tools)
        
        if not tasks:
            return {
                "success": False,
                "message": "Could not create execution plan",
                "steps": []
            }
        
        # Announce plan
        plan_description = f"I'll complete this in {len(tasks)} steps:\n"
        for i, task in enumerate(tasks, 1):
            plan_description += f"{i}. {task.description}\n"
        
        logger.info(f"Plan:\n{plan_description}")
        
        if self.voice_output:
            self.voice_output.speak(f"I'll help you with that. This will take {len(tasks)} steps.")
        
        # Execute tasks
        results = []
        context = {}  # Store results for later steps
        
        for i, task in enumerate(tasks):
            logger.info(f"Executing step {i+1}/{len(tasks)}: {task.description}")
            
            if self.voice_output:
                self.voice_output.speak(f"Step {i+1}: {task.description}")
            
            task.status = TaskStatus.IN_PROGRESS
            
            # Resolve parameter references (e.g., $RESULT_0)
            resolved_params = self._resolve_parameters(task.parameters, context)
            
            # Execute tool
            result = self.tool_executor.execute(task.tool_name, resolved_params)
            
            if result['success']:
                task.status = TaskStatus.COMPLETED
                task.result = result['result']
                context[f'RESULT_{i}'] = result['result']
                
                logger.info(f"✓ Step {i+1} completed")
                results.append(task.to_dict())
            else:
                task.status = TaskStatus.FAILED
                task.error = result['message']
                
                logger.error(f"✗ Step {i+1} failed: {result['message']}")
                
                # Try error recovery
                if not self._recover_from_error(task, tasks[i+1:]):
                    # Can't recover, abort
                    logger.error("Cannot recover from error, aborting")
                    if self.voice_output:
                        self.voice_output.speak("I'm sorry, I hit a snag and couldn't finish the task. Let me know if you want to try a different way.")
                    
                    results.append(task.to_dict())
                    break
                
                results.append(task.to_dict())
        
        # Generate summary
        completed = sum(1 for t in tasks if t.status == TaskStatus.COMPLETED)
        failed = sum(1 for t in tasks if t.status == TaskStatus.FAILED)
        
        summary = {
            "success": failed == 0,
            "total_steps": len(tasks),
            "completed": completed,
            "failed": failed,
            "steps": results,
            "final_result": tasks[-1].result if tasks and tasks[-1].status == TaskStatus.COMPLETED else None
        }
        
        # Announce completion
        if summary['success']:
            message = f"Done! Completed all {completed} steps successfully."
            logger.info(message)
            if self.voice_output:
                self.voice_output.speak(message)
        else:
            message = f"Partially completed. {completed} of {len(tasks)} steps successful."
            logger.warning(message)
            if self.voice_output:
                self.voice_output.speak(message)
        
        return summary
    
    def _resolve_parameters(self, parameters: Dict[str, Any], context: Dict[str, Any]) -> Dict[str, Any]:
        """Resolve parameter references like $RESULT_0"""
        resolved = {}
        
        for key, value in parameters.items():
            if isinstance(value, str) and value.startswith('$'):
                # Reference to previous result
                ref_key = value[1:]  # Remove $
                resolved[key] = context.get(ref_key, value)
            else:
                resolved[key] = value
        
        return resolved
    
    def _recover_from_error(self, failed_task: Task, remaining_tasks: List[Task]) -> bool:
        """
        Attempt to recover from task failure
        
        Returns:
            True if recovery successful, False otherwise
        """
        # Simple recovery: skip non-critical tasks
        # In production, could ask LLM for alternative approach
        
        logger.warning(f"Attempting recovery from: {failed_task.description}")
        
        # For now, just log and don't recover
        # Production would implement retry logic, alternative paths, etc.
        return False
    
    def get_task_status(self, tasks: List[Task]) -> str:
        """Get human-readable status of tasks"""
        status_lines = []
        
        for i, task in enumerate(tasks, 1):
            status_icon = {
                TaskStatus.COMPLETED: "✓",
                TaskStatus.IN_PROGRESS: "⏳",
                TaskStatus.FAILED: "✗",
                TaskStatus.PENDING: "○",
                TaskStatus.CANCELLED: "⊗"
            }.get(task.status, "?")
            
            status_lines.append(f"{status_icon} Step {i}: {task.description}")
        
        return "\n".join(status_lines)


if __name__ == "__main__":
    # Test agent system
    import sys
    from pathlib import Path
    sys.path.append(str(Path(__file__).parent.parent))
    
    from config.config import config
    from brain.llm import NovaBrain
    from tools.executor import ToolExecutor
    from tools.security import SecurityManager
    
    # Initialize components
    brain = NovaBrain(config)
    security = SecurityManager(config)
    tool_executor = ToolExecutor(config, security)
    
    agent = AgentExecutor(tool_executor, brain)
    
    # Test complex request
    result = agent.execute_request(
        "Create a file called test.txt with the content 'Hello NOVA' and then read it back to me"
    )
    
    print("\n" + "="*60)
    print("AGENT EXECUTION RESULT")
    print("="*60)
    print(json.dumps(result, indent=2))
