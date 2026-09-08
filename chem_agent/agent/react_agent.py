"""ReAct 循环引擎：解析 LLM 输出、执行工具、迭代推理。

增强模块：
- 反思自纠错：工具失败时自动注入反思提示
- 经验记忆：检索相似历史经验 / 存储成功交互
- 任务预规划：复杂问题进入循环前制定计划
"""

import asyncio
import json
import logging
import re
from typing import TYPE_CHECKING, Optional

from langchain_core.messages import AIMessage, HumanMessage, SystemMessage
from langchain_core.output_parsers import StrOutputParser
from langchain_core.language_models import BaseChatModel

from chem_agent.agent.models import AgentResponse, AgentStep, ParsedAction, ToolDef
from chem_agent.agent.prompts import build_react_system_prompt
from chem_agent.agent.tools import ToolExecutor

if TYPE_CHECKING:
    from chem_agent.agent.memory import AgentMemoryService
    from chem_agent.agent.planner import TaskPlanner

logger = logging.getLogger(__name__)


class ReActAgent:
    """ReAct 工具调用智能体（支持反思、记忆、规划增强）。"""

    def __init__(
        self,
        llm: BaseChatModel,
        tools: dict[str, tuple[ToolDef, ToolExecutor]],
        max_iterations: int = 10,
        memory_service: Optional["AgentMemoryService"] = None,
        enable_planning: bool = True,
        enable_reflection: bool = True,
        max_reflections: int = 2,
        llm_timeout: int = 60,
    ):
        self._llm = llm
        self._all_tools = tools
        self._max_iterations = max_iterations
        self._memory = memory_service
        self._enable_reflection = enable_reflection
        self._max_reflections = max_reflections
        self._llm_timeout = llm_timeout

        # 延迟初始化规划器，避免循环导入
        self._planner: Optional["TaskPlanner"] = None
        if enable_planning:
            from chem_agent.agent.planner import TaskPlanner
            self._planner = TaskPlanner(llm)

    def reload_llm(self, new_llm: BaseChatModel):
        """热替换 LLM 实例（Provider 切换后调用）"""
        self._llm = new_llm
        if self._planner is not None:
            self._planner._llm = new_llm

    async def run(
        self,
        query: str,
        user_permissions: list[str],
        chat_history: Optional[list] = None,
    ) -> AgentResponse:
        """执行 ReAct 循环（含规划、记忆、反思增强）。"""
        steps: list[AgentStep] = []
        tools_used: list[str] = []

        # 根据用户权限过滤可用工具
        available = self._filter_tools_by_permission(user_permissions)
        if not available:
            return AgentResponse(
                reply="当前用户没有可用的工具权限。",
                steps=[AgentStep(type="error", content="无可用工具权限")],
            )

        # 构建系统提示词（仅包含有权限的工具）
        tool_defs = {name: td for name, (td, _) in available.items()}
        system_prompt = build_react_system_prompt(tool_defs)
        history_messages = []
        for h in chat_history or []:
            if isinstance(h, dict):
                role = str(h.get("role", "")).lower()
                content = h.get("content")
                if role == "user":
                    history_messages.append(HumanMessage(content=str(content or "")))
                elif role in ("assistant", "ai"):
                    history_messages.append(AIMessage(content=str(content or "")))
            elif getattr(h, "type", "") in ("human", "user"):
                history_messages.append(HumanMessage(content=getattr(h, "content", "") or ""))
            elif getattr(h, "type", "") in ("ai", "assistant"):
                history_messages.append(AIMessage(content=getattr(h, "content", "") or ""))

        # ========== 预处理：并行执行规划 + 记忆检索 ==========
        plan_steps = None
        similar_memories: list[dict] = []

        tasks_to_run = {}
        if self._planner:
            tasks_to_run["plan"] = self._planner.analyze_and_plan(query, tool_defs)
        if self._memory:
            tasks_to_run["memory"] = self._memory.retrieve_similar(query)

        if tasks_to_run:
            results = await asyncio.gather(
                *tasks_to_run.values(), return_exceptions=True,
            )
            for key, result in zip(tasks_to_run.keys(), results):
                if isinstance(result, Exception):
                    logger.warning("%s 预处理失败: %s", key, result)
                    continue
                if key == "plan":
                    plan_steps = result
                elif key == "memory":
                    similar_memories = result or []

        # ========== 构建初始 scratchpad ==========
        scratchpad = ""

        # 注入规划
        if plan_steps:
            plan_text = "\n".join(f"{i}. {s}" for i, s in enumerate(plan_steps, 1))
            steps.append(AgentStep(
                type="planning",
                content=f"已制定 {len(plan_steps)} 步执行计划",
                plan_steps=plan_steps,
            ))
            scratchpad += f"[任务计划]:\n{plan_text}\n请按计划逐步执行。\n\n"

        # 注入历史经验
        if similar_memories:
            memory_lines = ["[历史参考经验]:"]
            for i, mem in enumerate(similar_memories, 1):
                memory_lines.append(
                    f"{i}. 问题: {mem['query'][:80]} | "
                    f"使用工具: {mem['tools']} | "
                    f"相似度: {mem['similarity']}"
                )
            scratchpad += "\n".join(memory_lines) + "\n\n"

        # ========== ReAct 循环 ==========
        reflection_count = 0  # 连续反思计数

        for iteration in range(1, self._max_iterations + 1):
            # 构建当前轮的 prompt
            user_content = query
            if scratchpad:
                user_content = f"{query}\n\n{scratchpad}"

            messages = [
                SystemMessage(content=system_prompt),
                *history_messages,
                HumanMessage(content=user_content),
            ]

            # 调用 LLM
            try:
                chain = self._llm | StrOutputParser()
                raw_output = await asyncio.wait_for(
                    chain.ainvoke(messages),
                    timeout=self._llm_timeout,
                )
            except asyncio.TimeoutError:
                logger.error("LLM 调用超时 (iter %d): 超过 %d 秒", iteration, self._llm_timeout)
                steps.append(AgentStep(type="error", content=f"LLM 调用超时: 超过 {self._llm_timeout} 秒"))
                break
            except Exception as e:
                logger.error("LLM 调用失败 (iter %d): %s", iteration, e)
                steps.append(AgentStep(type="error", content=f"LLM 调用失败: {e}"))
                break

            # 清理 LLM 可能输出的 <think>...</think> 标签
            clean_output = self._strip_think_tags(raw_output)

            # 解析输出
            thought, action, final_answer = self._parse_output(clean_output)

            # 记录 Thought
            if thought:
                steps.append(AgentStep(type="thought", content=thought))
                scratchpad += f"\nThought: {thought}"

            # 如果有 Final Answer，结束循环
            if final_answer:
                steps.append(AgentStep(type="answer", content=final_answer))

                # 异步存储成功经验（不阻塞返回）
                if self._memory:
                    asyncio.ensure_future(self._store_memory_safe(
                        query, final_answer, tools_used, iteration,
                    ))

                return AgentResponse(
                    reply=final_answer,
                    steps=steps,
                    tools_used=list(set(tools_used)),
                    iterations=iteration,
                )

            # 如果有 Action，执行工具
            if action:
                steps.append(AgentStep(
                    type="action",
                    content=f"调用 {action.tool_name}",
                    tool_name=action.tool_name,
                    tool_input=action.tool_input,
                ))
                scratchpad += f"\nAction: {action.tool_name}"
                scratchpad += f"\nAction Input: {json.dumps(action.tool_input, ensure_ascii=False)}"

                observation = await self._execute_tool(action, available)
                tools_used.append(action.tool_name)

                steps.append(AgentStep(type="observation", content=observation))
                scratchpad += f"\nObservation: {observation}\n"

                # ===== 反思检测 =====
                if self._enable_reflection:
                    trigger = self._detect_reflection_trigger(observation)
                    if trigger:
                        if reflection_count < self._max_reflections:
                            reflection_count += 1
                            hint = self._build_reflection_hint(trigger, action.tool_name)
                            steps.append(AgentStep(
                                type="reflection",
                                content=f"[{trigger}] {hint}",
                            ))
                            scratchpad += f"[系统提示: {hint}]\n"
                        else:
                            scratchpad += "[系统提示: 已多次重试，建议直接给出 Final Answer 或告知用户当前数据不足]\n"
                    else:
                        reflection_count = 0  # 成功则重置

                continue

            # 既没有 Action 也没有 Final Answer，尝试把整段输出当作最终答案
            if clean_output.strip():
                steps.append(AgentStep(type="answer", content=clean_output.strip()))

                if self._memory:
                    asyncio.ensure_future(self._store_memory_safe(
                        query, clean_output.strip(), tools_used, iteration,
                    ))

                return AgentResponse(
                    reply=clean_output.strip(),
                    steps=steps,
                    tools_used=list(set(tools_used)),
                    iterations=iteration,
                )

            # 空输出，记录错误
            steps.append(AgentStep(type="error", content="LLM 返回了空输出"))
            break

        # 达到最大迭代次数
        partial = self._build_partial_answer(steps)
        steps.append(AgentStep(
            type="error",
            content=f"已达最大推理步数 ({self._max_iterations})，以下是部分结果。",
        ))
        return AgentResponse(
            reply=partial or "推理过程复杂，已达到最大步骤限制。请尝试更简化的问题。",
            steps=steps,
            tools_used=list(set(tools_used)),
            iterations=self._max_iterations,
        )

    # ---------- 记忆辅助 ----------

    async def _store_memory_safe(
        self, query: str, answer: str, tools_used: list[str], iterations: int,
    ):
        """安全地存储记忆，不抛异常。"""
        try:
            if self._memory:
                await self._memory.store_success(
                    query=query,
                    answer=answer,
                    tools_used=list(set(tools_used)),
                    iterations=iterations,
                )
        except Exception as e:
            logger.warning("记忆存储失败（已忽略）: %s", e)

    # ---------- 反思辅助 ----------

    @staticmethod
    def _build_reflection_hint(trigger: str, tool_name: str) -> str:
        """根据触发类型生成反思提示。"""
        if trigger == "tool_error":
            return (
                f"工具 {tool_name} 执行出错，请检查参数格式是否正确，"
                f"或考虑换用其他工具。"
            )
        elif trigger == "empty_result":
            return (
                f"工具 {tool_name} 返回空结果，可能原因：关键词过于具体、"
                f"数据库中无此数据。请尝试简化关键词、放宽条件或换用其他工具。"
            )
        return f"工具 {tool_name} 结果异常，请反思后调整策略。"

    # ---------- 解析 ----------

    @staticmethod
    def _strip_think_tags(text: str) -> str:
        """移除 LLM 可能输出的 <think>...</think> 标签。"""
        return re.sub(r"<think>.*?</think>", "", text, flags=re.DOTALL).strip()

    @staticmethod
    def _parse_output(text: str) -> tuple[str, Optional[ParsedAction], Optional[str]]:
        """
        解析 LLM 输出，返回 (thought, action, final_answer)。
        使用多种正则模式容错匹配。
        """
        thought = ""
        action = None
        final_answer = None

        # 提取 Thought
        thought_match = re.search(
            r"Thought:\s*(.+?)(?=\nAction:|\nFinal Answer:|\Z)",
            text, re.DOTALL,
        )
        if thought_match:
            thought = thought_match.group(1).strip()

        # 提取 Final Answer
        fa_match = re.search(r"Final Answer:\s*(.+)", text, re.DOTALL)
        if fa_match:
            final_answer = fa_match.group(1).strip()
            return thought, None, final_answer

        # 提取 Action + Action Input
        action_match = re.search(
            r"Action:\s*([a-zA-Z_]+)\s*\n\s*Action Input:\s*(.+?)(?=\n\s*(?:Thought:|Observation:|Final Answer:)|\Z)",
            text, re.DOTALL,
        )
        if action_match:
            tool_name = action_match.group(1).strip()
            raw_input = action_match.group(2).strip()
            tool_input = _parse_json_safe(raw_input)
            action = ParsedAction(tool_name=tool_name, tool_input=tool_input)

        return thought, action, final_answer

    # ---------- 工具执行 ----------

    @staticmethod
    async def _execute_tool(
        action: ParsedAction,
        available: dict[str, tuple[ToolDef, ToolExecutor]],
    ) -> str:
        """执行工具调用。"""
        if action.tool_name not in available:
            return f"未知工具: {action.tool_name}。请使用可用工具列表中的工具。"

        _, executor = available[action.tool_name]
        try:
            result = await executor(action.tool_input)
            return result
        except Exception as e:
            logger.error("工具 %s 执行失败: %s", action.tool_name, e)
            return f"工具执行失败: {e}"

    # ---------- 权限过滤 ----------

    def _filter_tools_by_permission(
        self, user_permissions: list[str],
    ) -> dict[str, tuple[ToolDef, ToolExecutor]]:
        """根据用户权限过滤可用工具。"""
        if "*" in user_permissions:
            return dict(self._all_tools)
        filtered = {}
        for name, (tool_def, executor) in self._all_tools.items():
            if tool_def.permission in user_permissions:
                filtered[name] = (tool_def, executor)
        return filtered

    # ---------- 辅助 ----------

    @staticmethod
    def _detect_reflection_trigger(observation: str) -> Optional[str]:
        """检测 observation 是否需要触发反思。返回触发类型或 None。"""
        error_patterns = ["错误", "失败", "异常", "未知工具", "工具执行失败"]
        empty_patterns = ["未找到", "不存在", "为空", "无可用", "未初始化", "尚未训练"]

        for p in error_patterns:
            if p in observation:
                return "tool_error"
        for p in empty_patterns:
            if p in observation:
                return "empty_result"
        return None

    @staticmethod
    def _build_partial_answer(steps: list[AgentStep]) -> str:
        """从已有步骤中提取部分回答。"""
        observations = [s.content for s in steps if s.type == "observation"]
        thoughts = [s.content for s in steps if s.type == "thought"]
        if observations:
            last_thought = thoughts[-1] if thoughts else ""
            return f"{last_thought}\n\n相关数据:\n" + "\n---\n".join(observations[-3:])
        return ""


def _parse_json_safe(text: str) -> dict:
    """安全解析 JSON，容错处理。"""
    text = text.strip()
    # 尝试直接解析
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        pass

    # 尝试提取第一个 {...} 块
    match = re.search(r"\{[^{}]*\}", text, re.DOTALL)
    if match:
        try:
            return json.loads(match.group())
        except json.JSONDecodeError:
            pass

    # 尝试提取嵌套 {...} 块
    match = re.search(r"\{.*\}", text, re.DOTALL)
    if match:
        try:
            return json.loads(match.group())
        except json.JSONDecodeError:
            pass

    logger.warning("无法解析 Action Input JSON: %s", text[:200])
    return {}
