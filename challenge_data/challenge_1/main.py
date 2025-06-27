import pandas as pd

def evaluate(test_annotation_file, user_submission_file, phase_codename, **kwargs):
    print("Starting Evaluation...")

    gt_df = pd.read_csv(test_annotation_file)
    pred_df = pd.read_csv(user_submission_file)

    merged = pd.merge(gt_df, pred_df, on=["date", "sku", "warehouse"], suffixes=('_gt', '_pred'))

    merged = merged.dropna(subset=["mean_gt", "mean_pred"])  # 결측 제거
    merged["abs_error"] = abs(merged["mean_gt"] - merged["mean_pred"])
    total_gt = merged["mean_gt"].sum()

    wape = (merged["abs_error"].sum() / total_gt * 100) if total_gt != 0 else float("inf")

    print(f"Computed WAPE: {wape:.4f}%")

    return {
        "result": [
            {
                "split": {
                    "WAPE": round(wape, 4),
                }
            }
        ],
        "submission_result": {
            "WAPE": round(wape, 4),
        }
    }
