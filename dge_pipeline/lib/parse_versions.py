import re
import sys
import yaml
import json

from os import listdir
from os.path import abspath
from pathlib import Path


ANALYSIS_STEPS = [
    'preprocessing',
    'premapping',
    'mapping',
    'analyses',     # should be analysis
]


def parse_config_yml(report_dir: Path):
    steps = dict()
    with open(report_dir / '..' / '..' / 'pipeline.yml') as yaml_config:
        json_config = yaml.load(yaml_config, Loader=yaml.BaseLoader)
        for step in ANALYSIS_STEPS:
            if 'module' in json_config[step]:
                steps[json_config[step]['module']] = step
            else:
                for module in json_config[step]['modules']:
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
    root_dir = Path(abspath(sys.argv[1]))
    report_dir = Path(abspath(sys.argv[2]))
    steps = parse_config_yml(report_dir)
    output_list = []
    for file in [f for f in listdir(root_dir) if f.endswith('.yaml')]:
        with open(root_dir / file, 'r') as yaml_file:
            first_line = yaml_file.readline()
            if first_line.startswith("# module:"):
                module = first_line.split(": ")[1].strip()

        conda_env = file.split(".")[0]
        with open(root_dir / conda_env / 'conda-meta' / 'history', 'r') as history_file:
            dependencies = history_file.readlines()
            primary_dependencies, secondary_dependencies = get_dependencies(dependencies)

        step = steps[module] if module in steps else ''

        output_list.append({
            'name': module,
            'step': step,
            'primaryDependencies': primary_dependencies,
            'secondaryDependencies': secondary_dependencies
        })

    with open(report_dir / 'data' / 'versions.json', 'w') as f:
        json.dump(output_list, f, indent=4)


if __name__ == '__main__':
    main()
