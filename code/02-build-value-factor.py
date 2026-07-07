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


sorting_variables = (
    size.join(book_to_market, how="inner", on=["permno", "sorting_date"])
    .drop_nulls(["me", "bm"])
    .unique(subset=["permno", "sorting_date"])
)

# monthly returns mapped to the July-to-June period each sort governs
portfolios_returns = crsp_monthly.with_columns(
    sorting_date=pl.when(pl.col("date").dt.month() >= 7)
    .then(pl.date(pl.col("date").dt.year(), 7, 1))
    .otherwise(pl.date(pl.col("date").dt.year() - 1, 7, 1))
).select(["permno", "sorting_date", "date", "ret_excess", "mktcap_lag"])

value_portfolios_indep = (
    sorting_variables.with_columns(
        portfolio_bm=assign_portfolio("bm", n_portfolios=3).over("sorting_date"),
        # assign portfolio_me independently of portfolio_bm
        portfolio_me=assign_portfolio("me", n_portfolios=3).over("sorting_date"),
    )
    # merge with monthly returns - already done for you in `portfolios_returns`
    .join(portfolios_returns, on=["permno", "sorting_date"])
    .group_by(["date", "portfolio_bm", "portfolio_me"])
    .agg(
        ret=(pl.col("ret_excess") * pl.col("mktcap_lag")).sum()
        / pl.col("mktcap_lag").sum()
    )
)

value_premium_indep = (
    value_portfolios_indep.group_by(["date", "portfolio_bm"])
    .agg(ret=pl.col("ret").mean())
    .group_by("date")
    .agg(
        # high B/M (top portfolio) minus low B/M (bottom portfolio)
        value_premium=(
            pl.col("ret")
            .filter(pl.col("portfolio_bm") == pl.col("portfolio_bm").max())
            .mean()
            - pl.col("ret")
            .filter(pl.col("portfolio_bm") == pl.col("portfolio_bm").min())
            .mean()
        )
    )
    .select(pl.col("value_premium").mean())
)

value_portfolios_dep = (
    sorting_variables.with_columns(
        portfolio_me=assign_portfolio("me", n_portfolios=3).over("sorting_date")
    )
    # sort by bm *within* each size bucket: partition by sorting_date AND portfolio_me
    .with_columns(
        portfolio_bm=assign_portfolio("bm", n_portfolios=3).over(
            ["sorting_date", "portfolio_me"]
        )
    )
    .join(portfolios_returns, on=["permno", "sorting_date"])
    .group_by(["date", "portfolio_bm", "portfolio_me"])
    .agg(
        ret=(pl.col("ret_excess") * pl.col("mktcap_lag")).sum()
        / pl.col("mktcap_lag").sum()
    )
)

# Compute the value premium exactly as in the independent case
value_premium_dep = (
    value_portfolios_dep.group_by(["date", "portfolio_bm"])
    .agg(ret=pl.col("ret").mean())
    .group_by("date")
    .agg(
        value_premium=(
            pl.col("ret")
            .filter(pl.col("portfolio_bm") == pl.col("portfolio_bm").max())
            .mean()
            - pl.col("ret")
            .filter(pl.col("portfolio_bm") == pl.col("portfolio_bm").min())
            .mean()
        )
    )
    .select(pl.col("value_premium").mean())
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
