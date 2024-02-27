"""
Convert edgeR results to usable data for the large report

Usage:
    generate_report_data.py --fc_stats <featureCounts_stats> --fc_main_feature <fc_main_feature> --comparison_dir <edger_comparison_dir> --visualization <vis_dir> --output <output> --counttable <count_table> [--paired-end]
    generate_report_data.py (--version | --help)

Options:
    -h --help               Show this help message and exit
    --version               Show version and exit

    -f <featureCounts_stats> --fc_stats <featureCounts_stats>           TSV containing the statistics of all featureCounts runs
    -t <fc_main_feature> --fc_main_feature <fc_main_feature>            GFF main featue for usage in featureCounts (e.g. CDS)
    -c <edger_comparison_dir> --comparison_dir <edger_comparison_dir> Folder containing all edgeR comparison
    -v <vis_dir> --visualization <vis_dir>                              Folder containing all visualization
    -c <count_table> --counttable <count_table>                         Created count table
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


def parse_edger_comparison(comp_folder: Path) -> List[Dict[str, str]]:
    summary_table: List[Dict[str, str]] = []
    for child in comp_folder.iterdir():
        if child.is_file() and str(child).endswith('.csv'):
            name_splitted: List[str] = child.name[len('edger_results_'):-len('.csv')].split('_Vs_')
            summary: Dict[str, Any] = {
                'comparison': '{} Vs. {}'.format(name_splitted[0], name_splitted[1]),
                'adjP_smaller_5': 0,
                'adjP_smaller_1': 0,
                'adjP_smaller_0.1': 0,
                'lowest_lfc': 0,
                'lowest_lfc_name': '-',
                'highest_lfc': 0,
                'highest_lfc_name': '-'
            }
            with child.open() as file:
                comp_file: List[str] = file.readlines()

            header: List[str] = comp_file[0].strip().split('\t')
            comp_file = comp_file[1:]
            for line in comp_file:
                name, length, log2FC, logCPM, pvalue, FDR = line.strip().split('\t')
                if FDR != 'NA':
                    FDR = float(FDR)
                    if FDR < 0.05:
                        summary['adjP_smaller_5'] += 1
                    if FDR < 0.01:
                        summary['adjP_smaller_1'] += 1
                    if FDR < 0.001:
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
                name, length, log2FC, logCPM, pvalue, FDR = line.strip().split('\t')
                if log2FC != 'NA':
                    log2FC: float = float(log2FC)
                    baseline: float = (float(log2FC) - float(lfc_dist_label[0])) * 10
                    bucket: int = int(baseline // stepsize)
                    lfc_dist_data[bucket] += 1
            lfc_dist_label.append(str(float(lfc_dist_label[-1]) + 0.5))  # need one additional label for x-axis
            summary['lfc_distribution'] = {'label': lfc_dist_label, 'data': lfc_dist_data}

            summary_table.append(summary)

    return summary_table


def parse_feat_assignment_folder(folder: Path) -> Dict[str, str]:
    return {file.name[:-len('.svg')]: file.name for file in folder.iterdir() if file.name.endswith('svg')}


def generate_report_data(output_file: Path, fc_file: Path, comnparison_folder: Path, vis_folder: Path, is_paired_end: bool, fc_main_feature: str, count_table_file: Path):
    featurecounts: List[Dict[str, str]] = parse_featurecounts_stats(fc_file)
    edger_summary: List[Dict[str, str]] = parse_edger_comparison(comnparison_folder.resolve())
    feature_assignemnt: Dict[str, str] = parse_feat_assignment_folder(vis_folder / "feature_assignments")

    with output_file.open('w') as f:
        f.write('window.Curare.edger = (function() {\n')
        f.write('  const paired_end = {}\n'.format("true" if is_paired_end else "false"))
        f.write('  const fc_main_feature = "{}"\n'.format(fc_main_feature))
        f.write('  const count_table_path = "{}"\n'.format(count_table_file))
        f.write('  const edger_dir_path = "{}"\n'.format(comnparison_folder))


        f.write('  const featurecounts = ')
        f.write(json.dumps(featurecounts, indent=2).replace('\n', '\n  '))
        f.write('\n')

        f.write('  const edger_summary = ')
        f.write(json.dumps(edger_summary, indent=2).replace('\n', '\n  '))
        f.write('\n')

        f.write('  const feature_assignment = ')
        f.write(json.dumps(feature_assignemnt, indent=2).replace('\n', '\n  '))
        f.write('\n')

        f.write('  return {paired_end: paired_end, fc_main_feature: fc_main_feature, featurecounts: featurecounts, edger_summary: edger_summary, feature_assignment: feature_assignment, count_table_path: count_table_path, edger_dir_path: edger_dir_path};\n')
        f.write('}());')


def main():
    args = docopt(__doc__, version='1.1')
    fc_file = Path(args["--fc_stats"]).resolve()
    fc_main_feature = args["--fc_main_feature"]
    comparison_dir = Path(args["--comparison_dir"])
    output_file = Path(args["--output"]).resolve()
    visualization = Path(args["--visualization"]).resolve()
    count_table_file: Path = Path(args["--counttable"])


    generate_report_data(output_file, fc_file, comparison_dir, visualization, args["--paired-end"], fc_main_feature, count_table_file)


if __name__ == '__main__':
    main()
