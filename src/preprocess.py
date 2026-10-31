import os
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns

def run_preprocessing_and_categorization():
    print("=" * 65)
    print("PHASE 2: PREPROCESSING, DENSIFICATION & DEMAND CATEGORIZATION")
    print("=" * 65)

    # 1. Paths
    raw_path = os.path.join("data", "raw", "sri_lanka_hardware_retail_sales_2024_2025.csv")
    processed_dir = os.path.join("data", "processed")
    tables_dir = os.path.join("results", "tables")
    figures_dir = os.path.join("results", "figures")

    for directory in [processed_dir, tables_dir, figures_dir]:
        os.makedirs(directory, exist_ok=True)

    if not os.path.exists(raw_path):
        raise FileNotFoundError(f"Raw data file not found at: {raw_path}")

    # 2. Load Raw Transaction Records
    print(f"\n[1/5] Loading raw transactions from: {raw_path}")
    df = pd.read_csv(raw_path)
    df['date'] = pd.to_datetime(df['transaction_date'])
    print(f"      -> Rows loaded: {len(df):,}")
    print(f"      -> Date range: {df['date'].min().strftime('%Y-%m-%d')} to {df['date'].max().strftime('%Y-%m-%d')}")

    # Extract unique SKU catalog metadata
    sku_metadata = (
        df[['sku_id', 'product_name', 'category', 'unit_cost_lkr', 'selling_price_lkr']]
        .drop_duplicates(subset=['sku_id'])
        .reset_index(drop=True)
    )

    # 3. Weekly Aggregation
    print("\n[2/5] Aggregating daily records into weekly intervals (W-MON)...")
    weekly_sales = (
        df.groupby(['sku_id', pd.Grouper(key='date', freq='W-MON')])['quantity_sold']
        .sum()
        .reset_index()
    )

    # 4. Calendar Densification (Zero-Filling Missing Weeks)
    print("\n[3/5] Densifying time series to reconstruct structural zero periods...")
    all_skus = df['sku_id'].unique()
    min_date = df['date'].min()
    max_date = df['date'].max()
    all_weeks = pd.date_range(start=min_date, end=max_date, freq='W-MON')

    full_grid = (
        pd.MultiIndex.from_product([all_skus, all_weeks], names=['sku_id', 'date'])
        .to_frame()
        .reset_index(drop=True)
    )

    densified_df = pd.merge(full_grid, weekly_sales, on=['sku_id', 'date'], how='left')
    densified_df['quantity_sold'] = densified_df['quantity_sold'].fillna(0).astype(int)

    # Merge metadata back
    densified_df = pd.merge(densified_df, sku_metadata, on='sku_id', how='left')
    densified_df = densified_df.sort_values(by=['sku_id', 'date']).reset_index(drop=True)

    # Save densified weekly series
    weekly_output_path = os.path.join(processed_dir, "weekly_demand.csv")
    densified_df.to_csv(weekly_output_path, index=False)
    print(f"      -> Densified dataset saved: {weekly_output_path}")
    print(f"      -> Matrix size: {len(densified_df):,} rows (30 SKUs x 105 weeks)")

    # 5. Syntetos-Boylan-Croston (SBC) Categorization
    print("\n[4/5] Computing ADI, CV^2, and demand profile classification...")
    categorization_records = []

    for sku_id, group in densified_df.groupby('sku_id'):
        series = group.sort_values('date')['quantity_sold'].values
        non_zero_idx = np.where(series > 0)[0]
        non_zero_values = series[non_zero_idx]

        total_periods = len(series)
        num_non_zero = len(non_zero_values)

        if num_non_zero > 1:
            # ADI: Average Demand Interval
            intervals = np.diff(non_zero_idx)
            adi = float(np.mean(intervals))

            # CV^2: Squared Coefficient of Variation of non-zero demand size
            mean_demand = float(np.mean(non_zero_values))
            std_demand = float(np.std(non_zero_values, ddof=1))
            cv2 = (std_demand / mean_demand) ** 2 if mean_demand > 0 else 0.0
        else:
            adi = float(total_periods)
            cv2 = 0.0

        # SBC academic decision rules (Syntetos et al., 2005)
        # ADI cut-off = 1.32, CV^2 cut-off = 0.49
        if adi < 1.32 and cv2 < 0.49:
            sbc_class = "Smooth"
        elif adi >= 1.32 and cv2 < 0.49:
            sbc_class = "Intermittent"
        elif adi < 1.32 and cv2 >= 0.49:
            sbc_class = "Erratic"
        else:
            sbc_class = "Lumpy"

        zero_ratio = float((series == 0).sum() / total_periods)

        categorization_records.append({
            "sku_id": sku_id,
            "adi": round(adi, 2),
            "cv2": round(cv2, 3),
            "category_sbc": sbc_class,
            "zero_percentage": round(zero_ratio * 100, 1),
            "total_units_sold": int(series.sum()),
            "mean_non_zero_qty": round(float(np.mean(non_zero_values)), 2) if num_non_zero > 0 else 0.0
        })

    cat_df = pd.DataFrame(categorization_records)
    cat_df = pd.merge(cat_df, sku_metadata, on='sku_id', how='left')
    cat_df = cat_df.sort_values(by=['category_sbc', 'sku_id']).reset_index(drop=True)

    # Save classification summary table
    cat_output_path = os.path.join(tables_dir, "sku_classification.csv")
    cat_df.to_csv(cat_output_path, index=False)
    print(f"      -> Classification table saved: {cat_output_path}")

    # 6. Generate Publication-Quality SBC Matrix Scatter Plot
    print("\n[5/5] Generating publication-ready SBC scatter plot figure...")
    plt.figure(figsize=(10, 6.5))
    palette = {
        "Intermittent": "#2563EB",  # Blue
        "Lumpy": "#DC2626",         # Red
        "Smooth": "#16A34A",        # Green
        "Erratic": "#F59E0B"        # Amber
    }

    sns.scatterplot(
        data=cat_df,
        x="adi",
        y="cv2",
        hue="category_sbc",
        palette=palette,
        s=130,
        edgecolor="black",
        linewidth=0.8,
        zorder=3
    )

    # Reference cut-off lines
    plt.axvline(x=1.32, color="gray", linestyle="--", linewidth=1.2, label="ADI Cut-off (1.32)")
    plt.axhline(y=0.49, color="gray", linestyle=":", linewidth=1.2, label=r"$CV^2$ Cut-off (0.49)")

    # Quadrant text labels
    plt.text(0.7, 0.15, "SMOOTH", fontsize=11, fontweight="bold", color="#16A34A", alpha=0.7)
    plt.text(4.2, 0.15, "INTERMITTENT", fontsize=11, fontweight="bold", color="#2563EB", alpha=0.7)
    plt.text(4.2, 1.25, "LUMPY", fontsize=11, fontweight="bold", color="#DC2626", alpha=0.7)

    plt.title("Syntetos-Boylan-Croston (SBC) Demand Categorization Matrix", fontsize=13, fontweight="bold", pad=12)
    plt.xlabel(r"Average Demand Interval ($ADI$ in weeks)", fontsize=11)
    plt.ylabel(r"Squared Coefficient of Variation ($CV^2$ of demand size)", fontsize=11)
    plt.xlim(0.5, max(cat_df['adi']) + 0.8)
    plt.ylim(-0.1, max(cat_df['cv2']) + 0.25)
    plt.grid(True, linestyle="--", alpha=0.5, zorder=0)
    plt.legend(title="Demand Profile", loc="upper right")
    plt.tight_layout()

    fig_output_path = os.path.join(figures_dir, "sbc_matrix.png")
    plt.savefig(fig_output_path, dpi=300)
    plt.close()
    print(f"      -> Scatter plot figure saved: {fig_output_path}")

    # Summary table output
    print("\n" + "=" * 65)
    print("CLASSIFICATION BREAKDOWN:")
    print(cat_df['category_sbc'].value_counts().to_string())
    print("=" * 65)
    print("Phase 2 executed successfully!\n")

if __name__ == "__main__":
    run_preprocessing_and_categorization()