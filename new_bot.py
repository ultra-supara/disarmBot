import autogen
import discord
import os
import json
import aiohttp
import bs4
import traceback
import chromadb as cdb
import pathlib as pl
from dotenv import load_dotenv
from ddgs import DDGS
from datetime import datetime
import io
import jsonschema
import re
import asyncio
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
    locale_info = json.loads(fp.read())
    locale_info = ','.join([x["locale"] for x in locale_info])
print(locale_info)
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
                            "description": f"Region information to search in. default is us-en. candidates are {locale_info}",
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
     try:
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
     except Exception as e:
        return f"fetch from: {url}\n###CONTENT BEGIN###\n{e}\n###CONTENT END###\n"
func_list = {
    "searchDisarmFramework": searchDisarmFramework,
    "searchDuckDuckGo": searchDuckDuckGo,
    "fetchDirectURL": fetchDirectURL,
}

oldAssistant = [ {
        "name": "searchDisarmFramework",
        "prompt": f"You are information search expert. Please generate a query based on the contents of the README.md below and user query, search using the searchDisarmFramework function, and summarize it.\n#### README.md\n {readMe}",
    },
    {
        "name": "Attackers",
        "prompt": "You are an expert in disinformation attacks. Your role is to use your expertise in disinformation attacks to find vulnerabilities in the case. Use the `searchDisarmFramework` function and DuckDuckGo search tool to search for strategies/tactics related to the red framework and may follow the link by fetchDirectURL and discuss them.",
    },
    {
        "name": "Defenders",
        "prompt": "You are a disinformation countermeasure/defense expert. It is your role to use your expertise on the disinformation defense side to think about responses to the vulnerabilities in the case. Use the `searchDisarmFramework` function and DuckDuckGo search tool to search for strategies/tactics related to blue framework and may follow the link by fetchDirectURL and discuss them.",
    },
    {
        "name": "Skeptics",
        "prompt": "You are a skeptic. Your role is to act as devil's advocate and provide a critical perspective on what other agents say. Also look critically at what they don't say and mention it. Use the `searchDisarmFramework` function and DuckDuckGo search tool to search for what other agents say and may follow the link by fetchDirectURL and ask your skeptical questions.",
    },
    {
        "name": "SolutionArchitects",
        "prompt": "You are a solution architect. Your role is to provide a solution to the problem using expert's information. Your role is providing an answer, not a question. Use the `searchDisarmFramework` functions and DuckDuckGo search tool and may follow the link by fetchDirectURL to provide a solution.",
    },
    {
        "name": "Clown",
        "prompt": "You are a clown. So what? you can say anything non related or you should questions to expert in simple perspective. Your role is questioning, not answering",
    },
    {
        "name": "TheGeniusOfReasoning",
        "prompt": "Let's have a very detailed inference about existing facts and think clearly about logic that will defeat your opponent. Your are an expert, It's good to be inspired by the comments, but don't play together like clown. Your role is providing a bizarre and insightful opinion.",
    },]

assistantQueries = {
    "Detective":   {
        "prompt": f"You are a detective. you have to deep dive into what is the user's actual wants to know. guess the context of users question with 5W1H(What,When,Where,Why,Who,How) to make more searchable on the internet. Please also dig deeper into the subtle nuances of the question phrase. Consider that the phrase of the question may be common sense in this way, but this way of asking this question may be a different intent. You haven't been given any specific search skills, but your initial guess is very important for the subsequent internet search. Please do NOT mention about what you cannot do.",
    },
    "Search":{
        "prompt": "You are an Internet search expert. Your role is to introduce outside information and stimulate discussion. You must use the DuckDuckGo search tool to search the Internet and may follow the link by fetchDirectURL. use the internet power. Choose the best region for the information you are looking for. Please exclude information that already in prefetched information.",
    },
    "Summarizer": {
        "prompt": "Your are a content summarizer. Please summarize the content in fact based. Not too long, not too short."
    },
    "Selector": {
        "prompt": "Your role is url candidate selector. Please select urls that related to user requirement. Do not select prefetched informations."
    },
    "Translater": {
        "prompt": "Your role is translate json text into natural plain text. Do not omit the original information but be natural for human reading. You can use markdown for translated content. You can omit meaningless message, like error flags(internally used) and role name. Summarize all in requested language even if each is diffrent language. Please try to use simple and easy-to-understand language (not necessarily avoiding technical terms, but rather focusing on writing in a way that is easy to read)."
    }   
}


