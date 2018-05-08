import argparse
import errno
import os
import shutil
import filecmp
import re
from typing import Dict, List, Tuple, Any

import yaml

from snakemake import snakemake

PROGRAM_NAME = "Differential gene expression pipeline"

SNAKEFILES_LIBRARY = os.path.join(os.path.dirname(os.path.realpath(__file__)), "snakefiles")

SNAKEFILES_TARGET_DIRECTORY = 'snakemake_lib'


def main():
    args = parse_arguments()
    used_modules, paired_end = load_config_file(args.config_file)
    validate_argsfiles(args.groups_file, args.config_file)
    groups = parse_groups_file(args.groups_file, used_modules, paired_end)
    create_output_directory(args.output_folder)
    snakefile = create_snakefile(args.output_folder, groups, used_modules)
    if not snakemake(snakefile, cores=args.threads, workdir=args.output_folder, verbose=args.verbose, printshellcmds=True):
        exit(1)


def check_columns(col_names: List[str], modules: Dict[str, List['Module']], paired_end: bool) -> List[Tuple[str, str]]:
    col2module = [('', '') for entry in col_names] # type: List[Tuple[str, str]]
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


def parse_groups_file(groups_file: str, modules: Dict[str, List['Module']], paired_end: bool) -> Dict[str, Dict[str, Dict[str, Any]]]:
    table = {} # type: Dict[str, Dict[str, Dict[str, Any]]]
    with open(groups_file, 'r') as file:
        col_names = file.readline().strip().split('\t')
        col2module = check_columns(col_names, modules, paired_end)
        for line in file:
            if len(line.strip()) == 0:
                continue
            columns = line.strip().split('\t')
            entries = {}
            for index, col in enumerate(columns):
                if col2module[index] == '' or col2module[index] == 'name':
                    continue
                elif col2module[index][0] not in entries:
                    entries[col2module[index][0]] = {}
                if col2module[index][1] == 'file' and not col.startswith('/'):
                    entries[col2module[index][0]][col_names[index]] = os.path.join(
                        os.path.dirname(os.path.realpath(groups_file)), col)
                else:
                    entries[col2module[index][0]][col_names[index]] = col
            table[columns[0]] = entries
    return table


def load_config_file(config_file: str) -> Tuple[Dict[str, List['Module']], bool]:
    modules = {"preprocessing": [],
               "premapping": [],
               "mapping": [],
               "analyses": []}      # type: Dict[str, List[str]]

    used_modules = {"preprocessing": [],
                    "premapping": [],
                    "mapping": [],
                    "analyses": []}     # type: Dict[str, List['Module']]
    config = yaml.load(open(config_file, 'r'))
    if "preprocessing" in config:
        if "module" in config["preprocessing"]:
            if not isinstance(config["preprocessing"]["module"], str):
                raise InvalidConfigFileError("preprocessing: Only one module as a string is allowed")
            elif config["preprocessing"]["module"] == '':
                modules["preprocessing"].append('none')
            else:
                modules["preprocessing"].append(config["preprocessing"]["module"])
        else:
            modules["preprocessing"].append('none')
    else:
        modules["preprocessing"].append('none')
    if "premapping" in config:
        if "modules" in config["premapping"]:
            if "module" in config["premapping"]:
                raise InvalidConfigFileError('premapping: Please use either "module" or "modules"')
            if not isinstance(config["premapping"]["modules"], list):
                raise InvalidConfigFileError("premapping: modules must be a LIST of modules")
            else:
                for module in config["premapping"]["modules"]:
                    modules["premapping"].append(module)
        elif "module" in config["premapping"]:
            if not isinstance(config["premapping"]["modules"], str):
                raise InvalidConfigFileError(
                    'premapping: Only one module as a string is allowed. For multiple modules use "modules"')
            else:
                modules["premapping"].append(config["premapping"]["module"])
    if "mapping" in config:
        if "module" in config["mapping"]:
            if not isinstance(config["mapping"]["module"], str):
                raise InvalidConfigFileError("mapping: Only one module as a string is allowed")
            else:
                modules["mapping"].append(config["mapping"]["module"])
    if "analyses" in config:
        if "modules" in config["analyses"]:
            if "module" in config["analyses"]:
                raise InvalidConfigFileError('analyses: Please use either "module" or "modules"')
            if not isinstance(config["analyses"]["modules"], list):
                raise InvalidConfigFileError("analyses: modules must be a LIST of modules")
            else:
                for module in config["analyses"]["modules"]:
                    modules["analyses"].append(module)
        elif "module" in config["analyses"]:
            if not isinstance(config["analyses"]["modules"], str):
                raise InvalidConfigFileError(
                    'analyses: Only one module as a string is allowed. For multiple modules use "modules"')
            else:
                modules["analyses"].append(config["analyses"]["module"])
    if "pipeline" in config:
        if "paired_end" in config["pipeline"]:
            if not isinstance(config["pipeline"]["paired_end"], bool) and not (config["pipeline"]["paired_end"] == 'True' or config["pipeline"]["paired_end"] == 'False'):
                raise InvalidConfigFileError('Pipeline: paired_end value must be "True" or "False"')
            else:
                paired_end = config["pipeline"]["paired_end"]
        else:
            raise InvalidConfigFileError('Pipeline: Option "paired_end" must be set')

    for category in modules:
        for module_name in modules[category]:
            settings = config[category].get(module_name, {})
            used_modules[category].append(load_module(category, module_name, settings, config_file, paired_end))

    return used_modules, paired_end


