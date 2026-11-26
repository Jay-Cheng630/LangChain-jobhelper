# AI 求职岗位分析智能体

大学课程项目：输入招聘 JD、技能自述、每天学习时间和计划天数，使用 LangChain Agent 调用三个工具，生成岗位要求、技能差距和每日学习计划。中文界面由 Streamlit 提供，模型通过兼容 OpenAI 的 DeepSeek API 接入。

## 功能说明

- 提取岗位名称、学历、经验、必备技术、加分技术和职责。
- 将技能标记为已掌握、部分掌握、尚未掌握，展示重要性、判断原因和 JD 原文依据。
- 按指定天数和每天可用时间制定练习任务、优先级、验收成果和阶段目标。
- 显示 LangChain 消息中实际发生的工具调用输入、输出和状态。
- 下载 JSON 分析结果。

技能判断依据自述，不能代替实际能力测评。未提及的技能暂归为尚未掌握，需要用户确认。短期计划不保证达到招聘要求或获得工作。

工具重新生成上游结果时会清除旧的下游结果，避免展示不匹配的岗位、差距和计划。输出校验还会拒绝重复差距记录、空白每日任务和空白验收成果。

## 技术架构

```text
Streamlit 页面 → run_analysis → LangChain create_agent → DeepSeek
                                     ↕ 工具调用循环
                     extract_job_requirements → 岗位 JSON
                     analyze_skill_gaps → 差距 JSON
                     generate_learning_plan → 计划 JSON
```

Agent 模型决定工具名称和参数，工具结果以 ToolMessage 返回，再由模型决定下一步。Python 没有固定依次执行三个工具；工具内部检查依赖和原始输入，避免模型跳过岗位提取或篡改学习时间。完整请求要求三个结果齐全，否则明确报错。

三个工具使用同一个 DeepSeek 模型分别完成语义分析，通过 Pydantic 验证 JSON，并检查 JD 原文依据、技能覆盖、日期和学习时间。正常流程通常包含四次 Agent 决策调用和三次工具内部模型调用；具体次数由 Agent 行为决定。未接入搜索、数据库或本地文件执行工具。

| 文件 | 作用 |
| --- | --- |
| app.py | 输入表单、结果展示、工具记录及下载 |
| agent.py | 环境变量、模型接入、Agent、工具及错误处理 |
| schemas.py | 工具输出数据结构 |
| tests/test_agent.py | 工具和真实 Agent 循环的 Mock 测试 |
| tests/test_app.py | Streamlit 页面测试 |
| requirements.txt | 直接依赖版本范围 |
| requirements-lock.txt | 实际验证环境的完整依赖版本（安装验证后生成） |

## 环境准备

Windows 推荐 Python 3.12，使用 PowerShell。先进入项目目录：

```powershell
cd E:\LangChain
py -3.12 -m venv .venv
```

如果 `py` 不存在，请使用已安装 Python 3.12 的完整路径替换 `py -3.12`。本次开发若已创建 `.venv312`，可直接使用该环境，下列命令中的 `.venv` 替换为 `.venv312`。不需要激活虚拟环境，也不需要修改 PowerShell 执行策略。

## 安装依赖

```powershell
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
```

需要复现本次验证版本时，改为安装 `requirements-lock.txt`。不建议混用其他项目的全局 Python 包。

## API Key 配置

```powershell
Copy-Item .env.example .env
notepad .env
```

在本机填写：

```dotenv
DEEPSEEK_API_KEY=你的真实密钥
DEEPSEEK_MODEL=deepseek-chat
```

模型名可按账号支持情况修改，须支持工具调用。API 地址固定为 `https://api.deepseek.com`。不要把密钥粘贴到聊天、课堂投影或 GitHub。`.env` 已在 `.gitignore` 中忽略。已有同名系统环境变量时，系统变量优先；修改后如仍使用旧配置，请重启终端和服务。模型请求会发送 JD 和技能描述，请先删除个人及企业敏感信息。

没有真实密钥也能运行测试和打开页面，点击分析时会提示配置，不会伪造分析结果。

## 启动项目

```powershell
.\.venv\Scripts\python.exe -m streamlit run app.py --server.address 127.0.0.1
```

浏览器打开终端显示的本地地址，通常是 http://127.0.0.1:8501 。输入完成后点击“开始分析”。真实请求可能需要数分钟；API 请求有超时和有限重试，Agent 有循环次数上限。停止服务按 Ctrl+C。

API 失败时页面显示安全错误提示，不直接输出 SDK 原始异常。请检查密钥、网络、余额、模型名；模型没有正确调用工具或 JSON 格式不合规也会导致失败。可缩短计划至 3 天再试。当前不展示失败请求的部分结果，重新提交会清除旧结果。

## 测试方法

```powershell
.\.venv\Scripts\python.exe -m pytest -q
.\.venv\Scripts\python.exe -m pip check
```

所有自动化测试使用 Mock，不访问 DeepSeek，不消耗 API 额度。Agent 流程测试仍使用真正的 `create_agent` 和 LangChain 工具执行，只替换模型响应。它能证明工具执行和结果收集可用，不能证明真实 DeepSeek 的输出质量或联网连接成功。

本次实际运行情况见 `VALIDATION.md`。课堂流程见 `课堂演示说明.md`，入门解释和问答见 `初学者教程.md`。

## 官方参考

- [LangChain create_agent](https://reference.langchain.com/python/langchain/agents/factory/create_agent)
- [LangChain 官方工具文档](https://github.com/langchain-ai/docs/blob/main/src/oss/langchain/tools.mdx)
- [DeepSeek 工具调用](https://api-docs.deepseek.com/guides/tool_calls/)
- [DeepSeek OpenAI 兼容接口](https://api-docs.deepseek.com/quick_start/agent_integrations/)
