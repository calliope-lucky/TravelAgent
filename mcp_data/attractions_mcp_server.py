import json
from typing import List, Dict
from mcp.server.fastmcp import FastMCP
from pathlib import Path

# 获取项目根目录（mcp_data 的父目录）
PROJECT_ROOT = Path(__file__).parent.parent

mcp = FastMCP("AttractionsTools")


def load_attractions_data() -> Dict:
    """加载景点数据"""
    try:
        with open("mcp_data/sample_attractions.json", "r", encoding="utf-8") as f:
            return json.load(f)
    except FileNotFoundError:
        return {}


@mcp.tool()
def get_attractions_by_city(city: str) -> List[Dict[str, str]] | str:
    """
    根据城市名称获取该城市的景点列表

    :param city: 城市名称，如"杭州"、"北京"、"上海"等
    :type city: str
    :return: 城市景点的基本信息列表，包含景点名称、等级、评分、门票价格、建议游玩时长等信息
    :rtype: List[Dict[str, str]]
    """
    data = load_attractions_data()

    if city not in data:
        available_cities = list(data.keys())
        return f"未找到该城市的景点信息！可用城市：{', '.join(available_cities)}"

    attractions = data[city]

    result = []
    for attraction in attractions:
        result.append({
            "景点名称": attraction.get("景点名称", ""),
            "等级": attraction.get("等级", ""),
            "评分": attraction.get("评分", ""),
            "门票价格": attraction.get("门票价格", ""),
            "具体位置": attraction.get("具体位置", ""),
            "开放时间": attraction.get("开放时间", ""),
            "景点介绍": attraction.get("景点介绍", ""),
            "主要看点": attraction.get("主要看点", ""),
            "建议游玩时长": attraction.get("建议游玩时长", "")
        })

    return result


if __name__ == "__main__":
    mcp.run(transport="stdio")
