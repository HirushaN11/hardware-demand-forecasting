import os
import numpy as np
import pandas as pd

def build_feature_pipeline():
    print("=" * 65)
    print("PHASE 3.2: FEATURE ENGINEERING FOR ML MODELS")
    print("=" * 65)

    input_path = os.path.join("data", "processed", "weekly_demand_with_baselines.csv")
    output_path = os.path.join("data", "processed", "model_features.csv")

    if not os.path.exists(input_path):
        raise FileNotFoundError(f"Missing input dataset: {input_path}")

    print(f"Loading data from: {input_path}")
    df = pd.read_csv(input_path)
    df['date'] = pd.to_datetime(df['date'])
    df = df.sort_values(by=['sku_id', 'date']).reset_index(drop=True)

    feature_dfs = []

    print("Constructing lag structures, rolling moments, and intermittency metrics per SKU...")

    for sku_id, group in df.groupby('sku_id'):
        g = group.sort_values('date').copy()

        # 1. Autoregressive Lags (strictly lagged to prevent data leakage)
        for lag in [1, 2, 3, 4, 8, 12]:
            g[f'lag_{lag}'] = g['quantity_sold'].shift(lag)

        # 2. Rolling Window Moments (computed over lagged series to avoid leakage)
        g['rolling_mean_4'] = g['lag_1'].rolling(window=4, min_periods=1).mean()
        g['rolling_std_4'] = g['lag_1'].rolling(window=4, min_periods=1).std().fillna(0)
        g['rolling_mean_12'] = g['lag_1'].rolling(window=12, min_periods=1).mean()
        g['rolling_std_12'] = g['lag_1'].rolling(window=12, min_periods=1).std().fillna(0)

        # Rolling count of zero-demand periods (measures local intermittency density)
        g['rolling_zeros_4'] = (g['lag_1'].rolling(window=4, min_periods=1)
                                .apply(lambda x: (x == 0).sum(), raw=True))
        g['rolling_zeros_12'] = (g['lag_1'].rolling(window=12, min_periods=1)
                                 .apply(lambda x: (x == 0).sum(), raw=True))

        # 3. Intermittency Intervals: Weeks elapsed since last non-zero sale
        non_zero_series = g['quantity_sold'].shift(1)
        periods_since_sale = []
        counter = 1

        for val in non_zero_series:
            if pd.isna(val):
                periods_since_sale.append(1)
            elif val > 0:
                counter = 1
                periods_since_sale.append(counter)
            else:
                counter += 1
                periods_since_sale.append(counter)

        g['periods_since_last_sale'] = periods_since_sale

        # Ratio of zeros in the recent window
        g['recent_zero_ratio_4'] = g['rolling_zeros_4'] / 4.0

        feature_dfs.append(g)

    featured_df = pd.concat(feature_dfs, axis=0).reset_index(drop=True)

    # 4. Calendar & Temporal Features
    print("Generating calendar and seasonal construction indicators...")
    featured_df['month'] = featured_df['date'].dt.month
    featured_df['quarter'] = featured_df['date'].dt.quarter
    featured_df['week_of_year'] = featured_df['date'].dt.isocalendar().week.astype(int)

    # Sri Lanka construction cycle proxy:
    # Construction picks up Jan-Apr (pre-Sinhala/Tamil New Year) and Sep-Nov
    featured_df['peak_construction_season'] = featured_df['month'].isin([1, 2, 3, 4, 9, 10, 11]).astype(int)

    # 5. Price and Economic Factors
    featured_df['margin_lkr'] = featured_df['selling_price_lkr'] - featured_df['unit_cost_lkr']
    featured_df['margin_rate'] = featured_df['margin_lkr'] / featured_df['selling_price_lkr']

    # 6. Categorical Encodings (SKU & Category frequency encoding)
    cat_counts = featured_df['category'].value_counts()
    featured_df['category_freq'] = featured_df['category'].map(cat_counts)

    sku_counts = featured_df['sku_id'].value_counts()
    featured_df['sku_freq'] = featured_df['sku_id'].map(sku_counts)

    # Clean initial warm-up periods where lag_12 is NaN
    print("Dropping warm-up window (first 12 weeks of historical lags)...")
    initial_rows = len(featured_df)
    featured_df = featured_df.dropna(subset=['lag_12']).reset_index(drop=True)
    retained_rows = len(featured_df)

    featured_df.to_csv(output_path, index=False)

    print(f"  -> Features saved to: {output_path}")
    print(f"  -> Rows retained: {retained_rows:,} (dropped {initial_rows - retained_rows} warm-up periods)")
    print(f"  -> Total features engineered: {featured_df.shape[1]}")

    print("\nEngineered Feature Sample:")
    preview_cols = ['date', 'sku_id', 'quantity_sold', 'lag_1', 'lag_4', 'rolling_mean_4', 'periods_since_last_sale']
    print(featured_df[preview_cols].head(6).to_string(index=False))

    print("\n" + "=" * 65)
    print("Step 3.2 completed successfully!")
    print("=" * 65 + "\n")

if __name__ == "__main__":
    build_feature_pipeline()