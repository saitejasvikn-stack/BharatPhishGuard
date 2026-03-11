import joblib
from sklearn.ensemble import RandomForestClassifier
from features import extract_features

# Re-Balanced Data
data = [
    ["http://sbi-kyc-verify.xyz", 1],
    ["http://v.gd/up-power-pay", 1],
    ["https://www.google.com", 0],
    ["https://www.amazon.in", 0],
    ["https://vahan.parivahan.gov.in", 0],
    ["Your electricity bill is due. Pay: http://bescom-pay.icu", 1]
]

X = [extract_features(item[0]) for item in data]
y = [item[1] for item in data]

model = RandomForestClassifier(n_estimators=100, random_state=42)
model.fit(X, y)

joblib.dump(model, 'phish_model.pkl')
print("✅ SUCCESS: Model updated with Domain Age feature!")