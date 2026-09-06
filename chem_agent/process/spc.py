"""SPC统计过程控制引擎。"""
import math, logging
import numpy as np
from chem_agent.process.models import SPCRequest, SPCResult, SPCChartData, ProcessCapability

logger = logging.getLogger(__name__)
_A2 = {2:1.880,3:1.023,4:0.729,5:0.577,6:0.483,7:0.419,8:0.373,9:0.337,10:0.308}
_D3 = {2:0,3:0,4:0,5:0,6:0,7:0.076,8:0.136,9:0.184,10:0.223}
_D4 = {2:3.267,3:2.574,4:2.282,5:2.114,6:2.004,7:1.924,8:1.864,9:1.816,10:1.777}

class SPCEngine:
    def analyze(self, req: SPCRequest) -> SPCResult:
        data = np.array(req.measurements)
        gm = float(np.mean(data)); gs = float(np.std(data, ddof=1))
        ns = req.subgroup_size; ng = len(data) // ns

        if ng < 2:
            mr = np.abs(np.diff(data)); rb = float(np.mean(mr))
            a2 = 2.66; ucl_x = gm + a2*rb; lcl_x = gm - a2*rb
            ucl_r = 3.267*rb; lcl_r = 0; rv = list(mr); rm = rb
        else:
            sgs = data[:ng*ns].reshape(ng, ns)
            xb = np.mean(sgs, axis=1); rgs = np.max(sgs, axis=1)-np.min(sgs, axis=1)
            rb = float(np.mean(rgs)); rv = list(rgs); rm = rb
            a2 = _A2.get(ns, 0.577); d3 = _D3.get(ns, 0); d4 = _D4.get(ns, 2.114)
            ucl_x = gm + a2*rb; lcl_x = gm - a2*rb
            ucl_r = d4*rb; lcl_r = d3*rb

        viols = sorted(set([i for i, v in enumerate(data) if v > ucl_x or v < lcl_x]))
        alerts = []

        # Western Electric rules
        rd = list(data)
        for i in range(len(rd)-7):
            if sum(1 for v in rd[i:i+8] if v > gm) >= 8:
                alerts.append(f"点{i+1}-{i+8}: 连续8点同侧"); break
        for i in range(len(rd)-5):
            if all(rd[i+j] < rd[i+j+1] for j in range(5)):
                alerts.append(f"点{i+1}-{i+6}: 连续6点递增"); break

        cap = self._cap(data, req.usl, req.lsl)

        xc = SPCChartData(labels=list(range(1, len(data)+1)), values=[round(v,3) for v in data], mean=round(gm,3), ucl=round(ucl_x,3), lcl=round(lcl_x,3), usl=req.usl, lsl=req.lsl, violations=viols)

        rc = None
        if ng >= 2:
            rc = SPCChartData(labels=list(range(1, len(rv)+1)), values=[round(v,3) for v in rv], mean=round(rm,3), ucl=round(ucl_r,3), lcl=round(lcl_r,3))

        return SPCResult(process_name=req.process_name, capability=cap, xbar_chart=xc, r_chart=rc, summary=f"均值{gm:.2f} | Cp={cap.cp:.2f} Cpk={cap.cpk:.2f} | {cap.grade}级", alerts=alerts)

    def _cap(self, data, usl, lsl):
        if usl is None or lsl is None: return ProcessCapability()
        m = float(np.mean(data)); s = float(np.std(data, ddof=1))
        tol = usl - lsl
        cp = tol/(6*s) if s>0 else 0
        cpk = min((usl-m)/(3*s), (m-lsl)/(3*s)) if s>0 else 0
        sl = min(6.0, cpk*3)
        g = "A+" if cpk>=1.67 else "A" if cpk>=1.33 else "B" if cpk>=1.0 else "C" if cpk>=0.67 else "D"
        zu = (usl-m)/max(s,1e-10); zl = (m-lsl)/max(s,1e-10)
        ncdf = lambda z: 0.5*math.erfc(-z/math.sqrt(2))
        dr = (1-ncdf(zu)+ncdf(-zl))*100
        return ProcessCapability(cp=round(cp,3), cpk=round(cpk,3), pp=round(cp,3), ppk=round(cpk,3), sigma_level=round(sl,2), grade=g, out_of_spec_percent=round(dr,3))
