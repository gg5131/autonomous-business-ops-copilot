# Evaluation Guide

Information on semantic response metrics and golden datasets.

## 🏆 Ragas & DeepEval Metrics
- **Faithfulness**: Cosine similarity check between response sentence embeddings and retrieved context documents.
- **Answer Relevancy**: Word overlap and dense vector closeness between user queries and drafts.
- **Groundedness**: Identifies potential hallucinations or unsupported claims.
- **Citation Accuracy**: Validates correct formatting of source attribution codes (e.g. `[doc1]`).

## 📁 Golden Dataset (`evaluation/golden_dataset/`)
- Contains 50-100 high-quality target ticket descriptions mapped to correct resolutions.
- Used for regression analysis to prevent code modifications from degrading answer accuracy.
