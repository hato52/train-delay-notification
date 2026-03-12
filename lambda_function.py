# 下記コマンドで必要なライブラリをインストールして、このファイルとともにzipに固めてLambdaにアップロードしてください。
# pip install requests beautifulsoup4 \
#   -t ./package \
#   --platform manylinux2014_x86_64 \
#   --only-binary=:all:


import logging
import time
from dataclasses import dataclass, asdict

import boto3
import requests
from bs4 import BeautifulSoup

logger = logging.getLogger()
logger.setLevel(logging.INFO)

sns_client = boto3.client("sns")
SNS_TOPIC_ARN = "SNS_TOPIC_ARNをここに設定してください"  # 例: "arn:aws:sns:us-east-1:123456789012:MyTopic"

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


@dataclass
class TrainInfo:
    name: str
    status: str
    detail: str


def fetch_page(url: str) -> str:
    response = requests.get(url, timeout=30)
    response.raise_for_status()
    return response.text


def extract_train_info(html: str, line_name: str) -> TrainInfo:
    soup = BeautifulSoup(html, "html.parser")

    h1 = soup.find("h1", class_="title")
    line_name = h1.get_text(strip=True) if h1 else line_name

    status_section = soup.find("div", class_="elmServiceStatus")
    if status_section:
        dt = status_section.find("dt")
        status = dt.get_text(strip=True) if dt else "不明"
        dd = status_section.find("dd")
        detail = dd.get_text(strip=True) if dd else ""
    else:
        status = "取得失敗"
        detail = "運行情報を取得できませんでした。"

    return TrainInfo(name=line_name, status=status, detail=detail)


def get_all_train_info() -> list[TrainInfo]:
    results = []
    for line in TARGET_LINES:
        logger.info("Fetching info for %s...", line["name"])
        html = fetch_page(line["url"])
        info = extract_train_info(html, line["name"])
        results.append(info)
        time.sleep(1)
    return results


def format_message(results: list[TrainInfo]) -> str:
    lines = ["=== 運行情報 ===\n"]
    for info in results:
        lines.append(f"【{info.name}】")
        lines.append(f"  状況: {info.status}")
        lines.append(f"  詳細: {info.detail}\n")
    return "\n".join(lines)


def publish_to_sns(message: str) -> None:
    sns_client.publish(
        TopicArn=SNS_TOPIC_ARN,
        Subject="電車運行情報",
        Message=message,
    )
    logger.info("SNS送信完了")


def lambda_handler(event, context):
    try:
        results = get_all_train_info()
    except requests.RequestException as e:
        logger.error("通信エラー: %s", e)
        return {"statusCode": 500, "body": f"通信エラー: {e}"}

    message = format_message(results)
    publish_to_sns(message)

    body = [asdict(info) for info in results]
    logger.info("取得完了: %d路線", len(body))
    return {"statusCode": 200, "body": body}
