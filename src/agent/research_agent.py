"""研究 Agent - 核心推理逻辑"""

from typing import Dict, Any, List, Optional, Tuple
import re

from knowledge_base import KnowledgeBaseManager, Evidence
from tools import WebSearchTool
from memory import ConversationMemory
from agent.prompt_builder import PromptBuilder


class ResearchAgent:
    """研究 Agent - 整合知识库检索、网页搜索和 LLM 推理"""

    def __init__(
        self,
        llm_client,
        kb_manager: KnowledgeBaseManager,
        web_search: WebSearchTool,
        memory: ConversationMemory
    ):
        """
        初始化研究 Agent

        Args:
            llm_client: LLM 客户端
            kb_manager: 知识库管理器
            web_search: 网页搜索工具
            memory: 对话记忆
        """
        self.llm = llm_client
        self.kb_manager = kb_manager
        self.web_search = web_search
        self.memory = memory
        self.prompt_builder = PromptBuilder()
        self.last_report = None  # 保存最后一次报告

    def research(
        self,
        question: str,
        use_web_search: bool = True,
        top_k: int = 5
    ) -> Dict[str, Any]:
        """
        执行研究任务

        Args:
            question: 用户问题
            use_web_search: 是否使用网页搜索
            top_k: 知识库检索数量

        Returns:
            {
                "answer": str,           # LLM 生成的答案
                "evidence_chain": str,   # 格式化的证据链
                "evidences": List[Evidence],  # 证据列表
                "formatted_response": str  # 完整格式化响应
            }
        """
        print(f"\n{'='*50}")
        print(f"研究问题: {question}")
        print(f"{'='*50}")

        # 1. 从知识库检索
        print("\n[步骤1] 检索本地知识库...")
        local_evidences, local_evidence_text = self.kb_manager.search(
            query=question,
            top_k=top_k
        )

        # 2. 网页搜索（如果启用）
        web_evidences = []
        if use_web_search and self.web_search.is_available():
            print("\n[步骤2] 执行网页搜索...")
            web_results = self.web_search.search(question, max_results=3)

            # 将网页结果转换为证据格式
            for result in web_results:
                evidence = self.kb_manager.add_web_evidence(
                    title=result.title,
                    content=result.content,
                    url=result.url,
                    score=result.score
                )
                web_evidences.append(evidence)
        else:
            print("\n[步骤2] 跳过网页搜索")

        # 3. 合并所有证据
        all_evidences = local_evidences + web_evidences

        # 4. 构建证据文本
        evidence_text = self._build_evidence_text(all_evidences)

        # 5. 构建 Prompt 并调用 LLM
        print("\n[步骤3] 调用 LLM 生成答案...")
        messages = self.prompt_builder.build_messages(
            question=question,
            evidence_text=evidence_text,
            history=self.memory.get_recent(4)  # 最近2轮对话
        )

        try:
            answer = self.llm.chat(messages)
        except Exception as e:
            answer = f"生成答案时出错: {e}"

        # 6. 更新对话记忆
        self.memory.add_user_message(question)
        self.memory.add_assistant_message(answer)

        # 7. 构建结果
        evidence_chain = self.kb_manager.get_evidence_chain()
        formatted_response = self.prompt_builder.format_final_response(
            answer=answer,
            evidence_chain=evidence_chain
        )

        # 保存最后一次报告
        self.last_report = {
            "question": question,
            "formatted_response": formatted_response,
            "timestamp": None
        }

        print("\n[完成] 研究任务完成")

        return {
            "answer": answer,
            "evidence_chain": evidence_chain,
            "evidences": all_evidences,
            "formatted_response": formatted_response
        }

    def _build_evidence_text(self, evidences: List[Evidence]) -> str:
        """构建证据文本"""
        if not evidences:
            return "（未找到相关证据）"

        lines = []
        for e in evidences:
            source_info = f"[{e.evidence_id}] "
            if e.source_type == "local":
                source_info += f"来源: {e.source}"
                if e.page:
                    source_info += f" (第{e.page}页)"
            else:
                source_info += f"来源: {e.source} (网页搜索)"

            lines.append(source_info)
            lines.append(f"内容: {e.content}")
            lines.append("")

        return "\n".join(lines)

    def extract_evidence_ids(self, text: str) -> List[str]:
        """
        从文本中提取证据ID

        Args:
            text: 包含 [EVD-XXX] 引用的文本

        Returns:
            证据ID列表
        """
        pattern = r'\[EVD-\d{3}\]'
        matches = re.findall(pattern, text)
        # 去重并保持顺序
        seen = set()
        unique = []
        for m in matches:
            if m not in seen:
                seen.add(m)
                unique.append(m.strip('[]'))
        return unique

    def simple_chat(self, message: str) -> str:
        """
        简单对话（不走研究流程）

        Args:
            message: 用户消息

        Returns:
            LLM 响应
        """
        self.memory.add_user_message(message)

        messages = [
            {"role": "system", "content": "你是一个有帮助的助手。"},
        ]
        messages.extend(self.memory.get_history())

        try:
            response = self.llm.chat(messages)
            self.memory.add_assistant_message(response)
            return response
        except Exception as e:
            return f"对话出错: {e}"

    def clear_memory(self):
        """清空对话记忆"""
        self.memory.clear()
        print("对话记忆已清空")

    def save_report(self, filepath: str = None) -> bool:
        """
        保存最后一次报告到 Markdown 文件

        Args:
            filepath: 保存路径，如果为 None 则自动生成

        Returns:
            是否成功保存
        """
        import os
        from datetime import datetime

        if not self.last_report:
            print("错误：没有可保存的报告，请先进行一次研究")
            return False

        # 生成文件名
        if not filepath:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            reports_dir = "./reports"
            os.makedirs(reports_dir, exist_ok=True)
            filepath = os.path.join(reports_dir, f"report_{timestamp}.md")

        try:
            with open(filepath, 'w', encoding='utf-8') as f:
                # 写入标题
                f.write(f"# 研究报告\n\n")
                f.write(f"**问题**: {self.last_report['question']}\n\n")
                f.write(
                    f"**生成时间**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")
                f.write("---\n\n")
                # 写入报告内容
                f.write(self.last_report['formatted_response'])

            print(f"✅ 报告已保存到: {os.path.abspath(filepath)}")
            return True

        except Exception as e:
            print(f"❌ 保存报告失败: {e}")
            return False

    def save_pdf(self, filepath: str = None) -> bool:
        """
        保存最后一次报告到 PDF 文件

        Args:
            filepath: 保存路径，如果为 None 则自动生成

        Returns:
            是否成功保存
        """
        import os
        from datetime import datetime

        if not self.last_report:
            print("错误：没有可保存的报告，请先进行一次研究")
            return False

        try:
            from reportlab.lib.pagesizes import letter, A4
            from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
            from reportlab.lib.units import inch
            from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, PageBreak
            from reportlab.pdfbase import pdfmetrics
            from reportlab.pdfbase.ttfonts import TTFont
            from reportlab.lib.enums import TA_LEFT, TA_CENTER
        except ImportError:
            print("❌ 缺少PDF生成依赖，请先安装：pip install reportlab")
            return False

        # 生成文件名
        if not filepath:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            reports_dir = "./reports"
            os.makedirs(reports_dir, exist_ok=True)
            filepath = os.path.join(reports_dir, f"report_{timestamp}.pdf")

        try:
            # 注册中文字体（使用系统自带的微软雅黑）
            try:
                font_path = "C:/Windows/Fonts/msyh.ttc"  # 微软雅黑
                pdfmetrics.registerFont(TTFont('msyh', font_path))
                chinese_font = 'msyh'
            except:
                # 如果微软雅黑不可用，使用SimSun
                try:
                    font_path = "C:/Windows/Fonts/simsun.ttc"
                    pdfmetrics.registerFont(TTFont('simsun', font_path))
                    chinese_font = 'simsun'
                except:
                    print("⚠️  警告：无法加载中文字体，PDF可能无法正确显示中文")
                    chinese_font = 'Helvetica'

            # 创建PDF文档
            doc = SimpleDocTemplate(filepath, pagesize=A4)
            story = []

            # 定义样式
            styles = getSampleStyleSheet()

            # 标题样式
            title_style = ParagraphStyle(
                'CustomTitle',
                parent=styles['Heading1'],
                fontName=chinese_font,
                fontSize=24,
                textColor='#2c3e50',
                spaceAfter=30,
                alignment=TA_CENTER
            )

            # 正文样式
            body_style = ParagraphStyle(
                'CustomBody',
                parent=styles['Normal'],
                fontName=chinese_font,
                fontSize=11,
                leading=18,
                spaceAfter=12
            )

            # 问题样式
            question_style = ParagraphStyle(
                'Question',
                parent=styles['Normal'],
                fontName=chinese_font,
                fontSize=12,
                textColor='#e74c3c',
                spaceAfter=20
            )

            # 添加标题
            story.append(Paragraph("研究报告", title_style))
            story.append(Spacer(1, 0.2*inch))

            # 添加问题
            story.append(
                Paragraph(f"<b>问题：</b>{self.last_report['question']}", question_style))

            # 添加时间
            time_str = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            story.append(Paragraph(f"<b>生成时间：</b>{time_str}", body_style))
            story.append(Spacer(1, 0.3*inch))

            # 处理报告内容（简单的文本处理）
            content = self.last_report['formatted_response']

            # 按行分割并添加到PDF
            for line in content.split('\n'):
                if line.strip():
                    # 转义HTML特殊字符
                    line = line.replace('&', '&amp;').replace(
                        '<', '&lt;').replace('>', '&gt;')
                    story.append(Paragraph(line, body_style))
                else:
                    story.append(Spacer(1, 0.1*inch))

            # 生成PDF
            doc.build(story)

            print(f"✅ PDF报告已保存到: {os.path.abspath(filepath)}")
            return True

        except Exception as e:
            print(f"❌ 保存PDF失败: {e}")
            import traceback
            traceback.print_exc()
            return False
