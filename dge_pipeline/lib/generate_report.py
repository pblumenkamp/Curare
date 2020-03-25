from datetime import datetime, timedelta
import getpass
import json
import shutil
import subprocess

from pathlib import Path
from typing import Dict, List



def create_report(src_folder: Path, output_folder: Path, curare_version: str, runtime: timedelta, curare_groups_file: Path):
    # Copy report-specific files such as the HTML, CSS, and JS files.
    try:
        shutil.copy(str(src_folder / 'report.html'), str(output_folder))
        shutil.copytree(str(src_folder / 'css'), str(output_folder / '.report' / 'css'))
        shutil.copytree(str(src_folder / 'js'), str(output_folder / '.report' / 'js'))
        shutil.copytree(str(src_folder / 'img'), str(output_folder / '.report' / 'img'))

        create_summary_js_object(output_folder / '.report' / 'data' / 'curare_summary.js', curare_version, runtime, curare_groups_file)

        create_navigationbar_js_object(output_folder / '.report' / 'data' / 'versions.json',
                                       output_folder / '.report' / 'data' / 'navigation.js')
        create_versions_js_object(output_folder / '.report' / 'data' / 'versions.json',
                                  output_folder / '.report' / 'data' / 'versions.js')
        (output_folder / '.report' / 'data' / 'versions.json').unlink()

    except shutil.Error as err:
        raise err
    except subprocess.CalledProcessError as err:
        raise err


def create_navigationbar_js_object(versions_json: Path, output_path: Path):
    versions: List = json.load(versions_json.open())
    nav: Dict[str, List] = {}
    for module in versions:
        if module["step"] not in nav:
            nav[module["step"]] = []
        nav[module["step"]].append(module["name"])

    with output_path.open('w') as f:
        f.write('window.Curare.navigation = (function() {\n')
        f.write('  const nav = ')

        # Copy contents of versions.json into report_data.js.
        f.write(json.dumps(nav, indent=2).replace('\n', '\n  '))
        f.write('\n')

        f.write('  return nav;\n')
        f.write('}());')


def create_summary_js_object(output_path: Path, curare_version: str, runtime: timedelta, curare_groups_file: Path):
    with curare_groups_file.open() as groups_file:
        groups = groups_file.readlines()
        groups = [line.strip().split('\t') for line in groups]

    with output_path.open('w') as f:
        f.write('window.Curare.summary = (function() {\n')
        f.write('  const summary = {\n')
        f.write('    user: "{}",\n'.format(getpass.getuser()))
        f.write('    date: "{}",\n'.format(datetime.isoformat(datetime.utcnow(), timespec='seconds')))
        f.write('    curare_version: "{}",\n'.format(curare_version))
        f.write('    runtime: {},\n'.format(runtime.total_seconds()))
        f.write('    groups: {},\n'.format(json.dumps(groups, indent=2).replace('\n', '\n    ')))
        f.write('  };\n')
        f.write('  return summary;\n')
        f.write('}());')


def create_versions_js_object(versions_json: Path, output_path: Path):
    with output_path.open('w') as f:
        f.write('window.Curare.versions = (function() {\n')
        f.write('  const versions = ')

        # Copy contents of versions.json into report_data.js.
        with versions_json.open() as versions:
            f.write(json.dumps(json.load(versions), indent=2).replace('\n', '\n  '))
        f.write('\n')

        f.write('  return versions;\n')
        f.write('}());')
