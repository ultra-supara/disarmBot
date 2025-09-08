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
from typing import Any
from duckduckgo_search import DDGS
from datetime import datetime



import sys
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
llm_config = autogen.LLMConfig(
    config_list = [
        config
    ],
    tools = [
        {
            "type": "function",
            "function": {
                "name": "searchDisarmFramework",
                "description": """
                    Search in the DISARM Disinformation TTP (Tactics, Techniques and Procedures) Framework
                    DISARM is a framework designed for describing and understanding disinformation incidents.
                    DISARM is part of work on adapting information security (infosec) practices to help track and counter disinformation and other information harms,
                    and is designed to fit existing infosec practices and tools.
                    Note that this is only a fixed English database, so if you need realtime information, please use searchDuckduckgo or fetchDirectURL instead
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
        {
            "type": "function",
            "function": {
                "name": "searchDuckDuckGo",
                "description": """
                    Search the internet with duckduckgo
                    use region parameter to search accurate information for user region
                    """,
                "parameters": {
                    "type": "object",
                    "properties": {
                        "query": {
                            "type": "string",
                            "description": "Query for searching information",
                        },
                        "num_results": {
                            "type": "number",
                            "description": "Number of search results. default is 5",
                        }
                        ,     
                        "region": {
                            "type": "string",
                            "description": "Region information to search in. default is en-us",
                        }
                    },
                    "required": ["query"],
                },
            }
        },
         {
            "type": "function",
            "function": {
                "name": "fetchDirectURL",
                "description": """
                    Fetch content directly from URL. 
                    You may use this after duckduckgo search
                    """,
                "parameters": {
                    "type": "object",
                    "properties": {
                        "url": {
                            "type": "string",
                            "description": "URL to fetch",
                        }
                    },
                    "required": ["url"],
                },
            }
        },
    ],
)

# Initialize DuckDuckGo search tool
duckduckgo_search_tool = DuckDuckGoSearchTool()
def searchDisarmFramework(question: str):
    print("DEBUG: searchDisarmFramework ",question,file=sys.stderr)
    global collection
    result = collection.query(
        query_texts=[question],
        n_results=5,
    )

    return json.dumps({"sources": result["ids"],  "documents": result["documents"]}) # temporary

def searchDuckduckgo(
    query: str,
    num_results: int = 5,
    region :str = "en-us"
):
    print("DEBUG: searchDuckduckgo ",query,num_results,region,file=sys.stderr)
    with DDGS() as ddgs:
        try:
            # region='wt-wt' means worldwide
            results = list(ddgs.text(query, region=region, max_results=num_results))
        except Exception as e:
            print(f"DuckDuckGo Search failed: {e}")
            results = []
    return json.dumps({"query": query,"results": results})

def splitandclear(text :str):
   return [x.strip() for x in text.splitlines() if x.strip() != '']

async def fetchDirectURL(url: str):
     print("DEBUG: fetchDirectURL ",url,file=sys.stderr)
     async with aiohttp.ClientSession() as session:
         async with session.get(url,timeout=aiohttp.ClientTimeout(total=10)) as response:
             content = await response.text()
             soup = bs4.BeautifulSoup(content, "html.parser")
             text = str(soup.findChild("body").get_text())
             content = '\n'.join(splitandclear(text))
             return f"fetch from: {url}\n###CONTENT BEGIN###\n{content}\n###CONTENT END###\n"
func_list = {
    "searchDisarmFramework": searchDisarmFramework,
    "searchDuckDuckGo": searchDuckduckgo,
    "fetchDirectURL": fetchDirectURL,
}
assistantQueries = [
    {
        "name": "Detective",
        "prompt": f"You are an detective. you have to deep dive into what is the user's actual wants to know. guess the context of users question with 5W1H(What,When,Where,Why,Who,How) to make more searchable on the internet. answer MUST be related to DISARM framework described as below\n#### README.md\n {readMe}",
        "function": func_list
    },
    {
        "name": "searchTheInternet",
        "prompt": "You are an Internet search expert. Your role is to introduce outside information and stimulate discussion. You must use the DuckDuckGo search tool to search the Internet and may follow the link by fetchDirectURL. Consider the fact that searches don't work with keywords that are too common",
        "function": func_list
    },
    {
        "name": "searchDisarmFramework",
        "prompt": f"You are information search expert. Please generate a query based on the contents of the README.md below and user query, search using the searchDisarmFramework function, and summarize it.\n#### README.md\n {readMe}",
        "function": func_list
    },
    {
        "name": "Attackers",
        "prompt": "You are an expert in disinformation attacks. Your role is to use your expertise in disinformation attacks to find vulnerabilities in the case. Use the `searchDisarmFramework` function and DuckDuckGo search tool to search for strategies/tactics related to the red framework and may follow the link by fetchDirectURL and discuss them.",
        "function": func_list
    },
    {
        "name": "Defenders",
        "prompt": "You are a disinformation countermeasure/defense expert. It is your role to use your expertise on the disinformation defense side to think about responses to the vulnerabilities in the case. Use the `searchDisarmFramework` function and DuckDuckGo search tool to search for strategies/tactics related to blue framework and may follow the link by fetchDirectURL and discuss them.",
        "function": func_list
    },
    {
        "name": "Skeptics",
        "prompt": "You are a skeptic. Your role is to act as devil's advocate and provide a critical perspective on what other agents say. Use the `searchDisarmFramework` function and DuckDuckGo search tool to search for what other agents say and may follow the link by fetchDirectURL and ask your skeptical questions.",
        "function": func_list
    },
    {
        "name": "SolutionArchitects",
        "prompt": "You are a solution architect. Your role is to provide a solution to the problem using expert's information. Your role is providing an answer, not a question. Use the `searchDisarmFramework` functions and DuckDuckGo search tool and may follow the link by fetchDirectURL to provide a solution.",
        "function": func_list
    },
    {
        "name": "OrdinalyPerson",
        "prompt": "You are an ordinaly person. So what? you can say anything non related or you should questions to expert in simple perspective. Your role is questioning, not answering",
        "function": func_list
    },
    {
        "name": "TheGeniusOfReasoning",
        "prompt": "Let's have a very detailed inference about existing facts and think clearly about logic that will defeat your opponent.",
        "function": func_list,
    },
]

async def run_assistant(msg :str):

    # AIアシスタントの設定
    assistants = []
    for query in assistantQueries:
        assistant = autogen.AssistantAgent(
            name=query["name"],
            system_message="Before you talk, you must say your role. Remind your role. it is not good to use tools if your role not required it. DO NOT VIOLATE YOUR ROLE\n" + query["prompt"],
            llm_config=llm_config,
            max_consecutive_auto_reply=5,
        )
        assistants.append(assistant)
        if "function" in query:
            assistant.register_function(query["function"])

        # Register DuckDuckGo search tool for agents that need internet search
        #if query["name"] in ["searchTheInternet", "Attackers", "Defenders", "Skeptics", "SolutionArchitects"]:
        #    duckduckgo_search_tool.register_for_llm(assistant)

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

    last_messages = []

    def select_speaker(
        last_speaker: autogen.Agent, groupchat: autogen.GroupChat
    ):
        print("DEBUG:",len(groupchat.messages),file=sys.stderr)
        removal = []
        for (i,msg) in enumerate(groupchat.messages):
            if msg.get("tool_responses"):
                if "error" in str(msg["content"]).lower():
                    removal.append(i-1)
                    removal.append(i)
                    print("DEBUG: removing ",msg,groupchat.messages[i-1],file=sys.stderr)
        groupchat.messages = [x for (i,x) in enumerate(groupchat.messages) if i not in removal]


        next_agent = None
        for (i,cand) in enumerate(assistantQueries):
            if cand["name"] == last_speaker.name:
                next_agent = groupchat.agents[(i + 1) % len(groupchat.agents)]
                print("Selected: ",next_agent.name,file=sys.stderr)
                break
        if next_agent is None:
            next_agent = groupchat.agents[0]
        nonlocal last_messages
        last_messages = groupchat.messages
        return next_agent

    group_chat = autogen.GroupChat(
        agents=assistants + [user_proxy],
        messages=[], max_round=30,
        speaker_selection_method=select_speaker,
    )

    # GroupChatManager用の設定（toolsを除く）
    manager_llm_config = {
        "config_list": llm_config["config_list"]
    }
    manager = autogen.GroupChatManager(groupchat=group_chat, llm_config=manager_llm_config)

    # タスクの依頼
    now = datetime.now()
    c = await user_proxy.a_initiate_chat(
        manager,
        message=f"Please respond to the following user's question as a group of experts in disinformation countermeasures. User questions are only one-off, so please do not leave the conclusion to the other party if you ask for a reply.\n########\nUser's question\n{msg}\n########\nAnswer in language user asked. Now is {now}",
    )

    return (c,last_messages)

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
        (c,last_messages) = await run_assistant(msg)
        color_candidates = [0x00FF00, 0xFF0000, 0x0000FF, 0xFFFF00, 0x00FFFF]
        color_per_person = dict()
        for i,hist in enumerate(last_messages):
            name = hist.get("name","unknown")
            if name not in color_per_person:
                color_per_person[name] = color_candidates[i % len(color_candidates)]
            content = hist.get("content","")
            role = hist['role']
            lines = splitandclear(content)
            if str(lines[0]).startswith("fetch from:") if len(lines) != 0 else False:
                lines = [lines[0]]
            try:
                result = ""
                for line in lines:
                    print("DEBUG: ",line,file=sys.stderr)
                    line = json.loads(line)
                    print("DEBUG: json ",line,file=sys.stderr)
                    if line.get("query"):
                        query = line.get("query")
                        # internet search result
                        result += f"Search: {query}\nResults:\n"
                        for news in line.get("results"):
                            title = news["title"]
                            href = news["href"]
                            body = news["body"]
                            result += f"### [{title}]({href})\n{body}\n"
                    else:
                        line = flatten(line["sources"])
                        line = "\n".join(line)
                        result += f"Information was retrieved from the following sources\n{line}"
                lines = result.splitlines()
            except Exception as e:
                print(e,"non json, only a text",file=sys.stderr)


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
