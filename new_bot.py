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
from pathlib import Path
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

def create_overlapping_chunks(text :str,chunk_size :int, overlap_lines :int,file :str,key :str):
    """
    複数行を1ブロックとしてチャンキングし、各ブロックの前後にオーバーラップを追加する関数

    Args:
        text (str): 元のテキストデータ
        chunk_size (int): 1つのメインブロックに含める行数
        overlap_lines (int): ブロックの前後に含めるオーバーラップ行数

    Returns:
        list: チャンクのテキストとメタデータを含む辞書のリスト
    """
    lines = text.strip().splitlines()
    documents = []
    metadatas = []
    ids = []
    

    
    # chunk_size ごとにループを回す (例: 0, 5, 10, 15...)
    for i in range(0, len(lines), chunk_size):
        # 1. メインとなるブロックの範囲を定義
        block_start = i
        block_end = i + chunk_size
        
        # 2. オーバーラップを含めた最終的なチャンクの範囲を計算
        #    max() と min() でドキュメントの最初と最後を超えないように調整
        context_start = max(0, block_start - overlap_lines)
        context_end = min(len(lines), block_end + overlap_lines)
        
        # 3. 範囲内の行をスライスして1つのテキストチャンクに結合
        chunk_lines = lines[context_start:context_end]
        chunk_text = "\n".join(chunk_lines)
        
        
        # 元のデータが何行目だったかをメタデータとして保持すると便利
        documents.append(chunk_text)
        metadatas.append({"file": file, "directory": key, "main_chunk_start_line": block_start + 1,"main_chunk_end_line": min(block_end, len(lines))})
        ids.append(f"{file}.{i+1}")
        
    return documents,metadatas,ids


if not exists:
    for dirpath,dirnames,files in os.walk("./generated_pages"):
        for file in files:
            try:
                print(f"adding {dirpath}/{file}")
                with open(f"{dirpath}/{file}", 'r', encoding='utf-8') as f:
                    content = f.read()
                    key = Path(dirpath).relative_to("./generated_pages").as_posix()
                    print("key: ",key)
                    documents,metadatas,ids = create_overlapping_chunks(content,20,3,file,key)
                    print(f"chunks: {len(documents)}")
                    collection.add(
                        documents=documents,
                        metadatas=metadatas,
                        ids=ids,
                    )
            except Exception as e:
                print(e)
                continue

base_path = Path("generated_pages")
disarm_files = [p.relative_to(base_path).as_posix() for p in base_path.rglob('*') if p.is_file()]
print(disarm_files)

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
)

# Initialize DuckDuckGo search tool

