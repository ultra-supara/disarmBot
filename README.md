# disarmBot

<div id="top"></div>

## 使用技術一覧

<!-- シールド一覧 -->
<!-- 該当するプロジェクトの中から任意のものを選ぶ-->
<p style="display: inline">
  <!-- バックエンドの言語一覧 -->
  <img src="https://img.shields.io/badge/-Python-F2C63C.svg?logo=python&style=for-the-badge">
</p>

## 目次

1. [プロジェクトについて](#プロジェクトについて)
2. [環境](#環境)
3. [ディレクトリ構成](#ディレクトリ構成)
4. [開発環境構築](#開発環境構築)
5. [トラブルシューティング](#トラブルシューティング)

<!-- READMEの作成方法のドキュメントのリンク -->
<br />
<div align="right">
    <a href="READMEの作成方法のリンク"><strong>READMEの作成方法 »</strong></a>
</div>
<br />

<div align="right">
    <a href="Dockerfileの詳細リンク"><strong>Dockerfileの詳細 »</strong></a>
</div>
<br />

<!-- プロジェクトの概要を記載 -->

  <p align="left">
    <br />
    <!-- プロジェクト詳細にBacklogのWikiのリンク -->
    <a href="Backlogのwikiリンク"><strong>プロジェクト詳細 »</strong></a>
    <br />
    <br />

<p align="right">(<a href="#top">トップへ</a>)</p>

## 環境

<!-- 言語、フレームワーク、ミドルウェア、インフラの一覧とバージョンを記載 -->

| 言語・フレームワーク  | バージョン |
| --------------------- | ---------- |
| Python                | 3.12.7     |
| autogen-agentchat     | 0.2.37     |


その他のパッケージのバージョンは pyproject.toml と package.json を参照してください

<p align="right">(<a href="#top">トップへ</a>)</p>

## ディレクトリ構成

<!-- Treeコマンドを使ってディレクトリ構成を記載 -->

❯ tree -L 2
.
├── README.md
├── bot.py
├── extract.py
└── generated_pages
    ├── actortypes
    ├── actortypes_index.json
    ├── actortypes_index.md
    ├── blue_framework.txt
    ├── counters
    ├── counters_index.json
    ├── counters_index.md
    ├── detections_index.json
    ├── detections_index.md
    ├── disarm_blue_framework.json
    ├── disarm_blue_framework.md
    ├── disarm_red_framework.json
    ├── disarm_red_framework.md
    ├── incidents
    ├── incidents_index.json
    ├── incidents_index.md
    ├── metatechniques
    ├── metatechniques_by_responsetype_table.json
    ├── metatechniques_by_responsetype_table.md
    ├── metatechniques_index.json
    ├── metatechniques_index.md
    ├── phases
    ├── phases_index.json
    ├── phases_index.md
    ├── red_framework.txt
    ├── responsetype_index.json
    ├── responsetype_index.md
    ├── tactics
    ├── tactics_by_responsetype_table.json
    ├── tactics_by_responsetype_table.md
    ├── tactics_index.json
    ├── tactics_index.md
    ├── tasks
    ├── tasks_index.json
    ├── tasks_index.md
    ├── techniques
    ├── techniques_index.json
    └── techniques_index.md

10 directories, 33 files

<p align="right">(<a href="#top">トップへ</a>)</p>

### 環境変数の配置

.env ファイルを以下の環境変数例と[環境変数の一覧](#環境変数の一覧)を元に作成

.env
```bash
OPENAI_API_KEY=AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA
DISCORD_TOKEN=AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA
BASE_URL=https://<something>.openai.azure.com/
```

## 開発環境構築

venvを用います

`python3 -m venv .venv`

bashの場合
`. ./.venv/bin/activate`

fishの場合
`. ./.venv/bin/activate.fish`

### 動作確認

`python3 bot.py`

![スクリーンショット 2024-11-03 23 28 21](https://github.com/user-attachments/assets/3973697f-8541-4ddf-9f0a-75386f5f039e)

以下のような画面になったらdisarm-ai-botがオンライン上で立ち上がります。

Discordにおいてコマンド入力をします。今回の例では「ロシアとウクライナの戦争におけるdisinfoについてTTPを元にして技術的な議論」をさせてみます。

`/discuss msg`

<img width="711" alt="スクリーンショット 2024-11-03 23 46 07" src="https://github.com/user-attachments/assets/06acd4ed-da5b-4b2a-b8b2-f0482e018897">

msgを入力してEnterすると以下のような表示がDiscord上に現れます。

<img width="637" alt="スクリーンショット 2024-11-03 23 24 06" src="https://github.com/user-attachments/assets/3ac6406e-f0c9-41b5-97e4-bc4ea329cb30">

ターミナルにマルチAIエージェントが立ち上がって、Hostである`user`と防御側のTTPの専門家である`defender_assistant`と攻撃側のTTPの専門家である`atacker_assistant`の3者がdisinfoに関する議論を開始します。

```bash
user_proxy (to chat_manager):

以下のユーザーのメッセージに対して偽情報に関連して議論を行ってください:
 ロシアとウクライナ戦争のdisinfoについて技術的な議論をしましょう！

--------------------------------------------------------------------------------

Next speaker: defender_assistant

defender_assistant (to chat_manager):

確かに、ロシアとウクライナ戦争において偽情報が広がっています。そのような状況に対処するには、偽情報を拡散するチャンネルやプラットフォームに対する規制が必要です。TA12「効果の評価」を行い、どの戦術が効果的かを評価することが重要です。また、TA13「ターゲットオーディエンス分析」を行うことによって、どのような人々が偽情報に感染しているかを理解し、対処する戦略を立てることも必要です。TA29「真実ベースのカウンターナラティブを開発する」ことも重要で、偽情報を拡散するのと同じくらい、真実を宣伝することも重要です。TA44「人々がすぐにソーシャルメディアに投稿できないようにする」という戦術も検討されるべきです。偽情報を防ぐためには、真実と偽情報を混同させることができないようにする必要があります。

-------------------------------------------------------------------------------

Next speaker: defender_assistant

defender_assistant (to chat_manager):

さらに、TA16「正当性の確立」が重要です。情報提供者が信頼できることが重要であり、信頼できる情報源を見つけることも必要です。多様な情報源をつくり、情報源に説得力を持たせることが必要です。これには、TA28「証明された情報源の情報起源を提供する」ための技術的なソリューションも必要です。また、TA22「イノキュレーション。安全感を促進するためのポジティブキャンペーンを開始する」というアプローチも検討することができます。偽情報を受け入れる可能性のある人々に真実を伝えることで、偽情報に対する免疫をつけるためです。

-------------------------------------------------------------------------------

Next speaker: atacker_assistant

atacker_assistant (to chat_manager):

さらに、TA48「人種、信条、性的指向などを基にしたハラスメント」やTA78「人々を失望させる」といった戦術が偽情報拡散のために利用される可能性もあります。これらの戦術に対して、明確なガイドラインや禁止事項を設定し、社交メディアプラットフォーム上の違反行為に対して罰則を設けることが必要です。また、TA85「テキストをベースとしたコンテンツを開発する」やTA87「ビデオをベースとしたコンテンツを開発する」といった戦術も使われることがあります。これに対して、偽情報を監視し、適切な対応をすることが重要です。TA133「効果の指標やKPIを測定する」ことによって、偽情報拡散に対する有効性を評価することができます。また、TA65「物理的放送能力を準備する」とTA126「イベントへの参加を促す」も戦略の一環として考慮することができます。偽情報と戦うには、複数の戦術やアプローチを継続的に実施しなければなりません。

-------------------------------------------------------------------------------

Next speaker: defender_assistant

defender_assistant (to chat_manager):

確かに、あらゆる戦術やアプローチを用いて偽情報と戦うことが重要です。他にもTA118「画像を再利用する」やTA122「コンテンツモデレーション」なども偽情報に対する対策として検討できます。また、TA193「現地調査を行う」ことで、偽情報の確認を行い、適切な対策を講じることもできます。さらに、TA31「コミュニケーションキャンペーンの実施」によって、真実を広めることで偽情報に対する対策を講じることもできます。偽情報の拡散や偽情報の根源に対して、継続的に取り組み、多角的なアプローチを用いることが必要です。

--------------------------------------------------------------------------------

Next speaker: user_proxy

user_proxy (to chat_manager):

完全に同意します。偽情報が拡散されることは現代の社会において大きな問題であり、これを解決するためには、さまざまな観点からアプローチする必要があります。そのためにも、偽情報に対処する多数の技術的手段が必要で、これらを集約することでより効果的な戦略が形成され、偽情報拡散は効果的に減少されることが期待されます。

--------------------------------------------------------------------------------

Next speaker: user_proxy

user_proxy (to chat_manager):

そうですね。今後も偽情報と戦うための新しい手段が開発されることに期待したいですね。しかし、現在までに開発された技術的な手段を適切に利用し、偽情報に対処することが最優先課題です。

--------------------------------------------------------------------------------

Next speaker: user_proxy

user_proxy (to chat_manager):

確かに、技術的な手段の開発は継続して進んでいますが、現状ではこれらの手段を最大限に活用することが重要です。偽情報の拡散や根源に対処するためには、国際的な協力も必要です。各国が協力して偽情報に対抗するためのインフラや戦略を共同で開発し、実行することが望ましいです。

--------------------------------------------------------------------------------

Next speaker: atacker_assistant

atacker_assistant (to chat_manager):

そのとおりです。偽情報は国際的な問題であり、解決策も国際的な協力が必要です。国際的な協力が不可欠な理由は、偽情報がグローバルなインターネット空間を利用して、国境を越えて拡散されるためです。加えて、偽情報拡散の背後には、より高い意図や政治的な動機があることがあるため、国際的な協力が必要となります。

--------------------------------------------------------------------------------

Next speaker: defender_assistant

defender_assistant (to chat_manager):

その通りです。偽情報は国際的な問題であり、解決策も国際的な協力が必要です。各国が協力して、偽情報に対して共同で取り組むことが重要です。そのためには、国際機関や各国政府が連携して、偽情報拡散に対する戦略やインフラの開発・実施を進める必要があります。偽情報は情報エコシステム全体に深刻な損害を与える問題であり、国際的な協力がなければ、これを根絶することは困難です。

--------------------------------------------------------------------------------
```

会話が終了するとDiscord上に会話履歴が出力されます。

<img width="775" alt="スクリーンショット 2024-11-03 23 47 52" src="https://github.com/user-attachments/assets/e66fd83f-1691-455c-b264-c20cbfdcb006">


<img width="775" alt="スクリーンショット 2024-11-03 23 48 21" src="https://github.com/user-attachments/assets/3c988b0f-dde1-4d55-bc09-9985fbfd778e">

<img width="775" alt="スクリーンショット 2024-11-03 23 48 51" src="https://github.com/user-attachments/assets/237e6f22-8f8f-4853-867f-ad9940a5cb83">

<img width="775" alt="スクリーンショット 2024-11-03 23 49 24" src="https://github.com/user-attachments/assets/8431fc05-227c-4f9e-8b16-ec844643be50">


### 環境変数の一覧

| 変数名                 | 役割                                      | どこから取得してくるのか                 | 
| ---------------------- | ----------------------------------------- | ---------------------------------- | 
| OPENAI_API_KEY        | azure open aiのキー                        | Azure Open AI Studioのエンドポイントのキー                      |                                          
| DISCORD_TOKEN         | Discordのtoken   | discordのdeveloper portalのbot tabにあるtoken                  |                                     
| BASE_URL             | azureのbase url         | Azure Open AI Develop tabのEndpoint                     |


## トラブルシューティング

### .env: no such file or directory

.env ファイルがないので環境変数の一覧を参考に作成しましょう

<p align="right">(<a href="#top">トップへ</a>)</p>
