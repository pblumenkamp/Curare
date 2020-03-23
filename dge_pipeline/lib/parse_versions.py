"""
Simple script for parsing conda environments to collect used software and its version.

Usage:
    parse_versions.py --conda-dir <conda_dir> --pipeline <pipeline_yaml> --output <output>
    parse_versions.py (--version | --help)

Options:
    -h --help               Show this help message and exit
    --version               Show version and exit

    -c <conda_dir> --conda-dir <conda_dir>                     Directory containing all conda environments
    -p <pipeline_yaml> --pipeline <pipeline_yaml>              Curare file containing moduleinformation (pipeline.yml)
    -o <output> --output <output>                              Created json containing software and version information
"""

import re
import yaml
import json


from docopt import docopt

from os import listdir
from pathlib import Path
from typing import Dict, List, Tuple, Any


ANALYSIS_STEPS: Tuple[str, str, str, str] = (
    'preprocessing',
    'premapping',
    'mapping',
    'analyses',     # should be analysis
)


def parse_config_yml(pipeline_file: Path):
    steps: Dict[str, str] = {}
    with pipeline_file.open() as yaml_config:
        yaml_config: Dict[Any, Any] = yaml.load(yaml_config, Loader=yaml.BaseLoader)
        for step in ANALYSIS_STEPS:
            if step in yaml_config:
                if 'module' in yaml_config[step]:
                    steps[yaml_config[step]['module']] = step
                elif 'modules' in yaml_config[step]:
                    for module in yaml_config[step]['modules']:
                        steps[module] = step
    return steps


def get_specified_tools(log_str: str):
    return re.findall(r'[\'"]([a-zA-Z0-9-]+)(?:\[version=\'[<>=]{1,2}[0-9.]*\'\])?[\'"]', log_str)


def get_dependencies(dependencies: list):
    primary_dependencies = []
    secondary_dependencies = []

    re_tool = re.compile(
        r'[+-](?P<repository>.*)::(?P<tool>[a-zA-Z0-9-_\.]+)-(?P<version>[0-9.a-z_]+)-(?P<hash>[a-z0-9_]*)')

    specified_tools = get_specified_tools(dependencies[-1])
    for line in dependencies:
        if line.startswith("+"):
            match = re_tool.search(line)
            dependency = {
                'full_dependency': line[1:].strip(),
                'repository': match.group('repository'),
                'tool': match.group('tool'),
                'version': match.group('version'),
                'hash': match.group('hash')
            }
            if match.group('tool') in specified_tools:
                primary_dependencies.append(dependency)
            else:
                secondary_dependencies.append(dependency)
    return primary_dependencies, secondary_dependencies


def main():
    args = docopt(__doc__, version='1.0')
    conda_dir = Path(args["--conda-dir"]).resolve()
    pipeline_file = Path(args["--pipeline"])
    output_json = Path(args["--output"]).resolve()

    steps = parse_config_yml(pipeline_file)
    output_list = []
    for file in [f for f in listdir(conda_dir) if f.endswith('.yaml')]:
        with open(conda_dir / file, 'r') as yaml_file:
            first_line = yaml_file.readline()
            if first_line.startswith("# module:"):
                module = first_line.split(": ")[1].strip()

        conda_env = file.split(".")[0]
        with open(conda_dir / conda_env / 'conda-meta' / 'history', 'r') as history_file:
            dependencies = history_file.readlines()
            primary_dependencies, secondary_dependencies = get_dependencies(dependencies)

        step = steps[module] if module in steps else ''

        output_list.append({
            'name': module,
            'step': step,
            'primaryDependencies': primary_dependencies,
            'secondaryDependencies': secondary_dependencies
        })

    with output_json.open('w') as f:
        json.dump(output_list, f, indent=4)


if __name__ == '__main__':
    main()
