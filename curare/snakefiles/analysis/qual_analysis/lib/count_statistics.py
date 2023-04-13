#!/usr/bin/env python3
"""
Visualize and summarize featureCounts statistics created with Curare "qual_analysis".

Usage:
    count_statistics.py --count_tables_dir <directory> --output_dir <directory> --start_column_counts <col_nr> --length_column <length_nr> --condition_table <condition_table> --exp_threshold <min_expression> [--benchmark]
    count_statistics.py (--version | --help)

Options:
    -h --help               Show this help message and exit
    --version               Show version and exit
    --benchmark             Run tool in benchmark mode

    -i <directory> --count_tables_dir <directory>               featureCounts count table
    -o <directory> --output_dir <directory>                     Normalized count table
    -c <col_nr> --start_column_counts <col_nr>                  First column with counts (counting starts at 1)
    -l <length_nr> --length_column <length_nr>                  Column containing gene length (counting starts at 1)
    -c <condition_table> --condition_table <condition_table>    Tab-separated table with two column. 
                                                                First column: sample name, second column: condition
    -t <min_expression> --exp_threshold <min_expression>        Minimal expression that an feature counts as expressed

"""

from pathlib import Path
import statistics
import sys
from typing import Dict, List, Tuple

from docopt import docopt
#import matplotlib.figure as fig
import matplotlib.pyplot as plt
import pandas as pd
import seaborn as sns
import time
from upsetplot import UpSet

from matplotlib import rcParams
rcParams.update({'figure.autolayout': True})



def main(count_table_dir: Path, output: Path, conditions_table_path: Path, start_column: int, length_column: int, expression_threshold: int, benchmark: bool):
    sns.set_theme(style="ticks", palette="pastel")
    if benchmark:
        timestamps: List[Tuple[str, float]] = []
        timestamps.append( ("Start", time.time()) )
    conditions_table: Dict[str, List[str]] = {}   # Key / Value <=> Condition / List of samples
    conditions_order: List[str] = []   # List of all conditions ordered by appearance in <conditions_table_path>
    with open(conditions_table_path) as conditions_table_file:
        for line in conditions_table_file:
            sample, condition = line.split("\t")
            conditions_table.setdefault(condition, []).append(sample.strip())
            if condition not in conditions_order:
                conditions_order.append(condition)

    if benchmark: timestamps.append( ("Read conditions", time.time()) )

    output_directories: Dict[str, Path] = init_directories(output)
    count_table_path: Path
    for count_table_path in count_table_dir.iterdir():
        if benchmark: timestamps.append( (count_table_path.stem + " - Start Count Table", time.time()) )
        if not count_table_path.is_file() or count_table_path.name.endswith("summary"):
            continue
        
        current_index_of_length_col: int = length_column
        current_index_of_start_col: int = start_column
        
        count_table: pd.DataFrame = pd.read_csv(count_table_path, sep="\t", comment="#")
        
        # Move gene names out of table into index
        count_table.set_index(["Geneid", "Chr"], inplace=True)
        current_index_of_start_col -= 2
        current_index_of_length_col -= 2
        
        # Remove directory and file extension from column names
        count_table.rename(columns=fix_col_names, inplace=True)

        # Create sub-dataframes
        gene_length: pd.Series = count_table.iloc[:, current_index_of_length_col]
        only_count_data: pd.DataFrame = count_table.iloc[:,current_index_of_start_col:]
        
        # Reorder columns
        column_order: List[str] = [entry for condition in conditions_order for entry in conditions_table[condition]]
        only_count_data = only_count_data[column_order]

        if benchmark: timestamps.append( (count_table_path.stem + " - Initialized Dataframe", time.time()) )

        # Horizontal boxplot with logarithmix x-axis
        axis: plt.Axes
        axis = sns.boxplot(data=only_count_data, orient="h")
        axis.set_xscale("log")
        plot_path: Path = output_directories["boxplot_log"] / Path(count_table_path.stem + "_boxplot_log.svg")
        plt.savefig(plot_path)
        plt.clf()
        if benchmark: timestamps.append( (count_table_path.stem + " - Horiz. Boxplot", time.time()) )

        # Vertical boxplot without outliers
        axis = sns.boxplot(data=only_count_data, showfliers=False)
        plot_path = output_directories["boxplot_trimmed_outliers"] / Path(count_table_path.stem + "_boxplot.svg")
        plt.savefig(plot_path)
        plt.clf()
        if benchmark: timestamps.append( (count_table_path.stem + " - Vertical Boxplot", time.time()) )

        # Violinplot
        axis = sns.violinplot(data=only_count_data)
        plot_path = output_directories["violinplot"] / Path(count_table_path.stem + "_violinplot.svg")
        plt.savefig(plot_path)
        plt.clf()
        if benchmark: timestamps.append( (count_table_path.stem + " - Violinplot", time.time()) )

        # Lineplot with samples as x-axis and each gene as a seperate line
        long_only_count_data: pd.DataFrame = only_count_data.copy()
        long_only_count_data.rename(columns=lambda x: "counts"+x, inplace=True)
        long_only_count_data["gene_name"] = long_only_count_data.index
        long_only_count_data = pd.wide_to_long(long_only_count_data, "counts", i="gene_name", j="sample", suffix=".+")
        axis = sns.lineplot(data=long_only_count_data, x="sample", y="counts", units="gene_name", estimator=None, legend=False)
        plot_path = output_directories["lineplot"] / Path(count_table_path.stem + "_lineplot.svg")
        plt.savefig(plot_path)
        plt.clf()
        if benchmark: timestamps.append( (count_table_path.stem + " - Lineplot", time.time()) )

        # Upset chart with genes found in every sample of a condition
        counts_per_condition: pd.DataFrame = sum_conditions(only_count_data, conditions_table, conditions_order)
        if benchmark: timestamps.append( (count_table_path.stem + " - Upset - Sum conditions", time.time()) )
        upset_data: pd.Series = (counts_per_condition >= expression_threshold).apply(lambda x: tuple(x), axis=1, raw=False)
        upset_value_counts: pd.Series[int] = upset_data.value_counts()
        stripped_conditions_order: List[str] = [label.strip() for label in counts_per_condition.columns.values]
        upset_value_counts = upset_value_counts.reindex(pd.MultiIndex.from_tuples(upset_value_counts.index, names=stripped_conditions_order))
        if benchmark: timestamps.append( (count_table_path.stem + " - Upset - Series Manipulation", time.time()) )
        rcParams.update({'figure.autolayout': False})
        UpSet(upset_value_counts, subset_size='sum', show_counts=True).plot()
        plt.ylabel("#Features")
        plot_path = output_directories["upsetplot"] / Path(count_table_path.stem + "_upsetplot.svg")
        plt.savefig(plot_path)
        plt.clf()
        rcParams.update({'figure.autolayout': True})
        if benchmark: timestamps.append( (count_table_path.stem + " - Upset - Print Plot", time.time()) )

        sums_file_path: Path = output_directories["upsetplot"] / Path(count_table_path.stem + "_sums.tsv")
        features_file_path: Path = output_directories["upsetplot"] / Path(count_table_path.stem + "_features.tsv")
        with sums_file_path.open(mode='w') as sums_file:
            sums_file.write("\t".join(stripped_conditions_order) + "\t#features" + "\n")
            for pattern, counts in upset_value_counts.items():
                pattern_output: str = "\t".join(["X" if value else "-" for value in pattern])
                sums_file.write("{}\t{}\n".format(pattern_output, counts))
        if benchmark: timestamps.append( (count_table_path.stem + " - Upset - Writing Sum Files", time.time()) )
        with features_file_path.open(mode='w') as feat_file:
            feat_file.write("\t".join(stripped_conditions_order) + "\tfeature_name\tchromosome" + "\n")
            for feature, pattern in upset_data.items():
                pattern_output: str = "\t".join(["X" if value else "-" for value in pattern])
                feat_file.write("{}\t{}\n".format(pattern_output, "\t".join(feature)))
        if benchmark: timestamps.append( (count_table_path.stem + " - Upset - Writing Features File", time.time()) )

        plt.close('all')
        if benchmark: timestamps.append( (count_table_path.stem + " - Closed Plots", time.time()) )
    
    if benchmark: 
        timestamps = [(timepoint[0], next_timepoint[1] - timepoint[1]) for timepoint, next_timepoint in zip(timestamps[:-1], timestamps[1:])]
        for label, timepoint in timestamps:
            print("{:30}\t{:.1f}".format(label, timepoint-timestamps[0][1]))
        print()
        times = [timepoint[1] for timepoint in timestamps]
        print("Mean: {:.1f}".format(statistics.mean(times)))
        print("Median: {:.1f}".format(statistics.median(times)))
        print("Std.Dev.: {:.1f}".format(statistics.stdev(times)))
        print("Min: {:.1f}".format(min(times)))
        print("Max: {:.1f}".format(max(times)))
        print("Sum: {:.1f}".format(sum(times)))
        print("#Timepoints: {:.1f}".format(len(times)))


