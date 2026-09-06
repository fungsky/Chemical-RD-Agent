"""DOE实验设计模块测试。"""
import pytest
from chem_agent.doe.models import (
    DesignMethod, Factor, DesignRequest, DesignRun, DesignResult,
)
from chem_agent.doe.designs import generate_design


class TestDOEModels:
    def test_factor_creation(self):
        f = Factor(name="温度", unit="°C", low=100, high=200, center=150)
        assert f.name == "温度"
        assert f.low == 100
        assert f.high == 200

    def test_factor_defaults(self):
        f = Factor(name="pH", low=5, high=9)
        assert f.unit == ""
        assert f.category == "continuous"
        assert f.center is None

    def test_design_request_defaults(self):
        req = DesignRequest(
            factors=[Factor(name="A", low=0, high=1)],
        )
        assert req.method == DesignMethod.FULL_FACTORIAL
        assert req.replicates == 1
        assert req.center_points == 0
        assert req.randomize is True

    def test_design_request_validation(self):
        with pytest.raises(Exception):
            DesignRequest(factors=[])  # min_length=1


class TestDOEGeneration:
    def test_full_factorial(self):
        req = DesignRequest(
            method=DesignMethod.FULL_FACTORIAL,
            factors=[
                Factor(name="A", low=10, high=20),
                Factor(name="B", low=30, high=40),
            ],
            randomize=False,
        )
        result = generate_design(req)
        assert result.total_runs == 4  # 2^2
        assert result.method == DesignMethod.FULL_FACTORIAL
        assert len(result.runs) == 4

    def test_full_factorial_limit(self):
        """ >8 factors should raise ValueError """
        factors = [Factor(name=f"F{i}", low=0, high=1) for i in range(9)]
        req = DesignRequest(
            method=DesignMethod.FULL_FACTORIAL,
            factors=factors,
        )
        with pytest.raises(ValueError, match="8"):
            generate_design(req)

    def test_two_level_factorial(self):
        req = DesignRequest(
            method=DesignMethod.TWO_LEVEL_FACTORIAL,
            factors=[Factor(name=f"F{i}", low=0, high=1) for i in range(3)],
        )
        result = generate_design(req)
        assert result.total_runs == 8  # 2^3

    def test_plackett_burman(self):
        req = DesignRequest(
            method=DesignMethod.PLACKETT_BURMAN,
            factors=[Factor(name=f"F{i}", low=0, high=1) for i in range(7)],
        )
        result = generate_design(req)
        assert result.total_runs >= 8  # min 12, adjusted to fit factors

    def test_latin_hypercube(self):
        req = DesignRequest(
            method=DesignMethod.LATIN_HYPERCUBE,
            factors=[Factor(name=f"F{i}", low=0, high=10) for i in range(3)],
        )
        result = generate_design(req)
        assert result.total_runs == 10  # min 10 when 2^3=8 < 10

    def test_central_composite(self):
        req = DesignRequest(
            method=DesignMethod.CENTRAL_COMPOSITE,
            factors=[Factor(name=f"F{i}", low=10, high=20) for i in range(2)],
            center_points=3,
        )
        result = generate_design(req)
        # 2^2 + 2*2 + 3 = 11
        assert result.total_runs == 11

    def test_design_run_structure(self):
        req = DesignRequest(
            method=DesignMethod.FULL_FACTORIAL,
            factors=[Factor(name="temp", low=100, high=200)],
            randomize=False,
        )
        result = generate_design(req)
        run = result.runs[0]
        assert isinstance(run, DesignRun)
        assert "temp" in run.factor_levels

    def test_replicates(self):
        req = DesignRequest(
            method=DesignMethod.FULL_FACTORIAL,
            factors=[Factor(name="A", low=0, high=1)],
            replicates=3,
        )
        result = generate_design(req)
        assert result.total_runs == 6  # 2 * 3


print("test_doe done")
