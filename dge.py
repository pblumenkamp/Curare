import argparse

PROGRAM_NAME = "Differential gene expression pipeline"


def main():
    args = parse_arguments()
    for arg in args.__dict__:
        print(f"{arg}: {args.__dict__[arg]}")


def parse_arguments():
    parser = argparse.ArgumentParser(prog=PROGRAM_NAME)
    parser.add_argument('--groups', dest='groups', required=True)
    parser.add_argument('--reference-genome', dest='ref_genome', required=True)
    parser.add_argument('--reference-annotation', dest='ref_annotation', required=True)
    parser.add_argument('--output', dest='output_folder', required=True)
    pe_se = parser.add_mutually_exclusive_group(required=True)
    pe_se.add_argument('--se', dest='se_folder')
    pe_se.add_argument('--pe', dest='pe_folder')
    parser.add_argument('-v', '--version', action='version', version='%(prog)s 0.1')
    return parser.parse_args()

if __name__ == '__main__':
    main()
