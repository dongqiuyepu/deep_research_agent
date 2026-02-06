"""任务队列管理 - 实现队列式问题分解和进度追踪"""

from dataclasses import dataclass, field
from typing import List, Optional


@dataclass
class SubTask:
    """子任务数据结构"""
    task_id: str                           # TASK-001, TASK-002, ...
    question: str                          # 子问题文本
    parent_task_id: str                    # 父任务ID（ROOT 为根任务）
    status: str                            # "pending" | "in_progress" | "resolved"
    created_at: int                        # 创建时的迭代轮次
    started_at: Optional[int] = None       # 开始处理时的轮次
    resolved_at: Optional[int] = None      # 完成时的轮次
    answer: Optional[str] = None           # 子任务答案
    evidence_ids: List[str] = field(default_factory=list)  # 关联证据


class TaskQueue:
    """任务队列管理器 - FIFO 顺序，单层分解"""

    def __init__(self):
        self.queue: List[SubTask] = []           # 待处理队列
        self.completed_tasks: List[SubTask] = [] # 已完成任务
        self.task_counter: int = 0               # ID计数器
        self.current_task: Optional[SubTask] = None  # 当前聚焦任务

    def enqueue(self, question: str, parent_id: str, iteration: int) -> SubTask:
        """
        将任务加入队列
        
        Args:
            question: 子问题文本
            parent_id: 父任务ID
            iteration: 当前迭代轮次
            
        Returns:
            创建的 SubTask 对象
        """
        self.task_counter += 1
        task = SubTask(
            task_id=f"TASK-{self.task_counter:03d}",
            question=question,
            parent_task_id=parent_id,
            status="pending",
            created_at=iteration
        )
        self.queue.append(task)
        return task

    def dequeue(self) -> Optional[SubTask]:
        """
        从队列取出任务并开始处理
        
        Returns:
            取出的 SubTask 对象，队列为空时返回 None
        """
        if not self.queue:
            return None
        task = self.queue.pop(0)
        task.status = "in_progress"
        task.started_at = task.created_at
        self.current_task = task
        return task

    def resolve_current(self, answer: str, evidence_ids: List[str], iteration: int):
        """
        完成当前任务
        
        Args:
            answer: 子任务答案
            evidence_ids: 关联的证据ID列表
            iteration: 完成时的迭代轮次
        """
        if self.current_task:
            self.current_task.status = "resolved"
            self.current_task.answer = answer
            self.current_task.evidence_ids = evidence_ids
            self.current_task.resolved_at = iteration
            self.completed_tasks.append(self.current_task)
            self.current_task = None

    def add_evidence_to_current(self, evidence_ids: List[str]):
        """将证据关联到当前任务"""
        if self.current_task:
            self.current_task.evidence_ids.extend(evidence_ids)

    def is_empty(self) -> bool:
        """检查待处理队列是否为空"""
        return len(self.queue) == 0

    def is_all_resolved(self) -> bool:
        """检查是否所有任务都已完成（队列空且有已完成任务）"""
        return self.is_empty() and len(self.completed_tasks) > 0

    def get_queue_summary(self) -> str:
        """
        生成队列状态摘要，用于注入 Prompt
        
        Returns:
            格式化的队列状态文本
        """
        lines = ["=== 任务队列状态 ==="]

        if self.current_task:
            lines.append(f"当前任务: [{self.current_task.task_id}] {self.current_task.question}")
            lines.append(f"  已收集证据: {len(self.current_task.evidence_ids)} 条")

        if self.queue:
            lines.append(f"\n待处理队列 ({len(self.queue)}):")
            for t in self.queue:
                lines.append(f"  - [{t.task_id}] {t.question}")

        if self.completed_tasks:
            lines.append(f"\n已完成任务 ({len(self.completed_tasks)}):")
            for t in self.completed_tasks:
                # 截断过长的问题文本
                q_text = t.question[:30] + "..." if len(t.question) > 30 else t.question
                lines.append(f"  [done] [{t.task_id}] {q_text}")

        return "\n".join(lines)

    def get_completed_answers_summary(self) -> str:
        """
        生成已完成任务的答案汇总，供 finish 工具使用
        
        Returns:
            格式化的答案汇总文本
        """
        if not self.completed_tasks:
            return ""

        lines = ["=== 子任务答案汇总 ==="]
        for t in self.completed_tasks:
            lines.append(f"[{t.task_id}] {t.question}")
            lines.append(f"  答案: {t.answer}")
            if t.evidence_ids:
                lines.append(f"  证据: {', '.join(t.evidence_ids)}")
            lines.append("")

        return "\n".join(lines)

    def reset(self):
        """重置队列状态"""
        self.queue.clear()
        self.completed_tasks.clear()
        self.task_counter = 0
        self.current_task = None
