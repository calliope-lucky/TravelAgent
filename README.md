# 智能旅游规划助手

基于 LangChain 和 MCP 的智能旅游规划系统，支持多轮对话交互，为用户提供完整的旅游行程规划服务。

## 功能特性

- 智能对话交互：基于 LangChain 和 LangGraph 构建多轮对话系统
- 景点推荐：智能推荐旅游目的地热门景点
- 美食推荐：提供各地特色美食和餐厅信息
- 火车票查询：集成 MCP 服务查询火车班次
- 酒店查询：集成 MCP 服务查询酒店信息
- 流式响应：支持实时流式输出，提升用户体验
- Web 界面：基于 Gradio 的友好交互界面

## 技术栈

- **核心框架**: LangChain + LangGraph
- **AI 模型**: OpenAI API (支持自定义 base URL)
- **MCP 服务**: Model Context Protocol 用于扩展工具能力
- **Web UI**: Gradio

## 项目结构

```
TravelProject/
├── main.py                 # 主程序入口
├── gradio_app.py          # Gradio Web 界面
├── config.py              # 配置文件
├── mcp_config.py          # MCP 服务器配置
├── sub_agents.py          # 子代理实现
├── requirements.txt       # 依赖包列表
├── mcp_data/              # MCP 数据文件夹
├── prompts/               # 提示词模板
└── logs/                  # 日志文件
```

## 快速开始

### 1. 克隆项目

```bash
git clone https://github.com/calliope-lucky/TravelAgent.git
cd TravelProject
```

### 2. 创建虚拟环境

```bash
python -m venv .venv
source .venv/bin/activate  # Linux/Mac
# 或
.venv\Scripts\activate     # Windows
```

### 3. 安装依赖

```bash
pip install -r requirements.txt
```

### 4. 配置环境变量

修改 `.env` 文件并配置以下参数：

```env
# API 配置
OPENAI_API_BASE=https://api.your-provider.com/v1
OPENAI_API_KEY=your-api-key

# 模型配置
MAIN_MODEL_NAME=your-model-name
EXECUTOR_MODEL_NAME=your-model-name
```

### 5. 配置 MCP 服务

编辑 `mcp_config.py` 文件，配置 MCP 服务的 URL：

- **酒店查询服务**：从 [ModelScope Amap Maps](https://www.modelscope.cn/mcp/servers/@amap/amap-maps) 获取 URL
- **火车票查询服务**：从 [ModelScope 同程旅行](https://www.modelscope.cn/mcp/servers/@wuchubuzai2018/tongchenglvxing-mcp-server) 获取 URL

将获取到的 URL 替换到 `mcp_config.py` 中的对应位置：

```python
# MCP 服务器 URL 常量
TRAIN_MCP_URL = "your-train-mcp-url"
HOTEL_MCP_URL = "your-hotel-mcp-url"
```

### 6. 运行项目

**Web 界面模式（推荐）：**

```bash
python gradio_app.py
```

**命令行模式：**

```bash
python main.py
```

<br />

## 许可证

MIT License

## 致谢

- [LangChain](https://github.com/langchain-ai/langchain)
- [LangGraph](https://github.com/langchain-ai/langgraph)
- [Gradio](https://github.com/gradio-app/gradio)
- [MCP](https://github.com/modelcontextprotocol)

