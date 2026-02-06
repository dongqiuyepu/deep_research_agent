"""ReAct 循环执行引擎 - 实现 Thought-Action-Observation 循环"""

import json
import re
from typing import Dict, List, Any, Optional
from dataclasses import dataclass, field

from tools.tool_registry import ToolRegistry
from tools.base_tool import ToolResult
from agent.task_queue import TaskQueue


@dataclass
class TrajectoryStep:
    """轨迹步骤"""
    iteration: int
    thought: str
    action_name: str
    action_params: Dict
    observation: str
    evidence_ids: List[str] = field(default_factory=list)


@dataclass
class ResearchTrajectory:
    """研究轨迹"""
    question: str
    steps: List[TrajectoryStep] = field(default_factory=list)
    final_answer: Optional[str] = None
    total_evidences: List = field(default_factory=list)

    def add_step(self, step: TrajectoryStep):
        self.steps.append(step)

    def get_history_prompt(self) -> str:
        """生成历史轨迹的Prompt文本"""
        if not self.steps:
            return ""

        lines = ["== 研究轨迹 ==\n"]
        for step in self.steps:
            lines.append(f"[轮次 {step.iteration}]")
            lines.append(f"Thought: {step.thought}")
            lines.append(
                f"Action: {step.action_name}({json.dumps(step.action_params, ensure_ascii=False)})")
            lines.append(f"Observation: {step.observation}")
            if step.evidence_ids:
                lines.append(f"证据: {', '.join(step.evidence_ids)}")
            lines.append("")
        return "\n".join(lines)


REACT_SYSTEM_PROMPT = """你是一位资深的研究专家，擅长通过工具调用进行深度研究。

## 可用工具
{tools_prompt}

## 工作流程
你需要通过多轮 Thought-Action-Observation 循环来研究问题：
1. Thought: 分析当前状态，思考下一步应该做什么
2. Action: 选择一个工具并提供参数
3. Observation: 工具执行结果（由系统提供）
4. 重复以上步骤，直到收集足够证据

## 任务分解与队列管理
- 使用 decompose 工具将复杂问题分解为子问题（自动入队，子问题也可继续分解）
- 使用 resolve_task 工具标记当前子任务完成（自动切换到下一个）
- 所有子任务完成后，使用 finish 工具生成综合性答案

{queue_status}

## 输出格式
每次回复必须严格遵守以下JSON格式：
```json
{{
  "thought": "你的思考过程，分析当前状态和下一步计划",
  "action": {{
    "tool": "工具名称",
    "params": {{"参数名": "参数值"}}
  }}
}}
```

## 重要规则
1. 每次只能调用一个工具
2. 优先使用 kb_search 搜索本地知识库
3. 如果本地证据不足，使用 web_search 搜索网页
4. 可以使用 decompose 将复杂问题分解为子问题
5. 当前子任务证据充分时，调用 resolve_task 标记完成
6. 所有子任务完成后，调用 finish 工具返回最终答案
7. 答案中必须引用证据编号 [EVD-XXX]
8. 区分"强制性要求"和"审慎性建议"

## 当前任务
问题: {question}

{history}

请输出下一步的 thought 和 action（JSON格式）："""


