import argparse
import errno
import os
import shutil
import filecmp
import re
from pathlib import Path
from typing import Dict, List, Tuple, Any

import yaml

from snakemake import snakemake

PROGRAM_NAME = "Differential gene expression pipeline generator"

SNAKEFILES_LIBRARY = Path(__file__).resolve().parent / "snakefiles"  # type: Path

SNAKEFILES_TARGET_DIRECTORY = 'snakemake_lib'  # type: str


def main():
    args = parse_arguments()
    used_modules, paired_end = load_config_file(args.config_file)
    validate_argsfiles(args.groups_file, args.config_file)
    groups = parse_groups_file(args.groups_file, used_modules, paired_end)
    create_output_directory(args.output_folder)
    snakefile = create_snakefile(args.output_folder, groups, used_modules)
    if not snakemake(str(snakefile), cores=args.threads, workdir=str(args.output_folder), verbose=args.verbose,
                     printshellcmds=True):
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
            entries = {}    # type: Dict[str, Dict[str, str]]
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
    config = yaml.load(config_file.open('r'))
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
                raise InvalidConfigFileError('premapping: Only one module as a string is allowed. For multiple modules use "modules"')
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
                raise InvalidConfigFileError('analyses: Only one module as a string is allowed. For multiple modules use "modules"')
            else:
                modules["analyses"].append(config["analyses"]["module"])
    if "pipeline" in config:
        if "paired_end" in config["pipeline"]:
            if not isinstance(config["pipeline"]["paired_end"], bool) and not (
                    config["pipeline"]["paired_end"] == 'True' or config["pipeline"]["paired_end"] == 'False'):
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


def load_module(category: str, module_name: str, settings: Dict[str, str], config_file_path: Path, paired_end: bool) -> 'Module':
    loaded_module = Module(module_name)
    module_yaml_file = SNAKEFILES_LIBRARY / category / module_name / (module_name + '.yaml')
    if module_yaml_file.is_file():
        module_yaml = yaml.load(module_yaml_file.open('r'))
        if 'required_settings' in module_yaml:
            for setting_name, properties in module_yaml['required_settings'].items():
                if setting_name not in settings:
                    raise InvalidConfigFileError(category.capitalize() + ': Required setting "' + setting_name + '" is missing')
                else:
                    if properties['type'] == 'file' and not settings[setting_name].startswith('/'):
                        loaded_module.add_setting(setting_name, str((config_file_path.parent / settings[setting_name]).resolve()))
                    else:
                        loaded_module.add_setting(setting_name, settings[setting_name])
        if 'optional_settings' in module_yaml:
            for setting_name, properties in module_yaml['optional_settings'].items():
                if setting_name not in settings:
                    loaded_module.add_setting(setting_name, '')
                else:
                    if properties['type'] == 'file' and not settings[setting_name].startswith('/'):
                        loaded_module.add_setting(setting_name, str((config_file_path.parent / settings[setting_name]).resolve()))
                    else:
                        loaded_module.add_setting(setting_name, settings[setting_name])
        if 'columns' in module_yaml:
            for column_name, properties in module_yaml['columns'].items():
                loaded_module.add_column(column_name, ColumnProperties(properties['type'], properties['description']))

        if paired_end:
            loaded_module.snakefile = SNAKEFILES_LIBRARY / category / module_name / module_yaml['paired_end']['snakefile']
            if 'required_settings' in module_yaml['paired_end']:
                for setting_name, properties in module_yaml['paired_end']['required_settings'].items():
                    if setting_name not in settings:
                        raise InvalidConfigFileError(category.capitalize() + ': Required setting "' + setting_name + '" is missing')
                    else:
                        if properties['type'] == 'file' and not settings[setting_name].startswith('/'):
                            loaded_module.add_setting(setting_name, str((config_file_path.parent / settings[setting_name]).resolve()))
                        else:
                            loaded_module.add_setting(setting_name, settings[setting_name])
            if 'optional_settings' in module_yaml['paired_end']:
                for setting_name, properties in module_yaml['paired_end']['optional_settings'].items():
                    if setting_name not in settings:
                        loaded_module.add_setting(setting_name, "")
                    else:
                        if properties['type'] == 'file' and not settings[setting_name].startswith('/'):
                            loaded_module.add_setting(setting_name, str((config_file_path.parent / settings[setting_name]).resolve()))
                        else:
                            loaded_module.add_setting(setting_name, settings[setting_name])
            if 'columns' in module_yaml['paired_end']:
                for column_name, properties in module_yaml['paired_end']['columns'].items():
                    loaded_module.add_column(column_name, ColumnProperties(properties['type'], properties['description']))

        else:
            loaded_module.snakefile = SNAKEFILES_LIBRARY / category / module_name / module_yaml['single_end']['snakefile']
            if 'required_settings' in module_yaml['single_end']:
                for setting_name, properties in module_yaml['single_end']['required_settings'].items():
                    if setting_name not in settings:
                        raise InvalidConfigFileError(category.capitalize() + ': Required setting "' + setting_name + '" is missing')
                    else:
                        if properties['type'] == 'file' and not settings[setting_name].startswith('/'):
                            loaded_module.add_setting(setting_name, str((config_file_path.parent / settings[setting_name]).resolve()))
                        else:
                            loaded_module.add_setting(setting_name, settings[setting_name])
            if 'optional_settings' in module_yaml['single_end']:
                for setting_name, properties in module_yaml['single_end']['optional_settings'].items():
                    if setting_name not in settings:
                        loaded_module.add_setting(setting_name, "")
                    else:
                        if properties['type'] == 'file' and not settings[setting_name].startswith('/'):
                            loaded_module.add_setting(setting_name, str((config_file_path.parent / settings[setting_name]).resolve()))
                        else:
                            loaded_module.add_setting(setting_name, settings[setting_name])
            if 'columns' in module_yaml['single_end']:
                for column_name, properties in module_yaml['single_end']['columns'].items():
                    loaded_module.add_column(column_name, ColumnProperties(properties['type'], properties['description']))

    else:
        raise InvalidConfigFileError(category.capitalize() + ': Unknown module "' + module_name + '"')

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
            module_content = re_rule_name.sub('rule {}__\g<rule_name>:'.format(module.name.lower()), module_content)
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
        for module in [module for (category, module_list) in modules.items() for module in module_list if category in ('premapping', 'analyses')]:
            snakefile.write('        rules.{module_name}__all.input,\n'.format(module_name=module.name))

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
    args.groups_file = Path(args.groups_file).resolve()
    args.output_folder = Path(args.output_folder)
    args.config_file = Path(args.config_file).resolve()

    return args


class Module:
    """Structure class for used modules

        Attributes:
            name -- name of module
            snakefile -- path to snakefile of module
            settings -- dictionary with all user-defined settings
            columns -- dictionary of all necessary columns in group file

    """

    def __init__(self, name: str, snakefile_path: Path = None):
        self.name = name  # type: str
        if snakefile_path is not None:
            self.snakefile = snakefile_path.resolve()  # type: Path
        else:
            self.snakefile = snakefile_path
        self.settings = {}  # type: Dict[str, Any]
        self.columns = {}  # type: Dict[str, 'ColumnProperties']

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


if __name__ == '__main__':
    main()
