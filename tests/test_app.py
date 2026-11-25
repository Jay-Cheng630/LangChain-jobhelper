from pathlib import Path

from streamlit.testing.v1 import AppTest


APP = str(Path(__file__).resolve().parents[1] / "app.py")


def test_page_loads():
    page = AppTest.from_file(APP).run()
    assert not page.exception
    assert page.title[0].value == "AI 求职岗位分析智能体"
    assert len(page.text_area) == 2
    assert len(page.number_input) == 2


def test_empty_submit():
    page = AppTest.from_file(APP).run()
    page.button[0].click().run()
    assert not page.exception
    assert "请填写" in page.error[0].value


def test_result_page(monkeypatch):
    from test_agent import GAPS, JOB, PLAN

    monkeypatch.setattr("agent.run_analysis", lambda *args: {
        "job": JOB, "gaps": GAPS, "plan": PLAN,
        "calls": [{"tool": "extract_job_requirements", "input": {},
                   "output": "Mock output", "status": "success"}],
    })
    page = AppTest.from_file(APP).run()
    page.text_area[0].input("示例 JD")
    page.text_area[1].input("Java 基础")
    page.button[0].click().run()
    assert not page.exception
    assert len(page.dataframe) == 2
    assert any(item.value == "Agent 工具调用记录" for item in page.subheader)
