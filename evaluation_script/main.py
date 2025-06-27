import os
import zipfile
import tempfile
import sqlite3
import pandas as pd
import gdown

# —————— 설정값 ——————
GDRIVE_ID = "1NijVso91VsJOKAbcTWm0Os48X3JaDErO"
LOCAL_ZIP_PATH = os.path.join(tempfile.gettempdir(), "annotations.zip")
# ——————————————

def _download_annotations():
    # 캐시된 ZIP이 유효하면 재사용, 아니면 재다운로드
    if os.path.exists(LOCAL_ZIP_PATH):
        try:
            with zipfile.ZipFile(LOCAL_ZIP_PATH, 'r'):
                return LOCAL_ZIP_PATH
        except zipfile.BadZipFile:
            os.remove(LOCAL_ZIP_PATH)
    gdown.download(id=GDRIVE_ID, output=LOCAL_ZIP_PATH, quiet=True)
    # 받은 파일이 진짜 ZIP인지 확인
    with zipfile.ZipFile(LOCAL_ZIP_PATH, 'r'):
        pass
    return LOCAL_ZIP_PATH

def _load_gt_from_zip(zip_path, db_filename, table_name):
    # ZIP에서 SQLite 파일을 임시 추출하여 DataFrame으로 읽기
    with zipfile.ZipFile(zip_path) as z, tempfile.NamedTemporaryFile(delete=False) as tmp:
        tmp.write(z.read(db_filename))
        db_path = tmp.name
    con = sqlite3.connect(db_path)
    df = pd.read_sql_query(f"SELECT date, sku, warehouse, demand FROM {table_name};", con)
    con.close()
    os.unlink(db_path)
    return df

def evaluate(test_annotation_file, user_submission_file, phase_codename, **kwargs):
    """
    EvalAI가 호출하는 함수 진입점입니다.
    - test_annotation_file, phase_codename는 무시하고 내부 GDrive ZIP에서 정답을 불러옵니다.
    - user_submission_file: CSV 파일 경로 (date, sku, warehouse, mean 컬럼 필요)
    - 반환값은 WAPE_Public (val split, %) 과 WAPE_Private (test split, %) 을 포함합니다.
    """

    # 1) 제출 파일 읽기
    sub = pd.read_csv(user_submission_file)

    # 2) 정답 로딩
    zip_path = _download_annotations()
    # val split (2023) → demand_eval.db 안의 demand_eval_truth
    gt_val  = _load_gt_from_zip(zip_path, "demand_eval.db", "demand_eval_truth")
    # test split (2024) → demand_test.db 안의 demand_test_truth
    gt_test = _load_gt_from_zip(zip_path, "demand_test.db",  "demand_test_truth")

    # 3) WAPE 계산 함수
    def _wape(gt_df):
        merged = gt_df.merge(sub, on=["date", "sku", "warehouse"])
        if merged.empty:
            # 매칭 실패 시 높은 점수 할당
            return 9999.0
        abs_err = (merged["demand"] - merged["mean"]).abs()
        total   = merged["demand"].sum()
        # total이 0이면 무한대 (또는 지정값)
        return (abs_err.sum() / total * 100) if total != 0 else float("inf")

    wape_val  = _wape(gt_val)
    wape_test = _wape(gt_test)

    # 4) EvalAI 결과 포맷으로 리턴
    return {
        "result": [
            {"val_split":  {"WAPE_Public":  round(wape_val,  4)}},
            {"test_split": {"WAPE_Private": round(wape_test, 4)}}
        ],
        "submission_result": {
            "WAPE_Public":  round(wape_val,  4),
            "WAPE_Private": round(wape_test, 4)
        }
    }