def searchDisarmFramework(question: str,directory :str):
    print("DEBUG: searchDisarmFramework ",question,file=sys.stderr)
    if not question.isascii():
        return "only accepts English"
    global collection
    result = collection.query(
        query_texts=[question],
        n_results=5,
        where={"directory": directory}
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

discussionActor = [ 
    {
        "name": "DisarmFrameworkMaster",
        "role_description": "You are an expert of DISARM Disinformation TTP (Tactics, Techniques and Procedures) Framework. You can provide both attacker and defender insight about systematic approach to combating disinformation"
    },
    {
        "name": "Skeptics",
        "role_description": "You are a skeptic. Your role is to act as devil's advocate and provide a critical perspective on what other agents say. Also look critically at what they don't say and mention it. ",
    },
    {
        "name": "SolutionArchitects",
        "role_description": "You are a solution architect. Your role is to provide a solution to the problem using expert's information. Your role is providing an answer, not a question. ",
    },
    {
        "name": "Clown",
        "role_description": "You are a clown. So what? you can say anything non related or you should questions to expert in simple perspective. Your role is questioning, not answering",
    },
]

old = [    {
        "name": "TheGeniusOfReasoning",
        "role_description": "Let's have a very detailed inference about existing facts and think clearly about logic that will defeat your opponent. Your are an expert, It's good to be inspired by the comments, but don't play together like clown. Your role is providing a bizarre and insightful opinion.",
    },]

assistantQueries = {
    "Detective":   {
        "prompt": "You are a detective. you have to deep dive into what is the user's actual wants to know. guess the context of users question with 5W1H(What,When,Where,Why,Who,How) to make more searchable on the internet. Please also dig deeper into the subtle nuances of the question phrase. Consider that the phrase of the question may be common sense in this way, but this way of asking this question may be a different intent. You haven't been given any specific search skills, but your initial guess is very important for the subsequent internet search. Please do NOT mention about what you cannot do.",
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
    },
    "DecisionMaker": {
        "prompt": "Your role is decision maker. Choose actor and request the task according to current context. Do NOT do as same as current_context do; it is already done. Do NOT Finish at first iteration."
    },
    "Attacker":{
        "prompt": "You are an expert in disinformation attacks. Your role is to use your expertise in disinformation attacks to find vulnerabilities in the case.",
    },
    "Defender": {
        "prompt": "You are a disinformation countermeasure/defense expert. It is your role to use your expertise on the disinformation defense side to think about responses to the vulnerabilities in the case.",
    },
    "DisarmFramework": {
        "prompt": f"You are information search expert. Please generate a query based on the contents of the README.md, file list below, user query, and perspective(Attacker or Defender) of question.\n#### README.md\n {readMe}\n#### File list\n{'\n'.join(disarm_files)}",
    },
}

assistantQueries.update([
    (x["name"],  {"prompt": x["role_description"]}) for x in discussionActor
])

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
        llm_config=llm_config,
        max_consecutive_auto_reply=1,
    )

