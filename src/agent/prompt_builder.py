"""Prompt 构建器 - 构建 RAG 和研究相关的 Prompt"""

from typing import List, Optional


class PromptBuilder:
    """Prompt 构建器"""

    # 系统 Prompt - 定义 Agent 角色
    SYSTEM_PROMPT = """你是一位金融合规领域的资深研究专家，专注于政策法规研究和合规分析。

你的职责：
1. 基于提供的证据回答用户关于政策合规的问题
2. 每个结论必须引用证据编号 [EVD-XXX]
3. 区分三类证据权重：
   - 强制性要求（法律法规明确规定，必须执行）
   - 审慎性建议（监管指引建议，最好执行）
   - 行业实践（常见做法，可以参考）
4. 如果证据不足以回答问题，明确说明并建议补充检索方向

回答格式要求：
- 【直接回答】：先给出明确的是/否/有条件允许的判断
- 【法律依据】：列出支持结论的法规条文，使用 [EVD-XXX] 标注
- 【实施建议】：给出具体可操作的建议
- 【风险提示】：指出潜在的合规风险（如有）"""

    # RAG Prompt 模板
    RAG_PROMPT_TEMPLATE = """【检索到的证据】
{evidence_text}

【用户问题】
{question}

请基于以上证据回答问题。要求：
1. 每个结论后必须用 [EVD-XXX] 标注证据来源
2. 如果多条证据支持同一结论，列出所有相关证据编号
3. 如果证据不足，明确说明"未找到明确规定"
4. 区分"强制性要求"和"审慎性建议"
"""

    # 无证据时的提示
    NO_EVIDENCE_PROMPT = """【注意】
未能从知识库和网页搜索中找到直接相关的证据。

【用户问题】
{question}

请基于你的专业知识谨慎回答，并明确指出：
1. 这是基于一般性理解的回答，而非基于具体法规条文
2. 建议用户查阅相关法规原文确认
3. 如果可能，指出应该查阅哪些法规或文件"""

    @classmethod
    def build_system_prompt(cls) -> str:
        """构建系统 Prompt"""
        return cls.SYSTEM_PROMPT

    @classmethod
    def build_rag_prompt(
        cls,
        question: str,
        evidence_text: str
    ) -> str:
        """
        构建 RAG Prompt

        Args:
            question: 用户问题
            evidence_text: 格式化的证据文本

        Returns:
            完整的 RAG Prompt
        """
        if not evidence_text or evidence_text.strip() == "（未找到相关证据）":
            return cls.NO_EVIDENCE_PROMPT.format(question=question)

        return cls.RAG_PROMPT_TEMPLATE.format(
            evidence_text=evidence_text,
            question=question
        )

    @classmethod
    def build_messages(
        cls,
        question: str,
        evidence_text: str,
        history: List[dict] = None
    ) -> List[dict]:
        """
        构建完整的消息列表

        Args:
            question: 用户问题
            evidence_text: 证据文本
            history: 历史对话（可选）

        Returns:
            消息列表，适用于 OpenAI API
        """
        messages = [
            {"role": "system", "content": cls.build_system_prompt()}
        ]

        # 添加历史对话（如果有）
        if history:
            # 只保留最近几轮对话，避免上下文过长
            recent_history = history[-6:]  # 最近3轮对话
            messages.extend(recent_history)

        # 添加当前问题（带证据）
        user_message = cls.build_rag_prompt(question, evidence_text)
        messages.append({"role": "user", "content": user_message})

        return messages

    @classmethod
    def build_search_query(cls, question: str) -> str:
        """
        优化搜索查询（提取关键词）

        Args:
            question: 原始问题

        Returns:
            优化后的搜索查询
        """
        # 简单实现：直接返回原问题
        # 可以扩展为使用 LLM 提取关键词
        return question

    @classmethod
    def format_final_response(
        cls,
        answer: str,
        evidence_chain: str
    ) -> str:
        """
        格式化最终响应

        Args:
            answer: LLM 生成的答案
            evidence_chain: 证据链

        Returns:
            格式化的完整响应
        """
        return f"""=== 研究结论 ===

{answer}

=== 证据链 ===

{evidence_chain}"""
