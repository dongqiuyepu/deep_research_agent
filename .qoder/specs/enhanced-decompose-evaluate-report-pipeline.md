# 增强 DecomposeTool、EvaluateTool 和内容摘要方案

## 一、背景与目标

### 问题分析
1. **DecomposeTool 问题拆解**：当前是被动记录工具，LLM 无法清晰感知子问题进度
2. **EvaluateTool 评估**：完全依赖 LLM 主观判断，缺乏客观评估标准
3. **web_search 内容处理**：内容无截断，可能导致上下文溢出

### 用户选择
- 子问题追踪：**显式状态追踪**（新增 SubQuestionTracker）
- 证据评估：**评估智能体**（独立的 EvaluatorAgent）
- 内容处理：**智能摘要**（使用 LLM 生成摘要）
- 报告格式：**暂不修改**

---

## 二、实现方案

### 模块 1：子问题显式追踪

#### 1.1 新增数据结构 `src/agent/sub_question_tracker.py`

```python
@dataclass
class SubQuestion:
    sub_question_id: str        # SQ-001, SQ-002, ...
    question_text: str          # 子问题文本
    status: str                 # "pending" / "in_progress" / "resolved"
    parent_question: str        # 原始问题
    evidence_ids: List[str]     # 关联的证据ID
    answer: str = ""            # 答案（resolved时填写）
    created_at: int = 0         # 创建轮次
    resolved_at: int = 0        # 解决轮次

class SubQuestionTracker:
    """子问题追踪器"""
    - create_sub_questions(original_question, sub_question_texts) -> List[SubQuestion]
    - mark_in_progress(sq_id)
    - mark_resolved(sq_id, answer, evidence_ids)
    - associate_evidence(sq_id, evidence_ids)
    - get_progress_summary() -> str  # 生成进度摘要供 Prompt 使用
    - get_pending_questions() -> List[SubQuestion]
    - reset()
```

#### 1.2 新增工具 `MarkResolvedTool`

在 `src/tools/research_tools.py` 中新增：

```python
class MarkResolvedTool(BaseTool):
    name = "mark_resolved"
    description = "标记某个子问题已解决，并记录答案和支持证据"
    parameters = {
        "sub_question_id": str,  # SQ-001
        "answer": str,           # 简洁答案
        "evidence_ids": List[str]  # 支持证据
    }
```

#### 1.3 修改 `DecomposeTool`

- 注入 `SubQuestionTracker` 实例
- 在 `execute()` 中调用 `tracker.create_sub_questions()`
- 返回结构化的子问题列表（包含 ID 和状态）

#### 1.4 修改 `ReActEngine`

- 初始化 `SubQuestionTracker` 并关联到 `ResearchTrajectory`
- 在工具执行后添加钩子：
  - `decompose` 执行后记录子问题
  - `kb_search`/`web_search` 执行后关联证据到当前 `in_progress` 子问题
  - `mark_resolved` 执行后更新状态
- 在 Prompt 中注入子问题进度摘要

#### 1.5 Prompt 增强

```
== 子问题进度 ==

[SQ-001] ✅ 已解决
  问题: 是否需要客户明确同意？
  答案: 必须取得明确同意（《个保法》第14条）
  证据: [EVD-005, EVD-012]

[SQ-002] 🔄 进行中
  问题: 是否需要数据脱敏？
  已收集证据: [EVD-018]

[SQ-003] ⏳ 待处理
  问题: 行业最佳实践是什么？
```

---

### 模块 2：评估智能体（EvaluatorAgent）

#### 2.1 新增数据结构 `src/agent/evaluation_report.py`

```python
@dataclass
class CoverageAnalysis:
    key_dimensions: List[str]      # 问题关键维度
    covered_dimensions: List[str]  # 已覆盖维度
    missing_dimensions: List[str]  # 缺失维度
    coverage_score: float          # 覆盖率 0-1

@dataclass
class QualityAnalysis:
    avg_relevance_score: float     # 平均相关性
    source_reliability: float      # 来源可靠性
    quality_score: float           # 综合质量 0-1
    quality_level: str             # "优秀"/"良好"/"一般"/"不足"

@dataclass
class DiversityAnalysis:
    local_count: int               # 本地证据数
    web_count: int                 # 网页证据数
    diversity_score: float         # 多样性 0-1

@dataclass
class EvidenceGap:
    dimension: str                 # 缺失维度
    reason: str                    # 原因
    suggested_query: str           # 建议搜索词

@dataclass
class EvaluationReport:
    overall_score: float           # 综合评分 0-1
    is_sufficient: bool            # 是否充分（>=0.75）
    coverage_analysis: CoverageAnalysis
    quality_analysis: QualityAnalysis
    diversity_analysis: DiversityAnalysis
    gaps: List[EvidenceGap]
    recommendations: List[str]
```

#### 2.2 新增评估智能体 `src/agent/evaluator_agent.py`

```python
class EvaluatorAgent:
    """证据评估智能体"""
    
    def evaluate_evidence_sufficiency(
        self, 
        question: str, 
        evidences: List[Evidence],
        trajectory: ResearchTrajectory
    ) -> EvaluationReport:
        """综合评估证据充分性"""
        
        # 1. 覆盖度分析
        coverage = self._analyze_coverage(question, evidences)
        
        # 2. 质量分析
        quality = self._analyze_quality(evidences)
        
        # 3. 多样性分析
        diversity = self._analyze_diversity(evidences)
        
        # 4. 缺口识别
        gaps = self._identify_gaps(question, evidences, coverage)
        
        # 5. 综合评分
        overall_score = coverage.score * 0.4 + quality.score * 0.4 + diversity.score * 0.2
        
        # 6. 生成建议
        recommendations = self._generate_recommendations(gaps, quality, diversity)
        
        return EvaluationReport(...)
```

