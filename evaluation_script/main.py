import sqlite3, zipfile, tempfile, os, requests
import pandas as pd
import numpy as np

KEYS   = ["date", "sku", "warehouse"]
GT_COL = "demand"
PRED_COL = "pred_demand"

GDRIVE_ID = "1NijVso91VsJOKAbcTWm0Os48X3JaDErO"
CACHE_ZIP = "/tmp/annotations.zip"

def gdrive_download(id_, out_path):
    if os.path.exists(out_path):
        return out_path
    print("Downloading annotations.zip from Google Drive…")
    URL = "https://drive.google.com/uc?export=download"
    session = requests.Session()
    resp = session.get(URL, params={'id': id_}, stream=True)
    # large files need confirmation token
    for k, v in resp.cookies.items():
        if k.startswith('download_warning'):
            resp = session.get(URL, params={'id': id_, 'confirm': v}, stream=True)
            break
    with open(out_path, "wb") as f:
        for chunk in resp.iter_content(32768):
            f.write(chunk)
    return out_path
def load_gt_from_zip(zip_file, member, table):
    with zipfile.ZipFile(zip_file) as z, tempfile.NamedTemporaryFile(delete=False) as tmp:
        tmp.write(z.read(member))
        db_path = tmp.name
    con = sqlite3.connect(db_path)
    df = pd.read_sql_query(f"SELECT date, sku, warehouse, demand FROM {table};", con)
    con.close(); os.unlink(db_path)
    return df

def mae(a, b): return (a - b).abs().mean()

def evaluate(sub_path, dummy_annotation_path):
    sub = pd.read_csv(sub_path)
    zip_path = gdrive_download(GDRIVE_ID, CACHE_ZIP)

    gt_val  = load_gt_from_zip(zip_path, "demand_test.db",  "demand_test_truth")
    gt_eval = load_gt_from_zip(zip_path, "demand_eval.db", "demand_eval_truth")

    def score(gt): 
        merged = gt.merge(sub, on=["date","sku","warehouse"])
        return mae(merged["demand"], merged["pred_demand"])

    return {
        "Val Split":  {"MAE_Public":  score(gt_val)},
        "Test Split": {"MAE_Private": score(gt_eval)}
    }