def fix_col_names(x):
    return x.split("/")[-1].split(".")[0]


def init_directories(output_dir: Path) -> Dict[str, Path] :
    directories: Dict[str, Path] = {
        "output": output_dir,
        "boxplot_log": output_dir / "boxplot_log",
        "boxplot_trimmed_outliers": output_dir / "boxplot_trimmed_outliers",
        "violinplot": output_dir / "violinplot",
        "lineplot": output_dir / "lineplot",
        "upsetplot": output_dir / "upsetplot",
    }
    for dir_path in directories.values():
        dir_path.mkdir(exist_ok=True)
    
    return directories


# Calculate the sum of every expression per gene and condition 
def sum_conditions(count_table: pd.DataFrame, conditions_dict: Dict[str, List[str]], condition_order: List[str]) -> pd.DataFrame:
    counts_per_condition: Dict[str, pd.DataFrame] = {}
    for condition in condition_order:
        condition_samples: List[str] = conditions_dict[condition]
        counts_per_condition[condition] = count_table[condition_samples].sum(axis=1)
    return pd.DataFrame(counts_per_condition)


if __name__ == "__main__":
    arguments = docopt(__doc__, version='1.0')

    arguments["--count_tables_dir"] = Path(arguments["--count_tables_dir"])
    if not arguments["--count_tables_dir"].is_dir():
        print("Error: \"--count_tables_dir\" must be an directory.", file=sys.stderr)
        sys.exit(10)

    arguments["--output_dir"] = Path(arguments["--output_dir"])

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

    arguments["--condition_table"] = Path(arguments["--condition_table"])
    if not (arguments["--condition_table"].exists() and arguments["--condition_table"].is_file()):
        print("Conditional file does not exist: \"{}\".".format(arguments["--condition_table"]), file=sys.stderr)
        sys.exit(13)

    try:
        arguments["--exp_threshold"] = int(arguments["--exp_threshold"])
    except:
        print("Expression threshold is not an integer: \"{}\".".format(arguments["--exp_threshold"]), file=sys.stderr)
        sys.exit(14)

    main(arguments["--count_tables_dir"], arguments["--output_dir"], arguments["--condition_table"], arguments["--start_column_counts"]-1, arguments["--length_column"]-1, arguments["--exp_threshold"], arguments["--benchmark"])