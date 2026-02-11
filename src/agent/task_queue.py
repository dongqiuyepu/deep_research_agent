"""任务队列管理 - 实现队列式问题分解和进度追踪"""

from dataclasses import dataclass, field
from typing import List, Optional, Dict


@dataclass
class SubTask:
    """子任务数据结构"""
    task_id: str                           # TASK-001, TASK-002, ...
    question: str                          # 子问题文本
    parent_task_id: str                    # 父任务ID（ROOT 为根任务）
    # "pending" | "in_progress" | "resolved" | "waiting_for_subtasks"
    status: str
    created_at: int                        # 创建时的迭代轮次
    started_at: Optional[int] = None       # 开始处理时的轮次
    resolved_at: Optional[int] = None      # 完成时的轮次
    answer: Optional[str] = None           # 子任务答案
    evidence_ids: List[str] = field(default_factory=list)  # 关联证据
    subtask_ids: List[str] = field(
        default_factory=list)   # 子任务ID列表（用于追踪分解的子任务）


class TaskQueue:
    """任务队列管理器 - FIFO 顺序，单层分解"""

    def __init__(self):
        self.queue: List[SubTask] = []           # 待处理队列
        self.completed_tasks: List[SubTask] = []  # 已完成任务
        self.task_counter: int = 0               # ID计数器
        self.current_task: Optional[SubTask] = None  # 当前聚焦任务
        self.waiting_parents: Dict[str, SubTask] = {}  # 挂起的父任务

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

    def get_leaf_task_progress(self) -> tuple[int, int]:
        """
        统计叶子任务的完成进度

        Returns:
            (completed_count, total_count) 元组
            - completed_count: 已完成的叶子任务数
            - total_count: 总叶子任务数（包括已完成、当前、队列中的）
        """
        # 已完成的叶子任务数
        completed_leaf_count = sum(
            1 for t in self.completed_tasks if self.is_leaf_task(t))

        # 队列中的叶子任务数
        queue_leaf_count = sum(1 for t in self.queue if self.is_leaf_task(t))

        # 当前任务如果是叶子任务，也计入
        current_leaf_count = 1 if (
            self.current_task and self.is_leaf_task(self.current_task)) else 0

        total = completed_leaf_count + queue_leaf_count + current_leaf_count

        return (completed_leaf_count, total)

    def get_queue_summary(self) -> str:
        """
        生成队列状态摘要，用于注入 Prompt

        Returns:
            格式化的队列状态文本
        """
        lines = ["=== 任务队列状态 ==="]

        # 使用新的进度统计方法
        completed_leaf_count, total = self.get_leaf_task_progress()

        # 显示总进度
        if total > 0:
            lines.append(f"子任务进度: {completed_leaf_count}/{total} 已完成")
            if self.current_task and self.is_leaf_task(self.current_task):
                lines.append(
                    f"  ⚠️ 当前子任务 [{self.current_task.task_id}] 尚未完成，请先调用 resolve_task")

            # 分别统计队列中的子任务和父任务
            queue_leaf_count = sum(
                1 for t in self.queue if self.is_leaf_task(t))
            waiting_parents = len(self.waiting_parents)
            if queue_leaf_count > 0:
                lines.append(f"  ⚠️ 还有 {queue_leaf_count} 个子任务在队列中等待")
            if waiting_parents > 0:
                lines.append(f"  ℹ️ 还有 {waiting_parents} 个父任务等待子任务完成")

        if self.current_task:
            lines.append(
                f"\n当前任务: [{self.current_task.task_id}] {self.current_task.question}")

            # 显示父任务信息
            if self.current_task.parent_task_id != "ROOT":
                lines.append(f"  父任务: {self.current_task.parent_task_id}")

            # 显示子任务信息及完成进度
            if self.current_task.subtask_ids:
                completed_subs = [sid for sid in self.current_task.subtask_ids
                                  if sid in {t.task_id for t in self.completed_tasks}]
                lines.append(f"  子任务: {self.current_task.subtask_ids}")
                lines.append(
                    f"  子任务进度: {len(completed_subs)}/{len(self.current_task.subtask_ids)} 已完成")

                # 关键提示：如果所有子任务已完成，提醒需要 resolve 父任务
                if len(completed_subs) == len(self.current_task.subtask_ids):
                    lines.append(
                        f"  ⚠️ **所有子任务已完成，请基于子任务答案汇总，调用 resolve_task 完成当前父任务**")

            lines.append(f"  已收集证据: {len(self.current_task.evidence_ids)} 条")

        if self.queue:
            lines.append(f"\n待处理队列 ({len(self.queue)}):")
            for t in self.queue:
                # 显示任务状态和父子关系
                parent_info = f" (父任务: {t.parent_task_id})" if t.parent_task_id != "ROOT" else ""

                lines.append(
                    f"  - [{t.task_id}] {t.question}{parent_info}")

        if self.completed_tasks:
            lines.append(f"\n已完成任务 ({len(self.completed_tasks)}):")
            for t in self.completed_tasks:
                # 截断过长的问题文本
                q_text = t.question
                parent_info = f" (父任务: {t.parent_task_id})" if t.parent_task_id != "ROOT" else ""
                lines.append(f"  [done] [{t.task_id}] {q_text}{parent_info}")

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
        self.waiting_parents.clear()
        self.task_counter = 0
        self.current_task = None

    def add_subtask_to_current(self, subtask_id: str):
        """
        将子任务ID添加到当前任务的 subtask_ids 列表

        Args:
            subtask_id: 子任务ID
        """
        if self.current_task:
            self.current_task.subtask_ids.append(subtask_id)

    def get_remaining_subtasks(self, task: SubTask) -> List[str]:
        """
        获取任务未完成的子任务ID列表

        Args:
            task: 要检查的任务

        Returns:
            未完成的子任务ID列表
        """
        if not task.subtask_ids:
            return []

        # 获取所有已完成任务的ID集合
        completed_ids = {t.task_id for t in self.completed_tasks}

        # 返回未完成的子任务ID列表
        return [sid for sid in task.subtask_ids if sid not in completed_ids]

    def register_waiting_parent(self, task: SubTask):
        """
        将父任务注册为挂起状态（不进入队列，等待子任务完成）
        """
        self.waiting_parents[task.task_id] = task

    def promote_ready_parents_from(self, task: SubTask):
        """
        从已完成的任务开始，向上检查父/祖先任务，
        如果其所有后代叶子任务都已完成，则将其加入待处理队列。
        """
        parent_id = task.parent_task_id
        while parent_id != "ROOT":
            parent = self.waiting_parents.get(parent_id)
            if not parent:
                # 父任务要么已经在队列/当前任务中，要么不存在，结束提升
                break

            # 仅当所有后代叶子任务都已完成时，才将父任务加入队列
            if not self.are_all_descendant_leaves_resolved(parent):
                break

            # 将已就绪的父任务从挂起集合中移除，并放入队列
            self.waiting_parents.pop(parent_id, None)
            parent.status = "pending"
            self.queue.append(parent)

            # 继续向上检查祖先任务
            parent_id = parent.parent_task_id

    def is_leaf_task(self, task: SubTask) -> bool:
        """
        判断任务是否为叶子任务（没有子任务）

        Args:
            task: 要检查的任务

        Returns:
            True 如果是叶子任务（没有子任务）
        """
        return len(task.subtask_ids) == 0

    def are_all_descendant_leaves_resolved(self, task: SubTask) -> bool:
        """
        递归检查任务的所有后代叶子节点是否都已完成

        逻辑：
        - 如果是叶子任务，返回 True
        - 如果是父任务，检查所有直接子任务：
          - 子任务是叶子：必须已完成
          - 子任务是父任务：递归检查其后代叶子

        Args:
            task: 要检查的父任务

        Returns:
            True 如果所有后代叶子任务都已完成
        """
        if not task.subtask_ids:
            return True

        # 构建任务ID到任务对象的映射（包括队列、当前任务、已完成任务、挂起父任务）
        all_tasks = {t.task_id: t for t in self.queue}
        all_tasks.update({t.task_id: t for t in self.completed_tasks})
        all_tasks.update(self.waiting_parents)
        if self.current_task:
            all_tasks[self.current_task.task_id] = self.current_task

        # 已完成任务的ID集合
        completed_ids = {t.task_id for t in self.completed_tasks}

        # 检查每个直接子任务
        for subtask_id in task.subtask_ids:
            if subtask_id not in all_tasks:
                # 子任务不存在，视为未完成
                return False

            subtask = all_tasks[subtask_id]

            if self.is_leaf_task(subtask):
                # 子任务是叶子，必须已完成
                if subtask_id not in completed_ids:
                    return False
            else:
                # 子任务是父任务，递归检查
                if not self.are_all_descendant_leaves_resolved(subtask):
                    return False

        return True
