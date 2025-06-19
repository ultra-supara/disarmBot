# disarmBot

![Image](https://github.com/user-attachments/assets/d569bb26-38ea-4a9f-ac7d-590d5ccddf36)

## Join our [LLM AgentBot Discord Community](https://discord.gg/dBgUNXmYcP) !!

<img width="861" alt="Image" src="https://github.com/user-attachments/assets/3ade408b-aa5d-4216-8b1c-6ec69e985838" />

## Abstract
**disarmBot** is a bot that uses [AG2](https://github.com/ag2ai/ag2?tab=readme-ov-file) (Formerly AutoGen), an OSS AI agent framework to create multiple AI Agents , automatically generate arguments about false information based on MITRE ATT&CK strategies drawn from RAG technology, and then return conclusions to the user. The bot automatically generates arguments about disinformation based on the MITRE ATT&CK strategy drawn from RAG technology and returns conclusions to the user.

Japanese, English, and Chinese are supported.

The framework for countermeasures against disinformation, the [DISARM Disinformation TTP Framework](https://github.com/DISARMFoundation/DISARMframeworks?tab=readme-ov-file) ,which is a framework for countermeasures against disinformation.

<img width="1166" alt="Image" src="https://github.com/user-attachments/assets/4401a4ce-1148-4045-bea5-0c92d1591986" />

## Demonstration Movie

[![YouTube Video](https://img.youtube.com/vi/Ee-JfL17L40/0.jpg)](https://www.youtube.com/watch?v=Ee-JfL17L40)

## Presentation

[[JSAC 2025 LT] Introduction to MITRE ATT&CK utilization tools by multiple LLM agents and RAG](https://speakerdeck.com/4su_para/jsac-2025-lt-introduction-to-mitre-att-and-ck-utilization-tools-by-multiple-llm-agents-and-rag)

<div id="top"></div>

## what is aim for?

disarmBot is a bot that can be deployed on Discord. Multiple LLM agents (GPT-4) are automatically launched and respond when a user enters a command. It is also based on the DISARM (Disinformation Analysis and Response Measures) TTP Frameworks, and DISARM is based on MITRE ATT&CK, the “theory” of CTI. In other words, these are measures for practical CTI utilization by LLM from theory to public assistance.

LLM agents, who have learned several different tactics, cooperate with each other and work together to develop a tactical and technical dialogue based on the disinformation framework from the perspective of an attacker_assistant, defender_assistant, user, skeptics, solution architect, and OSINT Specialist. Tactical and technical dialogues based on the disinformation framework will be conducted. Through the dialogues, agents discuss and deepen information with each other. disarmBot fulfills these requirements and provides an information environment that allows users to be exposed to a variety of opinions. This allows users to think for themselves and enhance their critical ability to digest information. Even if the assumed users' requirements are different positions and levels of abstraction, it is possible to optimize them individually and provide high-quality intelligence that meets the 4A (Accurate, Audience Focused, Actionable, and Adequate Timing) conditions in a proactive manner by breaking free from a defensive mindset. The 4As (Accurate, Audience Focused, Actionable, Adequate Timing) and can be provided in a proactive manner.

【Image of 5 AI Agents】

<img width="1166" alt="Image" src="https://github.com/user-attachments/assets/16b9cd1b-c010-4052-8c2e-9972afb83734" />

【Image of Group Chat in AutoGen】

<img width="1166" alt="Image" src="https://github.com/user-attachments/assets/4a77c096-2b14-4def-abd9-ec388000521a" />

---

## 使用技術

<!-- シールド一覧 -->
<!-- 該当するプロジェクトの中から任意のものを選ぶ-->
<p style="display: inline">
  <!-- バックエンドの言語一覧 -->
  <img src="https://img.shields.io/badge/-Python-F2C63C.svg?logo=python&style=for-the-badge">
</p>

---

## 目次

1. [Operating_Environment](#Operating Environment)
2. [File_Structure](#File Structure)
3. [Installation_Method](#Installation Method) 
4. [Preparation](#Preparation) 
5. [Set_environment_variables](#Set environment variables)
6. [Troubleshooting](#Troubleshooting)
7. [Special_Thanks!](#Special Thanks!)

---

## Operating Environment

| Software           | version |
| ---------------------- | ---------- |
| Python                 | 3.12.7     |
| autogen                | 0.7.3      |

---

## File Structure

**Project File Structure**

```plaintext
.
├── README.md
├── bot.py               # Japanese version of disarm bot program
├── bot_en.py            # English version of disarm bot program
├── bot_ch.py            # China version of disarm bot program
├── extract.py           # data processing script
└── generated_pages      # DISARM Frameworksのデータ
    ├── actortypes
    ├── counters
    ├── detections_index.md
    ├── disarm_blue_framework.md
    ├── others...
10 directories, 33 files
```
---

## Installation Method

1. **Create a virtual environment**.  
   Create a virtual environment with the following command

   ```bash
   python3 -m venv .venv
   ```` 

2. **Activate the virtual environment**.  
   Activate the virtual environment.

   - Bash:
     ```bash
     source ./.venv/bin/activate
     ```

   - Fish:
     ```fish
     . ./.venv/bin/activate.fish
     ```

3. **Install Dependent Packages**.  
   Install the required packages.

   ```bash
   pip install -r requirements.txt
   ```

4. **Get the OpenAI API (GPT-4) or azure API**
   [API keys - OpenAI API](https://platform.openai.com/settings/organization/api-keys)

5. **Run it**.
   Choose Japanese, English or Chinese version and run it.

   ```bash
   dotenv run python3 bot_en.py
   ````

6. **Confirm that it works on Discord**.  
   On Discord, type `/discuss msg` command and type your message in msg.
   Check if a thread is automatically created and the bot starts a conversation.

---

## Preparation

1. **Create an environment variable file (.env)**.  
   Create a `.env` file in the project folder and describe it as follows (for details, see [Setting Environment Variables](#Environment Variables)).
   When using OpenAI's API

   ```bash
   OPENAI_API_KEY=xxxxxxx
   DISCORD_TOKEN=xxxxxxx
   BASE_URL=https://xxxxxxxx.openai.azure.com/
   DEPLOYMENT=
   MODEL=gpt-4o-mini
   VERSION=2024-08-01-preview
   api_type=openai
   AUTOGEN_USE_DOCKER=0
   ```
---``

---

## Set environment variables

| Environment variable name | Description | How to get it |
| ---------------------- | ---------------------------- | --------------------------------- |
| OPENAI_API_KEY | API key for Azure Open AI | [Azure Open AI Studio](https://azure.microsoft.com/) |
| DISCORD_TOKEN | Bot Token for Discord | [Discord Developer Portal](https://discord.com/developers/applications) |
| BASE_URL | Azure endpoint URL | Develop tab of Azure Open AI |

---

## Troubleshooting

### `.env file not found` error

If the `.env` file does not exist, please create a file by referring to “[Set Environment Variables](#set environment variables)” above.

### Other problems

- **Virtual environment does not start**: Please check if the virtual environment is created correctly and recheck the path.
- **Dependent package installation error**: Please check if `requirements.txt` is up-to-date and run `pip install -r requirements.txt` again.

## Special Thanks!
Check out more projects built with AG2 at [Build with AG2](https://github.com/ag2ai/build-with-ag2)!

<p align="right">(<a href="#top">top</a>)</p>
