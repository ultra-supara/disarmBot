import autogen
import discord
import os

API_KEY = os.getenv("OPENAI_API_KEY")
DISCORD_TOKEN = os.getenv("DISCORD_TOKEN")

# LLMコンフィグ設定
llm_config = {
    "config_list": [
        {
            "model": "gpt-35-turbo",
            "base_url": "https://ai-ai.openai.azure.com/",
            "api_key": API_KEY,
            "api_type": "azure",
            "api_version": "2024-05-01-preview",
        }
    ],
}

def run_assistant():
    # AIアシスタントの設定
    assistant = autogen.AssistantAgent(
        name="assistant",
        system_message="""タスクを解く際、提供された関数に役立つものがある場合、それ利用して下さい。
            最終的な解答を提示した後は「タスク完了」というメッセージを出力してください。""",
        llm_config=llm_config,
        max_consecutive_auto_reply=5,
    )

    # ユーザプロキシの設定（コード実行やアシスタントへのフィードバック）
    user_proxy = autogen.UserProxyAgent(
        name="user_proxy",
        is_termination_msg=lambda x: x.get("content", "") and x.get("content", "").rstrip().endswith("タスク完了"),
        human_input_mode="NEVER",
        # human_input_mode="ALWAYS",
        llm_config=llm_config,
        max_consecutive_auto_reply=5,
        # code_execution_config={"use_docker":False},
        code_execution_config={"use_docker":False, "work_dir": "./generated_pages"},

    )

    # タスクの依頼
    c = user_proxy.initiate_chat(assistant, message="すべてのデータを学習分析し、偽情報に関する議論を行ってください")

    return c

# Botの大元となるオブジェクトを生成する
bot = discord.Bot(
        intents=discord.Intents.all(),  # 全てのインテンツを利用できるようにする
        activity=discord.Game("Disarm Framework"),  # "〇〇をプレイ中"の"〇〇"を設定,
)

@bot.event
async def on_ready():
    # 起動すると、実行したターミナルに"Hello!"と表示される
    print("Ready disarm framework bot")




@bot.command(name="discuss", description="discuss")
async def discuss(ctx: discord.ApplicationContext,msg :str):
    ctx.respond("AIアシスタントがデータを学習分析し、偽情報に関する議論を行います...")
    c = run_assistant()
    text = str(c)
    print(text) 
    lines = text.split("\n")
    # split lines into 2000 characters
    # discord has a limit of 2000 characters per message
    for line in lines:
        while True:
            if len(line) <= 2000:
                await ctx.send(line) 
                break
            else:
                await ctx.send(line[:2000])
                line = line[2000:]



# Botを起動
bot.run(DISCORD_TOKEN)
