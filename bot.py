import autogen
import discord
import os
import json
from autogen.agentchat.contrib.retrieve_user_proxy_agent import (
    RetrieveUserProxyAgent,
)
from more_itertools import flatten

API_KEY = os.getenv("OPENAI_API_KEY")
DISCORD_TOKEN = os.getenv("DISCORD_TOKEN")
BASE_URL = os.getenv("BASE_URL")

# LLMコンフィグ設定
llm_config = {
    "config_list": [
        {
            "model": "gpt-35-turbo",
            "base_url": BASE_URL,
            "api_key": API_KEY,
            "api_type": "azure",
            "api_version": "2024-05-01-preview",
        }
    ],
}

# def load_md_files_from_json(json_file_path):
#     """JSONファイルからMarkdownファイルのリストを読み込む"""
#     try:
#         with open(json_file_path, 'r', encoding='utf-8') as f:
#             data = json.load(f)
#             return data.get("md_files", [])
#     except FileNotFoundError:
#         print(f"JSON file not found: {json_file_path}")
#         return []
#     except json.JSONDecodeError:
#         print(f"Error decoding JSON from file: {json_file_path}")
#         return []

# def read_md_files():
#     # """Markdownファイルの内容を読み込む"""
#     # content = ""
#     # for md_file in md_files:
#     #     file_path = os.path.join("./generated_pages", md_file)
#     #     try:
#     #         with open(file_path, 'r', encoding='utf-8') as f:
#     #             content += f.read() + "\n\n"  # Add double newline for separation
#     #     except FileNotFoundError:
#     #         print(f"File not found: {file_path}")
#     #     except Exception as e:
#     #         print(f"Error reading {file_path}: {e}")
#     # return content
#     content = ""
#     for root, _, files in os.walk('./generated_pages'):
#         for file in files:
#             if file.endswith('.json'):
#                 md_path = os.path.join(root, file)
                
#                 # .mdファイルを読み込む
#                 with open(md_path, 'r', encoding='utf-8') as f:
#                     l = json.loads(f.read())
#                     markdown_text = json.dumps(l,indent=None)  
#                 content += markdown_text + "\n\n"
#         break # only read the first directory
#     return content

red_framework =""
blue_framework = ""

def load_and_flatten_json(framework :str) -> str:
    framework = json.loads(framework)
    framework = list(flatten(flatten(framework)))
    framework = framework[:len(framework) - int(len(framework) / 3.5)]
    framework = ' '.join(framework)
    return framework

def trim_tokens(framework :str) -> str:
    framework =  framework.replace("TA0","TA")
    framework =  framework.replace("(", "")
    framework =  framework.replace(")", "")
    framework = framework.replace(" a "," ")
    framework = framework.replace(" an "," ")
    framework = framework.replace(" / ","/")
    framework = framework.replace(" - ","-")
    framework = framework.replace(".00",".")
    return framework

with open("generated_pages/disarm_red_framework.json", 'r', encoding='utf-8') as f:
    red_framework = f.read()
    red_framework = load_and_flatten_json(red_framework)
    red_framework =  red_framework.replace("T00","T")
    red_framework =  red_framework.replace("T0","T")
    red_framework = trim_tokens(red_framework)


with open("generated_pages/disarm_blue_framework.json", 'r', encoding='utf-8') as f:
    blue_framework = f.read()
    blue_framework = load_and_flatten_json(blue_framework)
    blue_framework =  blue_framework.replace("C00","C")
    blue_framework =  blue_framework.replace("C0","C")
    blue_framework = trim_tokens(blue_framework)


with open("generated_pages/red_framework.txt", 'w', encoding='utf-8') as f:
     f.write(red_framework)

with open("generated_pages/blue_framework.txt", 'w', encoding='utf-8') as f:
     f.write(blue_framework)

# os.exit(0)

def run_assistant(msg :str):
    # Markdownファイルの内容を読み込む
    #md_content = read_md_files()

    # AIアシスタントの設定
    attacker_assistant = autogen.AssistantAgent(
        name="atacker_assistant",
        system_message=f"""{red_framework}\nあなたは偽情報の攻撃者側の視点に立って具体的な戦術(TA1 Plan Strategyなど)を参照し議論を行います。""",
        llm_config=llm_config,
        max_consecutive_auto_reply=5,
    )

    defender_assistant = autogen.AssistantAgent(
        name="defender_assistant",
        system_message=f"""{blue_framework}\nあなたは偽情報の防御者側の視点に立って具体的な戦術(TA1 Plan Strategyなど)を参照し議論を行います。""",
        llm_config=llm_config,
        max_consecutive_auto_reply=5,
    )

     # ユーザプロキシの設定（コード実行やアシスタントへのフィードバック）
    user_proxy = autogen.UserProxyAgent(
        name="user_proxy",
        system_message="偽情報に関する具体的な技術的議論を行います。",
        is_termination_msg=lambda x: x.get("content", "") and x.get("content", "").rstrip().endswith("タスク完了"),
        human_input_mode="NEVER",
        llm_config=llm_config,
        max_consecutive_auto_reply=5,
        code_execution_config={"use_docker": False, "work_dir": "./generated_pages"},
    )
    

    group_chat = autogen.GroupChat(
        agents=[user_proxy, attacker_assistant,defender_assistant], messages=[], max_round=10
    )

    manager = autogen.GroupChatManager(groupchat=group_chat, llm_config=llm_config)

    # タスクの依頼
    c = user_proxy.initiate_chat(manager, message=f"以下のユーザーのメッセージに対して偽情報に関連して議論を行ってください:\n {msg}")

    

    return c

# Botの大元となるオブジェクトを生成する
bot = discord.Bot(
    intents=discord.Intents.all(),
    activity=discord.Game("Disarm Framework"),
)

@bot.event
async def on_ready():
    print("Ready disarm framework bot")

@bot.command(name="discuss", description="discuss")
async def discuss(ctx: discord.ApplicationContext, msg: str):
    await ctx.respond("AIアシスタントがデータを学習分析し、偽情報に関する議論を行います...")
    try:
        c = run_assistant(msg)
    except Exception as e:
        await ctx.respond(f"エラーが発生しました: {e}。もう一度お試しください。")
        return

    color_candidates = [0x00FF00, 0xFF0000, 0x0000FF, 0xFFFF00, 0x00FFFF]
    color_per_person = dict()
    for i,hist in enumerate(c.chat_history):
        name = hist['name']
        if name not in color_per_person:
            color_per_person[name] = color_candidates[i % len(color_candidates)]
    for hist in c.chat_history:
        name = hist['name']
        content = hist['content']
        lines = str(content).split("\n")
        for line in lines:
            while True:
                if len(line) <= 2000:
                    await ctx.send(embed=discord.Embed(title=name, description=line,color=color_per_person[name]))
                    break
                else:
                    await ctx.send(embed=discord.Embed(title=name, description=line[:2000],color=color_per_person[name]))
                    line = line[2000:]


# Botを起動
bot.run(DISCORD_TOKEN)
