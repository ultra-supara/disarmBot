import autogen
import discord
import os
import json
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

def run_assistant(msg :str):
    # Markdownファイルの内容を読み込む
    #md_content = read_md_files()

    # AIアシスタントの設定
    attacker_assistant_1 = autogen.AssistantAgent(
        name="attacker_assistant_1",
        system_message=f"""事実のみを述べてください\n\nRed Framework\n{red_framework}\n\nあなたは前の発言者の提示したコードに関連する(MUST)英語の攻撃の戦略/戦術について更に具体的に補足を行ってください。TA1からTA18の戦略もしくはTで始まり数値が続くコードの戦術を参照すること。""",
        llm_config=llm_config,
        max_consecutive_auto_reply=5,
    )

    attacker_assistant_2 = autogen.AssistantAgent(
        name="attacker_assistant_2",
        system_message=f"""事実のみを述べてください\n\nRed Framework\n{red_framework}\n\nあなたは偽情報の攻撃者役として具体的な戦略/戦術を必ず(MUST)複数参照し議論を行います。TA1からTA18の戦略もしくはTで始まり数値が続くコードの戦術を参照すること。""",
        llm_config=llm_config,
        max_consecutive_auto_reply=5,
    )

    defender_assistant_1 = autogen.AssistantAgent(
        name="defender_assistant_1",
        system_message=f"""事実のみを述べてください\n\nBlue Framework\n{blue_framework}\n\nあなたは前の発言者の提示したコードに関連する(MUST)英語の防御の戦略/戦術について更に具体的に補足を行ってください。TA1からTA18の戦略もしくはCで始まり数値が続くコードの戦術を参照すること。""",
        llm_config=llm_config,
        max_consecutive_auto_reply=5,
    )

    defender_assistant_2 = autogen.AssistantAgent(
        name="defender_assistant_2",
        system_message=f"""事実のみを述べてください\n\nBlue Framework\n{blue_framework}\n\nあなたは偽情報の防御者役として具体的な戦略/戦術を必ず(MUST)複数参照し議論を行います。攻撃者に対して倫理面の問題ではなく具体的な技術的戦略/戦術で対抗してください。TA1からTA18の戦略もしくはCで始まり数値が続くコードの戦術を参照すること。""",
        llm_config=llm_config,
        max_consecutive_auto_reply=5,
    )

    # ユーザプロキシの設定（コード実行やアシスタントへのフィードバック）
    user_proxy = autogen.UserProxyAgent(
        name="user_proxy",
        system_message="事実のみを述べてください\n\n偽情報に関する具体的な攻撃及び防御の戦術/技術的議論のみに着目してChat中で言及された具体的な戦略/戦術とそのコードを用いてまとめてください",
        is_termination_msg=lambda x: x.get("content", "") and x.get("content", "").rstrip().endswith("タスク完了"),
        human_input_mode="NEVER",
        llm_config=llm_config,
        max_consecutive_auto_reply=5,
        code_execution_config={"use_docker": False, "work_dir": "./generated_pages"},
    )


    group_chat = autogen.GroupChat(
        agents=[user_proxy,attacker_assistant_2, attacker_assistant_1,defender_assistant_2,defender_assistant_1], messages=[], max_round=10,
        speaker_selection_method="round_robin"
    )

    manager = autogen.GroupChatManager(groupchat=group_chat, llm_config=llm_config)

    # タスクの依頼
    c = user_proxy.initiate_chat(manager, message=f"以下のユーザーのメッセージに対して偽情報に関して提供されたコンテキストのみに基づき具体的な戦術/技術的対話を行ってください。:\n {msg}")

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
            if line == "":
                continue
            while True:
                if len(line) <= 2000:
                    await ctx.send(embed=discord.Embed(title=name, description=line,color=color_per_person[name]))
                    break
                else:
                    await ctx.send(embed=discord.Embed(title=name, description=line[:2000],color=color_per_person[name]))
                    line = line[2000:]

# Botを起動
bot.run(DISCORD_TOKEN)