#### 2.3 评估 Prompt 模板 `src/agent/evaluator_prompts.py`

**覆盖度分析 Prompt**：提取问题关键维度
**缺口识别 Prompt**：识别缺失维度并生成搜索建议

#### 2.4 与 ReAct 集成

在 `ReActEngine.run()` 的每次工具执行后：

```python
# 调用评估智能体
all_evidences = self.kb_manager.evidence_tracker.get_all_evidence()
evaluation = self.evaluator_agent.evaluate_evidence_sufficiency(
    question, all_evidences, trajectory
)

# 将评估报告注入 Observation
observation += self._format_evaluation_report(evaluation)
```

**评估报告注入格式**：
```
[证据评估]
综合评分: 0.65 (不充分)
覆盖度: 50% (2/4 维度)
质量: 良好 (0.72)
多样性: 0.8

缺口:
  - 缺少金融监管专门规定
    建议搜索: "银行客户信息 模型训练 监管办法"
```

---

### 模块 3：Web 内容智能摘要

#### 3.1 新增摘要模块 `src/utils/content_summarizer.py`

```python
class ContentSummarizer:
    """内容摘要器"""
    
    CHAR_THRESHOLD = 2000      # 触发摘要的字符阈值
    TARGET_LENGTH = 600        # 目标摘要长度
    
    def should_summarize(self, content: str) -> bool:
        return len(content) > self.CHAR_THRESHOLD
    
    def summarize(self, content: str, title: str = "") -> str:
        """调用 LLM 生成摘要"""
        prompt = SUMMARY_PROMPT.format(content=content, title=title)
        return self.llm.chat([{"role": "user", "content": prompt}])
```

**摘要 Prompt**：
```
将以下网页内容压缩为 500-800 字符的摘要，保留：
1. 核心事实和数据（数字、日期、比例）
2. 关键引用和来源
3. 因果关系和逻辑链

原文:
{content}

摘要:
```

#### 3.2 扩展 Evidence 数据结构

在 `src/knowledge_base/evidence_tracker.py` 中：

```python
@dataclass
class Evidence:
    # 现有字段...
    
    # 新增字段
    is_summarized: bool = False     # 是否已摘要
    content_length: int = 0         # 原始内容长度
```

#### 3.3 修改 WebSearchTool

在 `src/tools/research_tools.py` 的 `WebSearchTool.execute()` 中：

```python
for r in results:
    content = r.content
    is_summarized = False
    
    # 判断是否需要摘要
    if self.summarizer.should_summarize(content):
        content = self.summarizer.summarize(content, r.title)
        is_summarized = True
    
    evidence = self.kb_manager.add_web_evidence(
        content=content,
        is_summarized=is_summarized,
        content_length=len(r.content),
        ...
    )
```

---

## 三、文件修改清单

### 新增文件
| 文件 | 说明 |
|------|------|
| `src/agent/sub_question_tracker.py` | 子问题追踪器数据结构和逻辑 |
| `src/agent/evaluation_report.py` | 评估报告数据结构 |
| `src/agent/evaluator_agent.py` | 评估智能体实现 |
| `src/agent/evaluator_prompts.py` | 评估相关提示词模板 |
| `src/utils/content_summarizer.py` | 内容摘要器 |

### 修改文件
| 文件 | 修改内容 |
|------|----------|
| `src/tools/research_tools.py` | 新增 MarkResolvedTool，修改 DecomposeTool 和 WebSearchTool |
| `src/agent/react_engine.py` | 集成 SubQuestionTracker 和 EvaluatorAgent，增强 Prompt |
| `src/agent/research_agent.py` | 初始化新增的组件 |
| `src/knowledge_base/evidence_tracker.py` | 扩展 Evidence 数据结构 |

---

## 四、实施顺序

### 阶段 1：子问题追踪（优先级：高）
1. 创建 `sub_question_tracker.py`
2. 新增 `MarkResolvedTool`
3. 修改 `DecomposeTool` 集成 tracker
4. 修改 `ReActEngine` 添加钩子和 Prompt 增强

### 阶段 2：评估智能体（优先级：高）
1. 创建 `evaluation_report.py` 数据结构
2. 创建 `evaluator_prompts.py` 提示词
3. 实现 `EvaluatorAgent` 核心逻辑
4. 集成到 `ReActEngine`

### 阶段 3：内容摘要（优先级：中）
1. 创建 `ContentSummarizer`
2. 扩展 `Evidence` 数据结构
3. 修改 `WebSearchTool` 调用摘要

---

## 五、验证方案

### 测试步骤
1. **单元测试**：
   - `SubQuestionTracker` 状态转换逻辑
   - `EvaluatorAgent` 评分计算
   - `ContentSummarizer` 摘要触发判断

2. **集成测试**：
   - 使用复杂问题（如"银行是否可以使用客户数据训练模型"）运行完整研究流程
   - 验证子问题进度在 Prompt 中正确显示
   - 验证评估报告正确反馈给 LLM
   - 验证长内容被正确摘要

3. **端到端测试**：
   ```bash
   python main.py
   # 输入复杂问题
   # 观察控制台输出的子问题进度和评估报告
   # 检查最终报告中的证据引用
   ```

### 成功标准
- LLM 能够感知并更新子问题状态
- 评估报告能够引导 LLM 补充缺失证据
- 长内容被摘要后不超过 800 字符
- 完整研究流程正常完成，无上下文溢出
