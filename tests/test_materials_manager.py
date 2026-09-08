"""原材料 JSON 管理器测试。"""

from chem_agent.materials.manager import MaterialManager


def test_empty_store_seeds_sample_materials(tmp_path):
    mgr = MaterialManager(data_dir=str(tmp_path))
    assert len(mgr.list_all()) == 78
    assert mgr.count() == 78


def test_empty_file_is_not_overwritten_on_load(tmp_path):
    store = tmp_path / "materials.json"
    store.write_text("{}", encoding="utf-8")
    mgr = MaterialManager(data_dir=str(tmp_path))
    assert mgr.count() == 78
    assert store.read_text(encoding="utf-8") == "{}"
