"""测试叶子任务进度统计的正确性"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from agent.task_queue import TaskQueue


def test_leaf_task_progress():
    """测试叶子任务进度统计，确保父任务不会被重复计数"""
    print("\n" + "=" * 80)
    print("测试：叶子任务进度统计")
    print("=" * 80)

    queue = TaskQueue()

    # 场景：
    # TASK-001 (根)
    #   ├─ TASK-002 (父任务，会被拆解)
    #   │   ├─ TASK-004 (叶子)
    #   │   └─ TASK-005 (叶子)
    #   └─ TASK-003 (叶子)
    #
    # 预期叶子任务数：3 (TASK-003, TASK-004, TASK-005)
    # 父任务（TASK-001, TASK-002）不应该计入进度

    # Step 1: 创建根任务
    root = queue.enqueue("根问题", parent_id="ROOT", iteration=0)
    queue.dequeue()
    print(f"\n✓ 根任务 [{root.task_id}] 创建")

    # Step 2: 分解为2个子任务
    sub1 = queue.enqueue("子问题1", parent_id=root.task_id, iteration=1)
    sub2 = queue.enqueue("子问题2", parent_id=root.task_id, iteration=1)
    queue.add_subtask_to_current(sub1.task_id)
    queue.add_subtask_to_current(sub2.task_id)
    print(f"✓ 根任务分解为: [{sub1.task_id}, {sub2.task_id}]")

    # 挂起根任务
    root.status = "waiting_for_subtasks"
    queue.current_task = None
    queue.queue.append(root)

    # Step 3: 处理 TASK-002，继续分解
    queue.dequeue()  # TASK-002
    print(f"\n✓ 当前任务: [{queue.current_task.task_id}]")

    sub2_1 = queue.enqueue("子问题1-1", parent_id=sub1.task_id, iteration=2)
    sub2_2 = queue.enqueue("子问题1-2", parent_id=sub1.task_id, iteration=2)
    queue.add_subtask_to_current(sub2_1.task_id)
    queue.add_subtask_to_current(sub2_2.task_id)
    print(f"✓ TASK-002 分解为: [{sub2_1.task_id}, {sub2_2.task_id}]")

    # 挂起 TASK-002
    sub1.status = "waiting_for_subtasks"
    queue.current_task = None
    queue.queue.append(sub1)

    print("\n" + "=" * 80)
    print("场景1：所有任务都在队列中，没有完成任何叶子任务")
    print("=" * 80)
    print(f"队列状态: {[(t.task_id, len(t.subtask_ids)) for t in queue.queue]}")
    
    summary = queue.get_queue_summary()
    print(summary)
    
    # 验证：应该显示 0/3 叶子任务
    assert "叶子任务进度: 0/3" in summary, "应该有3个叶子任务（TASK-003, TASK-004, TASK-005）"
    print("\n✅ 验证通过：正确识别出3个叶子任务")

    # Step 4: 完成 TASK-003
    print("\n" + "=" * 80)
    print("场景2：完成第一个叶子任务 TASK-003")
    print("=" * 80)
    
    queue.dequeue()  # TASK-003
    print(f"✓ 当前任务: [{queue.current_task.task_id}]")
    queue.resolve_current("答案3", ["EVD-001"], iteration=3)
    print(f"✅ TASK-003 已完成")
    
    summary = queue.get_queue_summary()
    print(summary)
    
    # 验证：应该显示 1/3
    assert "叶子任务进度: 1/3" in summary, "应该显示 1/3 叶子任务完成"
    print("\n✅ 验证通过：进度为 1/3")

    # Step 5: 完成 TASK-004
    print("\n" + "=" * 80)
    print("场景3：完成第二个叶子任务 TASK-004")
    print("=" * 80)
    
    # 跳过 TASK-001（父任务，未完成）
    next_task = queue.dequeue()
    while next_task and next_task.status == "waiting_for_subtasks":
        if not queue.are_all_subtasks_resolved(next_task):
            queue.queue.append(next_task)
            next_task = queue.dequeue() if not queue.is_empty() else None
        else:
            break
    
    print(f"✓ 当前任务: [{queue.current_task.task_id}]")
    queue.resolve_current("答案4", ["EVD-002"], iteration=4)
    print(f"✅ TASK-004 已完成")
    
    summary = queue.get_queue_summary()
    print(summary)
    
    # 验证：应该显示 2/3
    assert "叶子任务进度: 2/3" in summary, "应该显示 2/3 叶子任务完成"
    print("\n✅ 验证通过：进度为 2/3")

    # Step 6: 完成 TASK-005
    print("\n" + "=" * 80)
    print("场景4：完成第三个叶子任务 TASK-005")
    print("=" * 80)
    
    queue.dequeue()  # TASK-005
    print(f"✓ 当前任务: [{queue.current_task.task_id}]")
    queue.resolve_current("答案5", ["EVD-003"], iteration=5)
    print(f"✅ TASK-005 已完成")
    
    summary = queue.get_queue_summary()
    print(summary)
    
    # 验证：应该显示 3/3
    assert "叶子任务进度: 3/3" in summary, "应该显示 3/3 叶子任务完成"
    print("\n✅ 验证通过：进度为 3/3")

    # Step 7: 恢复并完成 TASK-002（父任务）
    print("\n" + "=" * 80)
    print("场景5：完成父任务 TASK-002，不应影响叶子任务进度")
    print("=" * 80)
    
    # 找到 TASK-002
    next_task = queue.dequeue()
    while next_task and next_task.status == "waiting_for_subtasks":
        if queue.are_all_subtasks_resolved(next_task):
            next_task.status = "in_progress"
            break
        else:
            queue.queue.append(next_task)
            next_task = queue.dequeue() if not queue.is_empty() else None
    
    print(f"✓ 当前任务: [{queue.current_task.task_id}]")
    print(f"✓ 任务类型: 父任务（有 {len(queue.current_task.subtask_ids)} 个子任务）")
    queue.resolve_current("汇总答案2", ["EVD-004"], iteration=6)
    print(f"✅ TASK-002（父任务）已完成")
    
    summary = queue.get_queue_summary()
    print(summary)
    
    # 关键验证：父任务完成后，叶子任务进度应该还是 3/3，不会变成 4/3
    assert "叶子任务进度: 3/3" in summary, "父任务完成不应影响叶子任务统计"
    print("\n✅ 验证通过：父任务不影响叶子任务进度（仍为 3/3）")

    print("\n" + "=" * 80)
    print("✅ 所有测试通过！叶子任务进度统计逻辑正确")
    print("=" * 80)

    # 最终验证
    print("\n📊 最终统计:")
    print(f"  - completed_tasks 总数: {len(queue.completed_tasks)}")
    print(f"  - 其中叶子任务数: {sum(1 for t in queue.completed_tasks if t.parent_task_id != 'ROOT' and len(t.subtask_ids) == 0)}")
    print(f"  - 其中父任务数: {sum(1 for t in queue.completed_tasks if len(t.subtask_ids) > 0)}")


if __name__ == "__main__":
    test_leaf_task_progress()
