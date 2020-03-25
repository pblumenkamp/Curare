import json
import sys
import pandas as pd

from os.path import abspath
from pathlib import Path


def parse_mapping_stats_to_json(src_dir: Path, target_dir: Path):
    tsv_df = pd.read_csv(src_dir / 'stats' / 'mapping_stats.tsv', sep="\t")
    json_obj = json.loads(tsv_df.to_json(orient='records'))
    with open(target_dir / 'data' / 'bowtie2_data.js', 'w') as f:
        json.dump(json_obj, f, indent=4)


def generate_report_data(src_dir: Path, target_dir: Path):
    parse_mapping_stats_to_json(src_dir, target_dir)


def main():
    mapping_dir = Path(abspath(sys.argv[1]))
    report_dir = Path(abspath(sys.argv[2]))

    generate_report_data(mapping_dir, report_dir)


if __name__ == '__main__':
    main()
