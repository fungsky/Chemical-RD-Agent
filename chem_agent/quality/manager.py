"""质量管理器。"""
import json, logging
from datetime import datetime
from pathlib import Path
from typing import Optional
from chem_agent.quality.models import (QualitySpec, COATemplate, COAResult, InspectionResult, SpecDirection)

logger = logging.getLogger(__name__)

class QualityManager:
    def __init__(self, data_dir: Optional[str] = None):
        self._dir = Path(data_dir or "data"); self._dir.mkdir(parents=True, exist_ok=True)
        self._tf = self._dir / "coa_templates.json"; self._cf = self._dir / "coa_results.json"
        self._templates: dict[str, COATemplate] = {}; self._coas: dict[str, COAResult] = {}
        self._load()

    def _load(self):
        for fp, attr, cls in [(self._tf, "_templates", COATemplate), (self._cf, "_coas", COAResult)]:
            if fp.exists():
                try:
                    with open(fp, "r", encoding="utf-8") as f: raw = json.load(f)
                    getattr(self, attr).clear()
                    for k, v in raw.items(): getattr(self, attr)[k] = cls(**v)
                except Exception as e: logger.warning("load fail: %s", e)

    def _st(self):
        r = {k: v.model_dump(mode="json") for k, v in self._templates.items()}
        with open(self._tf, "w", encoding="utf-8") as f: json.dump(r, f, ensure_ascii=False, indent=2, default=str)

    def _sc(self):
        r = {k: v.model_dump(mode="json") for k, v in self._coas.items()}
        with open(self._cf, "w", encoding="utf-8") as f: json.dump(r, f, ensure_ascii=False, indent=2, default=str)

    def add_template(self, tpl: COATemplate) -> COATemplate:
        self._templates[tpl.name] = tpl; self._st(); return tpl

    def get_template(self, name: str) -> Optional[COATemplate]:
        return self._templates.get(name)

    def check_against_template(self, tname: str, measurements: dict[str, float]) -> list[InspectionResult]:
        tpl = self._templates.get(tname)
        if not tpl: raise KeyError(f"template {tname} not found")
        r = []
        for s in tpl.specs:
            mv = measurements.get(s.name)
            if mv is None: r.append(InspectionResult(spec_name=s.name, measured_value=0, notes="未检测", is_pass=False)); continue
            ok, dev = True, None
            if s.direction == SpecDirection.MIN:
                ok = mv >= (s.min_value or 0); dev = mv - (s.min_value or 0)
            elif s.direction == SpecDirection.MAX:
                ok = mv <= (s.max_value or float("inf")); dev = mv - (s.max_value or 0)
            elif s.direction == SpecDirection.RANGE:
                ok = (s.min_value or -float("inf")) <= mv <= (s.max_value or float("inf"))
                dev = mv - ((s.min_value or 0)+(s.max_value or 0))/2
            elif s.direction == SpecDirection.TARGET:
                ok = abs(mv-(s.target_value or 0))/max(abs(s.target_value or 1), 0.001) < 0.1
                dev = mv - (s.target_value or 0)
            r.append(InspectionResult(spec_name=s.name, measured_value=mv, unit=s.unit, is_pass=ok, deviation=round(dev,3) if dev is not None else None, notes="" if ok else "不合格"))
        return r

    def create_coa(self, tname: str, rid: str, batch: str, measurements: dict[str, float], inspector: Optional[str] = None) -> COAResult:
        tpl = self._templates.get(tname)
        if not tpl: raise KeyError(f"template {tname} not found")
        results = self.check_against_template(tname, measurements)
        ok = all(r.is_pass for r in results) and len(results) > 0
        coa = COAResult(report_id=rid, template_name=tname, product_name=tpl.product_name, batch_number=batch, inspector=inspector, results=results, overall_pass=ok, remarks="全部合格" if ok else "存在不合格项")
        self._coas[rid] = coa; self._sc(); return coa

    def get_coa(self, rid: str) -> Optional[COAResult]: return self._coas.get(rid)
    def list_coas(self): return list(self._coas.values())
    def list_templates(self): return list(self._templates.values())
