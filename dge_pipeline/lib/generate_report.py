import json
import shutil
import subprocess

from pathlib import Path


def create_report(src_folder: Path, output_folder: Path):
    # Copy report-specific files such as the HTML, CSS, and JS files.
    try:
        shutil.copy(str(src_folder / 'report.html'), str(output_folder))
        shutil.copytree(str(src_folder / 'css'), str(output_folder / '.report' / 'css'))
        shutil.copytree(str(src_folder / 'js'), str(output_folder / '.report' / 'js'))
        shutil.copytree(str(src_folder / 'img'), str(output_folder / '.report' / 'img'))

        create_versions_js_object(output_folder / '.report' / 'data' / 'versions.json',
                                  output_folder / '.report' / 'data' / 'versions.js')
        (output_folder / '.report' / 'data' / 'versions.json').unlink()

    except shutil.Error as err:
        raise err
    except subprocess.CalledProcessError as err:
        raise err


def create_versions_js_object(versions_json: Path, output_path: Path):
    with output_path.open('w') as f:
        f.write('window.Curare = (function() {\n')
        f.write('  const versions = \n')

        # Copy contents of versions.json into report_data.js.
        with versions_json.open() as versions:
            f.write(json.dumps(json.load(versions), indent=2).replace('\n', '\n    '))
        f.write('\n')

        f.write('  return { versions: versions };\n')
        f.write('}());')
