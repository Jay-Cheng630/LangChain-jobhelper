"""离线 Mock 测试，不访问 DeepSeek。Agent 测试使用真实 create_agent。"""

import json
from unittest.mock import Mock

import pytest
from langchain_core.language_models.fake_chat_models import FakeMessagesListChatModel
from langchain_core.messages import AIMessage

from agent import AnalysisError, build_tools, run_analysis

JD = "Java 后端开发，本科，1年经验。必须掌握 Java、MySQL，负责接口开发。"
SKILLS = "Java 熟练，MySQL 初学"
JOB = {
    "title": "Java 后端开发", "education": "本科", "experience": "1年",
    "required": [{"skill": name, "evidence": "必须掌握 Java、MySQL"}
                 for name in ["Java", "MySQL"]],
    "preferred": [], "responsibilities": ["接口开发"],
}
GAPS = {"items": [
    {"skill": name, "status": status, "importance": "开发接口需要",
     "evidence": "必须掌握 Java、MySQL", "reason": reason}
    for name, status, reason in [("Java", "已掌握", "用户自述熟练"),
                                 ("MySQL", "部分掌握", "用户自述初学")]
]}
PLAN = {"days": [
    {"day": day, "hours": 2, "priority": "高", "topic": "SQL 练习",
     "tasks": ["练习查询和联表"], "outcome": "完成5道查询题"}
    for day in [1, 2]
], "milestones": ["第2天完成联表查询练习"]}


def reply(value):
    return AIMessage(content=json.dumps(value, ensure_ascii=False))


def toolset(responses):
    model = Mock()
    model.invoke.side_effect = [reply(value) for value in responses]
    results = {}
    return build_tools(model, JD, SKILLS, 2, 2, results), results


def test_extract_job_requirements():
    tools, results = toolset([JOB])
    assert tools[0].invoke({"job_description": JD}) == JOB
    assert results["job"]["required"][0]["skill"] == "Java"


def test_analyze_skill_gaps():
    tools, results = toolset([GAPS])
    results["job"] = JOB
    assert tools[1].invoke({"user_skills": SKILLS}) == GAPS


def test_generate_learning_plan():
    tools, results = toolset([PLAN])
    results.update(job=JOB, gaps=GAPS)
    assert tools[2].invoke({"daily_hours": 2, "plan_days": 2}) == PLAN


@pytest.mark.parametrize("jd,skills", [("", SKILLS), (JD, " ")])
def test_empty_input(jd, skills):
    with pytest.raises(AnalysisError, match="请填写"):
        run_analysis(jd, skills, 2, 2)


@pytest.mark.parametrize("hours,days", [
    (0, 2), (2, 0), (13, 2), (2, 31), (2, 1.5),
    (True, 2), (2, True), (float("nan"), 2), ("2", 2),
])
def test_invalid_time(hours, days):
    with pytest.raises(AnalysisError):
        run_analysis(JD, SKILLS, hours, days)


class ScriptedModel(FakeMessagesListChatModel):
    def bind_tools(self, tools, **kwargs):
        return self


def call(name, args, number):
    return AIMessage(content="", tool_calls=[
        {"name": name, "args": args, "id": str(number), "type": "tool_call"}
    ])


def test_real_agent_tool_flow():
    model = ScriptedModel(responses=[
        call("extract_job_requirements", {"job_description": JD}, 1), reply(JOB),
        call("analyze_skill_gaps", {"user_skills": SKILLS}, 2), reply(GAPS),
        call("generate_learning_plan", {"daily_hours": 2, "plan_days": 2}, 3),
        reply(PLAN), AIMessage(content="分析完成"),
    ])
    result = run_analysis(JD, SKILLS, 2, 2, model=model)
    assert result["plan"] == PLAN
    assert [item["tool"] for item in result["calls"]] == [
        "extract_job_requirements", "analyze_skill_gaps", "generate_learning_plan"]
    assert all(item["status"] == "success" for item in result["calls"])
    assert result["calls"][0]["input"]["job_description"] == JD


def test_api_failure(monkeypatch):
    model = Mock()
    model.invoke.side_effect = RuntimeError("secret-key-must-not-leak")
    monkeypatch.setattr("agent.create_agent", lambda **kwargs: model)
    with pytest.raises(AnalysisError, match="分析失败") as error:
        run_analysis(JD, SKILLS, 2, 2, model=Mock())
    assert "secret-key" not in str(error.value)


class FailingModel(ScriptedModel):
    def _generate(self, messages, stop=None, run_manager=None, **kwargs):
        raise ConnectionError("secret-key-must-not-leak")


def test_api_failure_in_real_agent():
    model = FailingModel(responses=[AIMessage(content="unused")])
    with pytest.raises(AnalysisError, match="分析失败") as error:
        run_analysis(JD, SKILLS, 2, 2, model=model)
    assert "secret-key" not in str(error.value)


def test_missing_api_key(monkeypatch):
    monkeypatch.setattr("agent.load_dotenv", lambda *args: None)
    monkeypatch.delenv("DEEPSEEK_API_KEY", raising=False)
    with pytest.raises(AnalysisError, match="尚未配置"):
        run_analysis(JD, SKILLS, 2, 2)


def test_incomplete_agent_flow():
    model = ScriptedModel(responses=[AIMessage(content="直接给建议")])
    with pytest.raises(AnalysisError, match="未完成"):
        run_analysis(JD, SKILLS, 2, 2, model=model)


def test_dependency_guard():
    tools, _ = toolset([])
    with pytest.raises(ValueError, match="先提取"):
        tools[1].invoke({"user_skills": SKILLS})


def test_fabricated_evidence():
    job = {**JOB, "required": [{"skill": "Redis", "evidence": "必须掌握 Redis"}]}
    tools, _ = toolset([job])
    with pytest.raises(ValueError, match="依据"):
        tools[0].invoke({"job_description": JD})


def test_wrong_plan_days():
    tools, results = toolset([{**PLAN, "days": PLAN["days"][:1]}])
    results.update(job=JOB, gaps=GAPS)
    with pytest.raises(ValueError, match="天数"):
        tools[2].invoke({"daily_hours": 2, "plan_days": 2})


def test_reextract_invalidates_downstream_results():
    tools, results = toolset([JOB])
    results.update(job=JOB, gaps=GAPS, plan=PLAN)
    tools[0].invoke({"job_description": JD})
    assert "gaps" not in results and "plan" not in results


def test_reanalyze_invalidates_plan():
    tools, results = toolset([GAPS])
    results.update(job=JOB, gaps=GAPS, plan=PLAN)
    tools[1].invoke({"user_skills": SKILLS})
    assert "plan" not in results


def test_duplicate_gap_rejected():
    tools, results = toolset([{"items": GAPS["items"] + GAPS["items"][:1]}])
    results["job"] = JOB
    with pytest.raises(ValueError):
        tools[1].invoke({"user_skills": SKILLS})


@pytest.mark.parametrize("changes", [
    {"tasks": []}, {"tasks": [" "]}, {"outcome": " "}, {"topic": ""},
])
def test_empty_plan_content_rejected(changes):
    plan = {**PLAN, "days": [{**PLAN["days"][0], **changes}, PLAN["days"][1]]}
    tools, results = toolset([plan])
    results.update(job=JOB, gaps=GAPS)
    with pytest.raises(ValueError):
        tools[2].invoke({"daily_hours": 2, "plan_days": 2})
