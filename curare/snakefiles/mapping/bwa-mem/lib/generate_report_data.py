"""
Convert samtools flagstat results to usable data for the large report

Usage:
    generate_report_data.py --stats <stats> --output <output> --settings <settings> [--paired-end]
    generate_report_data.py (--version | --help)

Options:
    -h --help               Show this help message and exit
    --version               Show version and exit

    -s <stats> --stats <stats>                                 TSV containing the statistics of all flagsts runs
    -t <settings> --settings <settings>                        All BWA settings as an yaml file
    -o <output> --output <output>                              Created js containing flagstat statistics
    --paired-end                                               Paired-End run, else Single-End
"""

import json
from pathlib import Path
from typing import Any, Dict
import yaml

import pandas as pd
from docopt import docopt


def create_bwa_stats_js_object(stats_file: Path) -> Dict[str, Any]:
    tsv_df = pd.read_csv(stats_file, sep="\t")
    return json.loads(tsv_df.to_json(orient='records'))

def create_bwa_settings_js_object(settings_file: Path) -> Dict[str, Any]:
    settings = yaml.safe_load(settings_file.open('r'))
    return settings

def generate_report_data(output_file: Path, stats_file: Path, settings_file: Path, is_paired_end: bool):
    stats = create_bwa_stats_js_object(stats_file)
    settings = create_bwa_settings_js_object(settings_file)

    with output_file.open('w') as f:
        f.write('window.Curare.bwa_mem = (function() {\n')
        f.write('  const paired_end = {}\n'.format("true" if is_paired_end else "false"))
        
        f.write('  const stats = ')
        f.write(json.dumps(stats, indent=2).replace('\n', '\n  '))
        f.write('\n')

        f.write('  const settings = ')
        f.write(json.dumps(settings, indent=2).replace('\n', '\n  '))
        f.write('\n')

        f.write('  return {paired_end: paired_end, stats: stats, settings: settings};\n')
        f.write('}());')


def main():
    args = docopt(__doc__, version='1.0')
    stats_file = Path(args["--stats"]).resolve()
    output_file = Path(args["--output"]).resolve()
    settings_file = Path(args["--settings"]).resolve()

    generate_report_data(output_file, stats_file, settings_file, args["--paired-end"])


if __name__ == '__main__':
    main()
