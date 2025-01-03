import autogen
import discord
import os
import json
from more_itertools import flatten
import chromadb as cdb
client = cdb.Client()

with open("./generated_pages/README.md") as f:
    readMe = f.read()

collection = client.create_collection("disarm-framework")


for dirpath,dirnames,files in os.walk("./generated_pages"):
    for file in files:
        try:
            print(f"adding {dirpath}/{file}")
            with open(f"{dirpath}/{file}", 'r', encoding='utf-8') as f:
                content = f.read()
                collection.add(
                    documents=[content],
                    metadatas=[{"source": dirpath}],
                    ids=[file],
                )
        except Exception as e:
            print(e)
            continue



API_KEY = os.getenv("OPENAI_API_KEY")
DISCORD_TOKEN = os.getenv("DISCORD_TOKEN")
BASE_URL = os.getenv("BASE_URL")
DEPLOYMENT=os.getenv("DEPLOYMENT")
MODEL=os.getenv("MODEL")
VERSION=os.getenv("VERSION")

# LLMコンフィグ設定
llm_config = {
    "config_list": [
        {
            "model": MODEL,
            "azure_deployment": DEPLOYMENT,
            "base_url": BASE_URL,
            "api_key": API_KEY,
            "api_type": "azure",
            "api_version": VERSION,
        }
    ],
    "stream": True,
}

def searchDisarmFramework(query: str):
    global collection
    result = collection.query(
        query_texts=[query],
        top_k_retriever=5,
        n_results=5,
    )

    return result["documents"][0][0] # temporary

autogen.register_function(searchDisarmFramework)

def omit():
    red_framework =""
    blue_framework = ""

    def load_and_flatten_json(framework :str) -> str:
        framework = json.loads(framework)
        framework = list(flatten(flatten(framework)))
        #framework = framework[:len(framework) - int(len(framework) / 3.5)]
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

assistantQueries = [
    {
        "name": "searchDisarmFramework",
        "prompt": f"以下のREADME.mdの内容を元にクエリを生成しseachDisarmFramework関数で検索をして要約してください\n#### README.md\n {readMe}",
    },
    {
        "name": "attackers",
        "prompt": "あなたは偽情報を使う攻撃者の専門家です。searchDisarmFramework関数を使ってred_frameworkに関連する戦略/戦術を検索し、それについて議論してください"
    },
    {
        "name": "defenders",
        "prompt": "あなたは偽情報を防ぐ防御者の専門家です。searchDisarmFramework関数を使ってblue_frameworkに関連する戦略/戦術を検索し、それについて議論してください"
    },
    {
        "name": "Skeptics",
        "prompt": "あなたは懐疑論者です。あなたの役目は悪魔の代弁者であり他のエージェントの発言に対する批判的視点を提供することです。他のエージェントの発言について懐疑的な質問を述べてください"
    }
]

async def run_assistant(msg :str):
    # Markdownファイルの内容を読み込む
    #md_content = read_md_files()

    # AIアシスタントの設定
    assistants = []
    for query in assistantQueries:
        assistant = autogen.AssistantAgent(
            name=query["name"],
            system_message=query["prompt"],
            llm_config=llm_config,
            max_consecutive_auto_reply=5,
        )
        assistants.append(assistant)

    # ユーザプロキシの設定（コード実行やアシスタントへのフィードバック）
    user_proxy = autogen.UserProxyAgent(
        name="user_proxy",
        system_message="偽情報に関する具体的な攻撃及び防御の戦術/技術的議論のみに着目してChat中で言及された具体的な戦略/戦術とそのコードを用いてStep by Stepでまとめてください",
        is_termination_msg=lambda x: x.get("content", "") and x.get("content", "").rstrip().endswith("タスク完了"),
        human_input_mode="NEVER",
        llm_config=llm_config,
        max_consecutive_auto_reply=5,
        
        # code_execution_config={"use_docker": False, "work_dir": "./generated_pages"},
    )


    group_chat = autogen.GroupChat(
        agents=[user_proxy]+assistants,
        messages=[], max_round=10,
        speaker_selection_method="round_robin",        
    )

    manager = autogen.GroupChatManager(groupchat=group_chat, llm_config=llm_config)

    # タスクの依頼
    c = await user_proxy.a_initiate_chat(
        manager,
        message=f"以下のユーザーからの質問に対して偽情報対策のエキスパート集団として回答をしてください\n {msg}"
    )

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
    try:
        await ctx.respond("AIアシスタントがデータを学習分析し、偽情報に関する議論を行います...")
        th = await ctx.send("disarmBot 議事録")
        channel = await th.create_thread(name="disarmBot 議事録")
        c = await run_assistant(msg)
        color_candidates = [0x00FF00, 0xFF0000, 0x0000FF, 0xFFFF00, 0x00FFFF]
        color_per_person = dict()        
        for i,hist in enumerate(c.chat_history):
            name = hist['name']
            if name not in color_per_person:
                color_per_person[name] = color_candidates[i % len(color_candidates)]
            content = hist['content']
            lines = str(content).split("\n")

            for line in lines:
                if line == "":
                    continue
                while True:
                    if len(line) <= 2000:
                        await channel.send(embed=discord.Embed(title=name, description=line,color=color_per_person[name]))
                        break
                    else:
                        await channel.send(embed=discord.Embed(title=name, description=line[:2000],color=color_per_person[name]))
                        line = line[2000:]
    except Exception as e:
        print(e)
        await ctx.respond(f"エラーが発生しました: {e}。もう一度お試しください。")
        return

# Botを起動
bot.run(DISCORD_TOKEN)
