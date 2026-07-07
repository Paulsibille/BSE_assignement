import tidyfinance as tf
import polars as pl
from plotnine import ggplot, aes, geom_histogram, geom_vline, labs
from joblib import Parallel, delayed, cpu_count
from itertools import product
import pyfixest as pf
