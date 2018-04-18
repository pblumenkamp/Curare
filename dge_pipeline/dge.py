import argparse
import errno
import os
import subprocess

from collections import namedtuple

from snakemake import snakemake

PROGRAM_NAME = "Differential gene expression pipeline"

SNAKEFILES = {
    "bowtie2": os.path.join(os.path.dirname(__file__), "snakefiles/dge_bowtie2_pe"),
    "bwa": os.path.join(os.path.dirname(__file__), "snakefiles/dge_bwa_samse")
}
RFILES = {
    "deseq2": os.path.join(os.path.dirname(__file__), "r_files/deseq2_analysis.R")
}

GroupEntry_PE = namedtuple('GroupEntry_PE', ['name', 'condition', 'forward', 'reverse'])
GroupEntry_SE = namedtuple('GroupEntry_SE', ['name', 'condition', 'file'])


def main():
    args = parse_arguments()
    validate_argsfiles(args.groups_file, args.ref_genome_file, args.ref_annotation_file)
    groups = parse_groups_file(args.groups_file, args.pe)
    validate_inputfiles(groups, args.pe)
    create_output_directory(args.output_folder)
    snakefile = create_snakefile(SNAKEFILES["bowtie2"], args, groups)
    if not snakemake(snakefile, cores=args.threads):
        exit(1)
    rfile = create_rfile(RFILES["deseq2"], os.path.join(args.output_folder, "counts.txt"), args.output_folder, groups, args.threads)
    subprocess.call("R --vanilla < " + rfile, shell=True)


def parse_groups_file(groups_file, isPE):
    groups = []
    file = open(groups_file, 'r')
    for entry in file:
        if len(entry.strip()) == 0:
            continue
        cols = entry.strip().split('\t')
        if not ((len(cols) == 4 and isPE) or (len(cols) == 3 and not isPE)):
            file.close()
            raise InvalidGroupsFileError(isPE)
        cols[2] = os.path.abspath(os.path.join(os.path.dirname(groups_file), cols[2]))
        if len(cols) == 3:
            groups.append(GroupEntry_SE._make(cols))
        if len(cols) == 4:
            cols[3] = os.path.abspath(os.path.join(os.path.dirname(groups_file), cols[3]))
            groups.append(GroupEntry_PE._make(cols))
    file.close()
    return groups


def validate_argsfiles(groups_file, ref_genome, ref_annotation):
    if not os.path.isfile(groups_file):
        raise FileNotFoundError(errno.ENOENT, os.strerror(errno.ENOENT), groups_file)
    if not os.path.isfile(ref_genome):
        raise FileNotFoundError(errno.ENOENT, os.strerror(errno.ENOENT), ref_genome)
    if not os.path.isfile(ref_annotation):
        raise FileNotFoundError(errno.ENOENT, os.strerror(errno.ENOENT), ref_annotation)


def validate_inputfiles(groups, isPE):
    for entry in groups:
        if not ((len(entry) == 4 and isPE) or (len(entry) == 3 and not isPE)):
            raise InvalidGroupsFileError(isPE)
        if not os.path.isfile(entry[2]):
            raise FileNotFoundError(errno.ENOENT, os.strerror(errno.ENOENT), entry[2])
        if isPE and not os.path.isfile(entry[3]):
            raise FileNotFoundError(errno.ENOENT, os.strerror(errno.ENOENT), entry[3])


def create_output_directory(output_path):
    if not os.path.exists(output_path):
        os.makedirs(output_path)
    elif not os.path.isdir(output_path):
        raise NotADirectoryError(filename=output_path)
    if not os.path.exists(os.path.join(output_path, "genome_index")):
        os.makedirs(os.path.join(output_path, "genome_index"))


def create_snakefile(snakefile, args, groups):
    with open(snakefile, 'r') as sf:
        content = sf.read()

    ref_genome = args.ref_genome_file
    output_folder = args.output_folder
    ref_annotation = args.ref_annotation_file
    isPE = args.pe
    count_single_mapped = args.count_single_mapped
    feature_type = args.gff_feature_type
    feature_name = args.gff_feature_name

    content = content.replace("%%SAMPLE_NAMES%%", ", ".join(['"' + entry.name + '"' for entry in groups]))
    if isPE:
        content = content.replace("%%SAMPLE_PATHS%%", ", ".join(
            ['"' + entry.name + '": ["' + entry.forward + '", "' + entry.reverse + '"]' for entry in groups]))
    else:
        content = content.replace("%%SAMPLE_PATHS%%", ", ".join(
            ['"' + entry.name + '": "' + entry.file + '"' for entry in groups]))

    featurecounts_options = []
    if isPE:
        featurecounts_options.append("-p")
        if not count_single_mapped:
            featurecounts_options.append("-B")
    content = content.replace("%%FEATURECOUNTS_OPTIONS%%", " ".join(featurecounts_options))
    content = content.replace("%%GENOME_FASTA%%", ref_genome)
    content = content.replace("%%GENOME_INDEX%%", os.path.join(output_folder, "genome_index/genome"))
    content = content.replace("%%GENOME_GFF%%", ref_annotation)
    content = content.replace("%%OUTPUT_FOLDER%%", output_folder)
    content = content.replace("%%GFF_FEATURE_TYPE%%", feature_type)
    content = content.replace("%%GFF_FEATURE_NAME%%", feature_name)
    with open(os.path.join(output_folder, "Snakefile"), 'w') as sf:
        sf.write(content)
    return os.path.join(output_folder, "Snakefile")


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
    required.add_argument('--reference-genome', dest='ref_genome_file', required=True)
    required.add_argument('--output', dest='output_folder', required=True)
    required.add_argument('--reference-annotation', dest='ref_annotation_file', required=True)
    pe_se = required.add_mutually_exclusive_group(required=True)
    pe_se.add_argument('--se', dest='se', action='store_true')
    pe_se.add_argument('--pe', dest='pe', action='store_true')

    feature_counts = parser.add_argument_group('FeatureCounts arguments')
    feature_counts.add_argument('--gff-feature-name', dest='gff_feature_name', default='ID')
    feature_counts.add_argument('--gff-feature-type', dest='gff_feature_type', default='gene')
    feature_counts.add_argument('--count-single-mapped', dest='count_single_mapped', action='store_true', help="Count reads with only one end aligned [Only for paired-end]")

    other = parser.add_argument_group('Other arguments')
    other.add_argument('-t', '--threads', dest='threads', default=1, type=int, help="Number of threads")
    other.add_argument('-v', '--version', action='version', version='%(prog)s 0.1', help="Show program's version number and exit")
    other.add_argument('-h', '--help', action="help", help="Show this help message and exit")

    return parser.parse_args()


class InvalidGroupsFileError(Exception):
    """Exception raised for errors in the groups file.

        Attributes:
            path -- path to groups file
            for_pe -- groups file for paired-end data
    """

    def __init__(self, for_pe):
        if for_pe:
            super(InvalidGroupsFileError, self).__init__("Groups file should contain 3 columns in each line")
        else:
            super(InvalidGroupsFileError, self).__init__("Groups file should contain 2 columns in each line")


if __name__ == '__main__':
    main()
