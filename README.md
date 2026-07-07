# Replication package for "Replicating the Value Factor"

Author: Paul Sibille

*Note*: this Readme was created using LLM (Claude Opus 4.8), following the guideliens provided by the RFS Data Editors website (https://review-of-financial-studies.github.io/readme.html). As a consequence, I ultimately checked the accuracy and consistency of the answer, and corrected mistakes. 

## 1. Overview

This replication package contains the code and data required to reproduce all results, tables, and figures of the assignment "Replicating the Value Factor". The workflow consists of (i) downloading and tidying the published Fama/French 5 Factors (2x3) from the Ken French Data Library, (ii) loading synthetic CRSP and Compustat data with the same structure as the original licensed databases, (iii) constructing the Fama-French sorting variables and computing the value premium under independent and dependent sorts, and (iv) recomputing the value premium across an extended grid of 96 specifications to assess non-standard errors.

All steps can be executed by rendering the main Quarto document `replicating-the-value-factor.qmd` from the project root. Total runtime is approximately 1-2 minutes on a standard laptop.

Because the original CRSP and Compustat databases are licensed and cannot be redistributed, this package uses synthetic data provided for teaching purposes. The synthetic data reproduce the structure and key variable definitions of the original sources, so the full analysis pipeline runs end to end without access to the licensed data.

## 2. Data Availability and Provenance

This paper analyzes external data (the published Fama-French factors) together with synthetic data that mimic the CRSP and Compustat databases.

I certify that I have legitimate access to and permission to use all data used in this manuscript. The published Fama-French factors are publicly available and are downloaded automatically by the replication code. The CRSP and Compustat files included in this package are synthetic (simulated) data generated for the course; they contain no records from the original licensed databases, so their inclusion does not violate any license agreement. No real CRSP or Compustat data are included in, or required by, this replication package.

Summary of availability:

- The published Fama-French factor data are publicly available and downloaded automatically by the code.
- The synthetic CRSP and Compustat data are included in the replication package.
- No confidential or licensed data are included in this package.

## 3. Data Sources

### Fama/French 5 Factors (2x3)

The published factor data are downloaded from the Ken French Data Library via the `tidyfinance` Python package.

- Data source: Kenneth R. French Data Library
- Dataset: Fama/French 5 Factors (2x3), monthly
- URL: <https://mba.tuck.dartmouth.edu/pages/faculty/ken.french/data_library.html>
- Access: Public use, no registration required
- Format: Parquet (after download and tidying by the code)
- License: Freely available for research and educational use per the Ken French Data Library terms
- Download method: Downloaded automatically by the code via `tf.download_data()` (internet connection required)
- Provided: Yes, a copy is stored in `data/raw/` and `data/clean/` so the package also runs offline

### Synthetic CRSP monthly data

- Data source: Synthetic data provided in the course, mimicking the CRSP Monthly Stock File
- Format: Parquet
- Access: Included in the package; no license required (simulated data)
- Download method: None; the file ships with the package
- Provided: Yes, `data/clean/crsp_monthly.parquet`

### Synthetic Compustat annual data

- Data source: Synthetic data provided in the course, mimicking Compustat Fundamentals Annual
- Format: Parquet
- Access: Included in the package; no license required (simulated data)
- Download method: None; the file ships with the package
- Provided: Yes, `data/clean/compustat_annual.parquet`

### Summary table

| Data file | Source | Notes | Provided |
|---|---|---|---|
| `data/raw/factors_ff5_monthly_raw.parquet` | Ken French Data Library | Raw FF5 factors, monthly | Yes |
| `data/clean/factors_ff5_monthly.parquet` | Derived | Tidied FF5 factors, 1970–2025 | Yes |
| `data/clean/crsp_monthly.parquet` | Synthetic (course) | Pseudo-CRSP monthly stock file | Yes |
| `data/clean/compustat_annual.parquet` | Synthetic (course) | Pseudo-Compustat annual fundamentals | Yes |
| `results/tables/value_premium_comparison.csv` | Derived | Output of the replication | Yes |
| `results/tables/p_hacking_results.csv` | Derived | Output of the specification grid | Yes |

Variable names follow the conventions of Tidy Finance (e.g., `permno`, `gvkey`, `mktcap`, `ret_excess`, `be`); variable definitions are documented in the code comments and in the Quarto document. I have verified that the synthetic data allow the replication code to execute without errors.

## 4. Computational Requirements

Software:

- Python >= 3.14 (the code was last run with CPython 3.14)
- `uv` for environment management (<https://docs.astral.sh/uv/>)
- Quarto >= 1.5 to render the main document (<https://quarto.org>)

Python packages are recorded in `pyproject.toml` and pinned in `uv.lock`; running `uv sync` installs them. The main dependencies are `polars`, `tidyfinance`, `pyfixest`, `joblib`, `plotnine`, and `numpy`.

- Random number generation: no pseudo-random number generator is used in the analysis; results are deterministic.
- Parallelism: the specification grid runs in parallel via `joblib`, using all available cores minus one. Results do not depend on the number of cores.
- Approximate runtime: 1-2 minutes on a standard (2025) laptop; the specification grid accounts for most of the computing time.
- The code was last run on an Apple Silicon laptop running macOS with 16 GB RAM.
- All file paths use forward slashes and are relative to the project root; no manual path adjustments are needed.

## 5. Description of Programs

The main entry point is `replicating-the-value-factor.qmd` in the project root. Rendering it executes all steps in the correct order: data preparation, value factor replication (independent and dependent sorts), and the non-standard errors analysis. It is fully self-contained.

The `code/` directory contains the same logic as standalone scripts, kept for development purposes. They must be run sequentially, as later scripts depend on objects created by earlier ones:

- `code/00-load-packages.py`: imports
- `code/01-prepare-data.py`: downloads the FF5 factors and loads the synthetic data
- `code/02-build-value-factor.py`: builds sorting variables and computes the value premium under both sorts
- `code/03-non-standard-errors.py`: defines `compute_value_premium()` and runs the 96-specification grid

## 6. Instructions to Replicators

1. Ensure Python >= 3.14, `uv`, and Quarto are installed.
2. From the project root, run `uv sync` to install all required packages.
3. Ensure you have an active internet connection (needed to download the FF5 factors; a cached copy in `data/` is used otherwise).
4. From the project root, run `uv run quarto render replicating-the-value-factor.qmd`.
5. The rendered document contains all results; the comparison table and grid results are also written to `results/tables/`.

No manual steps are required; all procedures are fully automated. The author verified that the instructions run successfully from a fresh environment on their local machine before submission.

## 7. List of Tables and Figures

All tables and figures in the document are reproduced by the main Quarto document:

| Output | Program (chunk) | Output file | Notes |
|---|---|---|---|
| Value premium comparison table | `value-factor-comparison` | `results/tables/value_premium_comparison.csv` | Independent vs. dependent vs. published HML |
| Specification grid results | `non-standard-errors-grid` | `results/tables/p_hacking_results.csv` | 96 specifications |
| Figure 1: value premium distribution | `fig-nse` | rendered in the document | Published HML marked as vertical line |
| Figure 2: CAPM-alpha distribution | `fig-nse-capm` | rendered in the document | Optional extension |

## 8. References

Fama, Eugene F., and Kenneth R. French. 2015. "A Five-Factor Asset Pricing Model." *Journal of Financial Economics* 116 (1): 1–22.

French, Kenneth R. 2026. *Data Library*. <https://mba.tuck.dartmouth.edu/pages/faculty/ken.french/data_library.html>

Scheuch, Christoph, Stefan Voigt, Patrick Weiss, and Christoph Frey. 2024. *Tidy Finance with Python*. Chapman & Hall/CRC. <https://www.tidy-finance.org/python/>

## 9. Acknowledgements

This README follows the structure of the Social Science Data Editors' README template, available at <https://social-science-data-editors.github.io/template_README/>. The analysis builds on code developed during the course hands-on sessions based on Tidy Finance with Python.
