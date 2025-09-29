# Estimate Automation MVP (GCP)

PDFファイルをGoogle Cloudにアップロードすると、自動的に **Document AI (OCR)** でテキスト化され、結果が **BigQuery** に保存される最小実装 (MVP) です。

---

## アーキテクチャ

```mermaid
flowchart LR
    A[PDF Upload (GCS input bucket)] -->|trigger| B[Cloud Function #1: Submit to Document AI]
    B --> C[Document AI Processor (OCR)]
    C -->|output JSON| D[GCS output bucket]
    D -->|trigger| E[Cloud Function #2: Load to BigQuery]
    E --> F[BigQuery Table (ocr_pages)]
