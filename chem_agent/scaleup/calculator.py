"""工艺放大计算引擎。"""
import math, logging
from chem_agent.scaleup.models import ScaleUpRequest, ScaleUpResult, ScaleUpMethod

logger = logging.getLogger(__name__)

class ScaleUpCalculator:
    def calculate(self, req: ScaleUpRequest) -> ScaleUpResult:
        sr = req.target_volume_l / req.lab_volume_l
        d_t = req.impeller_diameter_m * (sr ** (1/3))
        v_lab = req.impeller_diameter_m * math.pi * req.lab_speed_rpm / 60
        recs = []
        warns = []

        for m in req.methods:
            if m == ScaleUpMethod.CONSTANT_TIP_SPEED:
                n = req.lab_speed_rpm / (sr ** (1/3))
                recs.append({"method":"恒叶端线速度","target_speed_rpm":round(n,1),"tip_speed_ms":round(v_lab,2),"impeller_diameter_m":round(d_t,3),"applicable":"剪切敏感体系"})
                if sr > 100 and n < 50:
                    warns.append(f"目标转速仅 {n:.0f} rpm，混合可能不充分")
            elif m == ScaleUpMethod.CONSTANT_POWER_PER_VOLUME:
                n = req.lab_speed_rpm / (sr ** (2/9))
                pv = req.fluid_density * (req.lab_speed_rpm/60)**3 * req.impeller_diameter_m**5 * 5 / (req.lab_volume_l/1000)
                recs.append({"method":"恒单位体积功率","target_speed_rpm":round(n,1),"power_per_volume_w_m3":round(pv,1),"applicable":"传质控制体系"})
            elif m == ScaleUpMethod.CONSTANT_REYNOLDS:
                n = req.lab_speed_rpm * (req.impeller_diameter_m / d_t) ** 2
                re_v = req.fluid_density * req.lab_speed_rpm/60 * req.impeller_diameter_m**2 / req.fluid_viscosity
                recs.append({"method":"恒雷诺数","target_speed_rpm":round(n,1),"reynolds":round(re_v,0),"applicable":"流型敏感体系"})
            elif m == ScaleUpMethod.CONSTANT_MIXING_TIME:
                recs.append({"method":"恒混合时间","target_speed_rpm":round(req.lab_speed_rpm,1),"applicable":"快速反应体系"})
            elif m == ScaleUpMethod.GEOMETRIC_SIMILARITY:
                n = req.lab_speed_rpm / (sr ** (1/3))
                recs.append({"method":"几何相似","target_speed_rpm":round(n,1),"reactor_diameter_m":round(d_t*2.5,3),"applicable":"通用放大"})

        # Heat transfer check
        ha_lab = self._ha(req.lab_volume_l)
        ha_tar = self._ha(req.target_volume_l)
        if ha_tar / ha_lab / (sr ** (2/3)) < 0.7:
            warns.append(f"传热能力不足，建议增加换热面积")

        return ScaleUpResult(
            formula_name=req.formula_name, lab_volume_l=req.lab_volume_l,
            target_volume_l=req.target_volume_l, scale_ratio=round(sr,1),
            recommendations=recs, warnings=warns,
            summary=f"{req.lab_volume_l}L->{req.target_volume_l}L({sr:.0f}x) {len(recs)}条建议{len(warns)}条警告",
        )

    def _ha(self, vl): return 4.84 * (vl/1000) ** (2/3)
