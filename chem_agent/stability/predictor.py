"""稳定性预测引擎 --- Arrhenius/Q10/线性外推。"""
import math, logging
import numpy as np
from chem_agent.stability.models import StabilityRequest, StabilityResult, AgingTestPoint

logger = logging.getLogger(__name__)

class StabilityPredictor:
    def predict(self, req: StabilityRequest) -> StabilityResult:
        if req.model.value == "arrhenius": return self._arrhenius(req)
        elif req.model.value == "q10": return self._q10(req)
        else: return self._linear(req)

    def _arrhenius(self, req: StabilityRequest) -> StabilityResult:
        # Group by temp
        tr = {}
        for pt in req.aging_data:
            tr.setdefault(pt.temperature_c, []).append((pt.time_hours, pt.property_value))
        rates, temps_k = [], []
        for tc, pts in tr.items():
            if len(pts) < 2: continue
            times = np.array([p[0] for p in pts])
            vals = np.array([p[1] for p in pts])
            k, _ = np.linalg.lstsq(np.vstack([-times, np.ones(len(times))]).T, np.log(np.maximum(vals, 0.001)), rcond=None)[0]
            if k > 0: rates.append(k); temps_k.append(tc + 273.15)
        if len(rates) < 2:
            return StabilityResult(formula_name=req.formula_name, model=req.model, storage_temperature_c=req.storage_temperature_c, summary="数据不足", warnings=["需2个以上温度"])
        inv_t = np.array([1.0/tk for tk in temps_k])
        ea_r, ln_a = np.linalg.lstsq(np.vstack([-inv_t, np.ones(len(inv_t))]).T, np.log(rates), rcond=None)[0]
        tk_s = req.storage_temperature_c + 273.15
        ks = np.exp(ln_a - ea_r / tk_s)
        p0 = np.exp(np.linalg.lstsq(np.vstack([-np.array([p[0] for p in list(tr.values())[0]]), np.ones(len(list(tr.values())[0]))]).T, np.log(np.maximum([p[1] for p in list(tr.values())[0]], 0.001)), rcond=None)[0][1])
        days = abs(np.log(req.failure_threshold / max(p0, 0.001)) / max(ks, 1e-10)) / 24
        conf = "高" if len(rates) >= 3 else "中"
        ttf = {}
        for t in [25, 30, 35, 40]:
            kt = np.exp(ln_a - ea_r / (t+273.15))
            ttf[t] = round(abs(np.log(req.failure_threshold / max(p0, 0.001)) / max(kt, 1e-10)) / 24, 0)
        ea = ea_r * 8.314 / 1000
        return StabilityResult(formula_name=req.formula_name, model=req.model, storage_temperature_c=req.storage_temperature_c, predicted_shelf_life_days=round(days,1), predicted_shelf_life_years=round(days/365,2), confidence=conf, degradation_rate_per_day=round(float(ks*24),6), time_to_failure_at_temp=ttf, summary=f"{conf}置信度 | Ea={ea:.1f} kJ/mol | {days/365:.1f}年")

    def _q10(self, req: StabilityRequest) -> StabilityResult:
        temps = sorted(set(pt.temperature_c for pt in req.aging_data))
        if len(temps) < 2: return StabilityResult(formula_name=req.formula_name, model=req.model, storage_temperature_c=req.storage_temperature_c, summary="数据不足")
        def get_rate(tc):
            pts = [pt for pt in req.aging_data if pt.temperature_c == tc]
            if len(pts) < 2: return None
            times = np.array([p.time_hours for p in pts])
            vals = np.array([p.property_value for p in pts])
            k, _ = np.linalg.lstsq(np.vstack([-times, np.ones(len(times))]).T, np.log(np.maximum(vals, 0.001)), rcond=None)[0]
            return max(k, 1e-10)
        k_hi = get_rate(max(temps)); k_lo = get_rate(min(temps))
        if k_hi is None or k_lo is None: return StabilityResult(formula_name=req.formula_name, model=req.model, storage_temperature_c=req.storage_temperature_c, summary="速率计算失败")
        q10 = (k_hi/k_lo) ** (10/(max(temps)-min(temps)))
        ks = k_hi / (q10 ** ((req.storage_temperature_c - max(temps))/10))
        pts0 = [pt for pt in req.aging_data if pt.temperature_c == max(temps)]
        p0 = pts0[0].property_value
        days = abs(np.log(req.failure_threshold/max(p0,0.001))/max(ks,1e-10))/24
        return StabilityResult(formula_name=req.formula_name, model=req.model, storage_temperature_c=req.storage_temperature_c, predicted_shelf_life_days=round(days,1), predicted_shelf_life_years=round(days/365,2), confidence="中", degradation_rate_per_day=round(float(ks*24),6), summary=f"Q10={q10:.1f} | {days/365:.1f}年")

    def _linear(self, req: StabilityRequest) -> StabilityResult:
        times = np.array([pt.time_hours for pt in req.aging_data])
        vals = np.array([pt.property_value for pt in req.aging_data])
        slope, intercept = np.linalg.lstsq(np.vstack([times, np.ones(len(times))]).T, vals, rcond=None)[0]
        days = abs((req.failure_threshold-intercept)/max(abs(slope),1e-10))/24 if slope < 0 else 0
        return StabilityResult(formula_name=req.formula_name, model=req.model, storage_temperature_c=req.storage_temperature_c, predicted_shelf_life_days=round(days,1), predicted_shelf_life_years=round(days/365,2), confidence="低", summary=f"线性外推 | {days/365:.1f}年")
