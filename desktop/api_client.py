"""ChemAgent Desktop API Client --- covers all 17 modules."""

import json, logging, os
from typing import Optional
import requests

logger = logging.getLogger(__name__)
API_BASE = "http://localhost:8000"
TIMEOUT = 60
_token = os.environ.get("CHEMAGENT_TOKEN", "")

def set_api_base(base: str):
    global API_BASE; API_BASE = base.rstrip("/")

def set_token(token: str):
    global _token; _token = token or ""

def _headers() -> dict:
    return {"Authorization": f"Bearer {_token}"} if _token else {}

def _get(url: str, params: dict = None) -> Optional[dict]:
    try:
        r = requests.get(f"{API_BASE}{url}", params=params, headers=_headers(), timeout=TIMEOUT)
        r.raise_for_status(); return r.json()
    except Exception as e:
        logger.warning("GET %s fail: %s", url, e); return None

def _post(url: str, data: dict) -> Optional[dict]:
    try:
        r = requests.post(f"{API_BASE}{url}", json=data, headers=_headers(), timeout=TIMEOUT)
        r.raise_for_status(); return r.json()
    except Exception as e:
        logger.warning("POST %s fail: %s", url, e); return None

def health() -> Optional[dict]: return _get("/health")

# === Formulas ===
def search_formulas(keyword="", category="", limit=20):
    raw = _get("/api/formulas", {"keyword": keyword, "category": category, "limit": limit}) or []
    rows = []
    for item in raw:
        f = item.get("formula", item) if isinstance(item, dict) else {}
        if not isinstance(f, dict):
            continue
        items = f.get("items") or []
        comps = ", ".join(
            i.get("material", {}).get("name", "")
            for i in items[:5] if isinstance(i, dict)
        )
        rows.append({
            "code": f.get("code", "-"),
            "name": f.get("name", f.get("formula_name", "-")),
            "category": f.get("category", "-"),
            "components": comps,
            "similarity": item.get("similarity_score", 0.0),
        })
    return rows
def get_formula(code): return _get(f"/api/formulas/{code}")
def get_formula_versions(code): return _get(f"/api/formula-versions/{code}")
def diff_versions(code, v1, v2): return _get(f"/api/formula-versions/{code}/diff", {"v1":v1,"v2":v2})

# === DOE ===
def doe_generate(req: dict): return _post("/api/doe/generate", req)
def doe_methods(): return _get("/api/doe/methods")

# === Risk ===
def risk_analyze(req: dict): return _post("/api/risk/analyze", req)

# === Cost ===
def cost_calculate(req: dict): return _post("/api/cost/calculate", req)

# === Compliance ===
def compliance_check(req: dict): return _post("/api/compliance/check", req)
def compliance_domains(): return _get("/api/compliance/domains")

# === Experiments ===
def exp_add(result: dict): return _post("/api/experiments/results", result)
def exp_batch(batch: dict): return _post("/api/experiments/results/batch", batch)
def exp_query(q: dict): return _post("/api/experiments/query", q)
def exp_stats(): return _get("/api/experiments/stats")
def exp_export_training(exclude_outliers=True): return _get("/api/experiments/export/training-data", {"exclude_outliers":exclude_outliers})
def exp_mark_outlier(eid: str, is_outlier=True, reason=""):
    return requests.patch(f"{API_BASE}/api/experiments/results/{eid}/outlier", json={"is_outlier":is_outlier,"reason":reason}, headers=_headers(), timeout=TIMEOUT).json()

# === Optimization ===
def opt_run(req: dict): return _post("/api/optimization/run", req)
def opt_methods(): return _get("/api/optimization/methods")

# === Materials ===
def mat_add(rec: dict): return _post("/api/materials", rec)
def mat_get(name): return _get(f"/api/materials/{name}/detail")
def mat_query(q: dict): return _get("/api/materials", {"keyword": q.get("name", ""), "limit": q.get("limit", 100)})
def mat_list(): return _get("/api/materials", {"keyword": "", "limit": 100}) or []
def mat_categories(): return _get("/api/materials/categories")

# === ScaleUp ===
def scaleup_calculate(req: dict): return _post("/api/scaleup/calculate", req)

# === Stability ===
def stability_predict(req: dict): return _post("/api/stability/predict", req)

# === Sustainability ===
def sustainability_assess(req: dict): return _post("/api/sustainability/assess", req)

# === Quality ===
def quality_add_template(tpl: dict): return _post("/api/quality/templates", tpl)
def quality_list_templates(): return _get("/api/quality/templates/list/all")
def quality_generate_coa(tname, rid, batch, meas, insp=""):
    return _post("/api/quality/coa/generate?" + "&".join([f"template_name={tname}",f"report_id={rid}",f"batch_number={batch}",f"inspector={insp}"]), meas)
def quality_list_coas(): return _get("/api/quality/coa/list/all")

# === Process SPC ===
def spc_analyze(req: dict): return _post("/api/process/spc/analyze", req)

# === Prediction ===
def predict(req: dict): return _post("/api/predict", req)

# === Chat ===
def chat(message: str, agent_mode=False): return _post("/api/chat", {"message": message, "use_agent": agent_mode})

# === KG Stats ===
def kg_stats(): return _get("/api/graph/stats")
