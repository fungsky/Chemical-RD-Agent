"""研发上下文管理器（JSON 持久化，轻量）。"""

import json
import logging
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

from chem_agent.rd.models import ClientRequest, SampleRecord, TimelineEvent

logger = logging.getLogger(__name__)


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


class RDManager:
    def __init__(self, data_dir: Optional[str] = None):
        self._dir = Path(data_dir or "data")
        self._dir.mkdir(parents=True, exist_ok=True)
        self._file = self._dir / "rd_context.json"
        self._requests: dict[str, ClientRequest] = {}
        self._samples: dict[str, SampleRecord] = {}
        self._events: list[TimelineEvent] = []
        self._load()

    def _load(self):
        if not self._file.exists():
            return
        try:
            raw = json.loads(self._file.read_text(encoding="utf-8"))
            for k, v in raw.get("requests", {}).items():
                self._requests[k] = ClientRequest(**v)
            for k, v in raw.get("samples", {}).items():
                self._samples[k] = SampleRecord(**v)
            self._events = [TimelineEvent(**e) for e in raw.get("events", [])]
        except Exception as e:
            logger.warning("rd_context 加载失败: %s", e)

    def _save(self):
        raw = {
            "requests": {k: v.model_dump(mode="json") for k, v in self._requests.items()},
            "samples": {k: v.model_dump(mode="json") for k, v in self._samples.items()},
            "events": [e.model_dump(mode="json") for e in self._events],
        }
        self._file.write_text(json.dumps(raw, ensure_ascii=False, indent=2), encoding="utf-8")

    def list_requests(self) -> list[dict]:
        return [r.model_dump(mode="json") for r in self._requests.values()]

    def get_request(self, request_id: str) -> Optional[ClientRequest]:
        return self._requests.get(request_id)

    def create_request(self, customer: str, title: str, requirement: str = "", target_specs: dict = None) -> ClientRequest:
        rid = "REQ-" + uuid.uuid4().hex[:6].upper()
        req = ClientRequest(
            id=rid,
            customer=customer,
            title=title,
            requirement=requirement,
            target_specs=target_specs or {},
        )
        self._requests[rid] = req
        self._events.insert(0, TimelineEvent(
            event_id=uuid.uuid4().hex,
            request_id=rid,
            event_type="note",
            summary=f"新建需求：{title}（客户 {customer}）",
        ))
        self._save()
        return req

    def update_request(self, request_id: str, **kwargs) -> Optional[ClientRequest]:
        req = self._requests.get(request_id)
        if not req:
            return None
        for key, val in kwargs.items():
            if key in {"customer", "title", "requirement", "target_specs", "status"}:
                setattr(req, key, val)
        req.updated_at = _now()
        self._events.insert(0, TimelineEvent(
            event_id=uuid.uuid4().hex,
            request_id=request_id,
            event_type="note",
            summary=f"需求更新：{req.title} → {req.status}",
        ))
        self._save()
        return req

    def add_formula(self, request_id: str, code: str) -> Optional[ClientRequest]:
        req = self._requests.get(request_id)
        if not req:
            return None
        if code and code not in req.formula_codes:
            req.formula_codes.append(code)
            req.updated_at = _now()
            self.add_event(request_id, "note", f"关联配方 {code}", code)
            self._save()
        return req

    def add_event(self, request_id: str, event_type: str, summary: str, ref: str = "") -> TimelineEvent:
        ev = TimelineEvent(
            event_id=uuid.uuid4().hex,
            request_id=request_id,
            event_type=event_type,
            summary=summary,
            ref=ref,
        )
        self._events.insert(0, ev)
        self._save()
        return ev

    def list_samples(self) -> list[dict]:
        return [s.model_dump(mode="json") for s in self._samples.values()]

    def add_sample(self, request_id: str, formula_code: str, formula_name: str, batch_number: str = "") -> SampleRecord:
        sid = "SMP-" + uuid.uuid4().hex[:6].upper()
        sample = SampleRecord(
            sample_id=sid,
            request_id=request_id,
            formula_code=formula_code,
            formula_name=formula_name,
            batch_number=batch_number,
        )
        self._samples[sid] = sample
        self.add_event(request_id, "sample", f"寄出样品 {sid}（{formula_name or formula_code}）", sid)
        return sample

    def update_sample(self, sample_id: str, feedback_status: str = None, feedback: str = None) -> Optional[SampleRecord]:
        sample = self._samples.get(sample_id)
        if not sample:
            return None
        if feedback_status:
            sample.feedback_status = feedback_status
        if feedback is not None:
            sample.feedback = feedback
        if sample.feedback_status == "received":
            self.add_event(sample.request_id, "feedback", f"收到样品 {sample.sample_id} 反馈：{feedback[:200]}", sample.sample_id)
        self._save()
        return sample

    def events(self, limit: int = 100) -> list[dict]:
        return [e.model_dump(mode="json") for e in self._events[:limit]]
