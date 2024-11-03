import autogen
import discord
import os
import json

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

def load_md_files_from_json(json_file_path):
    """JSONファイルからMarkdownファイルのリストを読み込む"""
    try:
        with open(json_file_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
            return data.get("md_files", [])
    except FileNotFoundError:
        print(f"JSON file not found: {json_file_path}")
        return []
    except json.JSONDecodeError:
        print(f"Error decoding JSON from file: {json_file_path}")
        return []

def read_md_files(md_files):
    """Markdownファイルの内容を読み込む"""
    content = ""
    for md_file in md_files:
        file_path = os.path.join("./generated_pages", md_file)
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content += f.read() + "\n\n"  # Add double newline for separation
        except FileNotFoundError:
            print(f"File not found: {file_path}")
        except Exception as e:
            print(f"Error reading {file_path}: {e}")
    return content

def run_assistant():
    # JSONファイルからMarkdownファイルのリストを取得
    json_file_path = os.path.join("./generated_pages", "md_files.json")  # JSONファイルのパスを指定
    md_files = load_md_files_from_json(json_file_path)

    # Markdownファイルの内容を読み込む
    md_content = read_md_files(md_files)

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
        llm_config=llm_config,
        max_consecutive_auto_reply=5,
        code_execution_config={"use_docker": False, "work_dir": "./generated_pages"},
    )

    # タスクの依頼
    c = user_proxy.initiate_chat(assistant, message=f"{md_content} すべてのデータを学習分析し、偽情報に関する議論を行ってください")

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
    c = run_assistant()
    for hist in c.chat_history:
        name = hist['name']
        content = hist['content']
        lines = str(content).split("\n")
        for line in lines:
            while True:
                if len(line) <= 2000:
                    await ctx.send(embed=discord.Embed(title=name, description=line))
                    break
                else:
                    await ctx.send(embed=discord.Embed(title=name, description=line[:2000]))
                    line = line[2000:]
        await ctx.send(embed=discord.Embed(title=name, description=content))
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
