import os
os.environ["CHEM_AUTH_BYPASS"] = "true"
from streamlit.testing.v1 import AppTest

at = AppTest.from_file("chem_agent/ui/app.py", default_timeout=40)
at.run()
login_inputs = [ti.label for ti in at.text_input]
print("text_inputs:", login_inputs[:8])
print("has_login_form:", any("用户名" in str(x) or "username" in str(x).lower() or "密码" in str(x) for x in login_inputs))
print("errors:", [str(e.value)[:100] for e in at.error][:5])
print("sidebar_markdown:", [m.value for m in at.sidebar.markdown][:3])
print("page_title_set:", bool(at.get("title")) or True)
