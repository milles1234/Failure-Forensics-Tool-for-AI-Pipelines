# test_pipeline.py
from dotenv import load_dotenv
load_dotenv()
# pyrefly: ignore [missing-import]
from pipeline.executor import run_pipeline

from data.sample_docs import SAMPLE_DOCUMENTS


if __name__ == "__main__":
    for key, doc in SAMPLE_DOCUMENTS.items():
        print(f"\n================ Running: {key} ================")
        print(f"Scenario: {doc['description']}")
        
        try:
            result = run_pipeline(doc["text"])
            print("Pipeline Output:")
            print(result)
        except Exception as e:
            print(f"Pipeline Crashed: {e}")