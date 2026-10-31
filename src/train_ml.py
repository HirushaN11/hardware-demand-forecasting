import os
import joblib
import numpy as np
import pandas as pd
from sklearn.ensemble import RandomForestRegressor
import lightgbm as lgb

def train_and_evaluate_models():
    print("=" * 65)
    print("PHASE 3.3: ROLLING-ORIGIN ML MODEL TRAINING (RF & LIGHTGBM)")
    print("=" * 65)

    input_path = os.path.join("data", "processed", "model_features.csv")
    models_dir = os.path.join("models")
    results_dir = os.path.join("data", "processed")
    os.makedirs(models_dir, exist_ok=True)

    if not os.path.exists(input_path):
        raise FileNotFoundError(f"Engineered feature set not found: {input_path}")

    print(f"Loading engineered dataset from: {input_path}")
    df = pd.read_csv(input_path)
    df['date'] = pd.to_datetime(df['date'])
    df = df.sort_values(by=['date', 'sku_id']).reset_index(drop=True)

    # Define feature set (exclude target, metadata identifiers, and baseline forecasts)
    feature_cols = [
        'lag_1', 'lag_2', 'lag_3', 'lag_4', 'lag_8', 'lag_12',
        'rolling_mean_4', 'rolling_std_4', 'rolling_mean_12', 'rolling_std_12',
        'rolling_zeros_4', 'rolling_zeros_12', 'periods_since_last_sale',
        'recent_zero_ratio_4', 'month', 'quarter', 'week_of_year',
        'peak_construction_season', 'margin_lkr', 'margin_rate',
        'category_freq', 'sku_freq'
    ]
    target_col = 'quantity_sold'

    print(f"Number of input features: {len(feature_cols)}")
    print(f"Features: {', '.join(feature_cols[:8])} ... and {len(feature_cols)-8} more")

    # Temporal Split: Out-of-sample holdout test (weeks 86 to 105)
    unique_dates = sorted(df['date'].unique())
    total_weeks = len(unique_dates)
    train_cutoff_idx = int(total_weeks * 0.80)  # 80% train, 20% test
    cutoff_date = unique_dates[train_cutoff_idx]

    train_df = df[df['date'] < cutoff_date].copy()
    test_df = df[df['date'] >= cutoff_date].copy()

    print(f"\nTemporal Split Strategy (Rolling-Origin Holdout):")
    print(f"  -> Total active weeks available: {total_weeks}")
    print(f"  -> Training window: {train_df['date'].min().strftime('%Y-%m-%d')} to {train_df['date'].max().strftime('%Y-%m-%d')} ({len(train_df):,} records)")
    print(f"  -> Holdout test window: {test_df['date'].min().strftime('%Y-%m-%d')} to {test_df['date'].max().strftime('%Y-%m-%d')} ({len(test_df):,} records)")

    X_train = train_df[feature_cols]
    y_train = train_df[target_col]
    X_test = test_df[feature_cols]
    y_test = test_df[target_col]

    # 1. Random Forest Regressor
    print("\n[1/3] Training Random Forest Regressor...")
    rf_model = RandomForestRegressor(
        n_estimators=150,
        max_depth=12,
        min_samples_split=4,
        min_samples_leaf=2,
        random_state=42,
        n_jobs=-1
    )
    rf_model.fit(X_train, y_train)

    rf_train_preds = rf_model.predict(X_train)
    rf_test_preds = rf_model.predict(X_test)
    test_df['forecast_rf'] = np.round(np.clip(rf_test_preds, 0, None), 4)

    # 2. LightGBM Regressor (Tweedie objective for zero-inflated demand)
    print("[2/3] Training LightGBM Regressor (Tweedie distribution)...")
    lgb_model = lgb.LGBMRegressor(
        objective='tweedie',
        tweedie_variance_power=1.5,
        n_estimators=150,
        learning_rate=0.05,
        max_depth=6,
        num_leaves=31,
        min_child_samples=10,
        random_state=42,
        verbose=-1
    )
    lgb_model.fit(X_train, y_train)

    lgb_train_preds = lgb_model.predict(X_train)
    lgb_test_preds = lgb_model.predict(X_test)
    test_df['forecast_lgb'] = np.round(np.clip(lgb_test_preds, 0, None), 4)

    # 3. Save Model Artifacts
    print("\n[3/3] Exporting trained models and test predictions...")
    rf_path = os.path.join(models_dir, "random_forest_model.joblib")
    lgb_path = os.path.join(models_dir, "lightgbm_model.joblib")
    joblib.dump(rf_model, rf_path)
    joblib.dump(lgb_model, lgb_path)
    print(f"  -> RF Model saved: {rf_path}")
    print(f"  -> LightGBM Model saved: {lgb_path}")

    # Combine test predictions with baselines into evaluation file
    eval_cols = [
        'date', 'sku_id', 'product_name', 'category', 'unit_cost_lkr', 'selling_price_lkr',
        'quantity_sold', 'forecast_sma', 'forecast_croston', 'forecast_sba',
        'forecast_rf', 'forecast_lgb'
    ]
    test_eval_df = test_df[eval_cols].sort_values(by=['sku_id', 'date']).reset_index(drop=True)
    eval_output_path = os.path.join(results_dir, "test_predictions_all_models.csv")
    test_eval_df.to_csv(eval_output_path, index=False)
    print(f"  -> Master evaluation dataset saved: {eval_output_path}")

    # Feature Importance Preview (Top 5 features from LightGBM)
    importance_df = pd.DataFrame({
        'feature': feature_cols,
        'importance': lgb_model.feature_importances_
    }).sort_values('importance', ascending=False)

    print("\nTop 5 Most Informative Features (LightGBM):")
    for idx, row in importance_df.head(5).iterrows():
        print(f"  - {row['feature']:<25}: {row['importance']:.1f}")

    print("\n" + "=" * 65)
    print("Step 3.3 completed successfully! Ready for Phase 4 (Evaluation).")
    print("=" * 65 + "\n")

if __name__ == "__main__":
    train_and_evaluate_models()