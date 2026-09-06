"""原材料管理器 --- JSON持久化。"""

import json, logging
from datetime import datetime
from pathlib import Path
from typing import Optional

from chem_agent.materials.models import (
    MaterialRecord, MaterialQuery, SupplierInfo, MaterialPrice,
    MaterialBatch, ShelfLifeStatus,
)

logger = logging.getLogger(__name__)


class MaterialManager:
    def __init__(self, data_dir: Optional[str] = None):
        self._dir = Path(data_dir or "data")
        self._dir.mkdir(parents=True, exist_ok=True)
        self._file = self._dir / "materials.json"
        self._records: dict[str, MaterialRecord] = {}
        self._load()

    def _load(self):
        if self._file.exists():
            try:
                with open(self._file, "r", encoding="utf-8") as f:
                    raw = json.load(f)
                for k, v in raw.items():
                    self._records[k] = MaterialRecord(**v)
            except Exception as e:
                logger.warning("load materials fail: %s", e)

    def _save(self):
        raw = {k: v.model_dump(mode="json") for k, v in self._records.items()}
        with open(self._file, "w", encoding="utf-8") as f:
            json.dump(raw, f, ensure_ascii=False, indent=2, default=str)

    def _key(self, name: str) -> str: return name.strip().lower()

    def add(self, rec: MaterialRecord) -> MaterialRecord:
        k = self._key(rec.name)
        if k in self._records: raise ValueError(f"{rec.name} exists")
        self._records[k] = rec; self._save(); return rec

    def get(self, name: str) -> Optional[MaterialRecord]:
        return self._records.get(self._key(name))

    def update(self, name: str, updates: dict) -> MaterialRecord:
        k = self._key(name)
        if k not in self._records: raise KeyError(f"{name} not found")
        cur = self._records[k].model_dump()
        cur.update(updates); cur["updated_at"] = datetime.now()
        self._records[k] = MaterialRecord(**cur); self._save()
        return self._records[k]

    def delete(self, name: str) -> bool:
        k = self._key(name)
        if k in self._records: del self._records[k]; self._save(); return True
        return False

    def add_supplier(self, name: str, sup: SupplierInfo) -> MaterialRecord:
        k = self._key(name)
        if k not in self._records: raise KeyError(f"{name} not found")
        self._records[k].suppliers.append(sup)
        self._records[k].updated_at = datetime.now(); self._save()
        return self._records[k]

    def add_price(self, name: str, price: MaterialPrice) -> MaterialRecord:
        k = self._key(name)
        if k not in self._records: raise KeyError(f"{name} not found")
        for p in self._records[k].prices:
            if p.supplier_name == price.supplier_name: p.is_current = False
        self._records[k].prices.append(price)
        self._records[k].updated_at = datetime.now(); self._save()
        return self._records[k]

    def add_batch(self, name: str, batch: MaterialBatch) -> MaterialRecord:
        k = self._key(name)
        if k not in self._records: raise KeyError(f"{name} not found")
        self._records[k].batches.append(batch)
        self._records[k].updated_at = datetime.now(); self._save()
        return self._records[k]

    def query(self, q: MaterialQuery) -> list[MaterialRecord]:
        r = list(self._records.values())
        if q.name: r = [x for x in r if q.name.lower() in x.name.lower()]
        if q.cas_number: r = [x for x in r if x.cas_number and q.cas_number in x.cas_number]
        if q.category: r = [x for x in r if x.category == q.category]
        if q.supplier: r = [x for x in r if any(q.supplier.lower() in s.name.lower() for s in x.suppliers)]
        if q.shelf_life_status: r = [x for x in r if x.shelf_life_status == q.shelf_life_status]
        if q.has_price is not None: r = [x for x in r if (x.current_price is not None) == q.has_price]
        return r[:q.limit]

    def list_all(self): return list(self._records.values())
    def count(self): return len(self._records)
    def clear_all(self):
        n = len(self._records); self._records.clear(); self._save(); return n


_mgr: Optional[MaterialManager] = None

def get_material_manager() -> MaterialManager:
    global _mgr
    if _mgr is None: _mgr = MaterialManager()
    return _mgr
