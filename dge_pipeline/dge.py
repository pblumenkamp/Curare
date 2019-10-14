"""
DGE pipeline generator.

Usage:
    dge.py start --groups <groups_file> --config <config_file> --output <output_folder>
                 [--cluster-command <cluster_command>] [--cluster-config-file <config_file>] [--cluster-nodes <nodes>]
                 [--cores <cores>] [--latency-wait <seconds>] [--verbose]
    dge.py (--version | --help)

Options:
    -h --help               Show this help message and exit
    --version               Show version and exit

    Start:
    --groups <groups_file>                          File containing information about each sample
    --config <config_file>                          File containing information about the RNA-seq pipeline
    --output <output_folder>                        Output folder (will be created if not existing)
    --cluster-command <command>                     Command for cluster execution. , e.g. 'qsub'. For resource requests use also --cluster-config
    --cluster-config-file <config_file>             File containing cluster settings for individual rules.
                                                    See also: https://snakemake.readthedocs.io/en/stable/snakefiles/configuration.html#cluster-configuration
    --cluster-nodes <nodes>                         Maximal number of parallel jobs send to the cluster. Only used in cluster mode is used. [Default: 1]
    -t <cores> --cores <cores>                      Number of threads/cores. Defines locales cores in cluster mode. [Default: 1]
    --latency-wait <seconds>                        Seconds to wait before checking if all files of a rule were created. Should be increased if using cluster mode. [Default: 3]
    -v --verbose                                    Print additional information
"""


import argparse
import errno
import filecmp
import math
import os
import re
import shutil
import sys
import yaml

from pathlib import Path
from typing import Dict, List, Tuple, Any
from snakemake import snakemake
from docopt import docopt

import metadata

SNAKEFILES_LIBRARY = Path(__file__).resolve().parent / "snakefiles"  # type: Path

SNAKEFILES_TARGET_DIRECTORY = 'snakemake_lib'  # type: str


def main():
    args = parse_arguments()
    used_modules, paired_end = load_config_file(args["--config"])
    validate_argsfiles(args["--groups"], args["--config"])
    groups = parse_groups_file(args["--groups"], used_modules, paired_end)
    create_output_directory(args["--output"])
    snakefile = create_snakefile(args["--output"], groups, used_modules)
    if not snakemake(str(snakefile), cores=int(args["--cores"]), local_cores=int(args["--cores"]), nodes=int(args["--cluster-nodes"]), workdir=str(args["--output"]),
                     verbose=args["--verbose"], printshellcmds=True, cluster=args["--cluster-command"],
                     cluster_config=str(args["--cluster-config-file"]) if args["--cluster-config-file"] is not None else None,
                     latency_wait=int(args["--latency-wait"])):
        exit(1)


def check_columns(col_names: List[str], modules: Dict[str, List['Module']], paired_end: bool) -> List[Tuple[str, str]]:
    col2module = [('', '') for _ in col_names]  # type: List[Tuple[str, str]]
    if 'name' not in col_names:
        raise InvalidGroupsFileError('Groups file: Column "{}" is missing'.format('name'))
    else:
        col2module[col_names.index('name')] = ('main', 'string')
    if paired_end:
        if 'forward_reads' not in col_names:
            raise InvalidGroupsFileError('Groups file: Column "{}" is missing'.format('forward_reads'))
        else:
            col2module[col_names.index('forward_reads')] = ('main', 'file')
        if 'reverse_reads' not in col_names:
            raise InvalidGroupsFileError('Groups file: Column "{}" is missing'.format('reverse_reads'))
        else:
            col2module[col_names.index('reverse_reads')] = ('main', 'file')
    else:
        if 'reads' not in col_names:
            raise InvalidGroupsFileError('Groups file: Column "{}" is missing'.format('reads'))
        else:
            col2module[col_names.index('reads')] = ('main', 'file')

    for module in [module for module_list in modules.values() for module in module_list]:
        if len(module.columns) > 0:
            for col_name, properties in module.columns.items():
                if col_name not in col_names:
                    raise InvalidGroupsFileError('Groups file: Column "{}" is missing'.format(col_name))
                else:
                    col2module[col_names.index(col_name)] = (module.name, properties.type)
    return col2module


