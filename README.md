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


.env ファイルを作成後、以下のコマンドで開発環境を構築

make prepare

### 動作確認

`python3 bot.py`


### 環境変数の一覧

| 変数名                 | 役割                                      | どこから取得してくるのか                 | 
| ---------------------- | ----------------------------------------- | ---------------------------------- | 
| OPENAI_API_KEY        | azure open aiのキー                        | Azure Open AI Studioのエンドポイントのキー                      |                                          
| DISCORD_TOKEN         | Discordのtoken   | discordのdeveloper portalのbot tabにあるtoken                  |                                     
| BASE_URL             | azureのbase url         | Azure Open AI Develop tabのEndpoint                     |

### コマンド一覧

| Make                | 実行する処理                                                            | 元のコマンド                                                                               |
| ------------------- | ----------------------------------------------------------------------- | ------------------------------------------------------------------------------------------ |
| make prepare        | node_modules のインストール、イメージのビルド、コンテナの起動を順に行う | docker-compose run --rm front npm install<br>docker-compose up -d --build                  |
| make up             | コンテナの起動                                                          | docker-compose up -d                                                                       |
| make build          | イメージのビルド                                                        | docker-compose build                                                                       |
| make down           | コンテナの停止                                                          | docker-compose down                                                                        |
| make loaddata       | テストデータの投入                                                      | docker-compose exec app poetry run python manage.py loaddata crm.json                      |
| make makemigrations | マイグレーションファイルの作成                                          | docker-compose exec app poetry run python manage.py makemigrations                         |
| make migrate        | マイグレーションを行う                                                  | docker-compose exec app poetry run python manage.py migrate                                |
| make show_urls      | エンドポイントをターミナル上で一覧表示                                  | docker-compose exec app poetry run python manage.py show_urls                              |
| make shell          | テストデータの投入                                                      | docker-compose exec app poetry run python manage.py debugsqlshell                          |
| make superuser      | スーパーユーザの作成                                                    | docker-compose exec app poetry run python manage.py createsuperuser                        |
| make test           | テストを実行                                                            | docker-compose exec app poetry run pytest                                                  |
| make test-cov       | カバレッジを表示させた上でテストを実行                                  | docker-compose exec app poetry run pytest --cov                                            |
| make format         | black と isort を使ってコードを整形                                     | docker-compose exec app poetry run black . <br> docker-compose exec app poetry run isort . |
| make update         | Poetry 内のパッケージの更新                                             | docker-compose exec app poetry update                                                      |
| make app            | アプリケーション のコンテナへ入る                                       | docker exec -it app bash                                                                   |
| make db             | データベースのコンテナへ入る                                            | docker exec -it db bash                                                                    |
| make pdoc           | pdoc ドキュメントの作成                                                 | docker-compose exec app env CI_MAKING_DOCS=1 poetry run pdoc -o docs application           |
| make init           | Terraform の初期化                                                      | docker-compose -f infra/docker-compose.yml run --rm terraform init                         |
| make fmt            | Terraform の設定ファイルをフォーマット                                  | docker-compose -f infra/docker-compose.yml run --rm terraform fmt                          |
| make validate       | Terraform の構成ファイルが正常であることを確認                          | docker-compose -f infra/docker-compose.yml run --rm terraform validate                     |
| make show           | 現在のリソースの状態を参照                                              | docker-compose -f infra/docker-compose.yml run --rm terraform show                         |
| make apply          | Terraform の内容を適用                                                  | docker-compose -f infra/docker-compose.yml run --rm terraform apply                        |
| make destroy        | Terraform で構成されたリソースを削除                                    | docker-compose -f infra/docker-compose.yml run --rm terraform destroy                      |

## トラブルシューティング

### .env: no such file or directory

.env ファイルがないので環境変数の一覧を参考に作成しましょう

<p align="right">(<a href="#top">トップへ</a>)</p>
