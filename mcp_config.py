"""
MCP 服务器配置文件
集中管理所有 MCP 服务器的连接配置
"""
from pathlib import Path
import sys

# 获取项目根目录
PROJECT_ROOT = Path(__file__).parent

# 本地 Python 解释器路径
LOCAL_PYTHON_PATH = sys.executable

# MCP 服务器
TRAIN_MCP_URL = "your-train-mcp-url"
HOTEL_MCP_URL = "your-hotel-mcp-url"

# 工具脚本路径
ATTRACTIONS_CRAWLER_PATH = str(PROJECT_ROOT / "mcp_data" / "attractions_mcp_server.py")
FOOD_CRAWLER_PATH = str(PROJECT_ROOT / "mcp_data" / "food_mcp_server.py")


# 火车票查询 MCP 服务器配置
TRAIN_MCP_CONFIG = {
    "tongchenglvxing-mcp-server": {
        "transport": "streamable_http",
        "url": TRAIN_MCP_URL,
    }
}

# 酒店查询 MCP 服务器配置（高德地图）
HOTEL_MCP_CONFIG = {
    "amap-maps": {
        "transport": "streamable_http",
        "url": HOTEL_MCP_URL,
    }
}

# 景点查询 MCP 服务器配置
ATTRACTIONS_MCP_CONFIG = {
    "attractions_mcp_server": {
        "transport": "stdio",
        "command": LOCAL_PYTHON_PATH,
        "args": [ATTRACTIONS_CRAWLER_PATH],
    }
}

# 美食查询 MCP 服务器配置
FOOD_MCP_CONFIG = {
    "food_mcp_server": {
        "transport": "stdio",
        "command": LOCAL_PYTHON_PATH,
        "args": [FOOD_CRAWLER_PATH],
    }
}