def load_module(category: str, module_name: str, settings: Dict[str, Any], config_file_path: str, paired_end: bool) -> 'Module':
    loaded_module = Module(module_name)
    if os.path.isfile(os.path.join(SNAKEFILES_LIBRARY, category, module_name, module_name + '.yaml')):
        module_yaml = yaml.load(open(os.path.join(SNAKEFILES_LIBRARY, category, module_name, module_name + '.yaml'), 'r'))
        if 'required_settings' in module_yaml:
            for setting_name, properties in module_yaml['required_settings'].items():
                if setting_name not in settings:
                    raise InvalidConfigFileError(
                        category.capitalize() + ': Required setting "' + setting_name + '" is missing')
                else:
                    if properties['type'] == 'file' and not settings[setting_name].startswith('/'):
                        loaded_module.add_setting(setting_name, os.path.realpath(
                            os.path.join(os.path.dirname(config_file_path), settings[setting_name])))
                    else:
                        loaded_module.add_setting(setting_name, settings[setting_name])
        if 'optional_settings' in module_yaml:
            for setting_name, properties in module_yaml['optional_settings'].items():
                if setting_name not in settings:
                    loaded_module.add_setting(setting_name, '')
                else:
                    if properties['type'] == 'file' and not settings[setting_name].startswith('/'):
                        loaded_module.add_setting(setting_name, os.path.realpath(
                            os.path.join(os.path.dirname(config_file_path), settings[setting_name])))
                    else:
                        loaded_module.add_setting(setting_name, settings[setting_name])
        if 'columns' in module_yaml:
            for column_name, properties in module_yaml['columns'].items():
                loaded_module.add_column(column_name, ColumnProperties(properties['type'], properties['description']))

        if paired_end:
            loaded_module.snakefile = os.path.join(SNAKEFILES_LIBRARY, category, module_name,
                                                 module_yaml['paired_end']['snakefile'])
            if 'required_settings' in module_yaml['paired_end']:
                for setting_name, properties in module_yaml['paired_end']['required_settings'].items():
                    if setting_name not in settings:
                        raise InvalidConfigFileError(
                            category.capitalize() + ': Required setting "' + setting_name + '" is missing')
                    else:
                        if properties['type'] == 'file' and not settings[setting_name].startswith('/'):
                            loaded_module.add_setting(setting_name, os.path.realpath(
                                os.path.join(os.path.dirname(config_file_path), settings[setting_name])))
                        else:
                            loaded_module.add_setting(setting_name, settings[setting_name])
            if 'optional_settings' in module_yaml['paired_end']:
                for setting_name, properties in module_yaml['paired_end']['optional_settings'].items():
                    if setting_name not in settings:
                        loaded_module.add_setting(setting_name, "")
                    else:
                        if properties['type'] == 'file' and not settings[setting_name].startswith('/'):
                            loaded_module.add_setting(setting_name, os.path.realpath(
                                os.path.join(os.path.dirname(config_file_path), settings[setting_name])))
                        else:
                            loaded_module.add_setting(setting_name, settings[setting_name])
            if 'columns' in module_yaml['paired_end']:
                for column_name, properties in module_yaml['paired_end']['columns'].items():
                    loaded_module.add_column(column_name, ColumnProperties(properties['type'], properties['description']))

        else:
            loaded_module.snakefile = os.path.join(SNAKEFILES_LIBRARY, category, module_name,
                                                 module_yaml['single_end']['snakefile'])
            if 'required_settings' in module_yaml['single_end']:
                for setting_name, properties in module_yaml['single_end']['required_settings'].items():
                    if setting_name not in settings:
                        raise InvalidConfigFileError(
                            category.capitalize() + ': Required setting "' + setting_name + '" is missing')
                    else:
                        if properties['type'] == 'file' and not settings[setting_name].startswith('/'):
                            loaded_module.add_setting(setting_name, os.path.realpath(
                                os.path.join(os.path.dirname(config_file_path), settings[setting_name])))
                        else:
                            loaded_module.add_setting(setting_name, settings[setting_name])
            if 'optional_settings' in module_yaml['single_end']:
                for setting_name, properties in module_yaml['single_end']['optional_settings'].items():
                    if setting_name not in settings:
                        loaded_module.add_setting(setting_name, "")
                    else:
                        if properties['type'] == 'file' and not settings[setting_name].startswith('/'):
                            loaded_module.add_setting(setting_name, os.path.realpath(
                                os.path.join(os.path.dirname(config_file_path), settings[setting_name])))
                        else:
                            loaded_module.add_setting(setting_name, settings[setting_name])
            if 'columns' in module_yaml['single_end']:
                for column_name, properties in module_yaml['single_end']['columns'].items():
                    loaded_module.add_column(column_name, ColumnProperties(properties['type'], properties['description']))

    else:
        raise InvalidConfigFileError(category.capitalize() + ': Unknown module "' + module_name + '"')

    return loaded_module


