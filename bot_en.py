import autogen
import discord
import os
import json
from more_itertools import flatten
import aiohttp
import bs4
import traceback
import chromadb as cdb
import pathlib as pl
from dotenv import load_dotenv
from autogen.tools.experimental import DuckDuckGoSearchTool

# Load environment variables from .env file
load_dotenv()

exists = pl.Path("./chroma_db").exists()
client = cdb.PersistentClient("./chroma_db")

with open("./generated_pages/README.md") as f:
    readMe = f.read()

collection = client.get_or_create_collection("disarm_framework")

if not exists:
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
API_TYPE=os.getenv("API_TYPE")

AZURE_CONFIG = {
    "model": MODEL,
    "azure_deployment": DEPLOYMENT,
    "base_url": BASE_URL,
    "api_key": API_KEY,
    "api_type": "azure",
    "api_version": VERSION,
    "stream": True,
}

OAI_CONFIG ={
    "model": MODEL,
    "api_key": API_KEY,
    "api_type": "openai",
    "stream": True,
}

if API_TYPE == "azure":
    config = AZURE_CONFIG
elif API_TYPE == "openai":
    config = OAI_CONFIG
else:
    raise ValueError("API_TYPE must be either azure or openai")

# LLMコンフィグ設定
llm_config = {
    "config_list": [
        config
    ],
    "tools": [
        {
            "type": "function",
            "function": {
                "name": "searchDisarmFramework",
                "description": """
                    Search in the DISARM Disinformation TTP (Tactics, Techniques and Procedures) Framework
                    DISARM is a framework designed for describing and understanding disinformation incidents.
                    DISARM is part of work on adapting information security (infosec) practices to help track and counter disinformation and other information harms,
                    and is designed to fit existing infosec practices and tools.
                    """,
                "parameters": {
                    "type": "object",
                    "properties": {
                        "question": {
                            "type": "string",
                            "description": "Query for searching information related to the Disarm Framework",
                        }
                    },
                    "required": ["question"],
                },
            }
        },
    ],
}

# Initialize DuckDuckGo search tool
duckduckgo_search_tool = DuckDuckGoSearchTool()

def searchDisarmFramework(question: str):
    global collection
    result = collection.query(
        query_texts=[question],
        n_results=5,
    )

    return json.dumps({"sources": result["ids"],  "documents": result["documents"]}) # temporary

async def searchTheInternet(url: str):
    async with aiohttp.ClientSession() as session:
        async with session.get(url,timeout=aiohttp.ClientTimeout(total=10)) as response:
            content = await response.text()
            soup = bs4.BeautifulSoup(content, "html.parser")
            text = soup.findChild("body").get_text()
            return text

assistantQueries = [
    {
        "name": "searchDisarmFramework",
        "prompt": f"You are information search expert. Please generate a query based on the contents of the README.md below and user query, search using the searchDisarmFramework function, and summarize it.\n#### README.md\n {readMe}",
        "function": {
            "searchDisarmFramework": searchDisarmFramework
        }
    },
    {
        "name": "searchTheInternet",
        "prompt": "You are an Internet search expert. Your role is to introduce outside information and stimulate discussion. You must use the DuckDuckGo search tool to search the Internet and summarize the information.",
        "function": {}
    },
    {
        "name": "Attackers",
        "prompt": "You are an expert in disinformation attacks. Your role is to use your expertise in disinformation attacks to find vulnerabilities in the case. Use the `searchDisarmFramework` function and DuckDuckGo search tool to search for strategies/tactics related to the red framework and discuss them.",
        "function": {
            "searchDisarmFramework": searchDisarmFramework
        }
    },
    {
        "name": "Defenders",
        "prompt": "You are a disinformation countermeasure/defense expert. It is your role to use your expertise on the disinformation defense side to think about responses to the vulnerabilities in the case. Use the `searchDisarmFramework` function and DuckDuckGo search tool to search for strategies/tactics related to blue framework and discuss them.",
        "function": {
            "searchDisarmFramework": searchDisarmFramework
        }
    },
    {
        "name": "Skeptics",
        "prompt": "You are a skeptic. Your role is to act as devil's advocate and provide a critical perspective on what other agents say. Use the `searchDisarmFramework` function and DuckDuckGo search tool to search for what other agents say and ask your skeptical questions.",
        "function": {
            "searchDisarmFramework": searchDisarmFramework
        }
    },
    {
        "name": "SolutionArchitects",
        "prompt": "You are a solution architect. Your role is to provide a solution to the problem using expert's information. Use the `searchDisarmFramework` functions and DuckDuckGo search tool to provide a solution.",
        "function": {
            "searchDisarmFramework": searchDisarmFramework
        }
    },
]

async def run_assistant(msg :str):

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
        if "function" in query:
            assistant.register_function(query["function"])

        # Register DuckDuckGo search tool for agents that need internet search
        if query["name"] in ["searchTheInternet", "Attackers", "Defenders", "Skeptics", "SolutionArchitects"]:
            duckduckgo_search_tool.register_for_llm(assistant)

    # ユーザプロキシの設定（コード実行やアシスタントへのフィードバック）
    user_proxy = autogen.UserProxyAgent(
        name="user_proxy",
        system_message="You are moderator. Summarize the discussion and provide feedback to the assistants in English. Organize whether it matches the user's question and provide feedback to the assistants.",
        is_termination_msg=lambda x: x.get("content", "") and x.get("content", "").rstrip().endswith("task complete"),
        human_input_mode="NEVER",
        llm_config=llm_config,
        max_consecutive_auto_reply=5,
    )

    # Register DuckDuckGo search tool for execution
    duckduckgo_search_tool.register_for_execution(user_proxy)

    group_chat = autogen.GroupChat(
        agents=assistants + [user_proxy],
        messages=[], max_round=15,
        speaker_selection_method="round_robin", # ラウンドロビン方式で話者を選択
    )

    # GroupChatManager用の設定（toolsを除く）
    manager_llm_config = {
        "config_list": llm_config["config_list"]
    }
    manager = autogen.GroupChatManager(groupchat=group_chat, llm_config=manager_llm_config)

    # タスクの依頼
    c = await user_proxy.a_initiate_chat(
        manager,
        message=f"Please respond to the following user's question as a group of experts in disinformation countermeasures.\n########\nUser's question\n{msg}\n########\n",
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
        await ctx.respond("The AI assistant will learn and analyze the data to engage in a discussion about disinformation...")
        th = await ctx.send("disarmBot Minutes")
        channel = await th.create_thread(name="disarmBot Minutes")
        c = await run_assistant(msg)
        color_candidates = [0x00FF00, 0xFF0000, 0x0000FF, 0xFFFF00, 0x00FFFF]
        color_per_person = dict()
        for i,hist in enumerate(c.chat_history):
            name = hist['name']
            if name not in color_per_person:
                color_per_person[name] = color_candidates[i % len(color_candidates)]
            content = hist['content']
            role = hist['role']
            if role == "function" and name== "searchDisarmFramework":
                content = json.loads(content)
                content = flatten(content["sources"])
                content = "\n".join(content)
                content = f"Information was retrieved from the following sources\n{content}"

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
        await ctx.send("The discussion has concluded.")
    except Exception as e:
        print(e)
        print(traceback.format_exc())

        await ctx.respond(f"An error occurred: {e}. Please try again.")
        return

# Botを起動
bot.run(DISCORD_TOKEN)