for format in  assistantQueries:
    with open(f"agent_response/{format}.json") as fp:
        assistantQueries[format]["schema"]=json.load(fp)


def make_system_prompt(response_format :str,agent_desc :str):
    now = datetime.now()
    return f"Please respond to the following user's question according to your role.\nUser questions are only one-off, so please do not leave the conclusion to the other party.\n########\nResponse format json schema\n{response_format}########\nAnswer in language user asked and in json format schema described. Only json response is needed, no additonal comment nor json schema itself.\nNow is {now}\nBelow is your role description\n{agent_desc}"

def make_user_proxy():
    return autogen.UserProxyAgent(
        name="user_proxy",
        system_message= "Remind your role. Answer must follow the language user asked. You are moderator. Summarize the discussion and provide feedback to the assistants. Organize critically whether it matches the user's question  and provide feedback to the assistants.",
        is_termination_msg=lambda x: x.get("content", "") and x.get("content", "").rstrip().endswith("task complete"),
        human_input_mode="NEVER",
        llm_config={"config_list": llm_config["config_list"]},
        max_consecutive_auto_reply=1,
    )

def make_assistant(name :str, system_prompt :str):
    return autogen.AssistantAgent(
        name=name,
        system_message=system_prompt,
        llm_config={"config_list": llm_config["config_list"]},
        max_consecutive_auto_reply=2,
    )
async def do_action(msg :str,name :str,response_format :str,agent_prompt :str):
    system_prompt = make_system_prompt(response_format,agent_prompt)
    assistant = make_assistant(name,system_prompt)
    user_proxy = make_user_proxy()
    c = await user_proxy.a_initiate_chat(assistant,message=msg)
    print(f"Cost: {dumpjson(c.cost)}",file=sys.stderr)
    return c.chat_history[1]["content"]

async def askAgent(msg :str,name :str):
    schema = assistantQueries[name]["schema"]
    prompt = assistantQueries[name]["prompt"]
    exc = None
    for i in range(3):
        print(f"trial {i}",file=sys.stderr)
        try:
           response = json.loads(await do_action(msg,name,json.dumps(schema),prompt))
           jsonschema.validate(response,schema)
           return response
        except Exception as e:
           print(f"error ocurred: {e}",file=sys.stderr)
           exc = e
    raise exc


def dumpjson(obj,indent="  "):
    return json.dumps(obj,ensure_ascii=False,indent=indent)

url_regex = re.compile(r"https?://[-a-zA-Z0-9@:%._\+~#=]{1,256}\.[a-zA-Z0-9()]{1,6}\b(?:[-a-zA-Z0-9()@:%_\+.~#?&//=]*)")

async def send_progress(resp : asyncio.Queue, agent_name :str,what_to_do: str):
    await resp.put([{"name":agent_name,"content":what_to_do}])

