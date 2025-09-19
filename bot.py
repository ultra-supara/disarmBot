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
from typing import Any
from ddgs import DDGS
from datetime import datetime
import io



import sys

try:
  bot_ui_lang = sys.argv[1]
except Exception:
  bot_ui_lang = "en" # default to English
 
with open("bot_ui_template.json") as fp:
    bot_ui_message = json.loads(fp.read())
    bot_ui_message = bot_ui_message[bot_ui_lang]

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
    #"stream": True,
}

OAI_CONFIG ={
    "model": MODEL,
    "api_key": API_KEY,
    "api_type": "openai",
    #"stream": True,
}

with open("duckduckgo-locales.json") as fp:
    local_info = json.loads(fp.read())
    local_info = ','.join([x["locale"] for x in local_info])

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
                    Note that this is only a fixed English database, so if you need realtime information, please use searchDuckDuckGo or fetchDirectURL instead
                    This is NOT connected to the internet.
                    """,
                "parameters": {
                    "type": "object",
                    "properties": {
                        "question": {
                            "type": "string",
                            "description": "Query for searching information related to the Disarm Framework. Query must be English. This database is not suitable for asking specific questions, so please search for general information using keywords.",
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
                            "description": f"Region information to search in. default is us-en. candidates are {local_info}",
                        },
                        "page": {
                            "type": "number",
                            "description": "page to return. default is 1. If you want more deeper or specific information, increment pages to deep dive into"
                        },
                        "timelimit": {
                            "type": "string",
                            "description": "time limit for search. candidates are d, w, m, y. default is null. meanings are: d=last day,w=last week,m=last month,y=last year"
                        }
                    },
                    "required": ["query","timelimit"],
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

def searchDisarmFramework(question: str):
    print("DEBUG: searchDisarmFramework ",question,file=sys.stderr)
    if not question.isascii():
        return "only accepts English"
    global collection
    result = collection.query(
        query_texts=[question],
        n_results=5,
    )

    return json.dumps({"question": question, "sources": result["ids"],  "documents": result["documents"]}) # temporary

def searchDuckDuckGo(
    query: str,
    num_results: int = 5,
    page :int = 1,
    region :str = "en-us",
    timelimit :str | None = None,
):
    print("DEBUG: searchDuckDuckGo ",query,num_results,region,page,timelimit,file=sys.stderr)
    with DDGS() as ddgs:
        try:
            results = list(ddgs.text(query, region=region, max_results=num_results,page=page,timelimit=timelimit))
        except Exception as e:
            print(f"DuckDuckGo Search failed: {e}")
            results = []
    return json.dumps({"query": query,"region": region,"timelimit": timelimit,"results": results})

def splitandclear(text :str):
   return [x.strip() for x in text.splitlines() if x.strip() != '']

async def fetchDirectURL(url: str):
     print("DEBUG: fetchDirectURL ",url,file=sys.stderr)
     async with aiohttp.ClientSession() as session:
         async with session.get(url,timeout=aiohttp.ClientTimeout(total=10),allow_redirects=True) as response:
             content = await response.text()
             soup = bs4.BeautifulSoup(io.StringIO(content), "html.parser")
             try:
                 text = str(soup.findChild("body").get_text())
             except Exception as e:
                 print("DEBUG: get html body error ",e,file=sys.stderr)
                 text = str(soup.findChild("html").get_text())
             content = '\n'.join(splitandclear(text))
             return f"fetch from: {url}\n###CONTENT BEGIN###\n{content}\n###CONTENT END###\n"
func_list = {
    "searchDisarmFramework": searchDisarmFramework,
    "searchDuckDuckGo": searchDuckDuckGo,
    "fetchDirectURL": fetchDirectURL,
}
assistantQueries = [
    {
        "name": "Detective",
        "prompt": f"You are an detective. you have to deep dive into what is the user's actual wants to know. guess the context of users question with 5W1H(What,When,Where,Why,Who,How) to make more searchable on the internet. Please also dig deeper into the subtle nuances of the question phrase. Consider that the phrase of the question may be common sense in this way, but this way of asking this question may be a different intent. Answer MUST be related to DISARM framework described as below. In DISARM framework, there are no recent information. so if you need recent information, use the internet\n#### README.md\n {readMe}",
        "function": func_list
    },
    {
        "name": "searchTheInternet",
        "prompt": "You are an Internet search expert. Your role is to introduce outside information and stimulate discussion. You must use the DuckDuckGo search tool to search the Internet and may follow the link by fetchDirectURL. use the internet power. Choose the best region for the information you are looking for",
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
        "prompt": "You are a skeptic. Your role is to act as devil's advocate and provide a critical perspective on what other agents say. Also look critically at what they don't say and mention it. Use the `searchDisarmFramework` function and DuckDuckGo search tool to search for what other agents say and may follow the link by fetchDirectURL and ask your skeptical questions.",
        "function": func_list
    },
    {
        "name": "SolutionArchitects",
        "prompt": "You are a solution architect. Your role is to provide a solution to the problem using expert's information. Your role is providing an answer, not a question. Use the `searchDisarmFramework` functions and DuckDuckGo search tool and may follow the link by fetchDirectURL to provide a solution.",
        "function": func_list
    },
    {
        "name": "Clown",
        "prompt": "You are a clown. So what? you can say anything non related or you should questions to expert in simple perspective. Your role is questioning, not answering",
        "function": func_list
    },
    {
        "name": "TheGeniusOfReasoning",
        "prompt": "Let's have a very detailed inference about existing facts and think clearly about logic that will defeat your opponent. Your are an expert, It's good to be inspired by the comments, but don't play together like clown. Your role is providing a bizarre and insightful opinion.",
        "function": func_list,
    },
]

async def run_assistant(msg :str):

    # AIアシスタントの設定
    assistants = []
    for query in assistantQueries:
        assistant = autogen.AssistantAgent(
            name=query["name"],
            system_message="Before you talk, you must say your role. Remind your role. it is not good to use tools if your role not required it. DO NOT VIOLATE YOUR ROLE. Note that for realtime information, use the internet proior to searchDisarmFramework. searchDisarmFramework function only accepts English keywords, not general question. so pass the keyword in English. But answer must follow the language user asked.\n" + query["prompt"],
            llm_config=llm_config,
            max_consecutive_auto_reply=5,
        )
        assistants.append(assistant)
        if "function" in query:
            assistant.register_function(query["function"])

    # ユーザプロキシの設定（コード実行やアシスタントへのフィードバック）
    user_proxy = autogen.UserProxyAgent(
        name="user_proxy",
        system_message= "Remind your role. Answer must follow the language user asked. You are moderator. Summarize the discussion and provide feedback to the assistants. Organize critically whether it matches the user's question  and provide feedback to the assistants.",
        is_termination_msg=lambda x: x.get("content", "") and x.get("content", "").rstrip().endswith("task complete"),
        human_input_mode="NEVER",
        llm_config=llm_config,
        max_consecutive_auto_reply=5,
    )

    # Register DuckDuckGo search tool for execution
    user_proxy.register_function(func_list)

    last_messages = []

    def select_speaker(
        last_speaker: autogen.Agent, groupchat: autogen.GroupChat
    ):
        print("DEBUG:",len(groupchat.messages),file=sys.stderr)
        removal = []
        for (i,msg) in enumerate(groupchat.messages):
            if msg.get("tool_responses"):
                if str(msg["content"]).lower().startswith("error"):
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
    manager_llm_config =llm_config
    manager = autogen.GroupChatManager(groupchat=group_chat, llm_config=manager_llm_config)

    # タスクの依頼
    now = datetime.now()
    try:
        c = await user_proxy.a_initiate_chat(
            manager,
            message=f"Please respond to the following user's question as a group of experts in disinformation countermeasures. User questions are only one-off, so please do not leave the conclusion to the other party if you ask for a reply.\n########\nUser's question\n{msg}\n########\nAnswer in language user asked. Now is {now}",
        )
    except Exception as e:
        print(f"Error occured {e}, respond first",file=sys.stderr)
        return (last_messages,e)

    return (last_messages,None)



# Botの大元となるオブジェクトを生成する
bot = discord.Bot(
    intents=discord.Intents.all(),
    activity=discord.Game("Disarm Framework"),
)

@bot.event
async def on_ready():
    print("Ready disarm framework bot")

@bot.command(name="discuss", description="start agents discussion with query")
async def discuss(ctx: discord.ApplicationContext, query: str):
    try:
        await ctx.respond(bot_ui_message["ACCEPT_MESSAGE"])
        th = await ctx.send(bot_ui_message["RECORD_THREAD_TITLE"])
        channel = await th.create_thread(name=bot_ui_message["RECORD_THREAD_TITLE"])
        (last_messages,exc) = await run_assistant(query)
        color_candidates = [0x00FF00, 0xFF0000, 0x0000FF, 0xFFFF00, 0x00FFFF]
        color_per_person = dict()
        for i,hist in enumerate(last_messages):
            name = hist.get("name","unknown")
            if name not in color_per_person:
                color_per_person[name] = color_candidates[i % len(color_candidates)]
            content = hist.get("content","")
            lines = splitandclear(content)
            if str(lines[0]).strip().startswith("fetch from:") if len(lines) != 0 else False:
                lines[0] = str(lines[0]).replace("fetch from",bot_ui_message["DIRECT_FETCH"],1)
                lines = [lines[0]]
            try:
                result = ""
                for line in lines:
                        print("DEBUG: ",line,file=sys.stderr)
                        line = json.loads(line)
                        print("DEBUG: json ",line,file=sys.stderr)
                        try:
                            if line.get("query"):
                                query = line.get("query")
                                region = line.get("region")
                                timelimit = line.get("timelimit")
                                # internet search result
                                internet_result_msg = bot_ui_message["INTERNET_SEARCH_RESULT"]
                                result += f"{internet_result_msg}\nSearch: {query} (region: {region} time limit: {timelimit})\nResults:\n"
                                for news in line.get("results"):
                                    title = news["title"]
                                    href = news["href"]
                                    body = news["body"]
                                    result += f"### [{title}]({href})\n{body}\n"
                            else:
                                question = line["question"]
                                line = flatten(line["sources"])
                                line = "\n".join(line)
                                disarm_result_msg = bot_ui_message["DISARM_SEARCH_RESULT"]
                                result += f"{disarm_result_msg}\nSearch: {question}\n{line}"
                        except Exception as e:
                            result += f"Error: {e}, line skipped\n"
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
        if exc is not None:
            raise exc
        await ctx.send(bot_ui_message["END_MESSAGE"])
    except Exception as e:
        print(e)
        print(traceback.format_exc())
        print(f"Error: {e}\n",traceback.format_exc(),file=sys.stderr)
        msg = str(bot_ui_message["ERROR_MESSAGE"])
        msg = msg.replace("{error}",str(e))
        await ctx.respond(msg)
        return

# Botを起動
bot.run(DISCORD_TOKEN)
