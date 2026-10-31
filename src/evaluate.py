import os
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns

def compute_mase(y_true, y_pred, y_train):
    """
    Mean Absolute Scaled Error (Hyndman & Koehler, 2006).
    Scaled against in-sample naive benchmark.
    """
    mae_model = np.mean(np.abs(y_true - y_pred))
    naive_diff = np.abs(np.diff(y_train))
    mae_naive = np.mean(naive_diff) if len(naive_diff) > 0 and np.mean(naive_diff) > 0 else 1.0
    return mae_model / mae_naive

def compute_wape(y_true, y_pred):
    """
    Weighted Absolute Percentage Error (Total Absolute Error / Total Demand).
    """
    total_actual = np.sum(y_true)
    if total_actual == 0:
        return 0.0
    return np.sum(np.abs(y_true - y_pred)) / total_actual

def compute_rmse(y_true, y_pred):
    """
    Root Mean Squared Error.
    """
    return np.sqrt(np.mean((y_true - y_pred) ** 2))

def run_evaluation_and_simulation():
    print("=" * 65)
    print("PHASE 4: ACADEMIC MODEL EVALUATION & INVENTORY SIMULATION")
    print("=" * 65)

    test_preds_path = os.path.join("data", "processed", "test_predictions_all_models.csv")
    train_features_path = os.path.join("data", "processed", "model_features.csv")
    tables_dir = os.path.join("results", "tables")
    figures_dir = os.path.join("results", "figures")

    for d in [tables_dir, figures_dir]:
        os.makedirs(d, exist_ok=True)

    if not os.path.exists(test_preds_path):
        raise FileNotFoundError(f"Missing test predictions: {test_preds_path}")

    test_df = pd.read_csv(test_preds_path)
    train_full = pd.read_csv(train_features_path)
    test_dates = test_df['date'].unique()
    train_history = train_full[~train_full['date'].isin(test_dates)]

    models = ['forecast_sma', 'forecast_croston', 'forecast_sba', 'forecast_rf', 'forecast_lgb']
    model_labels = {
        'forecast_sma': 'SMA (4-Week)',
        'forecast_croston': 'Croston',
        'forecast_sba': 'SBA',
        'forecast_rf': 'Random Forest',
        'forecast_lgb': 'LightGBM'
    }

    print("\n[1/3] Computing WAPE, MASE, and RMSE across catalog...")

    # Load SBC classification category for granular evaluation
    cat_path = os.path.join("results", "tables", "sku_classification.csv")
    sbc_map = {}
    if os.path.exists(cat_path):
        sbc_df = pd.read_csv(cat_path)
        sbc_map = dict(zip(sbc_df['sku_id'], sbc_df['category_sbc']))

    test_df['category_sbc'] = test_df['sku_id'].map(sbc_map).fillna("Unclassified")

    overall_metrics = []
    category_metrics = []

    for m in models:
        y_true = test_df['quantity_sold'].values
        y_pred = test_df[m].values

        overall_wape = compute_wape(y_true, y_pred)
        overall_rmse = compute_rmse(y_true, y_pred)

        # SKU-averaged MASE
        mase_scores = []
        for sku_id, group in test_df.groupby('sku_id'):
            y_t = group['quantity_sold'].values
            y_p = group[m].values
            y_tr = train_history[train_history['sku_id'] == sku_id]['quantity_sold'].values
            mase_scores.append(compute_mase(y_t, y_p, y_tr))

        overall_mase = float(np.mean(mase_scores))

        overall_metrics.append({
            "Model": model_labels[m],
            "WAPE (%)": round(overall_wape * 100, 2),
            "MASE": round(overall_mase, 3),
            "RMSE": round(overall_rmse, 3)
        })

        # Breakdown by SBC demand type
        for sbc_type, sub_group in test_df.groupby('category_sbc'):
            sub_true = sub_group['quantity_sold'].values
            sub_pred = sub_group[m].values
            category_metrics.append({
                "SBC_Category": sbc_type,
                "Model": model_labels[m],
                "WAPE (%)": round(compute_wape(sub_true, sub_pred) * 100, 2),
                "RMSE": round(compute_rmse(sub_true, sub_pred), 3)
            })

    metrics_df = pd.DataFrame(overall_metrics)
    metrics_path = os.path.join(tables_dir, "model_accuracy_comparison.csv")
    metrics_df.to_csv(metrics_path, index=False)

    cat_metrics_df = pd.DataFrame(category_metrics)
    cat_metrics_path = os.path.join(tables_dir, "sbc_category_model_accuracy.csv")
    cat_metrics_df.to_csv(cat_metrics_path, index=False)

    print("\nOverall Model Benchmark Table:")
    print(metrics_df.to_string(index=False))

    # [2/3] Inventory Policy Simulation (Reorder Point Policy)
    print("\n[2/3] Simulating (s, S) inventory replenishment over test horizon...")
    lead_time_weeks = 2
    service_z = 1.645  # 95% cycle service level standard

    simulation_results = []

    for m in models:
        stockouts_count = 0
        total_demand_events = 0
        working_capital_weeks = []

        for sku_id, group in test_df.groupby('sku_id'):
            group = group.sort_values('date').reset_index(drop=True)
            unit_cost = group['unit_cost_lkr'].iloc[0]

            # Historical standard deviation for safety stock
            sku_train_std = train_history[train_history['sku_id'] == sku_id]['quantity_sold'].std()
            if pd.isna(sku_train_std) or sku_train_std == 0:
                sku_train_std = 1.0

            safety_stock = int(np.ceil(service_z * sku_train_std * np.sqrt(lead_time_weeks)))

            # Initial stock at Reorder Point + 2 weeks expected demand
            current_inventory = safety_stock + int(np.ceil(group[m].mean() * 2))

            for idx, row in group.iterrows():
                forecast = row[m]
                actual = row['quantity_sold']
                reorder_point = int(np.ceil(forecast * lead_time_weeks + safety_stock))
                order_up_to = reorder_point + int(np.ceil(forecast * 2))

                # Fulfill demand
                if actual > current_inventory:
                    stockouts_count += (actual - current_inventory)
                    current_inventory = 0
                else:
                    current_inventory -= actual

                total_demand_events += actual

                # Replenish if below reorder point
                if current_inventory < reorder_point:
                    order_qty = max(0, order_up_to - current_inventory)
                    current_inventory += order_qty

                # Track working capital value
                working_capital_weeks.append(current_inventory * unit_cost)

        stockout_rate = (stockouts_count / total_demand_events) * 100 if total_demand_events > 0 else 0
        mean_capital_lkr = float(np.mean(working_capital_weeks))

        simulation_results.append({
            "Model": model_labels[m],
            "Stockout_Rate (%)": round(stockout_rate, 2),
            "Mean_Working_Capital (LKR)": f"{mean_capital_lkr:,.2f}"
        })

    sim_df = pd.DataFrame(simulation_results)
    sim_path = os.path.join(tables_dir, "inventory_simulation_results.csv")
    sim_df.to_csv(sim_path, index=False)

    print("\nInventory Simulation Impact Table:")
    print(sim_df.to_string(index=False))

    # [3/3] Publication Figure: WAPE & RMSE Comparison
    print("\n[3/3] Generating performance comparison bar charts...")
    plt.figure(figsize=(10, 5))
    sns.set_theme(style="whitegrid")

    palette = ["#94A3B8", "#38BDF8", "#0284C7", "#10B981", "#6366F1"]
    ax = sns.barplot(data=metrics_df, x="Model", y="WAPE (%)", palette=palette)
    for p in ax.patches:
        ax.annotate(f"{p.get_height():.2f}%",
                    (p.get_x() + p.get_width() / 2., p.get_height()),
                    ha='center', va='bottom', fontsize=10, fontweight='bold', xytext=(0, 3),
                    textcoords='offset points')

    plt.title("Catalog-Wide Weighted Absolute Percentage Error (WAPE %)", fontsize=13, fontweight='bold', pad=12)
    plt.ylabel("WAPE (%) - Lower is Better", fontsize=11)
    plt.xlabel("Forecasting Architecture", fontsize=11)
    plt.ylim(0, max(metrics_df['WAPE (%)']) + 15)
    plt.tight_layout()

    fig_path = os.path.join(figures_dir, "model_accuracy_comparison.png")
    plt.savefig(fig_path, dpi=300)
    plt.close()
    print(f"  -> Model comparison chart saved: {fig_path}")

    print("\n" + "=" * 65)
    print("Phase 4 completed successfully! Evaluation tables and figures ready.")
    print("=" * 65 + "\n")

if __name__ == "__main__":
    run_evaluation_and_simulation()