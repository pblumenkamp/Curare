"""
Convert samtools flagstat results to usable data for the large report

Usage:
    generate_report_data.py --stats <stats> --output <output> [--paired-end]
    generate_report_data.py (--version | --help)

Options:
    -h --help               Show this help message and exit
    --version               Show version and exit

    -s <stats> --stats <stats>                 TSV containing the statistics of all flagsts runs
    -o <output> --output <output>                              Created js containing flagstat statistics
    --paired-end                                               Paired-End run, else Single-End
"""

import json
from pathlib import Path
from typing import Any, Dict

import pandas as pd
from docopt import docopt


def create_bwa_stats_js_object(stats_file: Path) -> Dict[str, Any]:
    tsv_df = pd.read_csv(stats_file, sep="\t")
    return json.loads(tsv_df.to_json(orient='records'))


def generate_report_data(output_file: Path, stats_file: Path, is_paired_end: bool):
    stats = create_bwa_stats_js_object(stats_file)

    with output_file.open('w') as f:
        f.write('window.Curare.bwa_sw = (function() {\n')
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
