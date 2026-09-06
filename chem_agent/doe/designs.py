"""实验设计生成引擎——全因子/2k因子/Plackett-Burman/拉丁超立方。"""

import math
import random
from typing import Optional

from chem_agent.doe.models import Factor, DesignRequest, DesignRun, DesignResult, DesignMethod


def generate_design(request: DesignRequest) -> DesignResult:
    method = request.method

    if method == DesignMethod.FULL_FACTORIAL:
        return _full_factorial(request)
    elif method == DesignMethod.TWO_LEVEL_FACTORIAL:
        return _two_level_factorial(request)
    elif method == DesignMethod.PLACKETT_BURMAN:
        return _plackett_burman(request)
    elif method == DesignMethod.LATIN_HYPERCUBE:
        return _latin_hypercube(request)
    elif method == DesignMethod.CENTRAL_COMPOSITE:
        return _central_composite(request)
    else:
        raise ValueError(f"未知设计方法: {method}")


def _encode_levels(factors: list[Factor], levels: list[int]) -> dict[str, float]:
    result = {}
    for factor, level in zip(factors, levels):
        if level == -1:
            result[factor.name] = factor.low
        elif level == 1:
            result[factor.name] = factor.high
        elif level == 0:
            result[factor.name] = factor.center if factor.center is not None else (factor.low + factor.high) / 2
        else:
            result[factor.name] = factor.low + (factor.high - factor.low) * (level + 1) / 2
    return result


def _full_factorial(req: DesignRequest) -> DesignResult:
    n_factors = len(req.factors)
    if n_factors > 8:
        raise ValueError(f"全因子设计最多8个因子 ({n_factors} 超过了限制，建议使用 2k 或 Plackett-Burman)")
    n_levels = 2
    runs = []
    for i in range(n_levels ** n_factors):
        levels = []
        for j in range(n_factors):
            level = ((i // (n_levels ** j)) % n_levels) * 2 - 1
            levels.append(level)
        runs.append(_encode_levels(req.factors, levels))

    return _build_result(req, runs, f"{n_levels}^{n_factors} = {n_levels ** n_factors} 次实验")


def _two_level_factorial(req: DesignRequest) -> DesignResult:
    n_factors = len(req.factors)
    n_runs = 2 ** n_factors
    runs = []
    for i in range(n_runs):
        levels = [((i >> j) & 1) * 2 - 1 for j in range(n_factors)]
        runs.append(_encode_levels(req.factors, levels))
    return _build_result(req, runs, f"2^{n_factors} = {n_runs} 次实验（含{req.replicates}次重复）")


def _plackett_burman(req: DesignRequest) -> DesignResult:
    n_factors = len(req.factors)
    n_runs = 12
    while n_runs < n_factors + 1:
        n_runs += 4
    if n_runs > 48:
        n_runs = 48

    known = {
        8: [1,1,1,-1,-1,-1,1,-1],
        12: [1,1,-1,1,1,1,-1,-1,-1,1,-1,-1],
        16: [1,1,1,1,-1,1,-1,1,1,-1,-1,1,-1,-1,-1,-1],
        20: [1,1,-1,-1,1,1,1,1,-1,1,-1,1,-1,-1,-1,-1,1,1,-1,-1],
    }
    base = known.get(n_runs)
    if base is None:
        base = [1 if (i * (i-1)) % n_runs < n_runs // 2 else -1 for i in range(n_runs - 1)]

    runs = []
    for shift in range(n_runs):
        row = base[shift:] + base[:shift]
        levels = row[:n_factors]
        runs.append(_encode_levels(req.factors, levels))

    return _build_result(req, runs, f"Plackett-Burman {n_runs} 次实验（筛选{req.replicates}次重复）")


def _latin_hypercube(req: DesignRequest) -> DesignResult:
    n_factors = len(req.factors)
    n_runs = 2 ** n_factors
    if n_runs < 10:
        n_runs = 10
    if n_runs > 100:
        n_runs = 50

    rng = random.Random(42)
    runs = []
    for i in range(n_runs * req.replicates):
        levels = {}
        for f in req.factors:
            segment = rng.random()
            offset = (i % n_runs) / n_runs
            val = f.low + (f.high - f.low) * ((segment + offset) % 1.0)
            levels[f.name] = round(val, 3)
        runs.append(levels)

    return _build_result(req, runs, f"拉丁超立方 {n_runs} 次采样（{req.replicates}次重复）")


def _central_composite(req: DesignRequest) -> DesignResult:
    n_factors = len(req.factors)
    alpha = (2 ** n_factors) ** 0.25

    runs = []
    # 立方点 (2^n)
    for i in range(2 ** n_factors):
        levels = [((i >> j) & 1) * 2 - 1 for j in range(n_factors)]
        runs.append(_encode_levels(req.factors, levels))

    # 轴向点 (2n)
    for axis in range(n_factors):
        for sign in [-1, 1]:
            levels = [0] * n_factors
            levels[axis] = sign * alpha
            encoded = {}
            for factor, level in zip(req.factors, levels):
                encoded[factor.name] = factor.center if factor.center and level == 0 else (
                    factor.low if level < 0 else factor.high
                )
            runs.append(encoded)

    # 中心点
    for _ in range(req.center_points):
        runs.append({f.name: f.center or (f.low + f.high) / 2 for f in req.factors})

    return _build_result(req, runs, f"CCD 中心复合设计 {2**n_factors + 2*n_factors + req.center_points} 次实验")


def _build_result(req: DesignRequest, runs_list: list[dict], summary: str) -> DesignResult:
    all_runs = []
    for rep in range(req.replicates):
        indices = list(range(len(runs_list)))
        if req.randomize:
            random.shuffle(indices)
        for run_idx, orig_idx in enumerate(indices):
            all_runs.append(DesignRun(
                run_order=run_idx + 1 + rep * len(runs_list),
                standard_order=orig_idx + 1,
                block=rep + 1,
                factor_levels=runs_list[orig_idx],
            ))

    return DesignResult(
        method=req.method,
        factors=req.factors,
        total_runs=len(all_runs),
        runs=all_runs,
        summary=f"{summary}，共 {len(all_runs)} 次运行",
    )
