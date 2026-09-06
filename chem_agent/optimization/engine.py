"""多目标优化引擎 --- 网格搜索 + 帕累托排序 + 加权评分。"""

import random
import logging
from typing import Optional, Callable

import numpy as np

from chem_agent.optimization.models import (
    OptimizationMethod,
    OptimizationObjective,
    OptimizationConstraint,
    OptimizationRequest,
    OptimizationResult,
    ParetoSolution,
    FactorRange,
    ObjectiveDirection,
)

logger = logging.getLogger(__name__)


class OptimizationEngine:
    """配方多目标优化引擎。

    工作原理:
    1. 在因子范围空间内采样（网格或随机）
    2. 对每个采样点用预测模型估算性能
    3. 应用约束条件过滤
    4. 计算帕累托前沿和加权评分
    5. 返回最优解集合
    """

    def __init__(self, predictor=None, cost_calculator=None, risk_analyzer=None):
        """注入依赖服务（可选）。"""
        self._predictor = predictor
        self._cost_calculator = cost_calculator
        self._risk_analyzer = risk_analyzer

    def optimize(self, req: OptimizationRequest) -> OptimizationResult:
        """执行多目标优化。"""
        # 1. 采样
        samples = self._sample_space(req.factor_ranges, req.population_size, req.random_seed)

        # 2. 评估每个采样点
        evaluated = []
        for factors in samples:
            # 检查基础约束（总重量等）
            if not self._check_constraints(factors, req):
                continue

            # 计算各目标值
            obj_values = self._evaluate_objectives(factors, req.objectives)
            if obj_values is None:
                continue

            # 检查目标硬性约束
            if not self._check_objective_constraints(obj_values, req.objectives):
                continue

            evaluated.append((factors, obj_values))

        if not evaluated:
            return OptimizationResult(
                method=req.method,
                total_evaluated=0,
                summary="无可行解：所有采样点均不满足约束条件",
            )

        # 3. 帕累托排序
        pareto_ranks = self._pareto_sort(evaluated, req.objectives)

        # 4. 加权评分
        scored = []
        for rank, factors, obj_values in pareto_ranks:
            score = self._weighted_score(obj_values, req.objectives)
            scored.append((rank, factors, obj_values, score))

        # 5. 排序
        if req.method == OptimizationMethod.WEIGHTED_SCORE:
            scored.sort(key=lambda x: -x[3])  # 按评分降序
        else:
            scored.sort(key=lambda x: (x[0], -x[3]))  # 先帕累托层，再评分

        # 6. 构建结果
        is_pareto = [s[0] == 0 for s in scored]
        dominated = [s[0] for s in scored]

        solutions = []
        for i, (rank, factors, obj_values, score) in enumerate(scored[:req.top_n]):
            solutions.append(ParetoSolution(
                rank=i + 1,
                factors=factors,
                objectives=obj_values,
                score=round(score, 4),
                is_pareto_optimal=is_pareto[i],
                dominated_count=dominated[i],
            ))

        best = solutions[0] if solutions else None
        pareto_count = sum(1 for s in solutions if s.is_pareto_optimal)
        pareto_front_data = [
            {"objectives": s.objectives, "score": s.score, "factors": s.factors}
            for s in solutions if s.is_pareto_optimal
        ]

        return OptimizationResult(
            method=req.method,
            total_evaluated=len(evaluated),
            pareto_front_size=pareto_count,
            solutions=solutions,
            best_solution=best,
            pareto_front=pareto_front_data,
            summary=(
                f"评估 {len(evaluated)} 个候选配方，帕累托前沿 {pareto_count} 个解"
                + (f"，最优评分: {best.score:.4f}" if best else "")
            ),
        )

    # ========== 采样 ==========

    def _sample_space(self, ranges: list[FactorRange], n: int, seed: int) -> list[dict[str, float]]:
        """在因子空间中采样。

        策略: 如果总组合数 <= n，用全网格；否则用拉丁超立方采样。
        """
        # 计算每个因子的离散点数
        points_per_factor = []
        for fr in ranges:
            if fr.type == "categorical":
                points_per_factor.append(2)  # 简化
            else:
                step = fr.step or (fr.max_value - fr.min_value) / 10
                n_pts = max(2, int((fr.max_value - fr.min_value) / step) + 1)
                points_per_factor.append(n_pts)

        total_combinations = 1
        for p in points_per_factor:
            total_combinations *= p

        if total_combinations <= n:
            # 全网格
            return self._grid_sample(ranges, points_per_factor)

        # 拉丁超立方
        rng = random.Random(seed)
        samples = []
        for _ in range(n):
            factors = {}
            for fr in ranges:
                if fr.type == "categorical":
                    factors[fr.name] = rng.choice([fr.min_value, fr.max_value])
                else:
                    segment = rng.random()
                    val = fr.min_value + (fr.max_value - fr.min_value) * segment
                    if fr.step:
                        val = round(val / fr.step) * fr.step
                    factors[fr.name] = round(val, 3)
            samples.append(factors)
        return samples

    def _grid_sample(self, ranges: list[FactorRange], points: list[int]) -> list[dict[str, float]]:
        """全网格采样。"""
        grids = []
        for fr, n_pts in zip(ranges, points):
            if fr.type == "categorical":
                grids.append([fr.min_value, fr.max_value])
            else:
                grids.append(np.linspace(fr.min_value, fr.max_value, n_pts).tolist())

        samples = []
        indices = [0] * len(ranges)

        def recurse(dim):
            if dim == len(ranges):
                factors = {}
                for i, fr in enumerate(ranges):
                    factors[fr.name] = round(grids[i][indices[i]], 3)
                samples.append(factors)
                return
            for j in range(len(grids[dim])):
                indices[dim] = j
                recurse(dim + 1)

        recurse(0)
        return samples

    # ========== 约束检查 ==========

    def _check_constraints(self, factors: dict[str, float], req: OptimizationRequest) -> bool:
        """检查基础约束。"""
        # 总重量
        total = sum(v for k, v in factors.items() if k in {fr.name for fr in req.factor_ranges})
        if abs(total - req.total_weight_constraint) > 5:
            return False

        # 自定义约束
        for c in req.constraints:
            val = factors.get(c.name)
            if val is None:
                continue
            if c.min_value is not None and val < c.min_value:
                return False
            if c.max_value is not None and val > c.max_value:
                return False
        return True

    def _check_objective_constraints(
        self, obj_values: dict[str, float], objectives: list[OptimizationObjective]
    ) -> bool:
        """检查目标硬性约束。"""
        for obj in objectives:
            val = obj_values.get(obj.name)
            if val is None:
                continue
            if obj.hard_min is not None and val < obj.hard_min:
                return False
            if obj.hard_max is not None and val > obj.hard_max:
                return False
        return True

    # ========== 评估 ==========

    def _evaluate_objectives(
        self, factors: dict[str, float], objectives: list[OptimizationObjective]
    ) -> Optional[dict[str, float]]:
        """评估一个采样点的各目标值。

        实际应用中，这里调用 ML 预测模型。当前版本使用模拟评估函数。
        """
        values = {}
        for obj in objectives:
            val = self._simulate_prediction(obj.name, factors)
            if val is None:
                return None
            values[obj.name] = val
        return values

    def _simulate_prediction(self, name: str, factors: dict[str, float]) -> float:
        """模拟预测函数（实际使用时替换为 ML 模型）。

        生成一个在合理范围内的伪预测值，用于演示和测试。
        """
        # 基于因子值生成确定性但看似合理的预测
        seed = hash(name) % 10000
        val = seed * 0.01
        for k, v in factors.items():
            val += hash(k) % 100 * v * 0.001
        # 归一化到合理范围
        val = 10 + abs(val) % 90
        return round(val, 2)

    # ========== 帕累托排序 ==========

    def _pareto_sort(
        self,
        evaluated: list[tuple[dict[str, float], dict[str, float]]],
        objectives: list[OptimizationObjective],
    ) -> list[tuple[int, dict[str, float], dict[str, float]]]:
        """非支配排序（NSGA-II 简化版）。

        对每个解，计算有多少个其他解在所有目标上都不差于它。
        支配数越少 = 帕累托层级越低 = 越优。
        """
        n = len(evaluated)
        dominated_by = [0] * n
        dominates = [[] for _ in range(n)]

        for i in range(n):
            for j in range(n):
                if i == j:
                    continue
                if self._dominates(evaluated[j][1], evaluated[i][1], objectives):
                    dominated_by[i] += 1
                    dominates[j].append(i)

        # 分层
        ranks = [-1] * n
        front = [i for i in range(n) if dominated_by[i] == 0]
        current_rank = 0

        while front:
            for i in front:
                ranks[i] = current_rank
            next_front = []
            for i in front:
                for j in dominates[i]:
                    dominated_by[j] -= 1
                    if dominated_by[j] == 0:
                        next_front.append(j)
            front = next_front
            current_rank += 1

        return [(ranks[i], evaluated[i][0], evaluated[i][1]) for i in range(n)]

    def _dominates(
        self,
        a: dict[str, float],
        b: dict[str, float],
        objectives: list[OptimizationObjective],
    ) -> bool:
        """判断解 a 是否支配解 b。"""
        at_least_one_better = False
        for obj in objectives:
            va = a.get(obj.name, 0)
            vb = b.get(obj.name, 0)
            if obj.direction == ObjectiveDirection.MAXIMIZE:
                if va < vb:
                    return False
                if va > vb:
                    at_least_one_better = True
            else:
                if va > vb:
                    return False
                if va < vb:
                    at_least_one_better = True
        return at_least_one_better

    # ========== 加权评分 ==========

    def _weighted_score(
        self,
        obj_values: dict[str, float],
        objectives: list[OptimizationObjective],
    ) -> float:
        """计算加权综合评分。

        先对每个目标做 min-max 归一化，再按权重加权求和。
        """
        if not objectives:
            return 0.0

        # 归一化（基于给定的 target_value 或简单估算）
        scores = []
        for obj in objectives:
            val = obj_values.get(obj.name, 0)
            if obj.target_value is not None:
                # 以目标值为基准归一化
                if obj.direction == ObjectiveDirection.MAXIMIZE:
                    s = min(1.0, max(0.0, val / obj.target_value))
                else:
                    s = min(1.0, max(0.0, obj.target_value / max(val, 0.001)))
            else:
                # 无目标值时，用简单缩放
                s = min(1.0, val / 100.0) if obj.direction == ObjectiveDirection.MAXIMIZE else max(0.0, 1.0 - val / 100.0)
            scores.append(s * obj.weight)

        total_weight = sum(obj.weight for obj in objectives)
        return sum(scores) / max(total_weight, 0.001) if total_weight > 0 else 0.0

