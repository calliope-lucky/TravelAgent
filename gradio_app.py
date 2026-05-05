import gradio as gr
from main import stream_chat


custom_css = """
/* 整体容器字体 */
.gradio-container, .contain {
    font-size: 16px !important;
}

/* 标题 */
h1 {
    font-size: 32px !important;
    font-weight: bold !important;
}

/* 描述文字 */
.prose, .description p {
    font-size: 18px !important;
}

/* 聊天消息 - 最重要 */
.chatbot-message, .message-wrap, [data-testid="chatbot-message"] {
    font-size: 18px !important;
    line-height: 1.6 !important;
}

/* 消息内容 */
.message-content, .markdown {
    font-size: 18px !important;
}

/* 输入框 - 重点调整 */
textarea, .textbox textarea, input[type="text"] {
    font-size: 18px !important;
    line-height: 1.5 !important;
}

/* 工具状态样式 */
.tool-status {
    margin: 8px 0;
    padding: 8px 12px;
    border-radius: 6px;
    font-size: 15px;
}

.tool-running {
    background: #fff8e1;
    border-left: 3px solid #ffc107;
    color: #856404;
    animation: pulse 2.5s ease-in-out infinite;
}

.tool-done {
    background: #e8f5e9;
    border-left: 3px solid #4caf50;
    color: #2e7d32;
}

@keyframes pulse {
    0%, 100% {
        opacity: 1;
    }
    50% {
        opacity: 0.6;
    }
}

/* 工具结果框 */
.tool-result-box {
    background: #f5f5f5;
    border-radius: 6px;
    margin: 6px 0;
    padding: 8px 12px;
    font-size: 13px;
    color: #666;
    max-height: 200px;
    overflow-y: auto;
    white-space: pre-wrap;
    word-break: break-all;
    cursor: pointer;
    transition: all 0.2s ease;
}

.tool-result-box:hover {
    background: #eeeeee;
    box-shadow: 0 2px 8px rgba(0,0,0,0.1);
}

/* 悬浮提示样式 */
[title] {
    position: relative;
}

/* 工具状态悬浮效果 */
.tool-status {
    transition: transform 0.2s ease, box-shadow 0.2s ease;
}

.tool-status:hover {
    transform: translateX(4px);
    box-shadow: 0 2px 6px rgba(0,0,0,0.1);
}

/* 发送按钮样式 */
.send-btn {
    width: 40px !important;
    min-width: 40px !important;
    max-width: 40px !important;
    padding: 0 !important;
}
"""


def generate_message(departure, destination, start_date, end_date, travelers):
    parts = []
    
    if departure and destination:
        parts.append(f"从{departure}出发，到{destination}")
    elif departure:
        parts.append(f"从{departure}出发")
    elif destination:
        parts.append(f"到{destination}")
    
    if start_date and end_date:
        parts.append(f"{start_date}去，{end_date}返回")
    elif start_date:
        parts.append(f"{start_date}出发")
    elif end_date:
        parts.append(f"{end_date}返回")
    
    if travelers and travelers != 1:
        parts.append(f"{int(travelers)}人游玩")
    
    if not parts:
        return "我想查询旅行信息"
    
    message = "我想" + "，".join(parts)
    return message


async def gradio_stream(message, history):
    is_first = len(history) == 0
    result = ""
    tool_results = {}
    last_was_tool = False

    async for chunk in stream_chat(
        message, thread_id="gradio_session", is_first_message=is_first
    ):
        if chunk["type"] == "text":
            if last_was_tool and result:
                result += "\n\n"
            result += chunk["content"]
            last_was_tool = False
        elif chunk["type"] == "tool":
            tool_key = chunk.get("tool_name", chunk["name"])
            tool_results[tool_key] = {
                "display_name": chunk["name"],
                "status": "running",
                "content": "",
            }
            last_was_tool = False
        elif chunk["type"] == "tool_result":
            tool_key = chunk.get("tool_name", chunk["name"])
            if tool_key in tool_results:
                tool_results[tool_key]["status"] = "done"
                tool_results[tool_key]["content"] = chunk.get("content", "")
            last_was_tool = True

        display = ""

        if tool_results:
            display += "### 📋 工具调用状态\n\n"
            for tool_key, tr in tool_results.items():
                if tr["status"] == "running":
                    display += f'<div class="tool-status tool-running" title="正在调用工具，请稍候...">🔄 正在调用 {tr["display_name"]}...</div>\n'
                else:
                    display += f'<div class="tool-status tool-done" title="工具调用已完成">✅ {tr["display_name"]} 完成</div>\n'
                    if tr["content"]:
                        display += f'<div class="tool-result-box" title="工具返回结果（可滚动查看完整内容）">{tr["content"]}</div>\n'
            display += "\n---\n\n"

        if result:
            display += result

        yield display


with gr.Blocks() as demo:
    gr.Markdown("# 🧳 AI 旅游规划助手")
    gr.Markdown("我可以帮你查询火车票、酒店、景点和美食信息，为你规划完美的旅行！")
    
    with gr.Row():
        with gr.Column(scale=1, min_width=280):
            gr.Markdown("### 📝 填写旅行需求")
            with gr.Group():
                departure = gr.Textbox(label="出发地", placeholder="例如：南京")
                destination = gr.Textbox(label="目的地", placeholder="例如：北京")
                start_date = gr.DateTime(label="出发时间", include_time=False)
                end_date = gr.DateTime(label="返回时间", include_time=False)
                travelers = gr.Number(label="游玩人数", value=1, minimum=1, interactive=True)
                submit_btn = gr.Button("🚀 开始规划", variant="primary")
        
        with gr.Column(scale=3):
            chatbot = gr.Chatbot(label="对话", height=600)
            with gr.Row():
                msg = gr.Textbox(
                    placeholder="输入你的问题...",
                    show_label=False,
                    container=False,
                    scale=10
                )
                submit_msg_btn = gr.Button("➤", variant="primary", min_width=40)

    def user_submit(message, history):
        history = history or []
        history.append({"role": "user", "content": message})
        return "", history

    async def bot_respond(history):
        user_message = history[-1]["content"]
        history.append({"role": "assistant", "content": ""})
        
        async for chunk in gradio_stream(user_message, history[:-2]):
            history[-1]["content"] = chunk
            yield history

    async def handle_form_and_respond(departure, destination, start_date, end_date, travelers, history):
        message = generate_message(departure, destination, start_date, end_date, travelers)
        history = history or []
        history.append({"role": "user", "content": message})
        history.append({"role": "assistant", "content": ""})
        
        async for chunk in gradio_stream(message, history[:-2]):
            history[-1]["content"] = chunk
            yield history

    submit_btn.click(
        fn=handle_form_and_respond,
        inputs=[departure, destination, start_date, end_date, travelers, chatbot],
        outputs=[chatbot]
    )

    msg.submit(user_submit, [msg, chatbot], [msg, chatbot], queue=False).then(
        bot_respond, chatbot, chatbot
    )
    
    submit_msg_btn.click(user_submit, [msg, chatbot], [msg, chatbot], queue=False).then(
        bot_respond, chatbot, chatbot
    )

if __name__ == "__main__":
    demo.launch(theme=gr.themes.Soft(), css=custom_css, server_port=8080)