class ReActEngine:
    """ReAct 循环执行引擎"""

    def __init__(
        self,
        llm_client,
        tool_registry: ToolRegistry,
        max_iterations: int = 10
    ):
        self.llm = llm_client
        self.registry = tool_registry
        self.max_iterations = max_iterations
        self.task_queue = TaskQueue()

    def run(self, question: str, memory_history: List[Dict] = None) -> Dict[str, Any]:
        """
        执行 ReAct 循环

        Args:
            question: 研究问题
            memory_history: 对话历史

        Returns:
            {
                "answer": str,
                "trajectory": ResearchTrajectory,
                "iterations": int,
                "status": str  # "completed" | "max_iterations" | "error"
            }
        """
        trajectory = ResearchTrajectory(question=question)
        all_evidences = []

        # 初始化任务队列
        self.task_queue.reset()
        self.task_queue.enqueue(question, parent_id="ROOT", iteration=0)
        self.task_queue.dequeue()  # 开始处理根任务

        print(f"\n{'='*60}")
        print(f"🔬 开始深度研究: {question}")
        print(f"{'='*60}")

        for iteration in range(1, self.max_iterations + 1):
            print(f"\n[轮次 {iteration}/{self.max_iterations}]")

            # 1. 构建 Prompt
            queue_status = ""
            if self.task_queue.current_task or self.task_queue.queue or self.task_queue.completed_tasks:
                queue_status = self.task_queue.get_queue_summary()

            prompt = REACT_SYSTEM_PROMPT.format(
                tools_prompt=self.registry.get_tools_prompt(),
                question=question,
                queue_status=queue_status,
                history=trajectory.get_history_prompt()
            )

            messages = [{"role": "user", "content": prompt}]
            if memory_history:
                messages = [{"role": "system", "content": "你是一位研究专家。"}] + \
                    memory_history[-4:] + messages

            # 2. 调用 LLM
            try:
                response = self.llm.chat(messages)
            except Exception as e:
                print(f"❌ LLM 调用失败: {e}")
                return {
                    "answer": f"研究失败: {e}",
                    "trajectory": trajectory,
                    "iterations": iteration,
                    "status": "error"
                }

            # 3. 解析 LLM 输出
            parsed = self._parse_response(response)
            if not parsed:
                print(f"⚠️ 解析失败，重试...")
                continue

            thought = parsed.get("thought", "")
            action = parsed.get("action", {})

            # 防御性检查：确保 action 是字典类型
            if not isinstance(action, dict):
                print(f"⚠️ action 格式错误 (类型: {type(action).__name__})，重试...")
                continue

            tool_name = action.get("tool", "")
            tool_params = action.get("params", {})

            print(f"💭 Thought: {thought[:100]}...")
            print(
                f"🔧 Action: {tool_name}({json.dumps(tool_params, ensure_ascii=False)})")

            # 4. 执行工具
            result = self.registry.execute(tool_name, tool_params)

            # === 任务队列钩子 ===
            # decompose 工具：子问题入队
            if tool_name == "decompose" and result.success:
                sub_questions = result.data.get("sub_questions", [])
                parent_id = self.task_queue.current_task.task_id if self.task_queue.current_task else "ROOT"
                for sub_q in sub_questions:
                    self.task_queue.enqueue(
                        sub_q, parent_id=parent_id, iteration=iteration)
                print(f"📋 已将 {len(sub_questions)} 个子问题加入队列")

            # 搜索工具：证据关联到当前任务
            if tool_name in ["kb_search", "web_search"] and result.success:
                new_evidence_ids = result.metadata.get("ids", [])
                if new_evidence_ids:
                    self.task_queue.add_evidence_to_current(new_evidence_ids)

            # resolve_task 工具：完成当前任务并切换
            if tool_name == "resolve_task" and result.success:
                answer = result.data.get("answer", "")
                current_evidence_ids = self.task_queue.current_task.evidence_ids if self.task_queue.current_task else []
                self.task_queue.resolve_current(
                    answer, current_evidence_ids, iteration)
                total_tasks = len(self.task_queue.completed_tasks) + len(
                    self.task_queue.queue) + (1 if self.task_queue.current_task else 0)
                print(
                    f"✅ 子任务完成，进度: {len(self.task_queue.completed_tasks)}/{total_tasks}")

                # 切换到下一个任务
                if not self.task_queue.is_empty():
                    next_task = self.task_queue.dequeue()
                    print(f"🔄 切换到: [{next_task.task_id}] {next_task.question}")
            # === 钩子结束 ===

            # 5. 处理结果
            observation = self._format_observation(result)
            evidence_ids = result.metadata.get(
                "ids", []) if result.success else []

            print(f"📋 Observation: {observation[:200]}...")

            # 6. 记录轨迹
            step = TrajectoryStep(
                iteration=iteration,
                thought=thought,
                action_name=tool_name,
                action_params=tool_params,
                observation=observation,
                evidence_ids=evidence_ids
            )
            trajectory.add_step(step)

            # 收集证据
            if result.success and result.data:
                evidences = result.data.get("evidences", [])
                all_evidences.extend(evidences)

            # 7. 检查终止条件
            if tool_name == "finish" and result.success:
                # 检查是否还有未完成的任务（包括队列中的任务和当前正在处理的任务）
                remaining_count = len(self.task_queue.queue)
                if self.task_queue.current_task is not None:
                    remaining_count += 1

                if remaining_count > 0:
                    print(
                        f"⚠️ 还有 {remaining_count} 个任务待处理（队列: {len(self.task_queue.queue)}, 当前: {'1' if self.task_queue.current_task else '0'}），继续研究")
                    continue

                answer = result.data.get("answer", "")
                trajectory.final_answer = answer
                trajectory.total_evidences = all_evidences

                print(f"\n✅ 研究完成 (轮次: {iteration})")
                return {
                    "answer": answer,
                    "trajectory": trajectory,
                    "iterations": iteration,
                    "status": "completed",
                    "evidences": all_evidences
                }

        # 达到最大轮次
        print(f"\n⚠️ 达到最大轮次限制 ({self.max_iterations})")

        # 强制生成答案
        forced_answer = self._force_generate_answer(
            question, trajectory, all_evidences)
        trajectory.final_answer = forced_answer
        trajectory.total_evidences = all_evidences

        return {
            "answer": forced_answer,
            "trajectory": trajectory,
            "iterations": self.max_iterations,
            "status": "max_iterations",
            "evidences": all_evidences
        }

    def _parse_response(self, response: str) -> Optional[Dict]:
        """解析 LLM 的 JSON 输出"""
        # 尝试直接解析
        try:
            return json.loads(response)
        except:
            pass

        # 尝试提取 JSON 块
        json_match = re.search(r'```json\s*(.*?)\s*```', response, re.DOTALL)
        if json_match:
            try:
                return json.loads(json_match.group(1))
            except:
                pass

        # 尝试提取花括号内容
        brace_match = re.search(r'\{.*\}', response, re.DOTALL)
        if brace_match:
            try:
                return json.loads(brace_match.group(0))
            except:
                pass

        return None

    def _format_observation(self, result: ToolResult) -> str:
        """格式化工具执行结果"""
        if not result.success:
            return f"错误: {result.error}"

        data = result.data
        if isinstance(data, dict):
            if "text" in data:
                return data["text"]
            if "answer" in data and data.get("is_final"):
                return f"最终答案: {data['answer']}"
            if "answer" in data:
                return f"子任务答案: {data['answer']}"
            if "sub_questions" in data:
                return f"分解为 {len(data['sub_questions'])} 个子问题: {data['sub_questions']}"
            if "assessment" in data:
                return f"评估: {data['assessment']} (充分: {data['is_sufficient']})"

        return str(data)

    def _force_generate_answer(
        self,
        question: str,
        trajectory: ResearchTrajectory,
        evidences: List
    ) -> str:
        """强制生成答案（当达到最大轮次时）"""
        evidence_text = ""
        for e in evidences[:10]:  # 最多使用10条证据
            evidence_text += f"[{e.evidence_id}] {e.content}\n"

        prompt = f"""基于以下证据回答问题。

问题: {question}

证据:
{evidence_text}

请给出答案，必须引用证据编号 [EVD-XXX]。如果证据不足，请说明。"""

        try:
            answer = self.llm.chat([{"role": "user", "content": prompt}])
            return answer
        except Exception as e:
            return f"无法生成答案: {e}"
