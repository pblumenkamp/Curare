import argparse
import errno
import os
import re

import yaml

from snakemake import snakemake

PROGRAM_NAME = "Differential gene expression pipeline"

SNAKEFILES_PATH = os.path.join(os.path.dirname(os.path.realpath(__file__)), "snakefiles")

paired_end = False


def main():
    args = parse_arguments()
    used_modules = load_config_file(args.config_file)  # {'name': module, 'path': '', 'settings': {}, columns: {}}
    validate_argsfiles(args.groups_file, args.config_file)
    groups = parse_groups_file(args.groups_file, used_modules)
    create_output_directory(args.output_folder)
    snakefile = create_snakefile(args.output_folder, groups, used_modules)
    if not snakemake(snakefile, cores=args.threads, workdir=args.output_folder, verbose=args.verbose):
        exit(1)
    # rfile = create_rfile(RFILES["deseq2"], os.path.join(args.output_folder, "counts.txt"), args.output_folder, groups,
    #                      args.threads)
    # subprocess.call("R --vanilla < " + rfile, shell=True)


def check_columns(col_names, modules):
    col2module = ['' for entry in col_names]
    for module in [module for module_list in modules.values() for module in module_list]:
        if len(module['columns']) > 0:
            for col_name, properties in module['columns'].items():
                if col_name not in col_names:
                    raise InvalidGroupsFileError('Groups file: Column "{}" is missing'.format(col_name))
                else:
                    col2module[col_names.index(col_name)] = (module['name'], properties['type'])
    return col2module


def parse_groups_file(groups_file, modules):
    table = {}
    with open(groups_file, 'r') as file:
        col_names = file.readline().strip().split('\t')
        col2module = check_columns(col_names, modules)
        for line in file:
            if len(line.strip()) == 0:
                continue
            columns = line.strip().split('\t')
            entries = {}
            for index, col in enumerate(columns[1:]):
                if col2module[index + 1] == '':
                    continue
                elif col2module[index + 1] not in entries:
                    entries[col2module[index + 1]] = {}
                if col2module[index + 1][1] == 'file' and not col.startswith('/'):
                    entries[col2module[index + 1]][col_names[index + 1]] = os.path.join(
                        os.path.dirname(os.path.realpath(groups_file)), col)
                else:
                    entries[col2module[index + 1]][col_names[index + 1]] = col
            table[columns[0]] = entries
    return table


def load_config_file(config_file):
    modules = {"preprocessing": [],
               "premapping": [],
               "mapping": [],
               "analyses": []}

    used_modules = {"preprocessing": [],
                    "premapping": [],
                    "mapping": [],
                    "analyses": []}
    config = yaml.load(open(config_file, 'r'))
    if "preprocessing" in config:
        if "module" in config["preprocessing"]:
            if not isinstance(config["preprocessing"]["module"], str):
                raise InvalidConfigFileError("preprocessing: Only one module as a string is allowed")
            else:
                modules["preprocessing"].append(config["preprocessing"]["module"])
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
            if not isinstance(config["pipeline"]["paired_end"], bool):
                raise InvalidConfigFileError('Pipeline: paired_end value must be "True" or "False"')
            else:
                global paired_end
                paired_end = config["pipeline"]["paired_end"]
        else:
            raise InvalidConfigFileError('Pipeline: Option "paired_end" must be set')

    for category in modules:
        for module_name in modules[category]:
            settings = config[category].get(module_name, {})
            used_modules[category].append(load_module(category, module_name, settings, config_file))

    return used_modules


