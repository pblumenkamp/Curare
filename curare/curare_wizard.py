#!/usr/bin/env python3
"""
Wizard script for creating pipeline and groups file for Curare.

Usage:
    curare_wizard.py (--output <output_folder> | --samples <samples> --pipeline <pipeline>) [--snakefiles <snakefiles>] [--verbose]
    curare_wizard.py (--version | --help)

Options:
    -h --help               Show this help message and exit
    --version               Show version and exit

    --output <output_folder>                        Output folder (will be created if not existing)
    --samples <samples>                             Path for output samples file (Default Name: <output_folder>/samples.tsv)
    --pipeline <pipeline>                           Path for output pipeline file (Default Name: <output_folder>/pipeline.yaml)

    --snakefiles <snakefiles>                       Folder containing all Curare snakefiles. Uses default curare snakefiles if not specified.
    -v --verbose                                    Print additional information
"""

"""
    Curare (Customizable and Reproducible Analysis Pipeline for RNA-Seq Experiments)
    Copyright (C) 2020  Patrick Blumenkamp

    This program is free software: you can redistribute it and/or modify
    it under the terms of the GNU General Public License as published by
    the Free Software Foundation, either version 3 of the License, or
    (at your option) any later version.

    This program is distributed in the hope that it will be useful,
    but WITHOUT ANY WARRANTY; without even the implied warranty of
    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
    GNU General Public License for more details.

    You should have received a copy of the GNU General Public License
    along with this program.  If not, see <http://www.gnu.org/licenses/>.
"""

from docopt import docopt
import os
from pathlib import Path
import pprint
import sys
from typing import Any, Callable, Dict, IO, List, Union
import yaml

import curare.metadata as metadata

PP = pprint.PrettyPrinter(indent=2)


class ClColors:
    HEADER = '\033[95m'
    OKBLUE = '\033[94m'
    OKGREEN = '\033[92m'
    WARNING = '\033[93m'
    FAIL = '\033[91m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'
    UNDERLINE = '\033[4m'


def check_paired_end() -> bool:
    i: str = ''
    while not (i == 'y' or i == 'n'):
        print("Is this a paired-end dataset? (y/n)")
        i = input()
    print()
    return True if i == 'y' else False


def parse_snakefiles(snakefiles_folder: Path, is_paired_end: bool) -> Dict[str, Dict[str, Dict[str, Union[Dict[str, Dict[str, str]], str]]]]:
    settings: Dict[str, Dict[str, Dict[str, Union[Dict[str, Dict[str, str]], str]]]] = {}  # Dict[module_group, Dict[module_name, Dict[]]]
    for group in ['analysis', 'mapping', 'premapping', 'preprocessing']:
        for module in sorted((snakefiles_folder / group).iterdir()):
            try:
                module_settings = yaml.safe_load((module / (module.name + '.yaml')).open())
            except PermissionError as ex:
                print(ClColors.FAIL + "Missing permissions to read file: {}".format(module / (module.name + '.yaml')) + ClColors.ENDC)
                sys.exit(2)
            sequencing_specific_settings: Dict = module_settings.get('paired_end' if is_paired_end else 'single_end', {})
            formatted_settings = {'label': module_settings.get('label', module.name), 'description': module_settings.get('description', ''),
                                  'required': {}, 'optional': {}}

            for name, entry in module_settings.get('required_settings', {}).items():
                formatted_settings['required'][name] = entry
            for name, entry in sequencing_specific_settings.get('required_settings', {}).items():
                formatted_settings['required'][name] = entry

            for name, entry in module_settings.get('optional_settings', {}).items():
                formatted_settings['optional'][name] = entry
            for name, entry in sequencing_specific_settings.get('optional_settings', {}).items():
                formatted_settings['optional'][name] = entry

            if 'columns' in module_settings:
                formatted_settings['columns'] = module_settings['columns']

            settings.setdefault(group, {})[module.name] = formatted_settings
    return settings