async def run_assistants(msg :str,user_input_queue :asyncio.Queue,response_queue :asyncio.Queue):
    async def search_assistants(msg :str):
        try:
            response = []
            urls = re.findall(url_regex, msg)
            directContent = []
            async def doFetchDirectContet(urls :list[str]):
                nonlocal directContent
                concurrent = asyncio.Queue(5)
                async def fetchURL(q :asyncio.Queue):
                    nonlocal directContent
                    try:
                        while True:
                            i,url = await q.get()
                            content = await fetchDirectURL(url)
                            await send_progress(response_queue,"Summarizer",f"Fetched: {url} ({i}/{len(urls)})")
                            summarized = await askAgent(content,"Summarizer")
                            if summarized["is_error"]:
                                await send_progress(response_queue,"Summarizer",f"Error detected, ignore: {url} ({i}/{len(urls)})")
                                return
                            await send_progress(response_queue,"Summarizer",f"Summaraized: {url} ({i}/{len(urls)})")
                            response.append({"name": "Summarizer","content":summarized})
                            directContent.append(summarized)
                    except asyncio.QueueShutDown:
                        pass
                urlFetcher = []
                for _ in range(5):
                    urlFetcher.append(asyncio.create_task(fetchURL(concurrent)))
                if len(urls) != 0:
                    await send_progress(response_queue,"Summarizer",f"Total {len(urls)} to fetch\n")
                for i,url in enumerate(urls):
                    await concurrent.put((i+1,url))
                    await send_progress(response_queue,"Summarizer",f"Enqueued ({i+1}/{len(urls)})")
                concurrent.shutdown()
                await send_progress(response_queue,"Summarizer","All enqueued, waiting for completion...")
                await asyncio.gather(*urlFetcher)
                await send_progress(response_queue,"Summarizer","All tasks completed")
            if urls:
                await doFetchDirectContet(urls)
            query = dumpjson({
                "user_query": msg,
                "prefetched_resource": directContent
            })
            await send_progress(response_queue,"Detective","Analyzing user queries...")
            userQueryDetected = await askAgent(query,"Detective")
            await send_progress(response_queue,"Detective","User query analysis done.")
            response.append({"name":"Detective","content":userQueryDetected})
            query = json.dumps({
                "answer_lang": userQueryDetected["lang"],
                "about": userQueryDetected["what"],
                "hypothesis": userQueryDetected["why"],
                "want_to_know": userQueryDetected["superficial_guess"],
                "prefetched_information": directContent,
                "keywords": userQueryDetected["keyword"]
            },ensure_ascii=False)
            await send_progress(response_queue,"Search","Generatiing search query...")
            loaded = await askAgent(query,"Search")
            await send_progress(response_queue,"Search","Search query generated. Now searching...")
            response.append({"name":"Search","content":loaded})
            queryResult = []
            for q in loaded["candidates"]:
                await send_progress(response_queue,"Search",f"Searching: {q["query"]} (region: {q["region"]} timelimit: {q["timelimit"]})")
                for p in range(q["page_min"],q["page_max"]+1):
                    result = searchDuckDuckGo(q["query"],q["num_results"],p,q["region"],q["timelimit"])
                    queryResult.append(result)
                    await asyncio.sleep(0.5)
            await send_progress(response_queue,"Search","All search done")
            query = json.dumps({
                "answer_lang": userQueryDetected["lang"],
                "about": userQueryDetected["what"],
                "hypothesis": userQueryDetected["why"],
                "want_to_know": userQueryDetected["superficial_guess"],
                "prefetched_information": directContent,
                "keywords": userQueryDetected["keyword"],
                "candidates": queryResult
            })
            await send_progress(response_queue,"Selector","Selecting fetch candidate...")
            selected = await askAgent(query,"Selector")
            await send_progress(response_queue,"Selector","Candidate selection done")
            await doFetchDirectContet(selected["candidate_urls"])
            query = dumpjson({
               "request_language": userQueryDetected["lang"],
               "translation_target": response
            })
            await send_progress(response_queue,"Translater","Summarizing the conversations...")
            translated_response = await askAgent(query,"Translater")
            fileContent = "Discussion Summery\n"
            for content in translated_response["translated"]:
                fileContent += "# "+ content["name"]+"\n"
                fileContent += content["content"]
                fileContent += "## For five years old\n"
                fileContent += content["five_years_old_content"]
            await response_queue.put([{"file": fileContent,"filename": "summary.txt"}])
        except Exception as e:
            await response_queue.put(e)
    await search_assistants(msg) # first loop
    response_queue.shutdown()



# Botの大元となるオブジェクトを生成する
bot = discord.Bot(
    intents=discord.Intents.all(),
    activity=discord.Game("Disarm Framework"),
)

@bot.event
async def on_ready():
    print("Ready disarm framework bot")

async def print_exception(response :Exception):
    print(response)
    print(traceback.format_exc())
    print(f"Error: {response}\n",traceback.format_exc(),file=sys.stderr)
    msg = str(bot_ui_message["ERROR_MESSAGE"])
    msg = msg.replace("{error}",str(response))
    return msg
