tf.set_backend("polars")

factors_ff5_monthly_raw = tf.download_data(
    domain="Fama-French",
    dataset="Fama/French 5 Factors (2x3)",
)

factors_ff5_monthly_raw.write_parquet("data/raw/factors_ff5_monthly_raw.parquet")

factors_ff5_monthly = factors_ff5_monthly_raw.filter(
    pl.col("date").dt.year().is_between(1970, 2025)
).with_columns(pl.col("date").cast(pl.Date))

factors_ff5_monthly.write_parquet("data/clean/factors_ff5_monthly.parquet")

crsp_monthly = pl.read_parquet("data/clean/crsp_monthly.parquet")

compustat = pl.read_parquet("data/clean/compustat_annual.parquet")
