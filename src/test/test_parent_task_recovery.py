"""测试父任务过早恢复的问题修复"""

import sys
from pathlib import Path

# 添加项目根目录到路径
sys.path.insert(0, str(Path(__file__).parent.parent))

from agent.task_queue import TaskQueue


def test_parent_task_premature_recovery():
    """测试父任务不会在子任务未完成时被过早恢复"""
    print("\n" + "=" * 80)
    print("测试：父任务过早恢复问题")
    print("=" * 80)

    queue = TaskQueue()

    # 场景：
    # 1. 根任务 TASK-001 分解为 [TASK-002, TASK-003]
    # 2. TASK-002 再分解为 [TASK-004, TASK-005]
    # 3. 队列顺序：[TASK-003, TASK-001(waiting), TASK-004, TASK-005, TASK-002(waiting)]
    # 4. 当 TASK-003 完成后，TASK-001 不应该被恢复（因为 TASK-002 还未完成）

    # Step 1: 创建根任务并分解
    root = queue.enqueue("根问题：如何确保数据安全？", parent_id="ROOT", iteration=0)
    queue.dequeue()
    print(f"\n✓ 根任务 [{root.task_id}] 已出队")

    # 分解为2个子任务
    sub1 = queue.enqueue("数据加密的最佳实践是什么？", parent_id=root.task_id, iteration=1)
    sub2 = queue.enqueue("数据访问权限如何控制？", parent_id=root.task_id, iteration=1)
    queue.add_subtask_to_current(sub1.task_id)
    queue.add_subtask_to_current(sub2.task_id)
    print(f"✓ 根任务分解为: [{sub1.task_id}, {sub2.task_id}]")

    # 挂起根任务
    root_task = queue.current_task
    root_task.status = "waiting_for_subtasks"
    queue.current_task = None
    queue.queue.append(root_task)
    print(f"✓ 根任务挂起，队列: {[t.task_id for t in queue.queue]}")

    # Step 2: 处理 TASK-002，并继续分解
    queue.dequeue()  # TASK-002
    print(f"\n✓ 当前任务: [{queue.current_task.task_id}]")

    sub2_1 = queue.enqueue("AES-256 加密的实现方式？", parent_id=sub1.task_id, iteration=2)
    sub2_2 = queue.enqueue("密钥管理的安全策略？", parent_id=sub1.task_id, iteration=2)
    queue.add_subtask_to_current(sub2_1.task_id)
    queue.add_subtask_to_current(sub2_2.task_id)
    print(f"✓ TASK-002 分解为: [{sub2_1.task_id}, {sub2_2.task_id}]")

    # 挂起 TASK-002
    sub1_task = queue.current_task
    sub1_task.status = "waiting_for_subtasks"
    queue.current_task = None
    queue.queue.append(sub1_task)
    print(f"✓ TASK-002 挂起，队列: {[t.task_id for t in queue.queue]}")
    print(f"  队列详情: {[(t.task_id, t.status) for t in queue.queue]}")

    # Step 3: 完成 TASK-003（根任务的第一个子任务）
    queue.dequeue()  # TASK-003
    print(f"\n✓ 当前任务: [{queue.current_task.task_id}]")
    queue.resolve_current("需要基于角色的访问控制（RBAC）", ["EVD-001"], iteration=3)
    print(f"✅ TASK-003 已完成")
    print(f"✓ 已完成任务: {[t.task_id for t in queue.completed_tasks]}")
    print(f"✓ 当前队列: {[(t.task_id, t.status) for t in queue.queue]}")

    # Step 4: 关键检查 - 下一个任务应该是什么？
    print("\n" + "=" * 80)
    print("关键检查：下一个任务应该是 TASK-004，而不是 TASK-001")
    print("=" * 80)

    # 模拟 react_engine 的切换逻辑
    if not queue.is_empty():
        # 这里使用修复后的逻辑：循环查找可执行任务
        found_executable = False
        while not queue.is_empty():
            next_task = queue.dequeue()
            print(f"📍 检查任务: [{next_task.task_id}] (status: {next_task.status})")

            if next_task.status == "waiting_for_subtasks":
                if queue.are_all_subtasks_resolved(next_task):
                    next_task.status = "in_progress"
                    print(f"✅ 父任务 [{next_task.task_id}] 的所有子任务已完成，可以恢复")
                    found_executable = True
                    break
                else:
                    remaining = [
                        sid for sid in next_task.subtask_ids
                        if sid not in {t.task_id for t in queue.completed_tasks}
                    ]
                    print(f"⚠️ 父任务 [{next_task.task_id}] 的子任务尚未全部完成（剩余: {remaining}），重新放回队列")
                    queue.queue.append(next_task)
                    # 继续循环
            else:
                print(f"✅ 找到可执行任务: [{next_task.task_id}]")
                found_executable = True
                break

        if found_executable and queue.current_task:
            print(f"\n🎯 最终选择的任务: [{queue.current_task.task_id}] {queue.current_task.question}")
            assert queue.current_task.task_id == sub2_1.task_id, \
                f"❌ 错误！应该是 {sub2_1.task_id}，但得到 {queue.current_task.task_id}"
            print("✅ 测试通过！父任务被正确跳过")
        else:
            print("⚠️ 没有找到可执行任务（可能陷入死锁）")
    else:
        print("❌ 队列为空，不应该发生")

    # Step 5: 验证队列状态
    print(f"\n✓ 当前队列: {[(t.task_id, t.status) for t in queue.queue]}")
    print(f"✓ 已完成: {[t.task_id for t in queue.completed_tasks]}")

    # 验证 TASK-001 和 TASK-002 都还在队列中等待
    waiting_tasks = [t for t in queue.queue if t.status == "waiting_for_subtasks"]
    print(f"✓ 等待中的父任务: {[t.task_id for t in waiting_tasks]}")
    
    assert root_task.task_id in [t.task_id for t in waiting_tasks], \
        "根任务应该还在队列中等待"
    assert sub1_task.task_id in [t.task_id for t in waiting_tasks], \
        "TASK-002 应该还在队列中等待"

    print("\n" + "=" * 80)
    print("✅ 测试通过！父任务恢复逻辑正确")
    print("=" * 80)


if __name__ == "__main__":
    test_parent_task_premature_recovery()
