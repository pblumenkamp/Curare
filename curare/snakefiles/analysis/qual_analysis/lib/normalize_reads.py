#!/usr/bin/env python3
"""
Normalize featureCounts count tables.

Usage:
    normalize_reads.py --input <input> --output <output> --method <normalization_method> --start_column_counts <col_nr> --length_column <length_nr>
    normalize_reads.py (--version | --help)

Options:
    -h --help               Show this help message and exit
    --version               Show version and exit

    -i <count_table_file> --input <count_table_file>           featureCounts count table
    -o <count_table_file> --output <count_table_file>          Normalized count table
    -m <normalization_method> --method <normalization_method>  Normalization method (TPM, FPKM)
    -c <col_nr> --start_column_counts <col_nr>                 First column with counts (counting starts at 1)
    -l <length_nr> --length_column <length_nr>                 Column containing gene length (counting starts at 1)
"""

import sys
from typing import List
from docopt import docopt
import pandas as pd

def main(count_table_path: str, output: str, normalization_method: str, start_column: int, length_column: int):
    count_table: pd.DataFrame = pd.read_csv(count_table_path, sep="\t", comment="#")
    only_count_data: pd.DataFrame = count_table.iloc[:,start_column:]
    gene_length: pd.Series = count_table.iloc[:, length_column]

    # Calculate normalization
    if normalization_method == "TPM":
        # TPM = (Counts_i / Gene_Length_i) / Sum(Counts / Gene_Lengths) * 10^6
        counts_per_basepair: pd.DataFrame = only_count_data.divide(gene_length, axis=0) 
        counts_per_basepair_sums: pd.Series = counts_per_basepair.sum(axis=0, numeric_only=True)
        tpm_normalized: pd.DataFrame = (counts_per_basepair*1_000_000).divide(counts_per_basepair_sums, axis=1)
        tpm_results: pd.DataFrame = pd.concat([count_table.iloc[:,:start_column], tpm_normalized], axis=1)
        tpm_results.to_csv(path_or_buf=output, sep="\t", index=False)
    if normalization_method == "FPKM":
        # FPKM = Counts_i / (Sum(Counts) * Gene_Length_i) * 10^9
        count_sums: pd.Series = only_count_data.sum(axis=0, numeric_only=True)
        fpkm_normalized: pd.DataFrame = (only_count_data*1_000_000_000).divide(count_sums, axis=1).divide(gene_length, axis=0)
        fpkm_results: pd.DataFrame = pd.concat([count_table.iloc[:,:start_column], fpkm_normalized], axis=1)
        fpkm_results.to_csv(path_or_buf=output, sep="\t", index=False)


if __name__ == "__main__":
    arguments = docopt(__doc__, version='1.0')

    allowed_normalization_methods = ["FPKM", "TPM"]
    arguments["--method"] = arguments["--method"].upper()
    if arguments["--method"] not in allowed_normalization_methods:
        print("Unknown normalization method \"{}\".\nFollowing methods are implemented: {}".format(
            arguments["--method"],
            ", ".join(allowed_normalization_methods)
        ), file=sys.stderr)
        sys.exit(10)

    try:
        arguments["--start_column_counts"] = int(arguments["--start_column_counts"])
    except:
        print("Start column is not an integer: \"{}\".".format(arguments["--start_column_counts"]), file=sys.stderr)
        sys.exit(11)
    
    try:
        arguments["--length_column"] = int(arguments["--length_column"]) 
    except:
        print("Length column is not an integer: \"{}\".".format(arguments["--length_column"]), file=sys.stderr)
        sys.exit(12)

    main(arguments["--input"], arguments["--output"], arguments["--method"], arguments["--start_column_counts"]-1, arguments["--length_column"]-1)