def parse_groups_file(groups_file: Path, modules: Dict[str, List['Module']], paired_end: bool) -> Dict[str, Dict[str, Dict[str, str]]]:
    table = {}  # type: Dict[str, Dict[str, Dict[str, str]]]
    with groups_file.open('r') as file:
        col_names = file.readline().strip().split('\t')
        col2module = check_columns(col_names, modules, paired_end)
        for line in file:
            if len(line.strip()) == 0:
                continue
            columns = line.strip().split('\t')
            entries = {}  # type: Dict[str, Dict[str, str]]
            for index, col in enumerate(columns):
                if col2module[index] == '' or col2module[index] == 'name':
                    continue
                elif col2module[index][0] not in entries:
                    entries[col2module[index][0]] = {}
                if col2module[index][1] == 'file' and not col.startswith('/'):
                    entries[col2module[index][0]][col_names[index]] = str((groups_file.parent / col).resolve())
                else:
                    entries[col2module[index][0]][col_names[index]] = col
            table[columns[0]] = entries
    return table


def load_config_file(config_file: Path) -> Tuple[Dict[str, List['Module']], bool]:
    modules = {"preprocessing": [],
               "premapping": [],
               "mapping": [],
               "analyses": []}  # type: Dict[str, List[str]]

    used_modules = {"preprocessing": [],
                    "premapping": [],
                    "mapping": [],
                    "analyses": []}  # type: Dict[str, List['Module']]
    config = yaml.safe_load(config_file.open('r'))

    if "preprocessing" in config:
        if "module" in config["preprocessing"]:
            config_module = config["preprocessing"]["module"]
            if isinstance(config_module, str):
                if config_module:
                    modules["preprocessing"].append(config_module)
                else:
                    modules["preprocessing"].append('none')  # Add "None" module
            elif isinstance(config_module, list):
                if len(config_module) > 1:
                    raise InvalidConfigFileError("preprocessing: Too many preprocessing modules are selected (max 1)")
                if config_module:
                    modules["preprocessing"].append(config_module[0])
                else:
                    modules["preprocessing"].append('none')  # Add "None" module
            else:
                raise InvalidConfigFileError("preprocessing: Modules must be a list or a string containing the module")
        else:
            modules["preprocessing"].append('none')  # Add "None" module
    else:
        modules["preprocessing"].append('none')  # Add "None" module

    if "premapping" in config:
        config_module = config["premapping"]["modules"]
        if "modules" in config["premapping"]:
            if isinstance(config_module, list):
                for module in config_module:
                    modules["premapping"].append(module)
            elif isinstance(config_module, str):
                modules["premapping"].append(config_module)
            else:
                raise InvalidConfigFileError("premapping: Modules must be a list or a string containing the module")

    if "mapping" in config:
        config_module = config["mapping"]["module"]
        if "module" in config["mapping"]:
            if isinstance(config_module, list):
                if len(config_module) != 1:
                    raise InvalidConfigFileError("mapping: Exactly one mapping module must be selected")
                modules["mapping"].append(config_module[0])
            elif isinstance(config_module, str):
                modules["mapping"].append(config_module)
            else:
                raise InvalidConfigFileError("mapping: Modules must be a list or a string containing the module")
    else:
        raise InvalidConfigFileError("mapping: No mapping module found")

    if "analyses" in config:
        config_module = config["analyses"]["modules"]
        if "modules" in config["analyses"]:
            if isinstance(config_module, list):
                for module in config_module:
                    modules["analyses"].append(module)
            elif isinstance(config_module, str):
                modules["mapping"].append(config_module)
            else:
                raise InvalidConfigFileError("analyses: Modules must be a list or a string containing the module")

    if "pipeline" in config:
        if "paired_end" in config["pipeline"]:
            config_paired_end = config["pipeline"]["paired_end"]
            if isinstance(config_paired_end, bool) or (config_paired_end.upper() in ['TRUE', 'FALSE']):
                paired_end = config_paired_end
            else:
                raise InvalidConfigFileError('Pipeline: paired_end value must either be "True" or "False"')
        else:
            raise InvalidConfigFileError('Pipeline: Option "paired_end" must be set')
    else:
        raise InvalidConfigFileError('Pipeline: Option "paired_end" must be set')

    for category in modules:
        for module_name in modules[category]:
            settings = config[category].get(module_name, {})
            used_modules[category].append(load_module(category, module_name, settings, config_file, paired_end))

    return used_modules, paired_end