def load_module(category, module, settings, config_file_path):
    loaded_module = {'name': module, 'path': '', 'settings': {}, 'columns': {}}
    if os.path.isfile(os.path.join(SNAKEFILES_PATH, category, module, module + '.yaml')):
        module_yaml = yaml.load(open(os.path.join(SNAKEFILES_PATH, category, module, module + '.yaml'), 'r'))
        if 'required_settings' in module_yaml:
            for setting_name, properties in module_yaml['required_settings'].items():
                if setting_name not in settings:
                    raise InvalidConfigFileError(
                        category.capitalize() + ': Required setting "' + setting_name + '" is missing')
                else:
                    if properties['type'] == 'file' and not settings[setting_name].startswith('/'):
                        loaded_module['settings'][setting_name] = os.path.realpath(
                            os.path.join(os.path.dirname(config_file_path), settings[setting_name]))
                    else:
                        loaded_module['settings'][setting_name] = settings[setting_name]
        if 'optional_settings' in module_yaml:
            for setting_name, properties in module_yaml['optional_settings'].items():
                if setting_name not in settings:
                    loaded_module['settings'][setting_name] = ''
                else:
                    if properties['type'] == 'file' and not settings[setting_name].startswith('/'):
                        loaded_module['settings'][setting_name] = os.path.realpath(
                            os.path.join(os.path.dirname(config_file_path), settings[setting_name]))
                    else:
                        loaded_module['settings'][setting_name] = settings[setting_name]
        if 'columns' in module_yaml:
            for column_name, properties in module_yaml['columns'].items():
                loaded_module['columns'][column_name] = {'type': properties['type'],
                                                         'description': properties['description']}

        if paired_end:
            loaded_module['path'] = os.path.join(SNAKEFILES_PATH, category, module,
                                                 module_yaml['paired_end']['snakefile'])
            if 'required_settings' in module_yaml['paired_end']:
                for setting_name, properties in module_yaml['paired_end']['required_settings'].items():
                    if setting_name not in settings:
                        raise InvalidConfigFileError(
                            category.capitalize() + ': Required setting "' + setting_name + '" is missing')
                    else:
                        if properties['type'] == 'file' and not settings[setting_name].startswith('/'):
                            loaded_module['settings'][setting_name] = os.path.realpath(
                                os.path.join(os.path.dirname(config_file_path), settings[setting_name]))
                        else:
                            loaded_module['settings'][setting_name] = settings[setting_name]
            if 'optional_settings' in module_yaml['paired_end']:
                for setting_name, properties in module_yaml['paired_end']['optional_settings'].items():
                    if setting_name not in settings:
                        loaded_module['settings'][setting_name] = ""
                    else:
                        if properties['type'] == 'file' and not settings[setting_name].startswith('/'):
                            loaded_module['settings'][setting_name] = os.path.realpath(
                                os.path.join(os.path.dirname(config_file_path), settings[setting_name]))
                        else:
                            loaded_module['settings'][setting_name] = settings[setting_name]
            if 'columns' in module_yaml['paired_end']:
                for column_name, properties in module_yaml['paired_end']['columns'].items():
                    loaded_module['columns'][column_name] = {'type': properties['type'],
                                                             'description': properties['description']}

        else:
            loaded_module['path'] = os.path.join(SNAKEFILES_PATH, category, module,
                                                 module_yaml['single_end']['snakefile'])
            if 'required_settings' in module_yaml['single_end']:
                for setting_name, properties in module_yaml['single_end']['required_settings'].items():
                    if setting_name not in settings:
                        raise InvalidConfigFileError(
                            category.capitalize() + ': Required setting "' + setting_name + '" is missing')
                    else:
                        if properties['type'] == 'file' and not settings[setting_name].startswith('/'):
                            loaded_module['settings'][setting_name] = os.path.realpath(
                                os.path.join(os.path.dirname(config_file_path), settings[setting_name]))
                        else:
                            loaded_module['settings'][setting_name] = settings[setting_name]
            if 'optional_settings' in module_yaml['single_end']:
                for setting_name, properties in module_yaml['single_end']['optional_settings'].items():
                    if setting_name not in settings:
                        loaded_module['settings'][setting_name] = ""
                    else:
                        if properties['type'] == 'file' and not settings[setting_name].startswith('/'):
                            loaded_module['settings'][setting_name] = os.path.realpath(
                                os.path.join(os.path.dirname(config_file_path), settings[setting_name]))
                        else:
                            loaded_module['settings'][setting_name] = settings[setting_name]
            if 'columns' in module_yaml['single_end']:
                for column_name, properties in module_yaml['single_end']['columns'].items():
                    loaded_module['columns'][column_name] = {'type': properties['type'],
                                                             'description': properties['description']}

    else:
        raise InvalidConfigFileError(category.capitalize() + ': Unknown module "' + module + '"')

    return loaded_module


def validate_argsfiles(groups_file, config_file):
    if not os.path.isfile(groups_file):
        raise FileNotFoundError(errno.ENOENT, os.strerror(errno.ENOENT), groups_file)
    if not os.path.isfile(config_file):
        raise FileNotFoundError(errno.ENOENT, os.strerror(errno.ENOENT), config_file)


def create_output_directory(output_path):
    if not os.path.exists(output_path):
        os.makedirs(output_path)
    elif not os.path.isdir(output_path):
        raise NotADirectoryError(filename=output_path)


