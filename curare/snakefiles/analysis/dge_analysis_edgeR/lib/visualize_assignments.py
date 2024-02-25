"""
Create barchart from multiple count tables

Usage:
    generate_report_data.py --input <count_table_folder> --output <image_output>
    generate_report_data.py (--version | --help)

Options:
    -h --help               Show this help message and exit
    --version               Show version and exit

    -i <count_table_folder> --input <count_table_folder>           Directory containing all count tables
    -o <image_output> --output <image_output>                      SVG output file
"""

from pathlib import Path
import sys
from typing import Any, Dict, List, Union
import pprint

import matplotlib
matplotlib.use('Agg')
matplotlib.rcParams.update({'figure.autolayout': True})
matplotlib.rcParams.update({'font.size': 12})
import matplotlib.pyplot as plt
import pandas
import numpy as np


from docopt import docopt
from matplotlib.colors import ListedColormap

PP = pprint.PrettyPrinter(indent=2)


def select_files(folder: Path, use_all: bool = True) -> List[Path]:
    file_list: List[Path] = []
    if use_all:
        for file in folder.iterdir():
            if file.name.endswith('.txt.summary') and not file.name.startswith('region'):
                file_list.append(file)
    else:
        used_types: List[str] = ['rRNA', 'tRNA']
        if (folder / 'CDS.txt.summary').exists():
            used_types.append('CDS')
        elif (folder / 'gene.txt.summary').exists():
            used_types.append('gene')
        elif (folder / 'exon.txt.summary').exists():
            used_types.append('exon')
        for feature_type in used_types:
            file_list.append(folder / (feature_type + '.txt.summary'))

    return file_list


def parse_input(files: List[Path]) -> Dict[str, Dict[str, int]]:
    assigned_alignments: Dict[str, Union[Dict[str, int], None]] = {}
    missing_features: List[str] = []
    for file in files:
        feature_type: str = file.name[:-len('.txt.summary')]
        if not file.exists():
            missing_features.append(feature_type)
        else:
            print(file)
            with file.open() as f:
                tsv: List[List[str]] = [line.strip().split('\t') for line in f]
            header: List[str] = [col[col.rindex('/')+1:col.rindex('.')] for col in tsv[0][1:]]
            for col in header:
                if col not in assigned_alignments:
                    assigned_alignments[col] = {}
            for line in tsv:
                if line[0] == 'Assigned':
                    for i, entry in enumerate(line[1:]):
                        assigned_alignments[header[i]][feature_type] = int(entry)
    for feature in missing_features:
        for col in assigned_alignments.values():
            col[feature] = 0
    return assigned_alignments


def print_visualizations(assignment_data: Dict[str, Dict[str, int]], output_folder: Path):
    for sample in assignment_data.keys():
        keys: List[str] = list(assignment_data[sample].keys())
        values: List[int] = [assignment_data[sample][key]for key in keys]
        df: pandas.DataFrame = pandas.DataFrame({'keys': keys, 'values': values})
        ax: plt.Axes = df.plot.bar(x='keys', y='values', legend=False, log=True, color='#4878d0')
        ax.set_xlabel("")
        ax.set_ylabel("# Assigned Reads")
        plt.savefig(output_folder / (sample + '.svg'))


def main():
    args = docopt(__doc__, version='1.0')
    input_dir = Path(args["--input"]).resolve()
    if not input_dir.exists() or not input_dir.is_dir():
        print("Input folder must be an existing directory!", file=sys.stderr)
        exit(1)
    output_folder = Path(args["--output"]).resolve()
    if not output_folder.exists():
        output_folder.mkdir(parents=True)
    if not output_folder.is_dir():
        print("Output folder exist and is no directory!", file=sys.stderr)
        exit(1)

    selected_files: List[Path] = select_files(input_dir)
    assignment_data: Dict[str, Dict[str, int]] = parse_input(selected_files)
    print_visualizations(assignment_data, output_folder)


if __name__ == '__main__':
    main()
