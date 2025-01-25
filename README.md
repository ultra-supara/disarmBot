# disarmBot

## Abstruct
**disarmBot**は、Microsoftが開発しているOSSのAIエージェントフレームワーク：AutoGenを使用し複数のAI Agentを立て、RAG技術により引き出されたMITRE ATT&CKの戦略に基づいて偽情報に関する議論を自動生成した後、ユーザに結論を返すBotです。

日本語・英語・中国語に対応しています。

偽情報対策のフレームワークである[DISARM Disinformation TTP Framework](https://github.com/DISARMFoundation/DISARMframeworks?tab=readme-ov-file)に基づいた情報を提供します。

<img width="1166" alt="Image" src="https://github.com/user-attachments/assets/4401a4ce-1148-4045-bea5-0c92d1591986" />

## Demonstration Movie

[![YouTube Video](https://img.youtube.com/vi/Ee-JfL17L40/0.jpg)](https://www.youtube.com/watch?v=Ee-JfL17L40)

## Presentation

[[JSAC 2025 LT] Introduction to MITRE ATT&CK utilization tools by multiple LLM agents and RAG](https://speakerdeck.com/4su_para/jsac-2025-lt-introduction-to-mitre-att-and-ck-utilization-tools-by-multiple-llm-agents-and-rag)

<div id="top"></div>

## what is aim for?

disarmBotは、Discord上に導入できるBotです。ユーザがコマンドを入力することで複数のLLMエージェント(GPT-4)が自動的に立ち上がり、応答します。また、DISARM（Disinformation Analysis and Response Measures）TTP Frameworksに基づいており、DISARMはCTIの「理論」にあたるMITRE ATT&CKに基づいています。つまり、理論から公助に向けたLLMによる実践的CTI利活用のための施策です。

複数の異なる戦術を学習したLLMエージェントが協力し、attacker_assistant、defender_assistant、user、skeptics、solution architect、OSINT Specialistの視点から偽情報フレームワークに基づいた戦術的・技術的な対話を行います。対話を通じてエージェント同士の議論を通じた情報の深堀りを行います。disarmBotは、これらの条件を満たし、ユーザーが多様な意見に触れることができる情報環境を提供します。これにより、ユーザーは自ら考え、情報を消化するクリティカルな能力を高めることができます。仮に、想定ユーザーの要求が異なる立場や抽象度であっても個別最適化可能で、かつ4A(Accurate,Audience Focused,Actionable,Adequate Timing)条件が整った質の高いインテリジェンスを、防衛マインドから脱却し、プロアクティブな形で提供できることを示します。

【5つのAI Agentのイメージ】

<img width="1166" alt="Image" src="https://github.com/user-attachments/assets/16b9cd1b-c010-4052-8c2e-9972afb83734" />

【AutoGenにおけるGroup Chatのイメージ】

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

1. [動作環境](#動作環境)
2. [ファイル構成](#ファイル構成)
3. [インストール方法](#インストール方法)
4. [実行方法](#実行方法)
5. [環境変数の設定](#環境変数の設定)
6. [トラブルシューティング](#トラブルシューティング)

---

## 動作環境

| ソフトウェア           | バージョン |
| ---------------------- | ---------- |
| Python                 | 3.12.7     |
| autogen-agentchat      | 0.2.37     |

---

## ディレクトリ構成

**プロジェクトのディレクトリ構成**

```plaintext
.
├── README.md
├── bot.py               # disarm botの日本語版プログラム
├── bot_en.py            # disarm botの英語版プログラム
├── bot_ch.py            # disarm botの中国語版プログラム
├── extract.py           # データ処理スクリプト
└── generated_pages      # DISARM Frameworksのデータ
    ├── actortypes
    ├── counters
    ├── detections_index.md
    ├── disarm_blue_framework.md
    ├── その他のファイル...
10 directories, 33 files
```
---

## インストール方法

1. **仮想環境の作成**  
   以下のコマンドで仮想環境を作成します。

   ```bash
   python3 -m venv .venv
   ```

2. **仮想環境の有効化**  
   仮想環境をアクティブにします。

   - Bashの場合:
     ```bash
     source ./.venv/bin/activate
     ```

   - Fishの場合:
     ```fish
     . ./.venv/bin/activate.fish
     ```

3. **依存パッケージのインストール**  
   必要なパッケージをインストールします。

   ```bash
   pip install -r requirements.txt
   ```
4. **OpenAIのAPI（GPT-4）かazure APIを取得してください**
   [API keys - OpenAI API](https://platform.openai.com/settings/organization/api-keys)

5. **実行する**
   日本語版か英語版か中国語版を選択して実行してください。

   ```bash
   dotenv run python3 bot_en.py
   ```

6. **Discordでの動作確認**  
   Discord上で`/discuss msg`コマンドを入力し、msg内にメッセージを入力してください。
   自動でスレッドが生成され、ボットが会話を開始するか確認してください。
---

## 事前準備

1. **環境変数ファイル（.env）の作成**  
   プロジェクトフォルダに`.env`ファイルを作成し、以下のように記述します（詳細は[環境変数の設定](#環境変数の設定)を参照）。
   OpenAIのAPIを使う場合

   ```bash
   OPENAI_API_KEY=xxxxx
   DISCORD_TOKEN=xxxxx
   BASE_URL=https://xxxxxxxx.openai.azure.com/
   DEPLOYMENT=
   MODEL=gpt-4o-mini
   VERSION=2024-08-01-preview
   API_TYPE=openai
   AUTOGEN_USE_DOCKER=0
   ```
---

## 環境変数の設定

| 環境変数名            | 説明                         | 取得方法                          |
| ---------------------- | ---------------------------- | --------------------------------- |
| OPENAI_API_KEY         | Azure Open AIのAPIキー       | [Azure Open AI Studio](https://azure.microsoft.com/) |
| DISCORD_TOKEN          | DiscordのBotトークン         | [Discord Developer Portal](https://discord.com/developers/applications) |
| BASE_URL               | AzureのエンドポイントURL     | Azure Open AIのDevelopタブ      |

---

## トラブルシューティング

### `.envファイルが見つからない` エラー

`.env`ファイルが存在しない場合は、上記の「[環境変数の設定](#環境変数の設定)」を参考にファイルを作成してください。

### その他の問題

- **仮想環境が起動しない**: 仮想環境が正しく作成されているか確認し、パスを再確認してください。
- **依存パッケージのインストールエラー**: `requirements.txt`が最新か確認し、`pip install -r requirements.txt`を再度実行してください。

<p align="right">(<a href="#top">トップへ</a>)</p>
