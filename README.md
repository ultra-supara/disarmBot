# disarmBot

![Logo](https://github.com/user-attachments/assets/047ae510-c961-4b9a-b7c5-fa62c0a6b09f)

<div id="top"></div>

## プロジェクト概要

**disarmBot**は、AutoGenを使用し複数のAI Agentを立て、偽情報に関する議論を行った後、ユーザに返答を返すBotです。

偽情報対策のフレームワークである[DISARM Disinformation TTP Framework](https://github.com/DISARMFoundation/DISARMframeworks?tab=readme-ov-file)に基づいた情報を提供します。

【AI Agentとの対話イメージ】
![disarmbot](https://github.com/user-attachments/assets/6506ce32-7c50-4758-ac96-7a040e7ba8ea)



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
├── bot.py               # disarm botのメインプログラム
├── extract.py           # データ処理スクリプト
└── generated_pages      # DISARM Frameworksのデータ
    ├── actortypes
    ├── counters
    ├── detections_index.json
    ├── disarm_blue_framework.json
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

---

## 実行方法

1. **環境変数ファイル（.env）の作成**  
   プロジェクトフォルダに`.env`ファイルを作成し、以下のように記述します（詳細は[環境変数の設定](#環境変数の設定)を参照）。

   ```bash
   OPENAI_API_KEY=YOUR_OPENAI_API_KEY
   DISCORD_TOKEN=YOUR_DISCORD_TOKEN
   BASE_URL=https://<something>.openai.azure.com/
   ```

2. **ボットの起動**  
   次のコマンドでボットを起動します。

   ```bash
   python3 bot.py
   ```

3. **Discordでの動作確認**  
   Discord上で`/discuss msg`コマンドを入力し、ボットが会話を開始するか確認してください。

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
