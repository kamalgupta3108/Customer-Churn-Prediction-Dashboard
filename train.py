"""
train.py
--------
Trains a customer churn prediction model on the Telco Customer Churn dataset.

WHAT THIS SCRIPT DOES (read this before running):
1. Loads raw customer data (each row = one customer, with a Churn Yes/No label)
2. Cleans it (there's a known messy column: TotalCharges has some blank strings)
3. Converts categorical columns (like "Contract", "InternetService") into numbers
   -> ML models can only work with numbers, not text categories
4. Splits data into train/test sets
5. Handles class imbalance (most customers do NOT churn, so a naive model could
   just predict "No churn" every time and still look "accurate" - we fix this)
6. Trains two models (Logistic Regression and Random Forest) and compares them
7. Evaluates using precision/recall/F1 (NOT just accuracy - explained below)
8. Saves the winning model + the preprocessing objects, so the API can reuse them

WHY THESE SPECIFIC CHOICES (you WILL be asked this in interviews):

- Why Logistic Regression?
  It's simple, fast, and highly interpretable - each feature gets a coefficient
  that directly tells you "this feature increases/decreases churn probability by X".
  Great baseline for a business problem like this where explainability matters.

- Why also Random Forest?
  It usually captures non-linear relationships/feature interactions better than
  logistic regression (e.g. "month-to-month contract AND high monthly charges"
  might matter together, not just separately). We compare both and pick the
  better one - that comparison itself is a good interview talking point.

- Why NOT just use accuracy to judge the model?
  ~73% of customers in this dataset do NOT churn. A lazy model that always
  predicts "No churn" would get ~73% accuracy while being completely useless.
  So we look at RECALL for the churn class specifically (did we catch the
  people who actually left?) and PRECISION (when we say "will churn", are we
  right?), balanced via F1-score. In churn prediction, missing an at-risk
  customer (false negative) is usually more costly than a false alarm, so we
  care more about recall on the churn class.

- Why class_weight='balanced'?
  Instead of throwing away data (undersampling) or duplicating rows (oversampling),
  this tells the model "pay more attention to the minority class (churners)
  during training by weighting their errors higher". Simple, no data leakage risk,
  easy to explain.
"""

import pandas as pd
import numpy as np
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import StandardScaler, LabelEncoder
from sklearn.linear_model import LogisticRegression
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import (
    precision_score, recall_score, f1_score,
    confusion_matrix, classification_report, roc_auc_score
)
import joblib
import json
import os

DATA_PATH = "data/Telco-Customer-Churn.csv"
MODEL_DIR = "model"
os.makedirs(MODEL_DIR, exist_ok=True)

# ---------------------------------------------------------------------------
# STEP 1: Load data
# ---------------------------------------------------------------------------
df = pd.read_csv(DATA_PATH)
print(f"Loaded {len(df)} rows, {df.shape[1]} columns")

# ---------------------------------------------------------------------------
# STEP 2: Clean data
# ---------------------------------------------------------------------------
# customerID is just an identifier, not a predictive feature - drop it
df = df.drop(columns=["customerID"])

# TotalCharges is read as text because some rows have " " (blank) instead of
# a number (these are new customers with 0 tenure). Convert to numeric,
# and fill the resulting NaNs with 0 (makes sense: 0 tenure = 0 total charges)
df["TotalCharges"] = pd.to_numeric(df["TotalCharges"], errors="coerce")
df["TotalCharges"] = df["TotalCharges"].fillna(0)

# Target column: convert "Yes"/"No" to 1/0
df["Churn"] = df["Churn"].map({"Yes": 1, "No": 0})

print(f"Churn rate in dataset: {df['Churn'].mean():.2%}")

# ---------------------------------------------------------------------------
# STEP 3: Encode categorical features
# ---------------------------------------------------------------------------
# Identify categorical (text) columns vs numeric columns
categorical_cols = df.select_dtypes(include="object").columns.tolist()
numeric_cols = df.select_dtypes(include=["int64", "float64"]).columns.tolist()
numeric_cols.remove("Churn")  # target isn't a feature

print(f"Categorical columns ({len(categorical_cols)}): {categorical_cols}")
print(f"Numeric columns ({len(numeric_cols)}): {numeric_cols}")

# Label-encode each categorical column and remember the encoders -
# we need the SAME encoders at prediction time in the API, so we save them.
label_encoders = {}
for col in categorical_cols:
    le = LabelEncoder()
    df[col] = le.fit_transform(df[col])
    label_encoders[col] = le

