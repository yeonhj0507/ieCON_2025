import pandas as pd

def evaluate(user_submission_file, gt_df_val, gt_df_test, **kwargs):
    print("Starting Evaluation...")

    # 1) 제출 파일 로드
    sub = pd.read_csv(user_submission_file)

    # 기본값으로 9999 설정
    mae_val = mae_test = 9999.0

    # 2) Val split MAE 계산
    try:
        merged_val = gt_df_val.merge(sub, on=["date", "sku", "warehouse"])
        if not merged_val.empty:
            mae_val = (merged_val["demand"] - merged_val["mean"]).abs().mean()
        else:
            print("⚠️ No matching rows found for val split. Using 9999.")
    except Exception as e:
        print(f"⚠️ Error computing val split MAE: {e}. Using 9999.")

    print(f"MAE_Public (val): {mae_val:.4f}")

    # 3) Test split MAE 계산
    try:
        merged_test = gt_df_test.merge(sub, on=["date", "sku", "warehouse"])
        if not merged_test.empty:
            mae_test = (merged_test["demand"] - merged_test["mean"]).abs().mean()
        else:
            print("⚠️ No matching rows found for test split. Using 9999.")
    except Exception as e:
        print(f"⚠️ Error computing test split MAE: {e}. Using 9999.")

    print(f"MAE_Private (test): {mae_test:.4f}")

    # 4) EvalAI 리턴 포맷 생성
    result = {
        "result": [
            {"val_split":  {"MAE_Public":  round(mae_val,  4)}},
            {"test_split": {"MAE_Private": round(mae_test, 4)}}
        ],
        "submission_result": {
            "MAE_Public":  round(mae_val,  4),
            "MAE_Private": round(mae_test, 4)
        }
    }

    print("Evaluation Completed.")
    return result