def create_pipeline(all_modules: Dict[str, List[Dict[str, str]]]) -> Dict[str, List[Dict[str, str]]]:
    selected_modules: Dict[str, List[Dict[str, str]]] = {}

    preprocessing_modules: List[Dict[str, str]] = [module for module in all_modules['preprocessing'] if module['name'] != 'none']
    none_module: Dict[str, str] = {}
    for module in all_modules['preprocessing']:
        if module['name'] == 'none':
            none_module = module
    print_modules('Select a preprocessing module:', preprocessing_modules, True)
    user_input: str = ''
    while not check_selection(user_input.upper(), 1, len(all_modules['preprocessing'])-1, ['N']):
        user_input = input('Select[1-{}, N]: '.format(len(all_modules['preprocessing'])-1))
    selected_modules['preprocessing'] = [preprocessing_modules[int(user_input)-1]] if user_input.upper() != 'N' else [none_module]

    print("\n")

    print_modules('Select any number of premapping modules:', all_modules['premapping'], True)
    user_input: str = ''
    while not check_multi_selection(user_input.upper(), 1, len(all_modules['premapping']), ['N']):
        user_input = input('Select[1-{}, N; Comma-separated]: '.format(len(all_modules['premapping'])))
    selected_modules['premapping'] = []
    if user_input.upper() != 'N':
        for value in user_input.split(','):
            selected_modules['premapping'].append(all_modules['premapping'][int(value) - 1])

    print("\n")

    mapping_modules: List[Dict[str, str]] = all_modules['mapping']
    print_modules('Select a mapping module:', mapping_modules)
    user_input: str = ''
    while not check_selection(user_input, 1, len(mapping_modules)):
        user_input = input('Select[1-{}]: '.format(len(mapping_modules)))
    selected_modules['mapping'] = [mapping_modules[int(user_input) - 1]]

    print("\n")

    print_modules('Select any number of analysis modules:', all_modules['analysis'], True)
    user_input: str = ''
    while not check_multi_selection(user_input.upper(), 1, len(all_modules['analysis']), ['N']):
        user_input = input('Select[1-{}, N; Comma-separated]: '.format(len(all_modules['analysis'])))
    selected_modules['analysis'] = []
    if user_input.upper() != 'N':
        for value in user_input.split(','):
            selected_modules['analysis'].append(all_modules['analysis'][int(value) - 1])

    print("\n")

    return selected_modules


def print_modules(title: str, modules: List[Dict[str, str]], include_none: bool = False):
    print(title)
    for i, module in enumerate(modules):
        print('[{:2d}] {}'.format(i + 1, module['label']))
        print('     {}'.format(module['description']))
        print()
    if include_none:
        print('[{:>2s}] {}'.format('N', 'None'))
        print('     {}'.format("Don't use any module."))
        print()


def check_selection(value: str, min_value: int, max_value: int, characters: List[str] = ()) -> bool:
    if value in characters:
        return True
    try:
        value = int(value)
        return min_value <= value <= max_value
    except:
        return False


def check_multi_selection(values: str, min_value: int, max_value: int, characters: List[str] = (), separator: str = ',') -> bool:
    if values in characters:
        return True
    try:
        values = [int(value) for value in values.strip().split(separator)]
        for value in values:
            if not min_value <= value <= max_value:
                return False
        return True
    except:
        return False


