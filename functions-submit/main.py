import os
import uuid
import functions_framework
from google.api_core.client_options import ClientOptions
from google.cloud import documentai_v1 as documentai

PROJECT_ID   = os.environ["htbwebsite-chatbot-462005"]
LOCATION     = os.environ["us"]       
PROCESSOR_ID = os.environ["7b719203d16ca8d6"]        
OUTPUT_BUCKET= os.environ["OUTPUT_BUCKET"]

@functions_framework.cloud_event
def submit_to_docai(event):
    data = event.data  # CloudEvent payload
    bucket = data["bucket"]
    name   = data["name"]

    if not name.lower().endswith(".pdf"):
        return

    input_gcs_uri = f"gs://{bucket}/{name}"

    client = documentai.DocumentProcessorServiceClient(
        client_options=ClientOptions(api_endpoint=f"{LOCATION}-documentai.googleapis.com")
    )
    processor_name = client.processor_path(PROJECT_ID, LOCATION, PROCESSOR_ID)

    # 入力: GCS上のPDFを1件
    gcs_doc = documentai.GcsDocument(
        gcs_uri=input_gcs_uri,
        mime_type="application/pdf",
    )
    input_cfg = documentai.BatchDocumentsInputConfig(
        gcs_documents=documentai.GcsDocuments(documents=[gcs_doc])
    )

    # 出力: GCS (DocAIはJSONを書き出す)
    out_prefix = f"gs://{OUTPUT_BUCKET}/{uuid.uuid4()}/"
    gcs_out = documentai.DocumentOutputConfig.GcsOutputConfig(
        gcs_uri=out_prefix,
        # 任意: 出力を軽量化したい場合はFieldMaskで絞る
        # field_mask="text,pages.layout"
    )
    out_cfg = documentai.DocumentOutputConfig(gcs_output_config=gcs_out)

    req = documentai.BatchProcessRequest(
        name=processor_name,
        input_documents=input_cfg,
        document_output_config=out_cfg,
    )

    # 非同期実行 (ここでは待たずに返す)
    op = client.batch_process_documents(request=req)
    # 必要なら op.result() で待機可能（長時間実行に注意）

    # ここではログだけ
    print({"submitted": input_gcs_uri, "output_prefix": out_prefix})