# --- 1. 送信内容を受け取るモーダルを定義 ---
# このモーダル自体は、データを渡すだけであり、使い捨てです
class HumanInTheLoopModal(discord.ui.Modal):
    additional_input = discord.ui.InputText(label="additional input", style=discord.InputTextStyle.multiline)

    def __init__(self):
        super().__init__(self.additional_input,title="Human in the Loop",timeout=None)

    # on_submitはinteractionを返すだけで、ここではメッセージを編集しない
    async def on_submit(self, interaction: discord.Interaction):
        await interaction.response.defer() # deferで応答を一旦保留

# --- 2. ボタンを持ち、モーダルを呼び出すViewを定義 ---
class HumanInTheLoopView(discord.ui.View):

    def __init__(self,output_queue :asyncio.Queue):
        super().__init__(timeout=None) # タイムアウトを無効化
        self.output_queue = output_queue

    @discord.ui.button(label="Human in the Loop", style=discord.ButtonStyle.primary)
    async def open_modal_button(self, button: discord.ui.Button, interaction: discord.Interaction):
        try:
            # ボタンが押されたらモーダルを作成
            modal = HumanInTheLoopModal()
            
            # send_modalでモーダルを表示
            await interaction.response.send_modal(modal)
            
            # modal.wait() でユーザーがモーダルを送信するまで待機する
            # これがこのパターンの重要な部分！
            await modal.wait()
            
            # 記録リストに入力内容を追加
            await self.output_queue.put(modal.additional_input.value)
            
            # メッセージを編集して、記録を追記していく
            # interaction.edit_original_response() で元のメッセージを編集
            # view=self を付け忘れないように！
            await interaction.edit_original_response(view=self)
        except Exception as e:
            await print_exception(e)
            pass

async def send_exception(response :Exception,ctx :discord.ApplicationContext):
    await ctx.respond(await print_exception(response))

async def send_to_user(user_input_queue :asyncio.Queue, response_queue :asyncio.Queue,ctx :discord.ApplicationContext,channel :discord.Thread):
    color_per_person = dict()
    color_index = 0
    try:
        while True:
            response = await response_queue.get()
            if isinstance(response,Exception):
                await send_exception(response,ctx)
                continue
            color_candidates = [0x00FF00, 0xFF0000, 0x0000FF, 0xFFFF00, 0x00FFFF]
            for i,hist in enumerate(response):
                file = hist.get("file")
                if file:
                    await channel.send(hist.get("filename"),file=discord.File(fp=io.BytesIO(str(file).encode()),filename=hist.get("filename")))
                    continue
                name = hist.get("name","unknown")
                if name not in color_per_person:
                    color_per_person[name] = color_candidates[color_index % len(color_candidates)]
                    color_index+=1
                content = hist.get("content","")
                lines = splitandclear(content)
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
    except asyncio.QueueShutDown:
        pass # normal ending
    except Exception as e:
        await send_exception(e,ctx)
    user_input_queue.shutdown(immediate=True)

@bot.command(name="discuss", description="start agents discussion with query")
async def discuss(ctx: discord.ApplicationContext, query: str):
    user_input_queue = asyncio.Queue()
    response_queue = asyncio.Queue()
    try:
        await ctx.respond(bot_ui_message["ACCEPT_MESSAGE"])
        th = await ctx.send(bot_ui_message["RECORD_THREAD_TITLE"])
        modal = await ctx.send(view=HumanInTheLoopView(user_input_queue))
        channel = await th.create_thread(name=bot_ui_message["RECORD_THREAD_TITLE"])
        tasks = [
            asyncio.create_task(run_assistants(query,user_input_queue,response_queue)),
            asyncio.create_task(send_to_user(user_input_queue,response_queue,ctx,channel))
        ]
        await asyncio.gather(*tasks)
        await ctx.send(bot_ui_message["END_MESSAGE"])
        await modal.edit(embed=discord.Embed(description="Human in the loop closed."))
    except Exception as e:
        await send_exception(e,ctx)
        return

# Botを起動
bot.run(DISCORD_TOKEN)
