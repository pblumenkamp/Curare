import argparse
import errno
import os

from dge_pipeline.customErrors import InvalidGroupsFileError

PROGRAM_NAME = "Differential gene expression pipeline"


def main():
    args = parse_arguments()
    for arg in args.__dict__:
        print(f"{arg}: {args.__dict__[arg]}")
    validate_argsfiles(args.groups_file, args.ref_genome_file, args.ref_annotation_file)
    groups = parse_groups_file(args.groups_file)
    validate_inputfiles(groups, args.pe)


def parse_groups_file(groups_file):
    groups = []
    file = open(groups_file, 'r')
    for entry in file:
        cols = entry.strip().split('\t')
        cols[0] = os.path.abspath(os.path.join(os.path.dirname(groups_file), cols[0]))
        if len(cols) == 3:
            cols[1] = os.path.abspath(os.path.join(os.path.dirname(groups_file), cols[1]))
        groups.append(tuple(cols))
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
        if not ((len(entry) == 3 and isPE) or (len(entry) == 2 and not isPE)):
            raise InvalidGroupsFileError(isPE)
        if not os.path.isfile(entry[0]):
            raise FileNotFoundError(errno.ENOENT, os.strerror(errno.ENOENT), entry[0])
        if isPE and not os.path.isfile(entry[1]):
            raise FileNotFoundError(errno.ENOENT, os.strerror(errno.ENOENT), entry[1])


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
