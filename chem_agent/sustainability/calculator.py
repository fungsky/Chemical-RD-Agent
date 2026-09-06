"""可持续性计算引擎。"""
import logging
from chem_agent.sustainability.models import SustainabilityRequest, SustainabilityResult, SustainabilityMetric

logger = logging.getLogger(__name__)
CO2_KWH = 0.58  # China grid

class SustainabilityCalculator:
    def calculate(self, req: SustainabilityRequest) -> SustainabilityResult:
        mets = []; recs = []; tk = req.batch_size_kg

        # VOC
        tv = sum(c.get("weight_percent",0)/100*tk*c.get("voc_content_percent",0)/100 for c in req.components)
        vp = tv/tk*100 if tk>0 else 0
        vs, sc = ("ok",90) if vp<5 else ("ok",70) if vp<20 else ("warning",40) if vp<40 else ("exceed",15)
        mets.append(SustainabilityMetric(name="VOC含量",value=round(vp,1),unit="%",threshold="<50g/L",status=vs,score=sc))
        if vs=="exceed": recs.append("建议用高固含/水性体系")

        # Carbon
        mc = sum(c.get("weight_percent",0)/100*tk*c.get("carbon_footprint_kgCO2_per_kg",2.0) for c in req.components)
        ec = req.energy_kwh_per_kg*tk*CO2_KWH
        cpk = (mc+ec)/max(tk,0.001)
        cs, cc = ("ok",90) if cpk<2 else ("ok",65) if cpk<5 else ("warning",35) if cpk<10 else ("exceed",10)
        mets.append(SustainabilityMetric(name="碳足迹",value=round(cpk,2),unit="kgCO2/kg",threshold="<5",status=cs,score=cc))

        # Bio-based
        bc = sum(c.get("weight_percent",0)*c.get("bio_based_percent",0)/100 for c in req.components)/max(sum(c.get("weight_percent",0) for c in req.components),0.001)
        bs, bsc = ("ok",90) if bc>50 else ("ok",60) if bc>20 else ("warning",30)
        mets.append(SustainabilityMetric(name="生物基含量",value=round(bc,1),unit="%",threshold=">50%",status=bs,score=bsc))

        # Water
        ws, wsc = ("ok",85) if req.water_l_per_kg<2 else ("ok",60) if req.water_l_per_kg<5 else ("warning",30)
        mets.append(SustainabilityMetric(name="水耗",value=round(req.water_l_per_kg,1),unit="L/kg",threshold="<5",status=ws,score=wsc))

        # Waste
        was, wac = ("ok",90) if req.waste_percent<1 else ("ok",60) if req.waste_percent<3 else ("warning",30)
        mets.append(SustainabilityMetric(name="废料率",value=round(req.waste_percent,1),unit="%",threshold="<2%",status=was,score=wac))

        ov = sum(m.score for m in mets)/max(len(mets),1)
        g = "A+" if ov>=90 else "A" if ov>=75 else "B" if ov>=60 else "C" if ov>=40 else "D"
        return SustainabilityResult(formula_name=req.formula_name, overall_score=round(ov,1), grade=g, metrics=mets, recommendations=recs, summary=f"评分{ov:.0f}/100({g}级) | VOC{vp:.1f}% | 碳{cpk:.2f}kgCO2/kg")