def get_setting(setting_name, setting_properties, user_settings, config_file_path):
    setting_type = setting_properties['type']
    if setting_type == 'file':
        if user_settings[setting_name].startswith('/'):
            setting = user_settings[setting_name]
        else:
            setting = str((config_file_path.parent / user_settings[setting_name]).resolve())
    elif setting_type == 'enum':
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
                raise InvalidNumberTypeError("{} - \"{}\" cannot be converted into integer".format(setting_name, value))
        elif number_type == 'float':
            try:
                value = float(value)
            except ValueError:
                raise InvalidNumberTypeError("{} - \"{}\" cannot be converted into float".format(setting_name, value))
        else:
            raise InvalidConfigFileError("{} - Unknown number type".format(setting_name))
        if min_value < value < max_value:
            setting = str(value)
        else:
            raise OutOfBondError('Parameter: {} - Used value: {} - Range: {}-{}'.format(setting_name, user_settings[setting_name], min_value, max_value))
    elif setting_type == 'string':
        setting = user_settings[setting_name]
    else:
        setting = user_settings[setting_name]

    return setting


def load_module(category: str, module_name: str, user_settings: Dict[str, str], config_file_path: Path, paired_end: bool) -> 'Module':
    loaded_module = Module(module_name)
    module_yaml_file = SNAKEFILES_LIBRARY / category / module_name / (module_name + '.yaml')
    try:
        if module_yaml_file.is_file():
            module_yaml = yaml.safe_load(module_yaml_file.open('r'))
            if 'required_settings' in module_yaml:
                for setting_name, setting_properties in module_yaml['required_settings'].items():
                    if setting_name in user_settings:
                        loaded_module.add_setting(setting_name, get_setting(setting_name, setting_properties, user_settings, config_file_path))
                    else:
                        raise InvalidConfigFileError(module_name.capitalize() + ': Required parameter "' + setting_name + '" is missing')
            if 'optional_settings' in module_yaml:
                for setting_name, setting_properties in module_yaml['optional_settings'].items():
                    if setting_name in user_settings:
                        loaded_module.add_setting(setting_name, get_setting(setting_name, setting_properties, user_settings, config_file_path))
                    else:
                        loaded_module.add_setting(setting_name, setting_properties['default'])
            if 'columns' in module_yaml:
                for column_name, column_properties in module_yaml['columns'].items():
                    loaded_module.add_column(column_name, ColumnProperties(column_properties['type'], column_properties['description']))

            if paired_end:
                loaded_module.snakefile = SNAKEFILES_LIBRARY / category / module_name / module_yaml['paired_end']['snakefile']
                if 'required_settings' in module_yaml['paired_end']:
                    for setting_name, setting_properties in module_yaml['paired_end']['required_settings'].items():
                        if setting_name in user_settings:
                            loaded_module.add_setting(setting_name, get_setting(setting_name, setting_properties, user_settings, config_file_path))
                        else:
                            raise InvalidConfigFileError(module_name.capitalize() + ': Required parameter "' + setting_name + '" is missing')
                if 'optional_settings' in module_yaml['paired_end']:
                    for setting_name, setting_properties in module_yaml['paired_end']['optional_settings'].items():
                        if setting_name in user_settings:
                            loaded_module.add_setting(setting_name, get_setting(setting_name, setting_properties, user_settings, config_file_path))
                        else:
                            loaded_module.add_setting(setting_name, setting_properties['default'])
                if 'columns' in module_yaml['paired_end']:
                    for column_name, column_properties in module_yaml['paired_end']['columns'].items():
                        loaded_module.add_column(column_name, ColumnProperties(column_properties['type'], column_properties['description']))

            else:
                loaded_module.snakefile = SNAKEFILES_LIBRARY / category / module_name / module_yaml['single_end']['snakefile']
                if 'required_settings' in module_yaml['single_end']:
                    for setting_name, setting_properties in module_yaml['single_end']['required_settings'].items():
                        if setting_name in user_settings:
                            loaded_module.add_setting(setting_name, get_setting(setting_name, setting_properties, user_settings, config_file_path))
                        else:
                            raise InvalidConfigFileError(module_name.capitalize() + ': Required parameter "' + setting_name + '" is missing')
                if 'optional_settings' in module_yaml['single_end']:
                    for setting_name, setting_properties in module_yaml['single_end']['optional_settings'].items():
                        if setting_name in user_settings:
                            loaded_module.add_setting(setting_name, get_setting(setting_name, setting_properties, user_settings, config_file_path))
                        else:
                            loaded_module.add_setting(setting_name, setting_properties['default'])
                if 'columns' in module_yaml['single_end']:
                    for column_name, column_properties in module_yaml['single_end']['columns'].items():
                        loaded_module.add_column(column_name, ColumnProperties(column_properties['type'], column_properties['description']))

        else:
            raise InvalidConfigFileError(category.capitalize() + ': Unknown module "' + module_name + '"')
    except InvalidConfigFileError as e:
        print(e, file=sys.stderr)
        sys.exit(1)
    except InvalidNumberTypeError as e:
        print("{}: {}".format(module_name, e), file=sys.stderr)
        sys.exit(2)
    except OutOfBondError as e:
        print("{}: Value out of bond. ({})".format(module_name, e), file=sys.stderr)
        sys.exit(2)
    except Exception as e:
        print(e, file=sys.stderr)
        raise e
        sys.exit(999)

    return loaded_module


