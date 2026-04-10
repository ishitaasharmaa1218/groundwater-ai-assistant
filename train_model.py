import pandas as pd
from sklearn.linear_model import LinearRegression
import joblib

df = pd.read_csv("datasets/maharashtra_groundwater_2020_clean.csv")

# Example features
X = df[["annual_recharge"]]
y = df["net_groundwater"]

model = LinearRegression()
model.fit(X, y)

joblib.dump(model, "groundwater_model.pkl")

print("Model trained and saved.")