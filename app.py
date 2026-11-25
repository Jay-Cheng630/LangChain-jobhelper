"""Streamlit 中文页面。"""

import json

import streamlit as st

from agent import AnalysisError, run_analysis

st.set_page_config(page_title="AI 求职岗位分析智能体", layout="wide")
st.title("AI 求职岗位分析智能体")
st.write("基于 LangChain Agent 与 DeepSeek，分析岗位要求、技能差距和学习安排。")
st.caption("输入将发送至 DeepSeek。请移除姓名、电话、公司内部信息等敏感内容。")
with st.form("analysis"):
    jd = st.text_area("招聘 JD", height=220, max_chars=15000)
    skills = st.text_area("已掌握技能（建议注明熟练程度）", max_chars=3000,
                          placeholder="Java 基础熟练，MySQL 会简单查询，Python 初学，暂无 Spring Boot 经验")
    left, right = st.columns(2)
    hours = left.number_input("每天可学习时间（小时）", 0.5, 12.0, 2.0, 0.5)
    days = right.number_input("学习计划天数", 1, 30, 14)
    submitted = st.form_submit_button("开始分析", type="primary")

if submitted:
    st.session_state.pop("result", None)
    try:
        with st.spinner("Agent 正在调用工具，可能需要数分钟……"):
            st.session_state.result = run_analysis(jd, skills, hours, days)
    except AnalysisError as exc:
        st.error(str(exc))

if "result" in st.session_state:
    result = st.session_state.result
    job = result["job"]
    st.subheader("岗位要求分析")
    st.write(f"岗位：{job['title']}　学历：{job['education']}　经验：{job['experience']}")
    for label, key in [("必备技术", "required"), ("加分技术", "preferred")]:
        st.write(label)
        if job[key]:
            st.dataframe(job[key], hide_index=True, use_container_width=True,
                         column_config={"skill": "技能", "evidence": "JD 原文依据"})
        else:
            st.caption("JD 未说明")
    st.write("岗位职责")
    for responsibility in job["responsibilities"]:
        st.write("• " + responsibility)
    st.subheader("技能差距分析")
    st.caption("依据用户自述推断；未提及的技能需进一步确认。")
    st.dataframe(result["gaps"]["items"], hide_index=True, use_container_width=True,
                 column_config={"skill": "技能", "status": "掌握状态",
                                "importance": "重要性", "evidence": "JD 原文依据",
                                "reason": "判断原因"})
    st.subheader("个性化学习计划")
    for milestone in result["plan"]["milestones"]:
        st.write("• " + milestone)
    for day in result["plan"]["days"]:
        with st.expander(f"第 {day['day']} 天 · {day['topic']} · {day['hours']} 小时 · {day['priority']}优先级"):
            for task in day["tasks"]:
                st.write("• " + task)
            st.write("验收成果：" + day["outcome"])
    st.subheader("Agent 工具调用记录")
    st.caption("来自本次 LangChain 消息中的真实工具调用；不含 API Key。")
    for index, call in enumerate(result["calls"], 1):
        with st.expander(f"{index}. {call['tool']} · {call['status']}"):
            st.json(call)
    st.download_button("下载分析结果", json.dumps(result, ensure_ascii=False, indent=2),
                       "analysis.json", "application/json")
