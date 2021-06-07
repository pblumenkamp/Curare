from datetime import datetime, timedelta, timezone
import getpass
import json
import shutil
import subprocess

from pathlib import Path
from typing import Dict, List


def create_report(src_folder: Path, output_folder: Path, curare_version: str, runtime: timedelta, curare_samples_file: Path):
    # Copy report-specific files such as the HTML, CSS, and JS files.
    try:
        shutil.copy(str(src_folder / 'report.html'), str(output_folder))

        copy_folder(src_folder / 'css', output_folder / '.report' / 'css')
        copy_folder(src_folder / 'js', output_folder / '.report' / 'js')
        copy_folder(src_folder / 'img', output_folder / '.report' / 'img')
        copy_folder(src_folder / 'modules', output_folder / '.report' / 'modules')

        create_navigationbar_js_object(output_folder / '.report' / 'data' / 'versions.json',
                                       output_folder / '.report' / 'data' / 'navigation.js',
                                       output_folder)

        create_summary_js_object(output_folder / '.report' / 'data' / 'curare_summary.js', curare_version, runtime, curare_samples_file)

        create_versions_js_object(output_folder / '.report' / 'data' / 'versions.json',
                                  output_folder / '.report' / 'data' / 'versions.js')
        (output_folder / '.report' / 'data' / 'versions.json').unlink()

    except shutil.Error as err:
        raise err
    except subprocess.CalledProcessError as err:
        raise err


def create_navigationbar_js_object(versions_json: Path, navigation_output: Path, curare_output: Path):
    versions: List = json.load(versions_json.open())
    nav: Dict[str, List] = {}
    for module in versions:
        if module["step"] not in nav:
            nav[module["step"]] = []
        html_name = module["name"] + ".html" if (curare_output / ".report" / "modules" / (module["name"] + ".html")).is_file() else None
        new_tab = True if module["name"] in ["multiqc"] else False
        nav[module["step"]].append({'name': module["name"], 'html_name': html_name, "new_tab": new_tab})

    with navigation_output.open('w') as f:
        f.write('window.Curare.navigation = (function() {\n')
        f.write('  const nav = ')

        # Copy contents of versions.json into report_data.js.
        f.write(json.dumps(nav, indent=2).replace('\n', '\n  '))
        f.write('\n')

        f.write('  return nav;\n')
        f.write('}());')


def create_summary_js_object(output_path: Path, curare_version: str, runtime: timedelta, curare_samples_file: Path):
    with curare_samples_file.open() as groups_file:
        groups = [line.strip().split('\t') for line in groups_file if not line.startswith('#') and line.strip()]

    with output_path.open('w') as f:
        f.write('window.Curare.summary = (function() {\n')
        f.write('  const summary = {\n')
        f.write('    user: "{}",\n'.format(getpass.getuser()))
        time: datetime = datetime.now(timezone(timedelta(0))).astimezone()
        f.write('    date: "{} ({})",\n'.format(datetime.strftime(time, "%Y-%m-%d %H:%M:%S"), time.tzinfo))
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


def copy_folder(src: Path, dst: Path):
    if not dst.exists():
        shutil.copytree(str(src), str(dst), copy_function=shutil.copy)
    else:
        for file in src.iterdir():
            if file.is_file():
                shutil.copy(str(file), str(dst))
            elif file.is_dir():
                copy_folder(file, (dst / file.stem))