def make_assistant(name :str, system_prompt :str):
    return autogen.AssistantAgent(
        name=name,
        system_message=system_prompt,
        llm_config=llm_config,
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

async def translate(response_queue :asyncio.Queue,requestLang :str,history :list,action :str):
    query = dumpjson({
        "request_language": requestLang,
        "translation_target": history
    })
    await send_progress(response_queue,"Translater",f"Summarizing the {action} result...")
    translated_response = await askAgent(query,"Translater")
    fileContent = f"{action[0].upper() + action[1:] } Summery\n"
    for content in translated_response["translated"]:
        fileContent += "# "+ content["name"]+"\n"
        fileContent += content["content"]
        fileContent += "## For five years old\n"
        fileContent += content["five_years_old_content"]
    await response_queue.put([{"file": fileContent,"filename": "summary.txt"}])
    return fileContent

async def search_assistants(response_queue :asyncio.Queue, msg :str):
    response = [{
        "user": msg,
    }]
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
    await send_progress(response_queue,"Detective",f"User query analysis done.\nGuessed: user want to know \"{userQueryDetected["superficial_guess"]}\" and \"{userQueryDetected["deep_guess"]}\"")
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
    return translate(response_queue,userQueryDetected["lang"],response,"search"),userQueryDetected["lang"]

def collect_related_documents(keywords :list):
    result = []
    for keyword in keywords:
        result.append(searchDisarmFramework(keyword["word"],keyword["directory"]))
    return result

async def disarm_assistants(response_queue :asyncio.Queue, msg :str):
    await send_progress(response_queue,"DisarmFramework","Generating query for attacker...")
    attacker_frameworks = await askAgent(dumpjson({
        "answer_language": "English",
        "prompt": msg,
        "perspective": "Attacker"
    }),"DisarmFramework")
    await send_progress(response_queue,"DisarmFramework","Query for attacker generated")
    await send_progress(response_queue,"Attacker","Asking attacker's opinion...")
    attacker_opinion = await askAgent(dumpjson({
        "user_prompt": msg,
        "resource": collect_related_documents(attacker_frameworks["keyword"]),
    }),"Attacker")
    await send_progress(response_queue,"Attacker","Attacker's opinion generated")
    await send_progress(response_queue,"DisarmFramework","Generating query for defender...")
    defender_frameworks = await askAgent(dumpjson({
        "answer_language": "English",
        "prompt": msg,
        "perspective": "Defender",
        "attacker_opinion": attacker_opinion,
    }),"DisarmFramework")
    await send_progress(response_queue,"DisarmFramework","Query for defender generated")
    await send_progress(response_queue,"Defender","Asking defender's opinion...")
    defender_optinion = await askAgent(dumpjson({
        "user_prompt": msg,
        "resource": collect_related_documents(defender_frameworks["keyword"]),
        "attacker_opinion": attacker_opinion,
    }),"Defender")
    await send_progress(response_queue,"Defender","Defender's opinion generated")
    return {
        "attacker": attacker_opinion,
        "defender": defender_optinion,
    }
    


async def make_decision(iteration :int,currentContext :str,userInputs :asyncio.Queue,response_queue :asyncio.Queue):
    user_input = []
    while not userInputs.empty():
        user_input.append(userInputs.get_nowait())
    if len(user_input) > 0:
        await send_progress(response_queue,"DecisionMaker",f"Human In the Loop: Accepted {len(user_input)} user input")
    copied = discussionActor.copy()
    if iteration != 1:
        copied.append({
            "name": "SearchInternet",
            "role_description": "Internet search expert. ask question then search on the internet!"
        })
    deceition_candidate = dumpjson({
        "current_context": currentContext,
        "additional_user_input": user_input,
        "action_limit": 5,
        "actors": {
            "experts": copied,
            "commands": [
                {
                    "name": "Finish",
                    "description": "finish actions. If no Finish is specified, next decition maker is called after all actions are finished and continue operations."
                },
                {
                    "name":"WaitForConcurrent",
                    "description":"wait for current concurrent tasks. If no concurrent task is run, this is nop. If no WaitForConcurrent is specified, all tasks are waited at the end of all actions."
                },
            ]
        },
        "iteration": iteration
    })
    decision = await askAgent(deceition_candidate,"DecisionMaker")
    return decision["actions"]

async def run_expert(resposne_queue :asyncio.Queue,prompt :str,history :list,name :str):
    ask = dumpjson({
        "history": history,
        "prompt": prompt,
    })
    await send_progress(resposne_queue,name,"Answering to prompt: "+prompt)
    if name == "SearchInternet":
        result = await search_assistants(resposne_queue,ask)
    elif name =="DisarmFrameworkMaster":
        result = await disarm_assistants(resposne_queue, ask)
    else:
        result = await askAgent(ask,name)
    await send_progress(resposne_queue,name,"Answer generated")
    return {
        "name": name,
        "prompt": prompt,
        "result": result,
    }

async def run_actions(response_queue :asyncio.Queue, actions :list):
    currentTasks = []
    history = []
    prevIsConcurrent = False
    fullHistory = []
    finalPhase = False
    for action in actions:
        if action["name"] == "Finish":
            finalPhase = True
            break
        if action["name"] == "WaitForConcurrent":
            if len(currentTasks) > 0:
                records = await asyncio.gather(*currentTasks)
                currentTasks.clear()
                history.extend(records)
            continue
        if not action["inherit_history"]:
            history.clear()
        if action["concurrent"]:
            currentTasks.append(asyncio.create_task(run_expert(response_queue,action["prompt"],history,action["name"])))
            prevIsConcurrent = True
        else:
            if prevIsConcurrent:
                history.clear()
            record = await run_expert(response_queue, action["prompt"],history,action["name"])
            history.append(record)
            fullHistory.append(record)
            prevIsConcurrent = False
    if len(currentTasks) > 0:
        records = await asyncio.gather(*currentTasks)
        fullHistory.extend(records)
    return fullHistory,finalPhase

async def run_assistants(msg :str,user_input_queue :asyncio.Queue,response_queue :asyncio.Queue):
    try:
        i = 1
        current_context, lang = await search_assistants(response_queue, msg) # first loop
        while True:
            actions = await make_decision(i,current_context,user_input_queue)
            fullHistory, finish = await run_actions(response_queue, actions)
            current_context = await translate(response_queue,lang,fullHistory,"disscussion")
            if finish:
                break
            i+=1
    except Exception as e:
        await response_queue.put(e)
    response_queue.shutdown()



# Botの大元となるオブジェクトを生成する
bot = discord.Bot(
    intents=discord.Intents.all(),
    activity=discord.Game("Disarm Framework"),
)

@bot.event
async def on_ready():
    print("Ready disarm framework bot")

def print_exception(response :Exception):
    print(response)
    print(traceback.format_exc())
    print(f"Error: {response}\n",traceback.format_exc(),file=sys.stderr)
    msg = str(bot_ui_message["ERROR_MESSAGE"])
    msg = msg.replace("{error}",str(response))
    return msg

async def send_exception(response :Exception,ctx :discord.ApplicationContext):
    await ctx.respond(print_exception(response))

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

global_user_map = {}
recent_discussion = {}
global_counter = 0
def register_discussion(user_name :str, user_map :asyncio.Queue):
    global global_counter
    global global_user_map
    global recent_discussion
    global_counter += 1
    global_counter = global_counter % 100000
    discuss = global_counter
    if global_user_map.get((user_name,discuss)):
        return None
    global_user_map[(user_name,discuss)] = user_map
    if recent_discussion.get(user_name):
        recent_discussion[user_name].append(discuss)
    else:
        recent_discussion[user_name] = [discuss]
    return discuss

def get_discussion(user_name :str,discuss :int|None) -> asyncio.Queue|None:
    global global_user_map
    global recent_discussion
    if discuss is None:
        recent = recent_discussion.get(user_name)
        if recent is None:
            return None
        discuss = recent
    return global_user_map.get((user_name,discuss))
    
def unregister_discussion(user_name :str,discuss :int):
    global global_user_map
    global recent_discussion
    del global_user_map[(user_name,discuss)]
    for i,x in enumerate(recent_discussion[user_name]):
        if x == discuss:
            del recent_discussion[user_name][i]
            if len(recent_discussion[user_name]) == 0:
                del recent_discussion[user_name]

@bot.command(name="hitl",description="human in the loop interaction")
async def human_in_the_loop(ctx: discord.ApplicationContext,query :str,id :int|None = None):
    try: 
        queue = get_discussion(ctx.user.name,id)
        if queue is None:
            await ctx.respond("No human in the loop queue found")
            return
        await queue.put(query)
        await ctx.respond("Enqueued human in the loop query")
    except Exception as e:
        await send_exception(e,ctx)

@bot.command(name="discuss", description="start agents discussion with query")
async def discuss(ctx: discord.ApplicationContext, query: str):
    user_input_queue = asyncio.Queue()
    response_queue = asyncio.Queue()
    human_in_the_loop_id = None
    user_name = ctx.user.name
    try:
        try:
            await ctx.respond(bot_ui_message["ACCEPT_MESSAGE"])
            human_in_the_loop_id = register_discussion(user_name,user_input_queue)
            if human_in_the_loop_id is None:
                await ctx.respond("Sorry, human in the loop is not usable")
            else:
                await ctx.respond(f"Your human in the loop id is {human_in_the_loop_id}")
            th = await ctx.send(bot_ui_message["RECORD_THREAD_TITLE"])
            channel = await th.create_thread(name=bot_ui_message["RECORD_THREAD_TITLE"])
            tasks = [
                asyncio.create_task(run_assistants(query,user_input_queue,response_queue)),
                asyncio.create_task(send_to_user(user_input_queue,response_queue,ctx,channel))
            ]
            await asyncio.gather(*tasks)
            await ctx.send(bot_ui_message["END_MESSAGE"])
        except Exception as e:
            await send_exception(e,ctx)
    except Exception as e:
        print_exception(e,ctx) # final fallback
    if human_in_the_loop_id is not None:
        unregister_discussion(user_name,human_in_the_loop_id)
    

# Botを起動
bot.run(DISCORD_TOKEN)
