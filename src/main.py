"""Deep Research Agent - 主程序入口"""

from agent import ResearchAgent
from memory import ConversationMemory
from tools import WebSearchTool
from knowledge_base import KnowledgeBaseManager
from llm import LLMClient
import os
import sys
from pathlib import Path

# 添加 src 目录到路径
sys.path.insert(0, str(Path(__file__).parent))


def print_banner():
    """打印欢迎信息"""
    print("""
╔════════════════════════════════════════════════════════════╗
║           Deep Research Agent - 政策合规研究助手            ║
╠════════════════════════════════════════════════════════════╣
║  功能：本地知识库 + 网页搜索 + 证据链追溯                    ║
║  模式：                                                     ║
║    - 普通对话：直接输入问题（快速响应）                      ║
║    - 深度研究：/research <问题>（ReAct自主决策流程）          ║
║  命令：                                                     ║
║    - /research     启动深度研究（ReAct模式，LLM自主决策）     ║
║    - /research_v1  启动旧版研究（固定流程）                   ║
║    - /rebuild      重建知识库索引                            ║
║    - /clear        清空对话历史                              ║
║    - /save         保存为Markdown报告                        ║
║    - /save_trace   保存带完整轨迹的Markdown报告              ║
║    - /pdf          保存为PDF报告                             ║
║    - /help         显示帮助信息                              ║
║    - quit/exit     退出程序                                  ║
╚════════════════════════════════════════════════════════════╝
""")


def print_help():
    """打印帮助信息"""
    print("""
可用命令：
  /research <问题>    - 启动深度研究（ReAct模式，LLM自主决策工具调用）
  /research_v1 <问题> - 启动旧版研究（固定7步流程）
  /rebuild            - 重建知识库索引（当添加新文档后使用）
  /clear              - 清空当前对话历史
  /save               - 保存最后一次研究报告为 Markdown 文件
  /save_trace         - 保存带完整推理轨迹的 Markdown 报告
  /pdf                - 保存最后一次研究报告为 PDF 文件
  /status             - 显示系统状态
  /help               - 显示此帮助信息
  quit/exit           - 退出程序

使用方式：
  1. 普通对话模式（默认）：
     直接输入问题，快速获得回答，不调用工具和搜索
     例如：你好
           什么是大模型？

  2. 深度研究模式（ReAct）：
     使用 /research 命令启动，LLM自主决定搜索策略
     例如：/research 银行是否可以直接使用客户原始交易数据训练内部大模型？

  3. 旧版研究模式（固定流程）：
     使用 /research_v1 命令启动固定的7步流程
     例如：/research_v1 基于大模型的自动授信/审批，是否必须保留人工干预？
""")


def get_data_dir() -> str:
    """获取数据目录路径"""
    # 相对于项目根目录
    current_dir = Path(__file__).parent.parent
    data_dir = current_dir / "data" / "documents"
    return str(data_dir)


def get_chroma_dir() -> str:
    """获取 Chroma 数据库目录"""
    current_dir = Path(__file__).parent.parent
    chroma_dir = current_dir / "data" / "chroma_db"
    return str(chroma_dir)


def ensure_data_dirs():
    """确保数据目录存在"""
    doc_dir = Path(get_data_dir())
    chroma_dir = Path(get_chroma_dir())

    doc_dir.mkdir(parents=True, exist_ok=True)
    chroma_dir.mkdir(parents=True, exist_ok=True)

    return doc_dir, chroma_dir


