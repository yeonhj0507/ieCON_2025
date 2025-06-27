import os
import sys
import zipfile
import tempfile
import sqlite3
import pandas as pd
import gdown
import importlib

# === Google Drive 정보 ===
GDRIVE_ID = "1NijVso91VsJOKAbcTWm0Os48X3JaDErO"
LOCAL_ZIP_PATH = os.path.join(tempfile.gettempdir(), "annotations.zip")

# === 평가 대상 제출파일 경로 ===
SUBMISSION_FILE = os.path.join(os.getcwd(), "forecast_submission.csv")

# === Google Drive에서 ZIP 다운로드 ===
def download_annotations():
    # 1) 캐시된 ZIP이 있으면, 일단 열어본다
    if os.path.exists(LOCAL_ZIP_PATH):
        try:
            with zipfile.ZipFile(LOCAL_ZIP_PATH, 'r'):
                print(f"✅ Using valid cached annotation zip: {LOCAL_ZIP_PATH}")
                return LOCAL_ZIP_PATH
        except zipfile.BadZipFile:
            print("⚠️ Cached ZIP is invalid (probably HTML). Removing and re-downloading.")
            os.remove(LOCAL_ZIP_PATH)

    # 2) 캐시가 없거나 invalid일 때, 다시 다운로드
    print("📥 Downloading annotations.zip from Google Drive...")
    gdown.download(id=GDRIVE_ID, output=LOCAL_ZIP_PATH, quiet=False)
    print("✅ Download complete:", LOCAL_ZIP_PATH)

    # 3) 다운로드된 파일이 진짜 ZIP인지 검증 (optional)
    try:
        with zipfile.ZipFile(LOCAL_ZIP_PATH, 'r') as z:
            print("✅ Verified ZIP contents:", z.namelist())
    except zipfile.BadZipFile:
        raise RuntimeError(f"Downloaded file at {LOCAL_ZIP_PATH} is not a valid ZIP.")

    return LOCAL_ZIP_PATH
# === ZIP에서 SQLite DB 꺼내서 정답 불러오기 ===
def load_gt_from_zip(zip_file_path, db_filename, table_name):
    with zipfile.ZipFile(zip_file_path) as z:
        with tempfile.NamedTemporaryFile(delete=False) as tmp:
            tmp.write(z.read(db_filename))
            db_path = tmp.name
    con = sqlite3.connect(db_path)
    df = pd.read_sql_query(f"SELECT date, sku, warehouse, demand FROM {table_name};", con)
    con.close()
    os.unlink(db_path)
    return df

# === 메인 실행 함수 ===
def run():
    # 평가 모듈 import (challenge_data.challenge_1.evaluate)
    sys.path.append(os.getcwd())
    sys.path.append(os.path.join(os.getcwd(), "challenge_data", "challenge_1"))
    challenge_module = importlib.import_module("challenge_data.challenge_1.main")

    # ZIP 다운로드 및 정답 불러오기
    zip_path = download_annotations()
    print(zip_path)
    gt_val = load_gt_from_zip(zip_path, "demand_eval.db", "demand_eval_truth")
    gt_test = load_gt_from_zip(zip_path, "demand_test.db", "demand_test_truth")

    # 평가 수행
    print("🚀 Running evaluation...")
    result = challenge_module.evaluate(
        user_submission_file=SUBMISSION_FILE,
        gt_df_val=gt_val,
        gt_df_test=gt_test,
        submission_metadata={"source": "run.py test"}
    )

    # 결과 출력
    print("\n✅ Evaluation Result:")
    print(result)


if __name__ == "__main__":
    run()
