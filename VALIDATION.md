# 实际验证记录

验证日期：2026-11-25，Windows，项目目录 E:\LangChain。

- 使用项目本地 Python 3.12.13、`.venv312` 虚拟环境。
- 依赖安装成功，完整版本见 requirements-lock.txt。
- `python -m pytest -q`：20 passed in 6.23s。
- `python -m pip check`：No broken requirements found。
- 测试包含三个工具、空输入、时间边界、API 失败、缺少 Key、真实 LangChain Agent 的 Mock 工具循环、依据校验、计划日期校验、页面加载及结果展示。
- 受限沙箱中的页面测试停滞，最终在允许的本地权限下运行上述测试通过。
- Streamlit 实际启动成功：127.0.0.1:8502。页面逻辑通过 Streamlit AppTest 验证，未进行人工浏览器视觉验收。
- 本地健康检查 `/_stcore/health`：HTTP 200，响应 ok。
- 未配置 .env，未执行真实 DeepSeek API 请求；Mock 测试通过不等于真实模型联通。

真实联调待办：复制 .env.example 为 .env，在本机填写 DEEPSEEK_API_KEY，按课堂演示说明输入示例，检查三个实际工具调用及结果。