feature_cols = categorical_cols + numeric_cols
X = df[feature_cols]
y = df["Churn"]

# ---------------------------------------------------------------------------
# STEP 4: Train/test split
# ---------------------------------------------------------------------------
# stratify=y ensures both train and test sets keep the same churn ratio
X_train, X_test, y_train, y_test = train_test_split(
    X, y, test_size=0.2, random_state=42, stratify=y
)
print(f"Train size: {len(X_train)}, Test size: {len(X_test)}")

# Scale numeric features (helps Logistic Regression converge properly;
# Random Forest doesn't need it, but scaling doesn't hurt it either)
scaler = StandardScaler()
X_train_scaled = X_train.copy()
X_test_scaled = X_test.copy()
X_train_scaled[numeric_cols] = scaler.fit_transform(X_train[numeric_cols])
X_test_scaled[numeric_cols] = scaler.transform(X_test[numeric_cols])

# ---------------------------------------------------------------------------
# STEP 5: Train models
# ---------------------------------------------------------------------------
log_reg = LogisticRegression(max_iter=1000, class_weight="balanced", random_state=42)
log_reg.fit(X_train_scaled, y_train)

rf = RandomForestClassifier(
    n_estimators=200, max_depth=8, class_weight="balanced",
    random_state=42, n_jobs=-1
)
rf.fit(X_train_scaled, y_train)

# ---------------------------------------------------------------------------
# STEP 6: Evaluate both models
# ---------------------------------------------------------------------------
def evaluate(name, model, X_test, y_test):
    y_pred = model.predict(X_test)
    y_proba = model.predict_proba(X_test)[:, 1]
    precision = precision_score(y_test, y_pred)
    recall = recall_score(y_test, y_pred)
    f1 = f1_score(y_test, y_pred)
    auc = roc_auc_score(y_test, y_proba)
    cm = confusion_matrix(y_test, y_pred)
    print(f"\n--- {name} ---")
    print(f"Precision (churn class): {precision:.3f}")
    print(f"Recall    (churn class): {recall:.3f}")
    print(f"F1-score  (churn class): {f1:.3f}")
    print(f"ROC-AUC:                 {auc:.3f}")
    print(f"Confusion matrix:\n{cm}")
    return {"precision": precision, "recall": recall, "f1": f1, "auc": auc}

results = {}
results["logistic_regression"] = evaluate("Logistic Regression", log_reg, X_test_scaled, y_test)
results["random_forest"] = evaluate("Random Forest", rf, X_test_scaled, y_test)

# ---------------------------------------------------------------------------
# STEP 7: Pick the winner (by F1 on churn class, since it balances
# precision and recall for the class we actually care about)
# ---------------------------------------------------------------------------
best_model_name = max(results, key=lambda k: results[k]["f1"])
best_model = log_reg if best_model_name == "logistic_regression" else rf
print(f"\n>>> Best model: {best_model_name} (F1={results[best_model_name]['f1']:.3f})")

# ---------------------------------------------------------------------------
# STEP 8: Feature importance (for the "why is this customer at risk" feature)
# ---------------------------------------------------------------------------
if best_model_name == "logistic_regression":
    importance = pd.Series(best_model.coef_[0], index=feature_cols).sort_values()
else:
    importance = pd.Series(best_model.feature_importances_, index=feature_cols).sort_values()

print("\nTop churn-driving features:")
print(importance.tail(10) if best_model_name != "logistic_regression" else importance.tail(5))
print("\nTop churn-REDUCING features (logistic regression only shows direction):")
if best_model_name == "logistic_regression":
    print(importance.head(5))

# ---------------------------------------------------------------------------
# STEP 9: Save everything the API will need
# ---------------------------------------------------------------------------
joblib.dump(best_model, f"{MODEL_DIR}/churn_model.pkl")
joblib.dump(scaler, f"{MODEL_DIR}/scaler.pkl")
joblib.dump(label_encoders, f"{MODEL_DIR}/label_encoders.pkl")
joblib.dump(feature_cols, f"{MODEL_DIR}/feature_cols.pkl")
joblib.dump(numeric_cols, f"{MODEL_DIR}/numeric_cols.pkl")

with open(f"{MODEL_DIR}/metrics.json", "w") as f:
    json.dump({
        "best_model": best_model_name,
        "results": results,
        "top_risk_factors": importance.tail(10).to_dict(),
    }, f, indent=2)

print(f"\nSaved model + preprocessing objects to '{MODEL_DIR}/'")
print("Day 1 done. You now have a trained, evaluated, saved churn model.")
