import numpy as np
from typing import Optional, TypeVar
from scipy.stats import skew, kurtosis, pearsonr

T = TypeVar("T")


def divide_by_zero_handler(a, b):
    if b != 0:
        return a/b
    return 0


def parse_optional(value: Optional[T], default_value: T) -> T:
    if value is None:
        return default_value
    return value


def get_gini_coeff(np_list):
    if len(np_list) == 0:
        return 0
    sorted_data = np.sort(np_list)
    n = len(np_list)
    gini_numerator = np.sum((2 * np.arange(1, n + 1) - n - 1) * sorted_data)
    gini_denominator = n * np.sum(sorted_data)

    gini_coefficient = divide_by_zero_handler(
        gini_numerator,
        gini_denominator
    )

    return gini_coefficient


def get_stat_data(raw_list: list[int]):
    np_list = np.array(raw_list, dtype=np.float64)

    value_min = np_list.min()
    value_max = np_list.max()
    value_range = value_max - value_min
    value_median = np.median(np_list)
    value_sum = np_list.sum()
    value_mean = np_list.mean()
    value_var = np.var(np_list)
    value_std = np_list.std()
    value_skew = skew(np_list)
    if np.isnan(value_skew):
        value_skew = 0
    value_kurt = kurtosis(np_list)
    if np.isnan(value_kurt):
        value_kurt = 0
    value_gini = get_gini_coeff(np_list)
    # if np.isnan(value_skew):
    #     print(f'NAN -> {np_list.shape}, skew={value_skew}, kurt={value_kurt}')
    return {
        'min': value_min,
        'max': value_max,
        'range': value_range,
        'median': value_median,
        'sum': value_sum,
        'mean': value_mean,
        'var': value_var,
        'std': value_std,
        'skew': value_skew,
        'kurt': value_kurt,
        'gini': value_gini
    }


def get_diversity_data(raw_list: list[int]):
    if len(raw_list) == 0:
        return 0
    np_list = np.array(raw_list, dtype=np.float64)
    s = np.sum(np_list)
    if s == 0:
        return 0
    probs = np_list / s
    entropy = -np.sum(probs * np.log2(probs))
    return entropy


def get_corr_coeff_data(x, y):
    corr_coeff = pearsonr(x, y)
    return {
        'cc_stat': corr_coeff.statistic,
        'cc_p': corr_coeff.pvalue
    }