def create_groups_file(selected_modules: Dict[str, List[Dict[str, str]]], all_modules: Dict[str, Dict[str, Dict[str, Union[Dict[str, Dict[str, str]], str]]]], output: Path, is_paired_end: bool) -> None:
    necessary_columns: List[Dict[str, str]] = []
    for category, modules in selected_modules.items():
        for module in modules:
            module_settings = all_modules[category][module['name']]
            if 'columns' in module_settings:
                for col_name, col_desc in module_settings.get('columns', {}).items():
                    column = {'name': col_name}
                    column.update(col_desc)
                    necessary_columns.append(column)

    table_header: str = 'name\t' + ('reads' if not is_paired_end else 'forward_reads\treverse_reads')
    output.parent.mkdir(parents=True, exist_ok=True)
    try:
        with output.open('w') as out:
            out.write('# name: Unique sample name. Only use alphanumeric characters and \'_\'. [Value Type: String]\n')
            if is_paired_end:
                out.write('# forward_reads: File path to fastq file containing forward reads. Either as an absolute path or relative to this file. [Value Type: Path]\n')
                out.write('# reverse_reads: File path to fastq file containing reverse reads. Either as an absolute path or relative to this file. [Value Type: Path]\n')
            else:
                out.write('# reads: File path to fastq file containing reads. Either as absolute path or relative to this file. [Value Type: Path]\n')
            for col in necessary_columns:
                out.write('# {}: {} [Value Type: {}]\n'.format(col['name'], col['description'] if col['description'].endswith('.') else col['description'] + '.', col['type'].capitalize()))
                table_header = table_header + '\t' + col['name']
            out.write('\n')
            out.write(table_header + '\n')
    except PermissionError as ex:
                print(ClColors.FAIL + "Missing permissions to write samples file: {}".format(output) + ClColors.ENDC)
                sys.exit(3)


def create_pipeline_file(selected_modules: Dict[str, List[Dict[str, str]]], all_modules: Dict[str, Dict[str, Dict[str, Union[Dict[str, Dict[str, str]], str]]]], output: Path, is_paired_end: bool) -> None:
    output.parent.mkdir(parents=True, exist_ok=True)
    try:
        with output.open('w') as out:
            out_write: Callable = lambda text='', indent=0: out.write(' ' * indent + text + '\n')
            out_write("## Curare Pipeline File")
            out_write("## This is an automatically created pipeline file for Curare.")
            out_write('## All required parameters must be set (replace <Insert Config Here> with real value).')
            out_write("## All optional parameters are commented out with a single '#'. For including these parameters, just remove the '#'.")
            out_write()
            out_write('pipeline:')
            out_write('paired_end: {}'.format('true' if is_paired_end else 'false'), 2)
            out_write()

            for category in ['preprocessing', 'premapping', 'mapping', 'analysis']:
                out_write(category + ':')
                modules:  List[Dict[str, str]] = selected_modules[category]
                out_write('modules: [{}]'.format(', '.join(['"' + module['name'] + '"' for module in modules])), 2)
                out_write()
                for module in modules:
                    module_settings = all_modules[category][module['name']]
                    if not module_settings.get('required', {}).keys() and not module_settings.get('optional', {}).keys():
                        continue
                    out_write(module['name'] + ':', 2)
                    for setting_name, setting in module_settings.get('required', {}).items():
                        for line in format_description(setting['description'], setting['type']):
                            out_write(line, 4)
                        if setting['type'] == 'enum':
                            out_write('## Enum choices: {}'.format(', '.join(['"{}"'.format(choice) for choice in setting['choices']])), 4)
                        out_write('{}: <Insert Config Here>'.format(setting_name), 4)
                        out_write()
                    for setting_name, setting in module_settings.get('optional', {}).items():
                        for line in format_description(setting['description'], setting['type']):
                            out_write(line, 4)
                        out_write('#{}: "{}"'.format(setting_name, setting['default']), 4)
                        out_write()
                    out_write()
    except PermissionError as ex:
        print(ClColors.FAIL + "Missing permissions to write pipeline file: {}".format(output) + ClColors.ENDC)
        sys.exit(4)

def format_description(description: str, parameter_type: str) -> List[str]:
    formatted_description = []
    if not description.endswith('.'):
        description += '.'
    description_lines: List[str] = description.split('\n')
    if len(description_lines) > 1:
        for line in description_lines:
            formatted_description.append("## {}".format(line))
        formatted_description.append("## [Value Type: {}]".format(parameter_type.capitalize()))
    else:
        formatted_description.append('## {} [Value Type: {}]'.format(description, parameter_type.capitalize()))
    return formatted_description


