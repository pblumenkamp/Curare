#! /usr/bin/env python3

import argparse
from typing import Dict
import sys

def main(gff_file: str, feature_type: str, reverse_strand: bool):
    with open(gff_file, 'r') as gff:
        for line in gff:
            try:
                if line.startswith("#"):
                    continue
                columns = line.strip().split("\t")
                if len(columns) != 9 or columns[2] != feature_type:
                    continue

                parsed_attributes = parse_attributes(columns[8])
                reverse_strand_dict: Dict[str, str] = {"+": "-", "-": "+"}
                print("{}\t{}\t{}\t{}\t{}\t{}\t{}\t{}\t{}\t{}\t{}\t{}".format(
                    columns[0],
                    columns[3],
                    columns[4],
                    parsed_attributes.get("ID", "-"),
                    max(min(int(columns[4]), 1000), 0),
                    reverse_strand_dict[columns[6]] if reverse_strand else columns[6],
                    columns[3],
                    columns[4],
                    "255,0,0",
                    1,
                    int(columns[4])-int(columns[3]),
                    0
                ))
            except Exception as e:
                print('Error while reading GFF file "{}"'.format(gff_file), file=sys.stderr)
                print(e, file=sys.stderr)
                sys.exit(1)


def parse_attributes(attributes: str, attribute_separator: str=';', key_value_separator: str='=', quotes: str='"') -> Dict[str,str]:
    state: str = 'first_letter_key'  # first_letter_key, key, value, quotes
    splitted_attributes: Dict[str, str] = {}
    key: str = ""
    value: str = ""

    for char in attributes:
        if state == 'first_letter_key':
            if char.isspace() or char in [attribute_separator, key_value_separator]:
                continue
            else:
                key += char
                state = 'key'
        elif state == 'key':
            if char == key_value_separator:
                state = 'value'
            else:
                key += char
        elif state == 'value':
            if char == quotes:
                value += char
                state = 'quotes'
            elif char == attribute_separator:
                splitted_attributes[key] = value
                key = ''
                value = ''
                state = 'first_letter_key'
            else:
                value += char
        else:  # quotes
            if char == quotes:
                value += char
                state = 'value'
            else:
                value += char
    if state == 'value':
        splitted_attributes[key] = value
    return splitted_attributes


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Convert GFF into RSeQC compatible bed12')

    required = parser.add_argument_group("Required arguments")
    required.add_argument("-g", "--gff", required=True, help="GFF File")
    required.add_argument("-t", "--type", required=True, help="GFF feature type")
    required.add_argument("-r", "--reverse", action='store_true', help="Reverse strand of features")
    try:
        args = parser.parse_args()
    except argparse.ArgumentTypeError:
        print("\n" + str(sys.exc_info()[1]) + "\n")
        parser.print_help()
        exit(1)
    main(args.gff, args.type, args.reverse)