def validate_argsfiles(groups_file: str, config_file: str):
    if not os.path.isfile(groups_file):
        raise FileNotFoundError(errno.ENOENT, os.strerror(errno.ENOENT), groups_file)
    if not os.path.isfile(config_file):
        raise FileNotFoundError(errno.ENOENT, os.strerror(errno.ENOENT), config_file)


def create_output_directory(output_path: str):
    if not os.path.exists(output_path):
        os.makedirs(output_path)
    elif not os.path.isdir(output_path):
        raise NotADirectoryError(filename=output_path)

    snakefiles_target_directory = os.path.join(output_path, SNAKEFILES_TARGET_DIRECTORY)
    if not os.path.exists(snakefiles_target_directory):
        os.makedirs(snakefiles_target_directory)
    elif not os.path.isdir(snakefiles_target_directory):
        raise NotADirectoryError(filename=snakefiles_target_directory)


def create_snakefile(output_folder: str, groups: Dict[str, Dict[str, Dict[str, Any]]], modules: Dict[str, List['Module']]) -> str:
    config_file = create_snakemake_config_file(output_folder, groups)
    re_rule_name = re.compile('^rule (?P<rule_name>.*):$', re.MULTILINE)
    re_lib_folder = re.compile('lib/(?P<file_name>[^\s]*)', re.MULTILINE)
    snakefile_module_paths = []
    for module in [module for module_list in modules.values() for module in module_list]:
        with open(module.snakefile, 'r') as module_file:
            module_content = module_file.read()
            module_content = re_rule_name.sub('rule {}__\g<rule_name>:'.format(module.name.lower()), module_content)
            module_content = re_lib_folder.sub(
                '{}/{}/{}_lib/\g<file_name>'.format(output_folder, SNAKEFILES_TARGET_DIRECTORY, module.name.lower()),
                module_content)
            for (wildcard, value) in module.settings.items():
                module_content = module_content.replace("%%{}%%".format(wildcard.upper()), value)
            module_path = os.path.join(output_folder, SNAKEFILES_TARGET_DIRECTORY, module.name.lower() + '.sm')
            with open(module_path, 'w') as module_output_file:
                module_output_file.write(module_content)
                snakefile_module_paths.append(os.path.basename(module_path))
            lib_src = os.path.join(os.path.dirname(module.snakefile), 'lib')
            if os.path.isdir(lib_src):
                lib_dest = os.path.join(output_folder, SNAKEFILES_TARGET_DIRECTORY, module.name.lower() + '_lib')
                if os.path.isdir(lib_dest):
                    dir_comp = filecmp.dircmp(lib_src, lib_dest)
                    if dir_comp.left_only or dir_comp.diff_files:
                        copy_lib(lib_src, lib_dest)
                    else:
                        for sub in dir_comp.subdirs.values():
                            if sub.left_only or sub.diff_files:
                                copy_lib(lib_src, lib_dest)
                else:
                    copy_lib(lib_src, lib_dest)

    snakefile_main_path = os.path.join(output_folder, 'Snakefile')
    with open(snakefile_main_path, 'w') as snakefile:
        snakefile.write(
            'configfile: "{}"\n\n'.format(os.path.join(SNAKEFILES_TARGET_DIRECTORY, os.path.basename(config_file))))
        for path in snakefile_module_paths:
            snakefile.write('include: "{}"\n'.format(os.path.join(SNAKEFILES_TARGET_DIRECTORY, path)))
        snakefile.write('\n')
        snakefile.write('rule all:\n')
        snakefile.write('    input:\n')
        for module in [module for (category, module_list) in modules.items() for module in module_list if
                       category in ('premapping', 'analyses')]:
            snakefile.write('        rules.{module_name}__all.input,\n'.format(module_name=module.name))

    return snakefile_main_path


