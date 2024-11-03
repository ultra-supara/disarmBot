import os
import markdown
import json
from bs4 import BeautifulSoup

def table_to_json(table):
    # テーブルの行を取得
    rows = table.find_all('tr')
    table_json = []
    for row in rows:
        # テーブルの列を取得
        cols = row.find_all('td')
        cols = [ele.text.strip() for ele in cols if ele.text.strip()]
        if len(cols) > 0:
            table_json.append(cols)
    # remove empty rows
    return table_json

def convert_md_to_html_in_directory(directory):
    lists = []
    # 指定されたディレクトリを再帰的に検索
    for root, _, files in os.walk(directory):
        for file in files:
            if file.endswith('.md'):
                md_path = os.path.join(root, file)
                
                # .mdファイルを読み込む
                with open(md_path, 'r', encoding='utf-8') as f:
                    markdown_text = f.read()
                
                html = markdown.markdown(markdown_text,extensions=['tables'])

                # print(html)

                soup = BeautifulSoup(html, 'html.parser')

                # tableタグを取得
                tables = soup.find_all('table')

                table_list = []

                #jsonに変換
                for table in tables:
                    table_json = table_to_json(table)
                    if len(table_json) > 0:
                        table_list.append(table_json)
                
                if len(table_list) > 0:
                   pass
                   #os.remove(md_path)
                   #with open(md_path.replace('.md', '.json'), 'w', encoding='utf-8') as f:
                   #     f.write(json.dumps(table_list, ensure_ascii=False, indent=4))
    return lists


                

# 使用例：現在のディレクトリから開始
converted = convert_md_to_html_in_directory('.')

print(converted)