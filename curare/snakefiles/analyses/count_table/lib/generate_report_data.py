"""
Convert featureCounts results to usable data for the large report

Usage:
    generate_report_data.py --stats <featureCounts_stats> --output <output> [--paired-end]
    generate_report_data.py (--version | --help)

Options:
    -h --help               Show this help message and exit
    --version               Show version and exit

    -s <featureCounts_stats> --stats <featureCounts_stats>                 TSV containing the statistics of all featureCounts runs
    -o <output> --output <output>                              Created js containing featureCounts statistics
    --paired-end                                               Paired-End run, else Single-End
"""

import json
from pathlib import Path
from typing import Any, Dict, List

from docopt import docopt


def create_featurecounts_stats_js_object(stats_file: Path) -> Dict[str, Any]:
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


def generate_report_data(output_file: Path, stats_file: Path, is_paired_end: bool):
    stats = create_featurecounts_stats_js_object(stats_file)

    with output_file.open('w') as f:
        f.write('window.Curare.count_table = (function() {\n')
        f.write('  const paired_end = {}\n'.format("true" if is_paired_end else "false"))
        f.write('  const stats = ')

        f.write(json.dumps(stats, indent=2).replace('\n', '\n  '))
        f.write('\n')

        f.write('  return {paired_end: paired_end, stats: stats};\n')
        f.write('}());')


def main():
    args = docopt(__doc__, version='1.0')
    stats_file = Path(args["--stats"]).resolve()
    output_file = Path(args["--output"]).resolve()

    generate_report_data(output_file, stats_file, args["--paired-end"])


if __name__ == '__main__':
    main()
