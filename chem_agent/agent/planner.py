"""任务复杂度分析与预规划。"""

import logging
import re
from typing import Optional

from langchain_core.messages import HumanMessage
from langchain_core.output_parsers import StrOutputParser
from langchain_core.language_models import BaseChatModel

from chem_agent.agent.models import ToolDef
from chem_agent.agent.prompts import build_planning_prompt

logger = logging.getLogger(__name__)


class TaskPlanner:
    """轻量级任务规划器：判断问题复杂度并生成执行计划。"""

    def __init__(self, llm: BaseChatModel):
        self._llm = llm

    async def analyze_and_plan(
        self,
        query: str,
        tools: dict[str, ToolDef],
    ) -> Optional[list[str]]:
        """分析任务复杂度，返回计划步骤列表或 None（简单任务）。

        Parameters
        ----------
        query : str
            用户问题。
        tools : dict[str, ToolDef]
            当前可用工具定义。

        Returns
        -------
        list[str] or None
            复杂任务返回 1-5 步计划，简单任务返回 None。
        """
        prompt = build_planning_prompt(query, tools)

        try:
            chain = self._llm | StrOutputParser()
            raw_output = await chain.ainvoke([HumanMessage(content=prompt)])
        except Exception as e:
            logger.warning("任务规划 LLM 调用失败，跳过规划: %s", e)
            return None

        # 清理 LLM 可能输出的 <think>...</think> 标签
        clean_output = re.sub(
            r"<think>.*?</think>", "", raw_output, flags=re.DOTALL
        ).strip()

        # 判断是否为简单任务
        if "SIMPLE" in clean_output.upper():
            logger.debug("规划判断: 简单任务，跳过规划")
            return None

        # 提取计划步骤
        plan_match = re.search(r"PLAN:\s*\n(.+)", clean_output, re.DOTALL)
        if plan_match:
            plan_text = plan_match.group(1)
            steps = re.findall(r"^\s*\d+\.\s*(.+)$", plan_text, re.MULTILINE)
            if steps:
                result = [s.strip() for s in steps[:5]]
                logger.info("规划完成: %d 步 - %s", len(result), result)
                return result

        # 无法解析 → 当作简单任务
        logger.debug("规划输出无法解析，当作简单任务处理")
        return None