def validate_argsfiles(groups_file: Path, config_file: Path):
    if not groups_file.is_file():
        raise FileNotFoundError(errno.ENOENT, os.strerror(errno.ENOENT), str(groups_file))
    if not config_file.is_file():
        raise FileNotFoundError(errno.ENOENT, os.strerror(errno.ENOENT), str(config_file))


def create_output_directory(output_path: Path):
    if not output_path.exists():
        output_path.mkdir(parents=True)
    elif not output_path.is_dir():
        raise NotADirectoryError(filename=output_path)

    snakefiles_target_directory = output_path / SNAKEFILES_TARGET_DIRECTORY
    if not snakefiles_target_directory.exists():
        snakefiles_target_directory.mkdir(parents=True)
    elif not snakefiles_target_directory.is_dir():
        raise NotADirectoryError(filename=snakefiles_target_directory)


def create_snakefile(output_folder: Path, groups: Dict[str, Dict[str, Dict[str, Any]]], modules: Dict[str, List['Module']]) -> Path:
    config_file = create_snakemake_config_file(output_folder, groups)
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
                module_content = module_content.replace("%%{}%%".format(wildcard.upper()), value)
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
            'configfile: "{}"\n\n'.format(os.path.join(SNAKEFILES_TARGET_DIRECTORY, config_file.name)))
        for path in snakefile_module_paths:
            snakefile.write('include: "{}"\n'.format(os.path.join(SNAKEFILES_TARGET_DIRECTORY, path)))
        snakefile.write('\n')
        snakefile.write('rule all:\n')
        snakefile.write('    input:\n')
        for module in [module for (category, module_list) in modules.items() for module in module_list if
                       category in ('premapping', 'analyses', 'mapping')]:
            snakefile.write('        rules.{module_name}__all.input,\n'.format(module_name=module.name.lower().replace('-', '_')))

    return snakefile_main_path


