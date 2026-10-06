import pandas as pd
import sqlite3

transactions = pd.read_csv("train_transaction.csv")
identity = pd.read_csv("train_identity.csv")

transactions = transactions.sample(n=20000, random_state=42)

conn = sqlite3.connect("fraud_data.db")
transactions.to_sql("transactions", conn, if_exists="replace", index=False)
identity.to_sql("identity", conn, if_exists="replace", index=False)

conn.close()
print("Done. Tables created: transactions, identity")