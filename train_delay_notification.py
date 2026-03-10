import sys
import time
from dataclasses import dataclass

import requests
from bs4 import BeautifulSoup

# 対象路線とURLを管理するデータ構造
TARGET_LINES = [
    {
        "name": "UTSUNOMIYA_TOKYO_LINE",
        "url": "https://transit.yahoo.co.jp/traininfo/detail/46/46/",
    },
    {
        "name": "UTSUNOMIYA_KUROISO_LINE",
        "url": "https://transit.yahoo.co.jp/traininfo/detail/46/47/",
    },
    {
        "name": "GINZA_LINE",
        "url": "https://transit.yahoo.co.jp/traininfo/detail/132/0/",
    },
]

# 路線の運行情報を表す構造体
@dataclass
class TrainInfo:
    name: str       # 路線名
    status: str     # 状況（平常運転、遅延など）
    detail: str     # 詳細

# 指定URLのHTMLを取得する
def fetch_page(url: str, line_name: str = "page") -> str:
    response = requests.get(url, timeout=30)
    response.raise_for_status()

    # # デバッグ用: HTMLをファイルに書き出す
    # os.makedirs(DEBUG_DIR, exist_ok=True)
    # file_path = os.path.join(DEBUG_DIR, f"{line_name}.html")
    # with open(file_path, "w", encoding="utf-8") as f:
    #     f.write(response.text)
    # print(f"  -> HTML saved: {file_path}")

    return response.text

# 個別の路線ページから運行情報を抽出する
def extract_train_info(html: str, line_name: str) -> TrainInfo:
    soup = BeautifulSoup(html, "html.parser")
    # title から路線名を取得
    h1 = soup.find("h1", class_="title")
    line_name = h1.get_text(strip=True) if h1 else "line_name"

    # elmServiceStatus から状況を取得
    status_section = soup.find("div", class_="elmServiceStatus")
    if status_section:
        # 運転状況の取得
        dt = status_section.find("dt")
        status = status_section.find("dt").get_text(strip=True) if dt else "不明"

        # 詳細の取得
        dd = status_section.find("dd")
        detail = dd.get_text(strip=True) if dd else ""
    else:
        status = "取得失敗"
        detail = "運行情報を取得できませんでした。"

    return TrainInfo(name=line_name, status=status, detail=detail)

# 全ての対象路線の運行情報を取得する
def get_all_train_info() -> list[TrainInfo]:
    results = []
    for line in TARGET_LINES:
        html = fetch_page(line["url"], line["name"])
        info = extract_train_info(html, line["name"])
        results.append(info)
        time.sleep(3)
    return results

# 運行情報を見やすくフォーマットする
def format_train_info(info: TrainInfo) -> str:
    return (
        f"  路線名: {info.name}\n"
        f"  状況: {info.status}\n"
        f"  詳細: {info.detail}"
    )

def main():
    try:
        results = get_all_train_info()
    except requests.RequestException as e:
        print(f"通信エラー: {e}", file=sys.stderr)
        sys.exit(1)

    print("=== 運行情報 ===\n")
    for info in results:
        print(format_train_info(info))
        print()

if __name__ == "__main__":
    main()
