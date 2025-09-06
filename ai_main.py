import requests
import json
from typing import Optional, List, Dict, Any


def deepseek_chat(
        api_key: str,
        prompt: str,
        stream: bool = True,
        max_tokens: int = 1024,
        temperature: float = 0.7,
        history: Optional[List[Dict[str, str]]] = None,
        model: str = "deepseek-chat"  # 支持切换模型
) -> Dict[str, Any]:
    """
    调用DeepSeek API进行对话（支持流式/非流式、输出长度限制、对话历史）

    参数:
        api_key: DeepSeek API密钥
        prompt: 当前提问内容
        stream: 是否启用流式输出（默认True）
        max_tokens: 最大输出token数（默认1024）
        temperature: 生成随机性（0-1，默认0.7）
        history: 对话历史，格式为[{"role": "user/assistant", "content": "..."}]
        model: 模型名称（默认deepseek-reasoner，可选deepseek-chat）

    返回:
        字典，包含"content"（完整响应内容）、"stream"（是否为流式）、"error"（错误信息，如有）
    """
    # 基础配置（使用你提供的可运行URL）
    url = "https://api.deepseek.com/chat/completions"
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {api_key}"
    }

    # 构建消息列表（历史对话+当前提问）
    messages = (history.copy() if history else []) + [
        {"role": "user", "content": prompt}
    ]

    # 请求参数
    payload = {
        "model": model,
        "messages": messages,
        "stream": stream,
        "max_tokens": max_tokens,
        "temperature": temperature
    }

    try:
        # 发送请求（流式需保持连接）
        response = requests.post(
            url,
            headers=headers,
            json=payload,
            stream=stream,
            timeout=30  # 超时保护
        )
        response.raise_for_status()  # 检查HTTP错误

        # 处理流式响应
        if stream:
            print("===== 流式输出开始 =====")
            for line in response.iter_lines():
                if line:
                    line_str = line.decode('utf-8').lstrip('data: ')
                    if line_str == '[DONE]':
                        break
                    try:
                        data = json.loads(line_str)
                        if "error" in data:
                            yield {"error": f"API错误: {data['error']['message']}", "stream": True}
                            return
                        if data.get("choices") and len(data["choices"]) > 0:
                            delta = data["choices"][0]["delta"]
                            content = delta.get("content", "")
                            if content:
                                print(content, end="", flush=True)
                                # 关键修改：每次获取到内容就立即yield
                                yield content  # 实时返回当前块内容
                    except Exception:
                        continue
            print("\n===== 流式输出结束 =====")
            # 流式结束后返回空标识（可选）
            yield None  # 用于标记结束
            return  # 不再返回完整内容字典

        # 处理非流式响应
        else:
            data = response.json()
            # 检查API错误
            if "error" in data:
                return {"error": f"API错误: {data['error']['message']}", "stream": False}

            # 提取完整内容
            if data.get("choices") and len(data["choices"]) > 0:
                content = data["choices"][0]["message"].get("content", "")
                return {"content": content, "stream": False}
            else:
                return {"error": "响应中未包含有效内容", "stream": False}

    except requests.exceptions.RequestException as e:
        return {"error": f"请求失败: {str(e)}", "stream": stream}


# 示例调用（使用方式示例）
"""
if __name__ == "__main__":
    # 替换为你的API密钥
    API_KEY = "sk-************************"

    # 1. 基础流式调用（使用deepseek-reasoner模型）
    print("=== 基础流式调用示例 ===")
    res = deepseek_chat(
        api_key=API_KEY,
        prompt="你是谁？简单介绍一下",
        max_tokens=100,  # 限制输出长度
        stream=True
    )
    if "error" in res:
        print(f"错误: {res['error']}")
    else:
        print(f"\n完整响应内容: {res['content']}\n")

    # 2. 带对话历史的非流式调用（使用deepseek-chat模型）
    print("=== 带历史的非流式调用示例 ===")
    history = [
        {"role": "user", "content": "你好"},
        {"role": "assistant", "content": "你好！我是DeepSeek Chat，有什么我可以帮你的吗？"}
    ]
    res = deepseek_chat(
        api_key=API_KEY,
        prompt="推荐一本Python入门书籍",
        history=history,
        stream=False,  # 关闭流式
        model="deepseek-chat",  # 切换模型
        max_tokens=200
    )
    if "error" in res:
        print(f"错误: {res['error']}")
    else:
        print(f"响应内容: {res['content']}")
"""