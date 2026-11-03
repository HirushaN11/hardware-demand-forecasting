import os
import joblib
import numpy as np
import pandas as pd

def generate_future_recommendations():
    print("=" * 65)
    print("GENERATING 4-WEEK FORWARD FORECASTS & REORDER DECISIONS")
    print("=" * 65)

    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    models_dir = os.path.join(base_dir, "models")
    processed_dir = os.path.join(base_dir, "data", "processed")
    tables_dir = os.path.join(base_dir, "results", "tables")
    os.makedirs(tables_dir, exist_ok=True)

    # 1. Load the trained LightGBM model and recent engineered features
    lgb_model = joblib.load(os.path.join(models_dir, "lightgbm_model.joblib"))
    features_df = pd.read_csv(os.path.join(processed_dir, "model_features.csv"))
    features_df['date'] = pd.to_datetime(features_df['date'])

    feature_cols = [
        'lag_1', 'lag_2', 'lag_3', 'lag_4', 'lag_8', 'lag_12',
        'rolling_mean_4', 'rolling_std_4', 'rolling_mean_12', 'rolling_std_12',
        'rolling_zeros_4', 'rolling_zeros_12', 'periods_since_last_sale',
        'recent_zero_ratio_4', 'month', 'quarter', 'week_of_year',
        'peak_construction_season', 'margin_lkr', 'margin_rate',
        'category_freq', 'sku_freq'
    ]

    sku_records = []

    # 2. Loop through all 30 SKUs and project forward 4 weeks
    for sku_id, group in features_df.groupby('sku_id'):
        group = group.sort_values('date').reset_index(drop=True)
        latest_row = group.iloc[-1].copy()

        horizon_preds = []
        sim_row = latest_row.copy()
        
        # Forecast Week 1, 2, 3, 4 recursively
        for _ in range(4):
            X_in = pd.DataFrame([sim_row[feature_cols]])
            pred = max(0.0, float(lgb_model.predict(X_in)[0]))
            horizon_preds.append(round(pred, 1))

            # Update lag features forward for the next week
            sim_row['lag_12'] = sim_row['lag_8']
            sim_row['lag_8'] = sim_row['lag_4']
            sim_row['lag_4'] = sim_row['lag_3']
            sim_row['lag_3'] = sim_row['lag_2']
            sim_row['lag_2'] = sim_row['lag_1']
            sim_row['lag_1'] = pred
            sim_row['rolling_mean_4'] = np.mean([sim_row['lag_1'], sim_row['lag_2'], sim_row['lag_3'], sim_row['lag_4']])

        w1, w2, w3, w4 = horizon_preds
        total_4w = round(sum(horizon_preds), 1)

        # 3. Calculate Practical Inventory Parameters
        lead_time = 2  # 2 weeks standard supplier lead time
        demand_std = group['quantity_sold'].tail(16).std()
        if pd.isna(demand_std) or demand_std <= 0:
            demand_std = 1.0

        safety_stock = int(np.ceil(1.645 * demand_std * np.sqrt(lead_time)))
        reorder_point = int(np.ceil((w1 + w2) + safety_stock))
        order_up_to = int(np.ceil(reorder_point + total_4w))

        # Sample physical stock on shelf to show realistic decisions
        simulated_stock = int(np.random.choice([
            max(0, reorder_point - 2), 
            reorder_point + 3, 
            safety_stock
        ]))

        needs_order = simulated_stock <= reorder_point
        order_qty = max(0, order_up_to - simulated_stock) if needs_order else 0
        total_cost_lkr = order_qty * float(latest_row['unit_cost_lkr'])

        sku_records.append({
            "sku_id": sku_id,
            "product_name": latest_row['product_name'],
            "category": latest_row['category'],
            "unit_cost_lkr": float(latest_row['unit_cost_lkr']),
            "selling_price_lkr": float(latest_row['selling_price_lkr']),
            "current_stock": simulated_stock,
            "safety_stock": safety_stock,
            "reorder_point": reorder_point,
            "order_up_to": order_up_to,
            "forecast_w1": w1,
            "forecast_w2": w2,
            "forecast_w3": w3,
            "forecast_w4": w4,
            "forecast_4w_total": total_4w,
            "reorder_status": "ORDER NOW" if needs_order else "HEALTHY",
            "suggested_order_units": order_qty,
            "capital_outlay_lkr": total_cost_lkr
        })

    # 4. Save to a CSV table so backend and frontend can display it
    out_df = pd.DataFrame(sku_records)
    out_path = os.path.join(tables_dir, "future_inventory_plan.csv")
    out_df.to_csv(out_path, index=False)
    print(f"\n[DONE] 4-Week Future Forecast table saved to: {out_path}")
    print("\nPreview of Actionable Output:")
    print(out_df[['sku_id', 'product_name', 'current_stock', 'reorder_point', 'reorder_status', 'suggested_order_units']].head(5).to_string())

if __name__ == "__main__":
    generate_future_recommendations()
    