import os
import numpy as np
import pandas as pd

class IntermittentBaselines:
    """
    Parametric baseline models for intermittent and lumpy demand forecasting.
    Includes:
      1. Simple Moving Average (SMA)
      2. Croston's Method (1972)
      3. Syntetos-Boylan Approximation (SBA, 2005)
    """

    @staticmethod
    def moving_average(series: np.ndarray, window: int = 4) -> np.ndarray:
        """
        Rolling Simple Moving Average with 1-step lookahead lag to prevent data leakage.
        """
        n = len(series)
        forecasts = np.zeros(n)
        for t in range(n):
            if t == 0:
                forecasts[t] = series[0]
            else:
                start_idx = max(0, t - window)
                forecasts[t] = np.mean(series[start_idx:t])
        return forecasts

    @staticmethod
    def croston(series: np.ndarray, alpha: float = 0.1) -> np.ndarray:
        """
        Croston's Method (1972).
        Separately updates demand magnitude (z) and inter-arrival time (p).
        y_hat = z / p
        """
        n = len(series)
        forecasts = np.zeros(n)

        # Find first non-zero demand for proper initialization
        first_nz_idx = np.where(series > 0)[0]
        if len(first_nz_idx) == 0:
            return forecasts

        init_idx = first_nz_idx[0]
        z = float(series[init_idx])
        p = 1.0
        q = 1.0  # Periods elapsed since last non-zero demand

        # Fill periods prior to the first occurrence
        for t in range(init_idx + 1):
            forecasts[t] = z / p

        for t in range(init_idx + 1, n):
            y_t = series[t - 1]

            if y_t > 0:
                z = alpha * y_t + (1 - alpha) * z
                p = alpha * q + (1 - alpha) * p
                q = 1.0
            else:
                q += 1.0

            forecasts[t] = z / p

        return forecasts

    @staticmethod
    def sba(series: np.ndarray, alpha: float = 0.1) -> np.ndarray:
        """
        Syntetos-Boylan Approximation (SBA, 2005).
        Applies bias deflation factor (1 - alpha / 2) to Croston's forecast.
        y_hat = (1 - alpha / 2) * (z / p)
        """
        croston_forecasts = IntermittentBaselines.croston(series, alpha=alpha)
        correction_factor = 1.0 - (alpha / 2.0)
        return croston_forecasts * correction_factor


def run_baselines():
    print("=" * 65)
    print("PHASE 3.1: COMPUTING PARAMETRIC BASELINES (SMA, CROSTON, SBA)")
    print("=" * 65)

    input_path = os.path.join("data", "processed", "weekly_demand.csv")
    output_dir = os.path.join("data", "processed")
    os.makedirs(output_dir, exist_ok=True)

    if not os.path.exists(input_path):
        raise FileNotFoundError(f"Missing processed dataset: {input_path}")

    print(f"Loading densified weekly demand from: {input_path}")
    df = pd.read_csv(input_path)
    df['date'] = pd.to_datetime(df['date'])
    df = df.sort_values(by=['sku_id', 'date']).reset_index(drop=True)

    records = []
    smoothing_alpha = 0.15  # Academic standard for spare-parts/hardware demand

    print(f"Generating rolling forecasts for {df['sku_id'].nunique()} SKUs (alpha={smoothing_alpha})...")

    for sku_id, group in df.groupby('sku_id'):
        group = group.sort_values('date').copy()
        y = group['quantity_sold'].values

        sma_preds = IntermittentBaselines.moving_average(y, window=4)
        croston_preds = IntermittentBaselines.croston(y, alpha=smoothing_alpha)
        sba_preds = IntermittentBaselines.sba(y, alpha=smoothing_alpha)

        group['forecast_sma'] = np.round(sma_preds, 4)
        group['forecast_croston'] = np.round(croston_preds, 4)
        group['forecast_sba'] = np.round(sba_preds, 4)

        records.append(group)

    baseline_df = pd.concat(records, axis=0).reset_index(drop=True)

    output_path = os.path.join(output_dir, "weekly_demand_with_baselines.csv")
    baseline_df.to_csv(output_path, index=False)

    print(f"  -> Generated baseline predictions saved to: {output_path}")
    print(f"  -> Total records with baselines: {len(baseline_df):,}")

    # Display sample prediction comparison for an intermittent SKU
    sample_sku = "HW-ELEC-002"
    sample_view = baseline_df[baseline_df['sku_id'] == sample_sku].tail(8)[
        ['date', 'sku_id', 'quantity_sold', 'forecast_sma', 'forecast_croston', 'forecast_sba']
    ]
    print(f"\nSample recent predictions for Intermittent SKU ({sample_sku}):")
    print(sample_view.to_string(index=False))

    print("\n" + "=" * 65)
    print("Step 3.1 completed successfully!")
    print("=" * 65 + "\n")

if __name__ == "__main__":
    run_baselines()