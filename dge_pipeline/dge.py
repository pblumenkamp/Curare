import argparse
import errno
import os
from collections import namedtuple

from snakemake import snakemake

from dge_pipeline.customErrors import InvalidGroupsFileError

PROGRAM_NAME = "Differential gene expression pipeline"

SNAKEFILES = {
    "bowtie2": os.path.join(os.path.dirname(__file__), "snakefiles/dge_bowtie2_pe"),
    "bwa": os.path.join(os.path.dirname(__file__), "snakefiles/dge_bwa_samse")
}

GroupEntry_PE = namedtuple('GroupEntry_PE', ['name', 'condition', 'forward', 'reverse'])
GroupEntry_SE = namedtuple('GroupEntry_SE', ['name', 'condition', 'file'])


def main():
    args = parse_arguments()
    for arg in args.__dict__:
        print(f"{arg}: {args.__dict__[arg]}")
    validate_argsfiles(args.groups_file, args.ref_genome_file, args.ref_annotation_file)
    groups = parse_groups_file(args.groups_file, args.pe)
    validate_inputfiles(groups, args.pe)
    create_output_directory(args.output_folder)
    create_snakefile(SNAKEFILES["bowtie2"], args.output_folder)


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
    os.makedirs(os.path.join(output_path, "genome_index"))


def create_snakefile(snakefile, output_folder, ref_genome, ref_annotation, groups, isPE):
    with open(snakefile, 'r') as sf:
        content = sf.read()
    content = content.replace("%%SAMPLE_NAMES%%", ", ".join([entry.name for entry in groups]))
    if isPE:
        content = content.replace("%%SAMPLE_PATHS%%", ", ".join(
            [entry.name + ": [" + entry.forward + ", " + entry.reverse + "]" for entry in groups]))
    else:
        content = content.replace("%%SAMPLE_PATHS%%", ", ".join(
            [entry.name + ": " + entry.file for entry in groups]))
    content = content.replace("%%GENOME_FASTA%%", ref_genome)
    content = content.replace("%%GENOME_INDEX%%", os.path.join(output_folder, "genome_index/genome"))
    content = content.replace("%%GENOME_GFF%%", ref_annotation)
    content = content.replace("%%OUTPUT_FOLDER%%", output_folder)
    with open(os.path.join(output_folder, "snakefile"), 'w') as sf:
        sf.write(content)


def parse_arguments():
    parser = argparse.ArgumentParser(prog=PROGRAM_NAME)
    parser.add_argument('--groups', dest='groups_file', required=True)
    parser.add_argument('--reference-genome', dest='ref_genome_file', required=True)
    parser.add_argument('--reference-annotation', dest='ref_annotation_file', required=True)
    parser.add_argument('--output', dest='output_folder', required=True)
    pe_se = parser.add_mutually_exclusive_group(required=True)
    pe_se.add_argument('--se', dest='se', action='store_true')
    pe_se.add_argument('--pe', dest='pe', action='store_true')
    parser.add_argument('-v', '--version', action='version', version='%(prog)s 0.1')
    return parser.parse_args()


if __name__ == '__main__':
    main()
