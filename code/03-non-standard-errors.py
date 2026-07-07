def assign_portfolio(data, exchanges, sorting_variable, n_portfolios):
    """Assign portfolios using breakpoints from the chosen exchanges."""
    quantiles = [i / n_portfolios for i in range(n_portfolios + 1)]
    subset = data.filter(pl.col("exchange").is_in(exchanges))
    breakpoints = [
        subset[sorting_variable].quantile(q, interpolation="linear") for q in quantiles
    ]
    breakpoints = sorted(set(breakpoints))
    breakpoints[0], breakpoints[-1] = float("-inf"), float("inf")
    return data.select(
        pl.col(sorting_variable)
        .cut(
            breaks=breakpoints[1:-1],
            labels=[str(i) for i in range(1, len(breakpoints))],
            left_closed=True,
        )
        .cast(pl.String)
        .cast(pl.Int64)
    ).to_series()


def calculate_returns(value_weighted):
    # value-weighted OR equal-weighted mean of ret_excess
    if value_weighted:
        return (pl.col("ret_excess") * pl.col("mktcap_lag")).sum() / pl.col(
            "mktcap_lag"
        ).sum()
    return pl.col("ret_excess").mean()


def compute_value_premium(
    n_portfolios=5,
    exchanges=["NYSE", "NASDAQ", "AMEX"],
    value_weighted=True,
    dependent_sort=False,
    sorting_variables=None,
    returns=None,
):
    if dependent_sort:
        groups = []
        for _, group in sorting_variables.group_by("sorting_date"):
            group = group.with_columns(
                portfolio_me=assign_portfolio(group, exchanges, "me", 3)
            )
            groups.append(
                pl.concat(
                    [
                        subgroup.with_columns(
                            portfolio=assign_portfolio(
                                subgroup, exchanges, "bm", n_portfolios
                            )
                        )
                        for _, subgroup in group.group_by("portfolio_me")
                    ]
                )
            )
        assigned = pl.concat(groups).drop("portfolio_me")
    else:
        assigned = pl.concat(
            [
                group.with_columns(
                    portfolio=assign_portfolio(group, exchanges, "bm", n_portfolios)
                )
                for _, group in sorting_variables.group_by("sorting_date")
            ]
        )

    value_premium = (
        assigned
        # attach the monthly returns governed by each sort
        .join(returns, on=["permno", "sorting_date"])
        .group_by(["portfolio", "date"])
        .agg(ret=calculate_returns(value_weighted))
        .group_by("date")
        .agg(
            # high B/M (top portfolio) minus low B/M (bottom portfolio)
            value_premium=(
                pl.col("ret")
                .filter(pl.col("portfolio") == pl.col("portfolio").max())
                .mean()
                - pl.col("ret")
                .filter(pl.col("portfolio") == pl.col("portfolio").min())
                .mean()
            )
        )
    )

    # Newey-West t-test of the average premium (3 lags)
    nw = pf.feols(
        "value_premium ~ 1",
        data=value_premium,
        vcov="NW",
        vcov_kwargs={"lag": 3, "time_id": "date"},
    ).tidy()

    # CAPM-alpha of the premium
    capm_data = value_premium.join(factors_ff5_monthly, on="date", how="left")
    capm = pf.feols(
        "value_premium ~ mkt_excess",
        data=capm_data,
        vcov="NW",
        vcov_kwargs={"lag": 3, "time_id": "date"},
    ).tidy()

    return pl.DataFrame(
        {
            "test": ["Newey-West", "CAPM-alpha"],
            "estimate": [
                nw.loc["Intercept", "Estimate"],
                capm.loc["Intercept", "Estimate"],
            ],
            "t_stat": [
                nw.loc["Intercept", "t value"],
                capm.loc["Intercept", "t value"],
            ],
        }
    )


n_portfolios = [2, 5, 10]
exchanges = [["NYSE"], ["NYSE", "NASDAQ", "AMEX"]]
value_weighted = [True, False]
dependent_sorts = [True, False]
samples = [
    sorting_variables,
    sorting_variables.filter(pl.col("industry") != "Finance"),
    sorting_variables.filter(pl.col("sorting_date") < pl.date(1990, 7, 1)),
    sorting_variables.filter(pl.col("sorting_date") >= pl.date(1990, 7, 1)),
]

# build the full Cartesian product of options (3 × 2 × 2 × 2 × 4 = 96)
p_hacking_setup = list(
    product(n_portfolios, exchanges, value_weighted, dependent_sorts, samples)
)

n_cores = cpu_count() - 1
p_hacking_results = pl.concat(
    Parallel(n_jobs=n_cores)(
        delayed(compute_value_premium)(x, y, z, d, sv, portfolios_returns)
        for x, y, z, d, sv in p_hacking_setup
    )
)
p_hacking_results.write_csv("results/tables/p_hacking_results.csv")

from plotnine import ggplot, aes, geom_histogram, geom_vline, labs

p_hacking_nw = p_hacking_results.filter(pl.col("test") == "Newey-West").with_columns(
    is_significant=pl.col("t_stat").abs() >= 1.96
)

hml_mean = factors_ff5_monthly["hml"].mean()
fig_p_hacking_nw = (
    ggplot(p_hacking_nw, aes(x="estimate", fill="is_significant"))
    + geom_histogram(binwidth=0.001)
    + geom_vline(xintercept=hml_mean)
    + labs(
        x="Value premium",
        y="Count",
        fill="Significant at 95%?",
        title="Value premiums across 96 specifications",
    )
)
fig_p_hacking_nw.save("results/figures/p_hacking_nw.png", width=8, height=6, dpi=300)
fig_p_hacking_nw

p_hacking_capm = p_hacking_results.filter(pl.col("test") == "CAPM-alpha").with_columns(
    is_significant=pl.col("t_stat").abs() >= 1.96
)

# CAPM-alpha of the published HML, for a like-for-like reference line
hml_capm_alpha = pf.feols(
    "hml ~ mkt_excess",
    data=factors_ff5_monthly,
    vcov="NW",
    vcov_kwargs={"lag": 3, "time_id": "date"},
).coef()["Intercept"]

fig_p_hacking_capm = (
    ggplot(p_hacking_capm, aes(x="estimate", fill="is_significant"))
    + geom_histogram(binwidth=0.001)
    + geom_vline(xintercept=hml_capm_alpha)
    + labs(
        x="Premium",
        y="Count",
        fill="Significant at 95%?",
        title="CAPM-alphas of the value factor across 96 specifications",
    )
)
fig_p_hacking_capm.save(
    "results/figures/p_hacking_capm.png", width=8, height=6, dpi=300
)
fig_p_hacking_capm