def user_question(question: str, answer_check: Callable):
    answer : str = ""
    while not answer_check(answer):
        answer = input(question)
    return answer


def print_verbose(text: Any = '', file: IO = sys.stderr) -> None:
    print(ClColors.OKBLUE + str(text) + ClColors.ENDC, file=file)


def main() -> None:
    args = docopt(__doc__, version=metadata.__version__)
    if args["--output"] is not None:
        args["--output"] = Path(args["--output"]).resolve()
        args["--samples"] = args['--output'] / 'samples.tsv'
        args["--pipeline"] = args['--output'] / 'pipeline.yaml'
    else:
        args["--samples"] = Path(args["--samples"]).resolve()
        args["--pipeline"] = Path(args["--pipeline"]).resolve()

    if args["--samples"].exists():
        user_input : str = user_question("File \"{}\" already exists. Do you want to overwrite it? [y/n]: ".format(args["--samples"]),
                                         lambda x: x in ["y", "n"])
        if user_input == 'n':
            sys.exit(1)
    if args["--pipeline"].exists():
        user_input : str = user_question("File \"{}\" already exists. Do you want to overwrite it? [y/n]: ".format(args["--pipeline"]),
                                         lambda x: x in ["y", "n"])
        if user_input == 'n':
            sys.exit(1)

    if not (os.access(args["--samples"], os.R_OK) and os.access(args["--samples"], os.W_OK)):
        print(ClColors.FAIL + "Missing permissions to write samples file: {}".format(args["--samples"]) + ClColors.ENDC)
        sys.exit(3)
    if not (os.access(args["--pipeline"], os.R_OK) and os.access(args["--pipeline"], os.W_OK)):
        print(ClColors.FAIL + "Missing permissions to write pipeline file: {}".format(args["--pipeline"]) + ClColors.ENDC)
        sys.exit(4)

    if args["--snakefiles"] is None:
        args["--snakefiles"] = Path(__file__).resolve().parent / "snakefiles"  
    else:
        args["--snakefiles"] = Path(args["--snakefiles"]).resolve()

    print()

    if args['--verbose']:
        print_verbose("Input Parameters:")
        print_verbose("Used output folder: {}".format(args["--output"]))
        print_verbose("Output samples file: {}".format(args["--samples"]))
        print_verbose("Output pipeline file: {}".format(args["--pipeline"]))
        print_verbose("Used snakefile folder: {}".format(args["--snakefiles"]))
        print_verbose()

    is_paired_end: bool = check_paired_end()
    settings: Dict[str, Dict[str, Dict[str, Union[Dict[str, Dict[str, str]], str]]]] = parse_snakefiles(args["--snakefiles"], is_paired_end)

    if args['--verbose']:
        print_verbose('Collected modules in "{}":'.format(args["--snakefiles"]))
        print_verbose(PP.pformat({category: [name for name in module.keys()] for category, module in settings.items()}))
        print_verbose()

    all_modules: Dict[str, List[Dict[str, str]]] = {
        category: [{'name': module_name, 'description': module['description'], 'label': module['label']} for module_name, module in modules.items()]
        for category, modules in settings.items()}
    user_pipeline: Dict[str, List[Dict[str, str]]] = create_pipeline(all_modules)
    if args['--verbose']:
        print_verbose('Selected modules:')
        print_verbose({category: [module['name'] for module in modules] for category, modules in user_pipeline.items()})
        print_verbose()

    create_groups_file(user_pipeline, settings, args["--samples"], is_paired_end)
    print('Samples file "{}" created.'.format(args["--samples"]))

    create_pipeline_file(user_pipeline, settings, args["--pipeline"], is_paired_end)
    print('Pipeline file "{}" created.'.format(args["--pipeline"]))


class MissingReadPermissionsError(Exception):
    """Exception raised when using unknown command line argument.

            Attributes:
                message -- message displayed
        """

    def __init__(self, message: str):
        super(MissingReadPermissionsError, self).__init__(message)


if __name__ == '__main__':
    main()