def create_snakemake_config_file(output_folder: Path, groups: Dict[str, Dict[str, Dict[str, Any]]]) -> Path:
    config_path = output_folder / SNAKEFILES_TARGET_DIRECTORY / 'snakefile_config.yml'
    with config_path.open('w') as config_file:
        config_file.write('entries:\n')
        for row, modules in groups.items():
            config_file.write('    "{}":\n'.format(row))
            for module_name, columns in modules.items():
                config_file.write('        "{}":\n'.format(module_name))
                for column, value in columns.items():
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
    args["--groups"] = Path(args["--groups"]).resolve()
    args["--output"] = Path(args["--output"])
    args["--config"] = Path(args["--config"]).resolve()
    if args["--cluster-config-file"] is not None:
        args["--cluster-config-file"] = Path(args["--cluster-config-file"]).resolve()
    return args


# def parse_arguments() -> argparse.Namespace:
#     parser = argparse.ArgumentParser(prog=metadata.__program_name__, add_help=False)
#
#     required = parser.add_argument_group('Required arguments')
#     required.add_argument('--groups', dest='groups_file', required=True)
#     required.add_argument('--config', dest='config_file', required=True)
#     required.add_argument('--output', dest='output_folder', required=True)
#
#     other = parser.add_argument_group('Other arguments')
#     other.add_argument('--cluster-command', dest='cluster_command', default=None, type=str,
#                        help="Command for cluster execution. , e.g. 'qsub'. For resource requests use also --cluster-config")
#     other.add_argument('--cluster-config-file', dest='cluster_config_file', default=None, type=str,
#                        help="Path to cluster config file. "
#                             "See also: https://snakemake.readthedocs.io/en/stable/snakefiles/configuration.html#cluster-configuration")
#     other.add_argument('-t', '--cores', dest='cores', default=1, type=int,
#                        help="Number of threads/cores [Default: 1]. Defines locales cores in cluster mode")
#     other.add_argument('--cluster-nodes', dest='cluster_nodes', default=1, type=int,
#                        help="Maximal number of parallel jobs send to the cluster [Default: 1]. Only used in cluster mode is used.")
#     other.add_argument('--latency-wait', dest='latency', default=3, type=int,
#                        help="Seconds to wait before checking if all files of a rule were created [Default: 3]. Should be increased if using cluster mode.")
#     other.add_argument('-v', '--version', action='version', version='%(prog)s \nVersion: {}'.format(metadata.__version__),
#                        help="Show program's version number and exit")
#     other.add_argument('--verbose', dest='verbose', action="store_true", help="Print debugging output")
#     other.add_argument('-h', '--help', action="help", help="Show this help message and exit")
#
#     args = parser.parse_args()
#     args.groups_file = Path(args.groups_file).resolve()
#     args.output_folder = Path(args.output_folder)
#     args.config_file = Path(args.config_file).resolve()
#     if args.cluster_config_file is not None:
#         args.cluster_config_file = Path(args.cluster_config_file).resolve()
#
#     return args


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

    def __init__(self, col_type: str, description: str):
        self.type = col_type
        self.description = description


class InvalidGroupsFileError(Exception):
    """Exception raised for errors in the groups file.

        Attributes:
            message -- message displayed
    """

    def __init__(self, message: str):
        super(InvalidGroupsFileError, self).__init__(message)


class InvalidConfigFileError(Exception):
    """Exception raised for errors in the config file.

        Attributes:
            message -- message displayed
    """

    def __init__(self, message: str):
        super(InvalidConfigFileError, self).__init__(message)


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



if __name__ == '__main__':
    main()
