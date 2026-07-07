size = (
    crsp_monthly.filter(pl.col("date").dt.month() == 6)
    .with_columns(sorting_date=pl.col("date").dt.offset_by("1mo"))
    .select(["permno", "exchange", "industry", "sorting_date", "mktcap"])
    .rename({"mktcap": "me"})
)

market_equity = (
    crsp_monthly.filter(pl.col("date").dt.month() == 12)
    .with_columns(sorting_date=pl.col("date").dt.offset_by("7mo"))
    .select(["permno", "gvkey", "sorting_date", "mktcap"])
    .rename({"mktcap": "me_dec"})
)

book_to_market = (
    compustat.with_columns(sorting_date=pl.date(pl.col("datadate").dt.year() + 1, 7, 1))
    .join(market_equity, how="inner", on=["gvkey", "sorting_date"])
    .with_columns(bm=pl.col("be") / pl.col("me_dec"))
    .select(["permno", "sorting_date", "bm"])
)


def assign_portfolio(sorting_variable, n_portfolios):
    """Assign each stock to a portfolio bin between breakpoints."""
    return pl.col(sorting_variable).qcut(
        n_portfolios,
        labels=[str(i) for i in range(1, n_portfolios + 1)],
        allow_duplicates=True,
    )


hml_published = factors_ff5_monthly["hml"].mean()

comparison_value_premium = pl.DataFrame(
    {
        "design": ["Independent", "Dependent", "Published HML"],
        "value_premium": [
            value_premium_indep.item(),
            value_premium_dep.item(),
            hml_published,
        ],
    }
)
comparison_value_premium.write_csv("results/tables/value_premium_comparison.csv")

comparison_value_premium
