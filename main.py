import os
import time

import pandas as pd
import requests

# ===== 設定(ここだけ書き換える) =====
KEYWORD = "プロテイン"  # 検索する商品名
MAX_PAGES = 2            # 取得するページ数
RESULTS_PER_PAGE = 50    # 1ページあたりの件数
SLEEP_SECONDS = 2        # リクエストの間隔(秒)
OUTPUT_FILE = "yahoo_products.csv"
# ====================================

API_URL = "https://shopping.yahooapis.jp/ShoppingWebService/V3/itemSearch"
APP_ID = os.environ.get("YAHOO_APP_ID")  # 環境変数から読む(コードに直書きしない)


def safe_get(data, *keys):
    """入れ子の辞書から、値を安全に取り出す。情報が欠けていればNoneを返す"""
    for key in keys:
        if not isinstance(data, dict):
            return None
        data = data.get(key)
    return data


def main():
    if not APP_ID:
        print("環境変数 YAHOO_APP_ID が設定されていません。")
        return

    rows = []
    error_occurred = False
    for page in range(MAX_PAGES):
        params = {
            "appid": APP_ID,
            "query": KEYWORD,
            "results": RESULTS_PER_PAGE,
            "start": page * RESULTS_PER_PAGE + 1,
        }
        try:
            res = requests.get(API_URL, params=params, timeout=15)
        except requests.RequestException as e:
            print("通信に失敗しました:", e)
            error_occurred = True
            break

        print(f"{page + 1}ページ目 ステータス: {res.status_code}")
        if res.status_code != 200:
            print("取得に失敗しました。")
            error_occurred = True
            break

        try:
            data = res.json()
        except ValueError:
            print("返ってきたデータを読めませんでした。")
            error_occurred = True
            break

        if not isinstance(data, dict):
            print("APIレスポンスの形式が不正です。")
            break

        hits = data.get("hits")

        if not isinstance(hits, list):
            print("商品一覧の形式が不正です。")
            break

        if not hits:
            print("キーワードに一致する商品がありません。")
            break

        for hit in hits:
            try:
                rows.append({
                    "商品名": hit.get("name"),
                    "価格": hit.get("price"),
                    "店舗名": safe_get(hit, "seller", "name"),
                    "URL": hit.get("url"),
                })
            except Exception as e:
                print("1件の処理に失敗しました。:", e)

        print(f"  {len(hits)} 件取得")
        time.sleep(SLEEP_SECONDS)

    df = pd.DataFrame(rows, columns=["商品名", "価格", "店舗名", "URL"])

    if error_occurred:
        print("通信エラーが発生しました。")
    else:
        df.to_csv(OUTPUT_FILE, index=False, encoding="utf-8-sig")
        if len(df) > 0:
            print(f"{len(df)} 件を {OUTPUT_FILE} に保存しました")


if __name__ == "__main__":
    main()