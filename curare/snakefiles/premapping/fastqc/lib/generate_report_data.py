"""
Convert fastqc results to usable data for the large report

Usage:
    generate_report_data.py --reports <reports> --output <output> [--paired-end]
    generate_report_data.py (--version | --help)

Options:
    -h --help               Show this help message and exit
    --version               Show version and exit

    -r <reports> --reports <reports>                           File containing all FastQC report paths as TSV
    -o <output> --output <output>                              Created js containing trim-galore statistics
    --paired-end                                               Paired-End run, else Single-End
"""

import json
import re
from pathlib import Path
from typing import Any, Dict, List, Match, Pattern

import pandas as pd
from docopt import docopt


def create_fastqc_stats_js_object(reports_path: Path, is_paired_end: bool) -> List[Dict[str, str]]:
    report_list = []
    with reports_path.open() as reports:
        next(reports)
        for line in reports:
            line = line.strip().split('\t')
            if is_paired_end:
                report_list.append({'name': line[0], 'forward': line[1], 'reverse': line[2]})
            else:
                report_list.append({'name': line[0], 'forward': line[1]})
    return report_list


def generate_report_data(output_file: Path, reports_file: Path, is_paired_end: bool):
    reports = create_fastqc_stats_js_object(reports_file, is_paired_end)

    with output_file.open('w') as f:
        f.write('window.Curare.fastqc = (function() {\n')
        f.write('  const paired_end = {}\n'.format("true" if is_paired_end else "false"))
        f.write('  const reports = ')

        f.write(json.dumps(reports, indent=2).replace('\n', '\n  '))
        f.write('\n')

        f.write('  return {paired_end: paired_end, reports: reports};\n')
        f.write('}());')


def main():
    args = docopt(__doc__, version='1.0')
    reports_file = Path(args["--reports"]).resolve()
    output_file = Path(args["--output"]).resolve()

    generate_report_data(output_file, reports_file, args["--paired-end"])


if __name__ == '__main__':
    main()
