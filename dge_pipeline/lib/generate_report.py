import json
import sys

from os.path import abspath
from pathlib import Path


def write_report_data_js(report_data_dir: Path):
    with open(report_data_dir / 'report_data.js', 'w') as f:
        f.write('window.Seed = (function() {\n')
        f.write('    const reportData = {\n')
        f.write('        "overview": {\n')

        # Copy contents of versions.json into report_data.js.
        versions_file = report_data_dir / 'versions.json'
        if versions_file.exists():
            f.write('            "toolsUsed": ')
            with open(versions_file, 'r') as versions:
                json.dump(json.load(versions), f, indent=4)
            f.write('\n')

        f.write('        },\n')
        f.write('        "mapping": {\n')

        # Copy contents of mapping_stats.json into report_data.js.
        mapping_stats_file = report_data_dir / 'mapping_stats.json'
        if mapping_stats_file.exists():
            f.write('            "stats": ')
            with open(report_data_dir / 'mapping_stats.json', 'r') as mapping_stats:
                json.dump(json.load(mapping_stats), f, indent=4)
            f.write('\n')

        f.write('        }\n')
        f.write('    };\n\n')
        f.write('    return { reportData: reportData };\n')
        f.write('}());')


def main():
    report_data_dir = Path(abspath(sys.argv[1]))
    write_report_data_js(report_data_dir)


if __name__ == '__main__':
    main()