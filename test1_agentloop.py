import subprocess
import os
from anthropic import Anthropic
from dotenv import load_dotenv

try:
    import readline
    # macOS 的 libedit 在处理中文输入时有退格问题，这四行修复它
    readline.parse_and_bind('set bind-tty-special-chars off')
    readline.parse_and_bind('set input-meta on')
    readline.parse_and_bind('set output-meta on')
    readline.parse_and_bind('set convert-meta off')
except ImportError:
    pass


#覆盖已有的环境变量
load_dotenv(override=True)


client = Anthropic(base_url=os.getenv("ANTHROPIC_BASE_URL"),api_key=os.getenv("ANTHROPIC_API_KEY"))

MODEL = "qwen-turbo"

SYSTEM = f"You are a coding agent at {os.getcwd()}. Use bash to solve tasks. Act, don't explain."

print(SYSTEM)


TOOLS = [{
    "name":"bash",
    "description":"Run a shell command",
    "input_schema":{
        "type":"object",
        "properties":{"command":{"type":"string"}},
        "required":["command"]
    }
}]


def run_bash(command:str) -> str:
    dangerous = ["rm -rf /", "sudo", "shutdown", "reboot", "> /dev/"]
    if any(d in command for d in dangerous):
        return "Error: Dangerous command blocked"
    try:
        r = subprocess.run(command,shell=True,cwd=os.getcwd(),
                           capture_output=True,text=True,timeout=120)
        out = (r.stdout + r.stderr).strip()
        return out[:50000] if out else "(no output)"
    except subprocess.TimeoutExpired:
        return "Error: Timeout expired(120s)"
    except (FileNotFoundError, OSError) as e:
        return "Error: {}".format(e)





def agent_loop(messages:list):
    response = client.messages.create(
        model=MODEL, system=SYSTEM, messages=messages,
        tools=TOOLS, max_tokens=8000,
    )

    messages.append({"role":"assistant","content":response.content})

    # stop_reason 属性，告诉程序"AI 为什么停止生成回复了"
    if response.stop_reason != "tool_use":
            return
    results = []

    for block in response.content:
        if block.type == "tool_use":
            print(f"\033[33m$ {block.input['command']}\033[0m")
            output = run_bash(block.input["command"])
            print(output[:200])
            results.append({
                "type": "tool_result",
                "tool_use_id": block.id,
                "content": output,
            })

    messages.append({
        "role": "user",
        "content": results
    })


if __name__ == "__main__":
    print("s01: Agent Loop")
    print("输入问题，回车发送。输入 q 退出。\n")
    history = []
    while True:
        try:
            query = input("\033[36ms01 >> \033[0m")
        except(EOFError, KeyboardInterrupt):
            break
        if query.strip().lower() in ("q","exit",""):
            break

        history.append({"role":"user","content":query})

        agent_loop(history)

        response_content = history[-1]["content"]
        if isinstance(response_content, list):
            for block in response_content:
                if getattr(block,"type",None) == "text":
                    print(block.text)
        print()