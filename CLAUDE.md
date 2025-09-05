# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## disarmBot Overview

disarmBot is a Discord bot that uses the AG2 (formerly AutoGen) framework to create multiple AI agents that automatically generate arguments about disinformation based on the DISARM (Disinformation Analysis and Response Measures) TTP Framework. The bot facilitates discussions between different AI personas (such as attackers, defenders, skeptics, and solution architects) and uses RAG technology to inform these discussions using the DISARM framework data.

The bot supports multiple languages:
- Japanese (bot.py)
- English (bot_en.py)
- Chinese (bot_ch.py)

## Core Commands

### Environment Setup

```bash
# Create a virtual environment
python3 -m venv .venv

# Activate the virtual environment (Bash)
source ./.venv/bin/activate

# Install dependencies
pip install -r requirements.txt
```

### Running the Bot

```bash
# Run the English version
dotenv run python3 bot_en.py

# Run the Japanese version
dotenv run python3 bot.py

# Run the Chinese version
dotenv run python3 bot_ch.py
```

### Docker Build & Run

```bash
# Build Docker image
docker build -t disarm-bot .

# Run Docker container
docker run --env-file .env disarm-bot
```

## Environment Variables

The bot requires the following environment variables to be set in a `.env` file:

```
OPENAI_API_KEY=your_openai_api_key
DISCORD_TOKEN=your_discord_bot_token
BASE_URL=your_azure_endpoint_url (if using Azure)
DEPLOYMENT=your_azure_deployment_name (if using Azure)
MODEL=gpt-4o-mini (or your preferred model)
VERSION=2024-08-01-preview (if using Azure)
API_TYPE=openai (or azure)
AUTOGEN_USE_DOCKER=0
```

## Architecture

1. **Discord Interface**: The bot uses py-cord for Discord integration and creates threads for discussions.

2. **Multi-Agent System**: Using AG2 (AutoGen), the bot creates several specialized AI agents:
   - Attackers: Focus on disinformation attack strategies
   - Defenders: Focus on countermeasures against disinformation
   - Skeptics: Provide critical perspectives on discussions
   - Solution Architects: Provide solutions based on expert information
   - Information Search experts: Search and summarize relevant information
   - Internet Search experts: Bring in outside information

3. **Vector Database**: Uses ChromaDB for storing and retrieving information from the DISARM framework.

4. **RAG (Retrieval Augmented Generation)**: Agents can search the DISARM framework documents using the `searchDisarmFramework` function to provide evidence-based responses.

5. **External Information**: Agents can also search the internet using the `searchTheInternet` function to bring in outside information.

6. **Group Chat**: The conversation is managed through a GroupChatManager that facilitates round-robin discussions between agents.

The data for the DISARM framework is stored in the `generated_pages` directory, which contains structured information about tactics, techniques, counters, incidents, and other aspects of the disinformation framework.

## Code Structure

- `bot.py`: Japanese version of the Discord bot
- `bot_en.py`: English version of the Discord bot
- `bot_ch.py`: Chinese version of the Discord bot
- `Dockerfile`: For containerizing the application
- `requirements.txt`: Lists dependencies
- `generated_pages/`: Contains the DISARM framework data in markdown files