def create_snakemake_config_file(output_folder: str, groups: Dict[str, Dict[str, Dict[str, Any]]]) -> str:
    config_path = os.path.join(output_folder, SNAKEFILES_TARGET_DIRECTORY, 'snakefile_config.yml')
    with open(config_path, 'w') as config_file:
        config_file.write('entries:\n')
        for row, modules in groups.items():
            config_file.write('    "{}":\n'.format(row))
            for module_name, columns in modules.items():
                config_file.write('        "{}":\n'.format(module_name))
                for column, value in columns.items():
                    config_file.write('            "{}": "{}"\n'.format(column, value))
    return config_path


def copy_lib(src_folder: str, dest_folder: str):
    try:
        if os.path.isdir(dest_folder):
            shutil.rmtree(dest_folder)
        shutil.copytree(src_folder, dest_folder, symlinks=True)
    except shutil.Error as err:
        raise err


def parse_arguments() -> argparse.Namespace:
    parser = argparse.ArgumentParser(prog=PROGRAM_NAME, add_help=False)

    required = parser.add_argument_group('Required arguments')
    required.add_argument('--groups', dest='groups_file', required=True)
    required.add_argument('--config', dest='config_file', required=True)
    required.add_argument('--output', dest='output_folder', required=True)

    other = parser.add_argument_group('Other arguments')
    other.add_argument('-t', '--threads', dest='threads', default=1, type=int, help="Number of threads")
    other.add_argument('-v', '--version', action='version', version='%(prog)s 0.1',
                       help="Show program's version number and exit")
    other.add_argument('--verbose', dest='verbose', action="store_true", help="Print debugging output")
    other.add_argument('-h', '--help', action="help", help="Show this help message and exit")

    args = parser.parse_args()
    args.groups_file = os.path.realpath(args.groups_file)
    args.output_folder = os.path.realpath(args.output_folder)
    args.config_file = os.path.realpath(args.config_file)

    return args


class Module:
    """Structure class for used modules

        Attributes:
            name -- name of module
            snakefile -- path to snakefile of module
            settings -- dictionary with all user-defined settings
            columns -- dictionary of all necessary columns in group file

    """

    def __init__(self, name: str, snakefile_path: str=''):
        self.name = name
        self.snakefile = snakefile_path
        self.settings = {}  # type: Dict[str, Any]
        self.columns = {}   # type: Dict[str, 'ColumnProperties']

    def add_setting(self, name: str, value: Any):
        self.settings[name] = value

    def get_setting(self, name: str) -> Any:
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


if __name__ == '__main__':
    main()