def create_snakefile(output_folder, groups, modules):
    config_file = create_snakemake_config_file(output_folder, groups)
    re_rule_name = re.compile('^rule (?P<rule_name>.*):$', re.MULTILINE)
    for module in [module for module_list in modules.values() for module in module_list]:
        with open(module['path'], 'r') as module_file:
            module_content = module_file.read()
            module_content = re_rule_name.sub('rule {}__\g<rule_name>:'.format(module['name']), module_content)
            for (wildcard, value) in module['settings'].items():
                module_content = module_content.replace("%%{}%%".format(wildcard.upper()), value)
            with open(os.path.join(output_folder, module['name'].upper()), 'w') as module_output_file:
                module_output_file.write(module_content)

    with open(os.path.join(output_folder, 'SNAKEFILE'), 'w') as snakefile:
        snakefile.write('configfile: "{}"\n\n'.format(os.path.basename(config_file)))
        for module in [module for module_list in modules.values() for module in module_list]:
            snakefile.write('include: "{}"\n'.format(module['name'].upper()))
        snakefile.write('\n')
        snakefile.write('rule all:\n')
        snakefile.write('    input:\n')
        for module in [module for (category, module_list) in modules.items() for module in module_list if
                       category in ('premapping', 'analyses')]:
            snakefile.write('        rules.{module_name}__all.input,\n'.format(module_name=module['name']))

    return os.path.join(output_folder, 'SNAKEFILE')

    # with open(snakefile, 'r') as sf:
    #     content = sf.read()
    #
    # ref_genome = args.ref_genome_file
    # output_folder = args.output_folder
    # ref_annotation = args.ref_annotation_file
    # isPE = args.pe
    # count_single_mapped = args.count_single_mapped
    # feature_type = args.gff_feature_type
    # feature_name = args.gff_feature_name
    #
    # content = content.replace("%%SAMPLE_NAMES%%", ", ".join(['"' + entry.name + '"' for entry in groups]))
    # if isPE:
    #     content = content.replace("%%SAMPLE_PATHS%%", ", ".join(
    #         ['"' + entry.name + '": ["' + entry.forward + '", "' + entry.reverse + '"]' for entry in groups]))
    # else:
    #     content = content.replace("%%SAMPLE_PATHS%%", ", ".join(
    #         ['"' + entry.name + '": "' + entry.file + '"' for entry in groups]))
    #
    # featurecounts_options = []
    # if isPE:
    #     featurecounts_options.append("-p")
    #     if not count_single_mapped:
    #         featurecounts_options.append("-B")
    # content = content.replace("%%FEATURECOUNTS_OPTIONS%%", " ".join(featurecounts_options))
    # content = content.replace("%%GENOME_FASTA%%", ref_genome)
    # content = content.replace("%%GENOME_INDEX%%", os.path.join(output_folder, "genome_index/genome"))
    # content = content.replace("%%GENOME_GFF%%", ref_annotation)
    # content = content.replace("%%OUTPUT_FOLDER%%", output_folder)
    # content = content.replace("%%GFF_FEATURE_TYPE%%", feature_type)
    # content = content.replace("%%GFF_FEATURE_NAME%%", feature_name)
    # with open(os.path.join(output_folder, "Snakefile"), 'w') as sf:
    #     sf.write(content)
    # return os.path.join(output_folder, "Snakefile")


def create_snakemake_config_file(output_folder, groups):
    with open(os.path.join(output_folder, 'snakefile_config.yml'), 'w') as config_file:
        config_file.write('entries:\n')
        for row, modules in groups.items():
            config_file.write('    "{}":\n'.format(row))
            for (module_name, module_type), columns in modules.items():
                config_file.write('        "{}":\n'.format(module_name))
                for column, value in columns.items():
                    config_file.write('            "{}": "{}"\n'.format(column, value))
    return os.path.join(output_folder, 'snakefile_config.yml')


def create_rfile(rfile, counttable, output_folder, groups, threads):
    with open(rfile, 'r') as rf:
        content = rf.read()
    content = content.replace("$$THREADS$$", str(threads))
    content = content.replace("$$COUNT_TABLE$$", counttable)
    content = content.replace("$$SAMPLE_NAMES$$", ", ".join(['"' + entry.name + '"' for entry in groups]))
    content = content.replace("$$CONDITIONS$$", ", ".join(['"' + entry.condition + '"' for entry in groups]))
    content = content.replace("$$RESULT_FOLDER$$", output_folder)
    print(os.path.join(output_folder, "dge_analysis.R"))
    with open(os.path.join(output_folder, "dge_analysis.R"), 'w') as rf:
        rf.write(content)
    return os.path.join(output_folder, "dge_analysis.R")


def parse_arguments():
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


class InvalidGroupsFileError(Exception):
    """Exception raised for errors in the groups file.

        Attributes:
            path -- path to groups file
            for_pe -- groups file for paired-end data
    """

    def __init__(self, message):
        super(InvalidGroupsFileError, self).__init__(message)


class InvalidConfigFileError(Exception):
    """Exception raised for errors in the config file.

        Attributes:
            path -- path to groups file
            for_pe -- groups file for paired-end data
    """

    def __init__(self, message):
        super(InvalidConfigFileError, self).__init__(message)


if __name__ == '__main__':
    main()
