import os
import json
import datetime as dt
import functions_framework
from google.cloud import storage, bigquery

PROJECT_ID   = os.environ["htbwebsite-chatbot-462005"]
DATASET      = os.environ["BQ_DATASET"]
TABLE        = os.environ["BQ_TABLE"]

def _resolve_text(text, anchor):
    # anchor.textSegments の startIndex/endIndex で text から抜き出す
    if not anchor or "textSegments" not in anchor:
        return ""
    out = []
    for seg in anchor["textSegments"]:
        s = int(seg.get("startIndex", 0))
        e = int(seg.get("endIndex", 0))
        out.append(text[s:e])
    return "".join(out)

@functions_framework.cloud_event
def load_to_bigquery(event):
    data = event.data
    bucket = data["bucket"]
    name   = data["name"]

    # DocAIのJSON以外は無視
    if not name.lower().endswith(".json"):
        return

    storage_client = storage.Client()
    b = storage_client.bucket(bucket)
    blob = b.blob(name)
    payload = json.loads(blob.download_as_text())

    # Document AIの出力は "document" キーに入っている
    doc = payload.get("document", {})
    full_text = doc.get("text", "")
    pages = doc.get("pages", [])

    bq = bigquery.Client(project=PROJECT_ID)
    table_id = f"{PROJECT_ID}.{DATASET}.{TABLE}"

    now = dt.datetime.utcnow().isoformat() + "Z"
    rows = []
    for i, p in enumerate(pages, start=1):
        anchor = (p.get("layout") or {}).get("textAnchor") or {}
        page_text = _resolve_text(full_text, anchor)
        rows.append({
            "output_blob": f"gs://{bucket}/{name}",
            "processor_id": doc.get("processorId", ""),  # あれば
            "page": i,
            "text": page_text,
            "processed_at": now,
        })

    # 小規模ならストリーミングでOK（大量/バーストはLoad Job推奨）
    errors = bq.insert_rows_json(table_id, rows)
    if errors:
        raise RuntimeError(str(errors))