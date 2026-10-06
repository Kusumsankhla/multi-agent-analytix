import requests
import pandas as pd
import sqlite3

def fetch_live_crypto_data():
    url = "https://api.binance.com/api/v3/ticker/24hr"
    response = requests.get(url)
    response.raise_for_status()
    data = response.json()

    df = pd.DataFrame(data)
    df = df[df["symbol"].str.endswith("USDT")]
    df = df[["symbol", "lastPrice", "priceChangePercent", "volume",
             "quoteVolume", "highPrice", "lowPrice", "count"]]
    df["lastPrice"] = df["lastPrice"].astype(float)
    df["priceChangePercent"] = df["priceChangePercent"].astype(float)
    df["volume"] = df["volume"].astype(float)
    df["quoteVolume"] = df["quoteVolume"].astype(float)
    df["highPrice"] = df["highPrice"].astype(float)
    df["lowPrice"] = df["lowPrice"].astype(float)
    return df

if __name__ == "__main__":
    df = fetch_live_crypto_data()
    print(df.head(10))
    print("\nColumns:", df.columns.tolist())
    print("Rows fetched:", len(df))

    conn = sqlite3.connect("crypto_data.db")
    df.to_sql("coins", conn, if_exists="replace", index=False)
    conn.close()
    print("\nSaved to crypto_data.db, table 'coins'")