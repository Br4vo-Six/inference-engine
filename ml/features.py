from functools import reduce

from multiset import Multiset
import numpy as np
from models.tx import Tx
from utils.ml_util import divide_by_zero_handler, get_corr_coeff_data, get_diversity_data, get_gini_coeff, get_stat_data, parse_optional


def get_basic_features(features: dict[str, float], tx: Tx):
    features['size'] = parse_optional(tx.size, 0)
    features['vsize'] = parse_optional(tx.vsize, 0)
    features['fee'] = parse_optional(tx.fees, 0)
    features['num_input'] = parse_optional(tx.vin_sz, 0)
    features['num_output'] = parse_optional(tx.vout_sz, 0)
    features['block_height'] = parse_optional(tx.block_height, -1)
    features['block_time'] = tx.confirmed.timestamp(
    ) if tx.confirmed is not None else -1
    return features


def get_stat_features(features: dict[str, float], tx: Tx):
    input_values = [
        inp.output_value
        for inp in parse_optional(tx.inputs, [])
        if inp.output_value is not None
    ]
    output_values = [
        outp.value
        for outp in parse_optional(tx.outputs, [])
        if outp.value is not None
    ]
    input_ages = [
        inp.age
        for inp in parse_optional(tx.inputs, [])
        if inp.age is not None
    ]

    for k, v in get_stat_data(input_values).items():
        features[f'input_value_{k}'] = v
    for k, v in get_stat_data(output_values).items():
        features[f'output_value_{k}'] = v
    for k, v in get_stat_data(input_ages).items():
        features[f'input_age_{k}'] = v

    return features


def get_derived_features(features: dict[str, float], tx: Tx):
    features['fee_size_ratio'] = divide_by_zero_handler(
        features['fee'], features['size'])
    features['fee_vsize_ratio'] = divide_by_zero_handler(
        features['fee'], features['vsize'])
    features['fee_in_ratio'] = divide_by_zero_handler(
        features['fee'], features['num_input'])
    features['fee_out_ratio'] = divide_by_zero_handler(
        features['fee'], features['num_output'])
    features['in_out_ratio'] = divide_by_zero_handler(
        features['num_input'], features['num_output'])
    features['sum_input_value_per_byte'] = divide_by_zero_handler(
        features['input_value_sum'], features['size'])
    features['sum_output_value_per_byte'] = divide_by_zero_handler(
        features['output_value_sum'], features['size'])

    return features


def get_address_features(features: dict[str, float], tx: Tx):
    features['num_address'] = len(parse_optional(tx.addresses, []))
    multi_input_address_list = reduce(
        lambda prev, curr: prev + curr,
        [parse_optional(inp.addresses, [])
         for inp in parse_optional(tx.inputs, [])],
        []
    )
    multi_output_address_list = reduce(
        lambda prev, curr: prev + curr,
        [parse_optional(outp.addresses, [])
         for outp in parse_optional(tx.outputs, [])],
        []
    )

    unique_input_address = Multiset(multi_input_address_list)
    unique_output_address = Multiset(multi_output_address_list)
    features['num_unique_input_address'] = len(
        unique_input_address.distinct_elements())
    features['num_unique_output_address'] = len(
        unique_output_address.distinct_elements())

    multiple_input_address = [
        k for k, v in unique_input_address.items() if v > 1]
    features['num_multiple_input_address'] = len(multiple_input_address)

    count_input_address = [v for k, v in unique_input_address.items()]
    count_output_address = [v for k, v in unique_output_address.items()]
    input_address_entropy = get_diversity_data(count_input_address)
    output_address_entropy = get_diversity_data(count_output_address)
    features['input_address_entropy'] = input_address_entropy
    features['output_address_entropy'] = output_address_entropy

    input_address_gini = get_gini_coeff(count_input_address)
    output_address_gini = get_gini_coeff(count_output_address)
    features['input_address_gini'] = input_address_gini
    features['output_address_gini'] = output_address_gini

    return features, unique_input_address, unique_output_address


def get_additional_output_features(
        features: dict[str, float],
        tx: Tx,
        multiset_input_address: Multiset,
        multiset_output_address: Multiset,
):
    common_address = multiset_output_address.intersection(
        multiset_input_address)
    features['num_change'] = len(common_address.distinct_elements())
    if len(common_address) == 0:
        features['total_change'] = 0
        features['mean_change'] = 0
        features['mean_change_ratio'] = 0
    else:
        input_value_by_address = {}
        for inp in parse_optional(tx.inputs, []):
            addresses = parse_optional(inp.addresses, [])
            n = len(addresses)
            for address in addresses:
                if address not in input_value_by_address:
                    input_value_by_address[address] = 0.0
                input_value_by_address[address] += inp.value / n
        output_value_by_address = {}
        for outp in parse_optional(tx.outputs, []):
            addresses = parse_optional(outp.addresses, [])
            n = len(addresses)
            for address in addresses:
                if address not in output_value_by_address:
                    output_value_by_address[address] = 0.0
                output_value_by_address[address] += outp.value / n

        changes = []
        changes_ratio = []
        for k, v in common_address.items():
            if k in output_value_by_address:
                changes.append(output_value_by_address[k])
                changes_ratio.append(
                    output_value_by_address[k] / input_value_by_address[k])
        features['total_change'] = np.sum(changes)
        features['mean_change'] = np.sum(changes) / len(changes)
        features['mean_change_ratio'] = np.sum(
            changes_ratio) / len(changes_ratio)

    dust = [
        parse_optional(outp.value, 0)
        for outp in parse_optional(tx.outputs, [])
        if parse_optional(outp.value, 0) < 546
    ]
    features['num_dust'] = len(dust)
    features['total_dust'] = np.sum(dust)

    return features


def get_corr_coeff_features(features: dict[str, float], tx: Tx):
    def get_stat_list(_k: str):
        return [
            features[f'{_k}_min'],
            features[f'{_k}_max'],
            features[f'{_k}_range'],
            features[f'{_k}_median'],
            features[f'{_k}_sum'],
            features[f'{_k}_mean'],
            features[f'{_k}_var'],
            features[f'{_k}_std'],
            features[f'{_k}_skew'],
            features[f'{_k}_kurt'],
            features[f'{_k}_gini'],
        ]

    input_value_stat = get_stat_list('input_value')
    output_value_stat = get_stat_list('output_value')
    input_age_stat = get_stat_list('input_age')

    for k, v in get_corr_coeff_data(input_value_stat, output_value_stat).items():
        features[f'in_out_value_{k}'] = v
    for k, v in get_corr_coeff_data(input_age_stat, input_value_stat).items():
        features[f'in_age_in_value_{k}'] = v
    for k, v in get_corr_coeff_data(input_age_stat, output_value_stat).items():
        features[f'in_age_out_value_{k}'] = v

    return features
