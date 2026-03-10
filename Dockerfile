FROM python:3.12-slim

WORKDIR /app

RUN pip install --no-cache-dir requests beautifulsoup4

COPY train_delay_notification.py .

# デバッグ用HTMLの出力先（ボリュームマウント対象）
ENV DEBUG_HTML_DIR=/app/debug_html

ENTRYPOINT ["python", "train_delay_notification.py"]