def main():
    """主函数"""
    print_banner()

    # 确保数据目录存在
    doc_dir, chroma_dir = ensure_data_dirs()
    print(f"文档目录: {doc_dir}")
    print(f"向量库目录: {chroma_dir}")

    # 初始化 LLM 客户端
    print("\n[初始化] 正在连接 LLM 服务...")
    try:
        llm = LLMClient()
        print("✓ LLM 客户端初始化成功")
    except ValueError as e:
        print(f"✗ LLM 初始化失败: {e}")
        return

    # 初始化知识库管理器
    print("\n[初始化] 正在初始化知识库...")
    kb_manager = KnowledgeBaseManager(
        persist_dir=str(chroma_dir),
        collection_name="policy_docs",
        chunk_size=512,
        chunk_overlap=50
    )

    if not kb_manager.initialize(str(doc_dir)):
        print("警告: 知识库初始化失败或为空")
        print(f"请将政策法规文档放入: {doc_dir}")
    else:
        print("✓ 知识库初始化成功")

    # 初始化网页搜索工具
    print("\n[初始化] 正在初始化网页搜索...")
    web_search = WebSearchTool()
    if web_search.is_available():
        print("✓ 网页搜索工具初始化成功")
    else:
        print("⚠ 网页搜索不可用（请检查 TAVILY_API_KEY）")

    # 初始化对话记忆
    memory = ConversationMemory(max_history=20)

    # 初始化研究 Agent
    agent = ResearchAgent(
        llm_client=llm,
        kb_manager=kb_manager,
        web_search=web_search,
        memory=memory
    )

    print("\n" + "="*60)
    print("初始化完成！")
    print("  - 普通对话：直接输入问题")
    print("  - 深度研究：/research <问题>")
    print("="*60 + "\n")

    # 主循环
    while True:
        try:
            user_input = input("问题> ").strip()
        except (EOFError, KeyboardInterrupt):
            print("\n再见！")
            break

        if not user_input:
            continue

        # 处理命令
        if user_input.lower() in ['quit', 'exit']:
            print("再见！")
            break

        if user_input.startswith('/'):
            handle_command(user_input, agent, kb_manager,
                           str(doc_dir), web_search)
            continue

        # 默认普通对话模式
        try:
            print("\n[普通对话模式]")
            response = agent.simple_chat(user_input)
            print(f"\n{response}")
            print("\n" + "-"*60 + "\n")

        except Exception as e:
            print(f"\n错误: {e}\n")


def handle_command(command: str, agent: ResearchAgent, kb_manager: KnowledgeBaseManager, doc_dir: str, web_search: WebSearchTool = None):
    """处理命令"""
    cmd = command.lower().strip()

    # 处理 /research 命令（新版 ReAct 模式）
    if cmd.startswith('/research') and not cmd.startswith('/research_v1'):
        # 提取问题
        question = command[9:].strip()  # 去掉 '/research ' 前缀
        if not question:
            print("请提供研究问题，例如：/research 银行是否可以使用客户数据训练模型？\n")
            return

        # 执行深度研究（ReAct 模式）
        try:
            result = agent.deep_research(question=question)
            # 输出结果
            print("\n" + result["formatted_response"])
            print("\n" + "-"*60 + "\n")
        except Exception as e:
            print(f"\n研究失败: {e}\n")
            import traceback
            traceback.print_exc()
        return

    # 处理 /research_v1 命令（旧版固定流程）
    if cmd.startswith('/research_v1'):
        question = command[12:].strip()  # 去掉 '/research_v1 ' 前缀
        if not question:
            print("请提供研究问题，例如：/research_v1 银行是否可以使用客户数据训练模型？\n")
            return

        try:
            result = agent.legacy_research(
                question=question,
                use_web_search=web_search.is_available() if web_search else False,
                top_k=5
            )
            print("\n" + result["formatted_response"])
            print("\n" + "-"*60 + "\n")
        except Exception as e:
            print(f"\n研究失败: {e}\n")
        return

    if cmd == '/help':
        print_help()

    elif cmd == '/clear':
        agent.clear_memory()
        print("对话历史已清空\n")

    elif cmd == '/rebuild':
        print("正在重建知识库索引...")
        if kb_manager.rebuild_index(doc_dir):
            print("知识库索引重建完成\n")
        else:
            print("知识库索引重建失败\n")

    elif cmd == '/save':
        agent.save_report()
        print()

    elif cmd == '/save_trace':
        agent.save_report_with_trace()
        print()

    elif cmd == '/pdf':
        agent.save_pdf()
        print()

    elif cmd == '/status':
        print("\n系统状态:")
        print(f"  - 对话历史: {len(agent.memory)} 条消息")
        print(f"  - 知识库状态: {'已初始化' if kb_manager.is_initialized else '未初始化'}")
        print(
            f"  - 网页搜索: {'可用' if agent.web_search.is_available() else '不可用'}")
        print()

    else:
        print(f"未知命令: {command}")
        print("输入 /help 查看可用命令\n")


if __name__ == "__main__":
    main()
