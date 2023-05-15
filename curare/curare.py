#!/usr/bin/env python3
"""
Customizable and Reproducible Analysis Pipeline for RNA-Seq Experiments (Curare).

Usage:
    curare.py --samples <samples_file> --pipeline <pipeline_file> --output <output_folder>
                 [--cluster-command <cluster_command>] [--cluster-config-file <config_file>] [--cluster-nodes <nodes>]
                 [--use-conda] [--conda-frontend <frontend>] [--conda-prefix <conda_prefix>] [--cores <cores>] [--latency-wait <seconds>] [--verbose]
    curare.py --samples <samples_file> --pipeline <pipeline_file> --output <output_folder> --create-conda-envs-only [--conda-frontend <frontend>] [--conda-prefix <conda_prefix>] [--verbose]
    curare.py (--version | --help)

Options:
    -h --help               Show this help message and exit
    --version               Show version and exit

    --samples <samples_file>                        File containing information about each sample
    --pipeline <pipeline_file>                      File containing information about the RNA-seq pipeline
    --output <output_folder>                        Output folder (will be created if not existing)

    --cluster-command <command>                     Command for cluster execution. , e.g. 'qsub'. For resource requests use also --cluster-config
    --cluster-config-file <config_file>             File containing cluster settings for individual rules.
                                                    See also: https://snakemake.readthedocs.io/en/stable/snakefiles/configuration.html#cluster-configuration
    --cluster-nodes <nodes>                         Maximal number of parallel jobs send to the cluster. Only used in cluster mode is used. [Default: 1]
    --use-conda                                     Install and use separate conda environments for pipeline modules [Default: False]
    --conda-frontend <frontend>                     Choose conda frontend for creating and installing conda environments (conda, mamba) [Default: mamba]
    --conda-prefix <conda_prefix>                   The directory in which conda environments will be created. Relative paths will be relative to output folder! (Default: Output_folder)
    --create-conda-envs-only                        Only download and create conda environments.
    -t <cores> --cores <cores>                      Number of threads/cores. Defines locales cores in cluster mode. [Default: 1]
    --latency-wait <seconds>                        Seconds to wait before checking if all files of a rule were created. Should be increased if using cluster mode. [Default: 5]
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

import datetime
import filecmp
import math
import re
import shutil
import subprocess
import sys
import yaml

from pathlib import Path
from typing import Dict, List, Tuple, Any, Optional
from docopt import docopt
from distutils.dir_util import copy_tree

import curare.metadata as metadata
from curare.lib import generate_report

CURARE_PATH: Path = Path(__file__).resolve().parent

SNAKEFILES_LIBRARY: Path = CURARE_PATH / "snakefiles"
SNAKEFILES_TARGET_DIRECTORY: Path = Path('snakemake_lib')

REPORT_SRC_DIRECTORY: Path = CURARE_PATH / 'report'
REPORT_TARGET_DIRECTORY: Path = Path('.report')

GLOBAL_LIB: Path = CURARE_PATH / 'lib'
GLOBAL_LIB_TARGET_DIR: Path = SNAKEFILES_TARGET_DIRECTORY / 'global_scripts'


class ClColors:
    HEADER = '\033[95m'
    OKBLUE = '\033[94m'
    OKGREEN = '\033[92m'
    WARNING = '\033[93m'
    FAIL = '\033[91m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'
    UNDERLINE = '\033[4m'


def main():
    start_time: datetime.datetime = datetime.datetime.utcnow()
    try:
        args = parse_arguments()
        used_modules, paired_end = load_pipeline_file(args["--pipeline"])
        samples: Dict[str, Dict[str, Dict[str, str]]] = parse_samples_file(args["--samples"], used_modules, paired_end)
        create_output_directory(args["--output"])
        snakefile: Path = create_snakefile(args["--output"], samples, used_modules, args["--use-conda"], args["--conda-prefix"], args["--pipeline"])
    except UnknownInputFileError as ex:
        print(ClColors.FAIL + str(ex) + ClColors.ENDC, file=sys.stderr)
        sys.exit(1)
    except InvalidPipelineFileError as ex:
        print(ClColors.FAIL + 'Error in {}:\n'.format(args["--pipeline"].name) + str(ex) + ClColors.ENDC, file=sys.stderr)
        sys.exit(2)
    except InvalidSamplesFileError as ex:
        print(ClColors.FAIL + 'Error in {}:\n'.format(args["--samples"].name) + str(ex) + ClColors.ENDC, file=sys.stderr)
        sys.exit(3)
    except NotADirectoryError as ex:
        print(ClColors.FAIL + str(ex) + ClColors.ENDC, file=sys.stderr)
        sys.exit(4)
    except EmptySamplesFileError as ex:
        print(ClColors.FAIL + 'Error in {}:\n'.format(args["--samples"].name) + str(ex) + ClColors.ENDC, file=sys.stderr)
        sys.exit(5)
    except Exception as ex:
        print(ClColors.FAIL + "Unknown Error occured:\n" + str(ex) + ClColors.ENDC, file=sys.stderr)
        sys.exit(9)

    if args['--create-conda-envs-only']:
        sm_command: List[str] = ["snakemake", "--snakefile", str(snakefile), "--directory", str(args["--output"]),
                                 "--cores", args["--cores"], "--use-conda", "--conda-create-envs-only",
                                 "--conda-frontend", args["--conda-frontend"]]
        if args["--conda-prefix"]:
            sm_command.extend(["--conda-prefix", args["--conda-prefix"]])
        if args["--verbose"]:
            sm_command.append("--verbose")
        try:
            subprocess_results = subprocess.run(sm_command, check=True)
        except subprocess.CalledProcessError as ex:
            print(ex, file=sys.stderr)
            sys.exit(98)
    else:
        sm_command: List[str] = ["snakemake", "--snakefile", str(snakefile), "--directory", str(args["--output"]),
                                 "--cores", args["--cores"], "--use-conda", "--conda-frontend", args["--conda-frontend"],
                                 "--printshellcmds", "--latency-wait", args["--latency-wait"]]
        if args["--use-conda"]:
            sm_command.append("--use-conda")
        if args["--conda-frontend"]:
            sm_command.extend(["--conda-frontend", args["--conda-frontend"]])
        if args["--conda-prefix"]:
            sm_command.extend(["--conda-prefix", args["--conda-prefix"]])
        if args["--verbose"]:
            sm_command.append("--verbose")
        try:
            subprocess_results = subprocess.run(sm_command, check=True)
        except subprocess.CalledProcessError as ex:
            print(ex, file=sys.stderr)
            sys.exit(99)

        finish_time: datetime.datetime = datetime.datetime.utcnow()
        if args["--use-conda"]:
            generate_report.create_report(
                src_folder=REPORT_SRC_DIRECTORY,
                snakefiles_folder=SNAKEFILES_LIBRARY,
                output_folder=args["--output"],
                curare_version=metadata.__version__,
                runtime=finish_time - start_time,
                curare_samples_file=args["--samples"]
            )


def check_columns(col_names: List[str], modules: Dict[str, List['Module']], paired_end: bool) -> List[Tuple[str, str, Optional[List[str]]]]:
    col2module: List[Tuple[str, str, Optional[List[str]]]] = [('', '', []) for _ in col_names]
    if 'name' not in col_names:
        raise InvalidSamplesFileError('Samples file: Column "{}" is missing'.format('name'))
    else:
        col2module[col_names.index('name')] = ('main', 'string', ['A-Z', 'a-z', '0-9', '_'])
    if paired_end:
        if 'forward_reads' not in col_names:
            raise InvalidSamplesFileError('Samples file: Column "{}" is missing'.format('forward_reads'))
        else:
            col2module[col_names.index('forward_reads')] = ('main', 'file', None)
        if 'reverse_reads' not in col_names:
            raise InvalidSamplesFileError('Samples file: Column "{}" is missing'.format('reverse_reads'))
        else:
            col2module[col_names.index('reverse_reads')] = ('main', 'file', None)
    else:
        if 'reads' not in col_names:
            raise InvalidSamplesFileError('Samples file: Column "{}" is missing'.format('reads'))
        else:
            col2module[col_names.index('reads')] = ('main', 'file', None)

    for module in [module for module_list in modules.values() for module in module_list]:
        if len(module.columns) > 0:
            for col_name, properties in module.columns.items():
                if col_name not in col_names:
                    raise InvalidSamplesFileError('Samples file: Column "{}" is missing'.format(col_name))
                else:
                    col2module[col_names.index(col_name)] = (module.name, properties.type.lower(), properties.character_set)
    return col2module


def parse_samples_file(samples_file: Path, modules: Dict[str, List['Module']], paired_end: bool) -> Dict[str, Dict[str, Dict[str, str]]]:
    table = {}  # type: Dict[str, Dict[str, Dict[str, str]]]
    with samples_file.open('r') as file:
        line: str = file.readline()
        while len(line.strip()) == 0 or line.startswith('#'):  # Ignore comments at the beginning of the TSV
            line = file.readline()

        col_names = [word.strip() for word in line.strip().split('\t')]
        col2module: List[Tuple[str, str, Optional[List[str]]]] = check_columns(col_names, modules, paired_end)
        for line in file:
            if len(line.strip()) == 0 or line.startswith('#'):
                continue
            columns: List[str] = [word.strip() for word in line.strip().split('\t')]
            entries: Dict[str, Dict[str, str]] = {}
            for index, col in enumerate(columns):
                module_name, value_type, value_char_set = col2module[index]
                if value_type == 'string' and value_char_set is not None:
                    is_valid, character = check_string_validity(col, value_char_set)
                    if not is_valid:
                        raise InvalidSamplesFileError(
                            'Column "{}" contains invalid character "{}" in entry "{}". Only these characters are allowed: {}'.format(
                                col_names[index], character, col, value_char_set
                            )
                        )
                if value_type == 'file':
                    if col.startswith('/'):
                        if not Path(col).resolve().exists():
                            raise InvalidSamplesFileError(
                                'Unknown file in Column "{}":\nUser input: {}\nResolved to: {}'.format(
                                    col_names[index], col, (samples_file.parent / col).resolve()
                                )
                            )
                    else:
                        if not (samples_file.parent / col).resolve().exists():
                            raise InvalidSamplesFileError(
                                'Unknown file in Column "{}":\nUser input: {}\nResolved to: {}'.format(
                                    col_names[index], col, (samples_file.parent / col).resolve()
                                )
                            )

                if col2module[index] == '' or col2module[index] == 'name':
                    continue
                elif module_name not in entries:
                    entries[module_name] = {}
                if value_type == 'file' and not col.startswith('/'):
                    entries[module_name][col_names[index]] = str((samples_file.parent / col).resolve())
                    if col_names[index] in ['reads', 'forward_reads', 'reverse_reads']:
                        if entries[module_name][col_names[index]].endswith(".gz"):
                            entries[module_name][col_names[index] + "_gzipped"] = True
                        else:
                            entries[module_name][col_names[index] + "_gzipped"] = False
                else:
                    entries[module_name][col_names[index]] = col
            table[columns[0]] = entries

    if not table:
        raise EmptySamplesFileError(
                                'Samples file does not contain in samples: {}'.format(
                                    samples_file.resolve()
                                )
                            )

    return table


def check_string_validity(string: str, character_set: List[str]) -> Tuple[bool, Optional[str]]:
    character_set = character_set.copy()
    if 'A-Z' in character_set:
        del character_set[character_set.index('A-Z')]
        character_set.extend([chr(x) for x in range(65, 91)])
    if 'a-z' in character_set:
        del character_set[character_set.index('a-z')]
        character_set.extend([chr(x) for x in range(97, 123)])
    if '0-9' in character_set:
        del character_set[character_set.index('0-9')]
        character_set.extend([chr(x) for x in range(48, 58)])
    for character in string:
        if character not in character_set:
            return False, character
    return True, None


def load_pipeline_file(pipeline_file: Path) -> Tuple[Dict[str, List['Module']], bool]:
    modules = {"preprocessing": [],
               "premapping": [],
               "mapping": [],
               "analysis": []}  # type: Dict[str, List[str]]

    used_modules = {"preprocessing": [],
                    "premapping": [],
                    "mapping": [],
                    "analysis": []}  # type: Dict[str, List['Module']]
    pipeline = yaml.safe_load(pipeline_file.open('r'))

    if "preprocessing" in pipeline:
        if "modules" in pipeline["preprocessing"]:
            pipeline_module = pipeline["preprocessing"]["modules"]
            if isinstance(pipeline_module, str):
                if pipeline_module:
                    modules["preprocessing"].append(pipeline_module)
                else:
                    modules["preprocessing"].append('none')  # Add "None" module
            elif isinstance(pipeline_module, list):
                if len(pipeline_module) > 1:
                    raise InvalidPipelineFileError('Error in category "preprocessing": Too many preprocessing modules are selected (max 1)')
                if pipeline_module:
                    modules["preprocessing"].append(pipeline_module[0])
                else:
                    modules["preprocessing"].append('none')  # Add "None" module
            else:
                raise InvalidPipelineFileError('Error in category "preprocessing": Modules must be a list or a string containing the module')
        else:
            modules["preprocessing"].append('none')  # Add "None" module
    else:
        modules["preprocessing"].append('none')  # Add "None" module

    if "premapping" in pipeline:
        pipeline_module = pipeline["premapping"]["modules"]
        if "modules" in pipeline["premapping"]:
            if isinstance(pipeline_module, list):
                for module in pipeline_module:
                    modules["premapping"].append(module)
            elif isinstance(pipeline_module, str):
                modules["premapping"].append(pipeline_module)
            else:
                raise InvalidPipelineFileError('Error in category "premapping": Modules must be a list or a string containing the module')

    if "mapping" in pipeline:
        pipeline_module = pipeline["mapping"]["modules"]
        if "modules" in pipeline["mapping"]:
            if isinstance(pipeline_module, list):
                if len(pipeline_module) != 1:
                    raise InvalidPipelineFileError('Error in category "mapping": Exactly one mapping module must be selected')
                modules["mapping"].append(pipeline_module[0])
            elif isinstance(pipeline_module, str):
                modules["mapping"].append(pipeline_module)
            else:
                raise InvalidPipelineFileError('Error in category "mapping": Modules must be a list or a string containing the module')
    else:
        raise InvalidPipelineFileError('Error in category "mapping": No mapping module found')

    if "analysis" in pipeline:
        pipeline_module = pipeline["analysis"]["modules"]
        if "modules" in pipeline["analysis"]:
            if isinstance(pipeline_module, list):
                for module in pipeline_module:
                    modules["analysis"].append(module)
            elif isinstance(pipeline_module, str):
                modules["mapping"].append(pipeline_module)
            else:
                raise InvalidPipelineFileError('Error in category "analysis": Modules must be a list or a string containing the module')

    if "pipeline" in pipeline:
        if "paired_end" in pipeline["pipeline"]:
            pipeline_paired_end = pipeline["pipeline"]["paired_end"]
            if isinstance(pipeline_paired_end, bool) or (pipeline_paired_end.upper() in ['TRUE', 'FALSE']):
                paired_end = pipeline_paired_end
            else:
                raise InvalidPipelineFileError('Option "paired_end" must either be "True" or "False"')
        else:
            raise InvalidPipelineFileError('Option "paired_end" must be set')
    else:
        raise InvalidPipelineFileError('Option "paired_end" must be set')

    for category, category_modules in modules.items():
        for module_name in category_modules:
            settings = pipeline[category].get(module_name, {})
            used_modules[category].append(load_module(category, module_name, settings, pipeline_file, paired_end))

    return used_modules, paired_end


def get_setting(setting_name, setting_properties, user_settings, pipeline_file_path):
    setting_type = setting_properties['type']
    if setting_type.startswith('file'):
        file: Path = Path(user_settings[setting_name]).resolve() if user_settings[setting_name].startswith('/') else (pipeline_file_path.parent / user_settings[setting_name]).resolve()
        if setting_type == 'file_input':
            if not file.exists():
                raise InvalidFileError('Error in option "{}": File does not exist.\nUser input: {}\nResolved to: {}'.format(setting_name, user_settings[setting_name], file))
        setting = str(file)
    elif setting_type == 'enum':
        if user_settings[setting_name] not in setting_properties['choices']:
            raise UnknownEnumError('Error in option "{}": Unknown value "{}". Allowed choices:\n{}'.format(setting_name, user_settings[setting_name], ''.join([' + {}\n'.format(choice) for choice in setting_properties['choices'].keys()])))
        setting = setting_properties['choices'][user_settings[setting_name]]
    elif setting_type == 'number':
        value = user_settings[setting_name]
        number_type = setting_properties['number_type']
        min_value = -math.inf if setting_properties['range']['min'] == "-Inf" else setting_properties['range']['min']
        max_value = math.inf if setting_properties['range']['max'] == "Inf" else setting_properties['range']['max']
        if number_type == 'integer':
            try:
                value = int(value)
            except ValueError:
                raise InvalidNumberTypeError('Error in option "{}": "{}" cannot be converted into an integer'.format(setting_name, value))
        elif number_type == 'float':
            try:
                value = float(value)
            except ValueError:
                raise InvalidNumberTypeError('Error in option "{}": "{}" cannot be converted into a float'.format(setting_name, value))
        else:
            raise InvalidPipelineFileError('Error in option "{}": Unknown number type'.format(setting_name))
        if min_value <= value <= max_value:
            setting = str(value)
        else:
            raise OutOfBondError('Error in option "{}": Value out of valid range. Used value: {} - Range: {}-{}'.format(setting_name, user_settings[setting_name], min_value, max_value))
    elif setting_type == 'string':
        setting = user_settings[setting_name]
    else:
        setting = user_settings[setting_name]

    return setting

def get_default_setting(setting_name, setting_properties):
    setting_type = setting_properties['type']
    default_setting: str = setting_properties['default']
    if setting_type == 'enum':
        if default_setting not in setting_properties['choices']:
            raise UnknownEnumError('Error in option "{}": Unknown default value "{}". Allowed choices:\n{}'.format(setting_name, default_setting, ''.join([' + {}\n'.format(choice) for choice in setting_properties['choices'].keys()])))
        return setting_properties['choices'][default_setting]
    else:
        return default_setting


def load_module(category: str, module_name: str, user_settings: Dict[str, str], pipeline_file_path: Path, paired_end: bool) -> 'Module':
    loaded_module = Module(module_name)
    module_yaml_file = SNAKEFILES_LIBRARY / category / module_name / (module_name + '.yaml')
    try:
        if module_yaml_file.is_file():
            module_yaml = yaml.safe_load(module_yaml_file.open('r'))
            if 'required_settings' in module_yaml:
                for setting_name, setting_properties in module_yaml['required_settings'].items():
                    if user_settings and setting_name in user_settings:
                        loaded_module.add_setting(setting_name, get_setting(setting_name, setting_properties, user_settings, pipeline_file_path))
                    else:
                        raise InvalidPipelineFileError(module_name.capitalize() + ': Required parameter "' + setting_name + '" is missing')
            if 'optional_settings' in module_yaml:
                for setting_name, setting_properties in module_yaml['optional_settings'].items():
                    if user_settings and setting_name in user_settings:
                        loaded_module.add_setting(setting_name, get_setting(setting_name, setting_properties, user_settings, pipeline_file_path))
                    else:
                        loaded_module.add_setting(setting_name, get_default_setting(setting_name, setting_properties))
            if 'columns' in module_yaml:
                for column_name, column_properties in module_yaml['columns'].items():
                    loaded_module.add_column(column_name, ColumnProperties(column_properties['type'], column_properties['description'], column_properties.get('character_set', None)))

            if paired_end:
                loaded_module.snakefile = SNAKEFILES_LIBRARY / category / module_name / module_yaml['paired_end']['snakefile']
                if 'required_settings' in module_yaml['paired_end']:
                    for setting_name, setting_properties in module_yaml['paired_end']['required_settings'].items():
                        if user_settings and setting_name in user_settings:
                            loaded_module.add_setting(setting_name, get_setting(setting_name, setting_properties, user_settings, pipeline_file_path))
                        else:
                            raise InvalidPipelineFileError(module_name.capitalize() + ': Required parameter "' + setting_name + '" is missing')
                if 'optional_settings' in module_yaml['paired_end']:
                    for setting_name, setting_properties in module_yaml['paired_end']['optional_settings'].items():
                        if user_settings and setting_name in user_settings:
                            loaded_module.add_setting(setting_name, get_setting(setting_name, setting_properties, user_settings, pipeline_file_path))
                        else:
                            loaded_module.add_setting(setting_name, get_default_setting(setting_name, setting_properties))
                if 'columns' in module_yaml['paired_end']:
                    for column_name, column_properties in module_yaml['paired_end']['columns'].items():
                        loaded_module.add_column(column_name, ColumnProperties(column_properties['type'], column_properties['description'], column_properties.get('character_set', None)))

            else:
                loaded_module.snakefile = SNAKEFILES_LIBRARY / category / module_name / module_yaml['single_end']['snakefile']
                if 'required_settings' in module_yaml['single_end']:
                    for setting_name, setting_properties in module_yaml['single_end']['required_settings'].items():
                        if user_settings and setting_name in user_settings:
                            loaded_module.add_setting(setting_name, get_setting(setting_name, setting_properties, user_settings, pipeline_file_path))
                        else:
                            raise InvalidPipelineFileError(module_name.capitalize() + ': Required parameter "' + setting_name + '" is missing')
                if 'optional_settings' in module_yaml['single_end']:
                    for setting_name, setting_properties in module_yaml['single_end']['optional_settings'].items():
                        if user_settings and setting_name in user_settings:
                            loaded_module.add_setting(setting_name, get_setting(setting_name, setting_properties, user_settings, pipeline_file_path))
                        else:
                            loaded_module.add_setting(setting_name, get_default_setting(setting_name, setting_properties))
                if 'columns' in module_yaml['single_end']:
                    for column_name, column_properties in module_yaml['single_end']['columns'].items():
                        loaded_module.add_column(column_name, ColumnProperties(column_properties['type'], column_properties['description'], column_properties.get('character_set', None)))

        else:
            raise UnknownModuleError(category.capitalize() + ': Unknown module "' + module_name + '"')
    except UnknownModuleError as e:
        raise e
    except InvalidFileError as e:
        raise InvalidPipelineFileError("Error in module {}:\n{}".format(module_name, e))
    except InvalidNumberTypeError as e:
        raise InvalidPipelineFileError("Error in module {}:\n{}".format(module_name, e))
    except OutOfBondError as e:
        raise InvalidPipelineFileError("Error in module {}:\n{}".format(module_name, e))
    except UnknownEnumError as e:
        raise InvalidPipelineFileError("Error in module {}:\n{}".format(module_name, e))
    except Exception as e:
        raise InvalidPipelineFileError("Unknown Error in module {}:\n{}".format(module_name, e))

    return loaded_module


def create_output_directory(output_path: Path):
    if not output_path.exists():
        output_path.mkdir(parents=True)
    elif not output_path.is_dir():
        raise NotADirectoryError("Cannot create directory: {}. File with this name found.".format(output_path))

    snakefiles_target_directory = output_path / SNAKEFILES_TARGET_DIRECTORY
    if not snakefiles_target_directory.exists():
        snakefiles_target_directory.mkdir(parents=True)
    elif not snakefiles_target_directory.is_dir():
        raise NotADirectoryError("Cannot create directory: {}. File with this name found.".format(output_path))

    report_data_directory = output_path / REPORT_TARGET_DIRECTORY / 'data'
    if not report_data_directory.exists():
        report_data_directory.mkdir(parents=True)
    elif not report_data_directory.is_dir():
        raise NotADirectoryError("Cannot create directory: {}. File with this name found.".format(output_path))


def create_snakefile(output_folder: Path, samples: Dict[str, Dict[str, Dict[str, Any]]], modules: Dict[str, List['Module']], use_conda: bool,
                     conda_environment: Path, curare_pipeline_file: Path) -> Path:
    config_file: Path = create_snakemake_config_file(output_folder, samples)
    # find every rule name
    re_rule_name = re.compile('^rule (?P<rule_name>.*):$', re.MULTILINE)
    # find every lib reference
    re_lib_folder = re.compile('lib/(?P<file_name>[^\s]*)', re.MULTILINE)
    snakefile_module_paths = []
    # for every Module in modules
    for module in [module for module_list in modules.values() for module in module_list]:
        with module.snakefile.open('r') as module_file:
            module_content = module_file.read()
            # change rule name from <rule name> to <module name>__<rule name>
            module_content = re_rule_name.sub('rule {}__\g<rule_name>:'.format(module.name.lower().replace('-', '_')), module_content)
            module_content = re_lib_folder.sub('{}/{}_lib/\g<file_name>'.format(SNAKEFILES_TARGET_DIRECTORY, module.name.lower()), module_content)
            for (wildcard, value) in module.settings.items():
                module_content = module_content.replace("%%{}%%".format(wildcard.upper()), str(value))
            module_path = output_folder / SNAKEFILES_TARGET_DIRECTORY / (module.name.lower() + '.sm')
            with module_path.open('w') as module_output_file:
                module_output_file.write(module_content)
                snakefile_module_paths.append(module_path.name)
            lib_src = module.snakefile.parent / 'lib'
            if lib_src.is_dir():
                lib_dest = output_folder / SNAKEFILES_TARGET_DIRECTORY / (module.name.lower() + '_lib')
                if lib_dest.is_dir():
                    dir_comp = filecmp.dircmp(str(lib_src), str(lib_dest))
                    if dir_comp.left_only or dir_comp.diff_files:
                        copy_lib(lib_src, lib_dest)
                    else:
                        for sub in dir_comp.subdirs.values():
                            if sub.left_only or sub.diff_files:
                                copy_lib(lib_src, lib_dest)
                else:
                    copy_lib(lib_src, lib_dest)

    snakefile_main_path = output_folder / 'Snakefile'
    with snakefile_main_path.open('w') as snakefile:
        snakefile.write(
            'configfile: "{}"\n\n'.format(SNAKEFILES_TARGET_DIRECTORY / config_file.name))
        for path in snakefile_module_paths:
            snakefile.write('include: "{}"\n'.format(SNAKEFILES_TARGET_DIRECTORY / path))
        snakefile.write('\n')
        snakefile.write('rule all:\n')
        snakefile.write('    input:\n')
        for module in [module for (category, module_list) in modules.items() for module in module_list]:
            snakefile.write('        rules.{module_name}__all.input,\n'.format(module_name=module.name.lower().replace('-', '_')))

        # copy parse_versions snakefile to parse conda versions for report.
        if use_conda:
            conda_environment = conda_environment if conda_environment is not None else Path(".snakemake/conda")
            # copy parse_versions.py script
            copy_tree(str(GLOBAL_LIB), str(output_folder / GLOBAL_LIB_TARGET_DIR), preserve_symlinks=True)
            with (SNAKEFILES_LIBRARY / 'misc' / 'parse_versions').open() as versions_snakefile:
                parse_versions_rule: List[str] = versions_snakefile.read()\
                    .replace('%%CONDA_ENVIRONMENT%%', str(conda_environment))\
                    .replace('%%PIPELINE_YAML%%', str(curare_pipeline_file))\
                    .split("\n")

                for i, line in enumerate(parse_versions_rule):
                    # Write output of parse_versions in input of rule "all"
                    if 'output:' in line:
                        next_line = parse_versions_rule[i+1]
                        snakefile.write('        {},\n'.format(next_line.strip()))
                        snakefile.write('\n')
                snakefile.writelines([line + "\n" for line in parse_versions_rule])

    return snakefile_main_path


def create_snakemake_config_file(output_folder: Path, samples: Dict[str, Dict[str, Dict[str, Any]]]) -> Path:
    config_path = output_folder / SNAKEFILES_TARGET_DIRECTORY / 'snakefile_config.yml'
    with config_path.open('w') as config_file:
        config_file.write('entries:\n')
        for row, modules in samples.items():
            config_file.write('    "{}":\n'.format(row))
            for module_name, columns in modules.items():
                config_file.write('        "{}":\n'.format(module_name))
                for column, value in columns.items():
                    if isinstance(value, (int, float, bool)):
                        config_file.write('            "{}": {}\n'.format(column, value))
                    else:
                        config_file.write('            "{}": "{}"\n'.format(column, value))
    return config_path


def copy_lib(src_folder: Path, dest_folder: Path):
    try:
        if dest_folder.is_dir():
            shutil.rmtree(str(dest_folder))
        shutil.copytree(str(src_folder), str(dest_folder), symlinks=True)
    except shutil.Error as err:
        raise err


def parse_arguments():
    args = docopt(__doc__, version=metadata.__version__)
    args["--samples"] = Path(args["--samples"]).resolve()
    args["--output"] = Path(args["--output"])
    args["--pipeline"] = Path(args["--pipeline"]).resolve()
    if args["--conda-prefix"]:
        args["--conda-prefix"] = Path(args["--conda-prefix"]).resolve()
    if args["--cluster-config-file"]:
        args["--cluster-config-file"] = Path(args["--cluster-config-file"]).resolve()
    if args["--conda-frontend"] not in ["conda", "mamba"]:
        raise UnknownCommandLineArgumentError("Command Line Arguments: Argument {} unknown for command line option '{}'".format(args["--conda-frontend"], "--conda-frontend"))

    for file in ["--samples", "--pipeline", "--cluster-config-file"]:
        if args[file]:
            if not args[file].exists():
                raise UnknownInputFileError("Command Line Arguments: Unknown file: {}".format(args[file]))

    return args


class Module:
    """Structure class for used modules

        Attributes:
            name -- name of module
            snakefile -- path to snakefile of module
            settings -- dictionary with all user-defined settings
            columns -- dictionary of all necessary columns in group file

    """

    def __init__(self, name: str, snakefile_path: Path = None, user_settings: Dict[str, Any] = None, columns: Dict[str, 'ColumnProperties'] = None):
        self.name = name  # type: str

        if snakefile_path is None:
            self.snakefile = None
        else:
            self.snakefile = snakefile_path.resolve()  # type: Path

        if user_settings is None:
            self.settings = {}  # type: Dict[str, Any]
        else:
            self.settings = user_settings

        if columns is None:
            self.columns = {}  # type: Dict[str, 'ColumnProperties']
        else:
            self.columns = columns

    def __str__(self):
        return self.name

    def __repr__(self):
        return "Module(name={}, snakefile_path={})".format(self.name, self.snakefile)

    def add_setting(self, name: str, value: str):
        self.settings[name] = value

    def get_setting(self, name: str) -> str:
        return self.settings[name]

    def add_column(self, name: str, value: 'ColumnProperties'):
        self.columns[name] = value

    def get_column(self, name: str) -> 'ColumnProperties':
        return self.columns[name]


class ColumnProperties:
    """Structure class for column properties

    """

    def __init__(self, col_type: str, description: str, chr_set: List[str] = None):
        self.type = col_type
        self.description = description
        self.character_set = chr_set


class EmptySamplesFileError(Exception):
    """Exception raised for errors in the samples file.

        Attributes:
            message -- message displayed
    """

    def __init__(self, message: str):
        super(EmptySamplesFileError, self).__init__(message)


class InvalidSamplesFileError(Exception):
    """Exception raised for errors in the samples file.

        Attributes:
            message -- message displayed
    """

    def __init__(self, message: str):
        super(InvalidSamplesFileError, self).__init__(message)


class InvalidPipelineFileError(Exception):
    """Exception raised for errors in the pipeline file.

        Attributes:
            message -- message displayed
    """

    def __init__(self, message: str):
        super(InvalidPipelineFileError, self).__init__(message)


class UnknownInputFileError(Exception):
    """Exception raised when input files as argument could not be found.

        Attributes:
            message -- message displayed
    """

    def __init__(self, message: str):
        super(UnknownInputFileError, self).__init__(message)


class OutOfBondError(Exception):
    """Exception raised for a value out of bond.

        Attributes:
            message -- message displayed
    """

    def __init__(self, message: str):
        super(OutOfBondError, self).__init__(message)


class InvalidNumberTypeError(Exception):
    """Exception raised for an invalid number type.

        Attributes:
            message -- message displayed
    """

    def __init__(self, message: str):
        super(InvalidNumberTypeError, self).__init__(message)


class InvalidFileError(Exception):
    """Exception raised when using an invalid file.

        Attributes:
            message -- message displayed
    """

    def __init__(self, message: str):
        super(InvalidFileError, self).__init__(message)


class UnknownEnumError(Exception):
    """Exception raised when using unknown enum value.

            Attributes:
                message -- message displayed
        """

    def __init__(self, message: str):
        super(UnknownEnumError, self).__init__(message)

class UnknownModuleError(Exception):
    """Exception raised when using unknown module.

            Attributes:
                message -- message displayed
        """

    def __init__(self, message: str):
        super(UnknownModuleError, self).__init__(message)

class UnknownCommandLineArgumentError(Exception):
    """Exception raised when using unknown command line argument.

            Attributes:
                message -- message displayed
        """

    def __init__(self, message: str):
        super(UnknownCommandLineArgumentError, self).__init__(message)

if __name__ == '__main__':
    try:
        main()
    except KeyboardInterrupt:
        print(ClColors.FAIL + 'Interrupted' + ClColors.ENDC, file=sys.stderr)
        sys.exit(130)