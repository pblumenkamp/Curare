"""
Convert DESeq2 results to usable data for the large report

Usage:
    generate_report_data.py --fc_stats <featureCounts_stats> --comparison_dir <deseq2_comparison_dir> --output <output> [--paired-end]
    generate_report_data.py (--version | --help)

Options:
    -h --help               Show this help message and exit
    --version               Show version and exit

    -f <featureCounts_stats> --fc_stats <featureCounts_stats>           TSV containing the statistics of all featureCounts runs
    -c <deseq2_comparison_dir> --comparison_dir <deseq2_comparison_dir> Folder containing all DESeq2 comparison
    -o <output> --output <output>                                       Created js containing featureCounts statistics
    --paired-end                                                        Paired-End run, else Single-End
"""

import json
import math
from pathlib import Path
from typing import Any, Dict, List

from docopt import docopt


def parse_featurecounts_stats(stats_file: Path) -> List[Dict[str, str]]:
    stats_table: List[Dict[str, str]] = []
    with stats_file.open() as file:
        header = next(file).strip().split("\t")
        for sample in header[1:]:
            sample = sample[len("mapping/"):-len(".bam")]
            stats_table.append({'name': sample})
        for line in file:
            line = line.strip().split("\t")
            category: str = line[0]
            for table, value in zip(stats_table, line[1:]):
                table[category] = value
    return stats_table


def parse_deseq2_comparison(comp_folder: Path) -> List[Dict[str, str]]:
    summary_table: List[Dict[str, str]] = []
    for child in comp_folder.iterdir():
        if child.is_file() and str(child).endswith('.csv'):
            name_splitted: List[str] = child.name[len('deseq2_results_'):-len('.csv')].split('_Vs_')
            summary: Dict[str, Any] = {
                'comparison': '{} Vs. {}'.format(name_splitted[0], name_splitted[1]),
                'adjP_smaller_5': 0,
                'adjP_smaller_1': 0,
                'adjP_smaller_0.1': 0,
                'lowest_lfc': 0,
                'lowest_lfc_name': '',
                'highest_lfc': 0,
                'highest_lfc_name': ''
            }
            with child.open() as file:
                comp_file: List[str] = file.readlines()

            header: List[str] = comp_file[0].strip().split('\t')
            comp_file = comp_file[1:]
            for line in comp_file:
                name, baseMean, log2FC, lfcSE, stat, pvalue, padj = line.strip().split('\t')
                if padj != 'NA':
                    padj = float(padj)
                    if padj < 0.05:
                        summary['adjP_smaller_5'] += 1
                    if padj < 0.01:
                        summary['adjP_smaller_1'] += 1
                    if padj < 0.001:
                        summary['adjP_smaller_0.1'] += 1
                if log2FC != 'NA':
                    log2FC = float(log2FC)
                    if log2FC > summary['highest_lfc']:
                        summary['highest_lfc'] = log2FC
                        summary['highest_lfc_name'] = name.strip('"')
                    elif log2FC < summary['lowest_lfc']:
                        summary['lowest_lfc'] = log2FC
                        summary['lowest_lfc_name'] = name.strip('"')

            lfc_dist_label: List[str] = []
            stepsize: int = 5    # real_stepsize = stepsize / 10
            for i in range(min(0, math.floor(summary['lowest_lfc'])*10), max(0, math.ceil(summary['highest_lfc'])*10), stepsize):
                lfc_dist_label.append(str(i / 10))
            lfc_dist_data: List[float] = [0 for x in range(len(lfc_dist_label))]
            for line in comp_file:
                name, baseMean, log2FC, lfcSE, stat, pvalue, padj = line.strip().split('\t')
                if log2FC != 'NA':
                    log2FC: float = float(log2FC)
                    baseline: float = (float(log2FC) - float(lfc_dist_label[0])) * 10
                    bucket: int = int(baseline // stepsize)
                    lfc_dist_data[bucket] += 1
            lfc_dist_label.append(str(float(lfc_dist_label[-1]) + 0.5))  # need one additional label for x-axis
            summary['lfc_distribution'] = {'label': lfc_dist_label, 'data': lfc_dist_data}

            summary_table.append(summary)

    return summary_table


def generate_report_data(output_file: Path, fc_file: Path, comnparison_folder: Path, is_paired_end: bool):
    featurecounts: List[Dict[str, str]] = parse_featurecounts_stats(fc_file)
    deseq2_summary: List[Dict[str, str]] = parse_deseq2_comparison(comnparison_folder)

    with output_file.open('w') as f:
        f.write('window.Curare.deseq2 = (function() {\n')
        f.write('  const paired_end = {}\n'.format("true" if is_paired_end else "false"))

        f.write('  const featurecounts = ')
        f.write(json.dumps(featurecounts, indent=2).replace('\n', '\n  '))
        f.write('\n')

        f.write('  const deseq2_summary = ')
        f.write(json.dumps(deseq2_summary, indent=2).replace('\n', '\n  '))
        f.write('\n')

        f.write('  return {paired_end: paired_end, featurecounts: featurecounts, deseq2_summary: deseq2_summary};\n')
        f.write('}());')


def main():
    args = docopt(__doc__, version='1.0')
    fc_file = Path(args["--fc_stats"]).resolve()
    comparison_dir = Path(args["--comparison_dir"]).resolve()
    output_file = Path(args["--output"]).resolve()

    generate_report_data(output_file, fc_file, comparison_dir, args["--paired-end"])


if __name__ == '__main__':
    main()
