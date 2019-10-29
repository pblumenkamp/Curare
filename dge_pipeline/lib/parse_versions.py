import re
import sys
import yaml

from os import listdir
from os.path import abspath
from pathlib import Path


def get_specified_tools(log_str: str):
    return re.findall(r'[\'"]([a-zA-Z0-9-]+)(?:\[version=\'[<>=]{1,2}[0-9.]*\'\])?[\'"]', log_str)


def get_dependencies(dependencies: list):
    primary_dependencies = []
    secondary_dependencies = []

    re_tool = re.compile(
        r'[+-](?P<repository>.*::)(?P<tool>[a-zA-Z0-9-_\.]+)(?P<version>-[0-9.a-z_]+)(?P<hash>-[a-z0-9_]*)')

    specified_tools = get_specified_tools(dependencies[-1])
    for line in dependencies:
        if line.startswith("+"):
            match = re_tool.search(line)
            formatted_line = str(
                match.group('repository') + match.group('tool') + match.group('version') + match.group('hash'))
            if match.group('tool') in specified_tools:
                primary_dependencies.append(formatted_line)
            else:
                secondary_dependencies.append(formatted_line)
    return primary_dependencies, secondary_dependencies


def main():
    root_dir = Path(abspath(sys.argv[1]))
    output = abspath(sys.argv[2])
    output_dict = {'modules': []}
    for file in [f for f in listdir(root_dir) if f.endswith('.yaml')]:
        with open(root_dir / file, 'r') as yaml_file:
            first_line = yaml_file.readline()
            if first_line.startswith("# module:"):
                module = first_line.split(": ")[1].strip()

        conda_env = file.split(".")[0]
        with open(root_dir / conda_env / 'conda-meta' / 'history', 'r') as history_file:
            dependencies = history_file.readlines()
            primary_dependencies, secondary_dependencies = get_dependencies(dependencies)

        output_dict['modules'].append({
            module: {
                'dependencies': {
                    'primary': primary_dependencies,
                    'secondary': secondary_dependencies
                }
            }
        })

    with open(output, 'w') as f:
        yaml.dump(output_dict, f)


if __name__ == '__main__':
    main()
