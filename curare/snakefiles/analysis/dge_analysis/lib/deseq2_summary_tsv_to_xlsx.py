#!/usr/bin/env python3

"""
Converts the TSV output of the DESeq2 module of the dge pipeline to XLSX

Exit codes:
    0: Program finished successful
    1: Error while reading GFF/GTF file
    2: GFF/GTF file does not contain specified identifier (--identifier)
    3: TSV file is empty or only contains a header (or one row and no header)
    4: Python module is missing
"""

import importlib.util
import sys
import csv
import argparse
import gzip

from importlib import util
from typing import Dict, List

missing_modules = []
for module in ['pandas', 'xlsxwriter']:
    if importlib.util.find_spec(module) is None:
        missing_modules.append(module)
if len(missing_modules) != 0:
    print('Missing python modules:', file=sys.stderr)
    for module in missing_modules:
        print('\t- {}'.format(module), file=sys.stderr)
    print('\nPlease use "conda" mode or install missing python packages.\n\n'.format(module), file=sys.stderr)
    sys.exit(4)

import pandas as pd


def parse_arguments():
    parser = argparse.ArgumentParser()
    parser.add_argument('--tsv', help="TSV file to convert. File must contain a header in the first row and must not have any comments.")
    parser.add_argument('--conditions', dest='number_of_conditions', type=int, help="Number of Conditions in TSV minus 1 (#Cond - 1)")
    parser.add_argument('--gff', help="GFF/GTF file used for creating the TSV")
    parser.add_argument('--identifier', help="GFF identifier, e.g. ID")
    parser.add_argument('--attributes', type=str, default="",
                        help="Comma-seperated GFF attributes (e.g product,locus_tag) to show as columns at the beginning of the XLSX file")
    parser.add_argument('--output', help="Output path for XLSX file")
    return parser.parse_args()


def get_col_widths(df):
    widths: List[int] = []
    for col in df.columns:
        entry_widths: List[int] = [len(col)]
        for x in df[col]:
            if x is not None:
                entry_widths.append(len(x))
        widths.append(max(entry_widths))
    return widths


def main():
    args = parse_arguments()

    tsv = args.tsv
    # number of conditions - 1
    number_of_conditions = args.number_of_conditions
    # output_file
    outfile = args.output
    # name of sheet
    sheet_name = "DGE"
    # gff file path
    gff_file = args.gff
    # e.g. ID
    identifier = args.identifier.upper()
    # e.g. gene or CDS
    wanted_gff_attributes = [arg.strip().upper() for arg in args.attributes.split(",")]

    annotations = {}
    if gff_file.endswith(".gz"):
        gff = gzip.open(gff_file, "rt")
        gtf_or_gff = "gtf" if gff_file.endswith("gtf.gz") else "gff"
    else:
        gff = open(gff_file, "r")
        gtf_or_gff = "gtf" if gff_file.endswith("gtf") else "gff"
    attribute_separator: str = ';' if gtf_or_gff == "gtf" else ';'
    key_value_separator: str = ' ' if gtf_or_gff == "gtf" else '='
    for line in gff:
        try:
            if line.startswith("#"):
                continue
            columns = line.strip().split("\t")
            if len(columns) != 9:
                continue
            
            wanted_gff_attributes_plus_id = wanted_gff_attributes + [identifier]
            attributes_string = columns[8]
            parsed_attributes = parse_attributes(attributes_string, attribute_separator=attribute_separator, key_value_separator=key_value_separator).items()
            attributes = {a.strip().upper(): b.strip() for a, b in parsed_attributes
                            if a.strip().upper() in wanted_gff_attributes_plus_id}
            if identifier in attributes:
                stripped_identifier: str = attributes[identifier].strip('"\'')
                annotations[stripped_identifier] = {}
                annotations[stripped_identifier]['attr'] = attributes_string.replace(';', '; ')
                annotations[stripped_identifier]['gff_chr'] = columns[0]
                annotations[stripped_identifier]['gff_start'] = columns[3]
                annotations[stripped_identifier]['gff_stop'] = columns[4]
                annotations[stripped_identifier]['gff_strand'] = columns[6]
                for attr in wanted_gff_attributes:
                    if attr in attributes:
                        annotations[stripped_identifier][attr] = attributes[attr]
                    else:
                        annotations[stripped_identifier][attr] = "-"
        except Exception as e:
            print('Error while reading GFF file "{}"'.format(gff_file), file=sys.stderr)
            print(e, file=sys.stderr)
            sys.exit(1)
    gff.close()
    if len(annotations) == 0:
        print('No identifier "{}" found in GFF file "{}"'.format(identifier, gff_file), file=sys.stderr)
        sys.exit(2)

    # fill list of lists:
    # first element = 1st row: header
    # second to n-th element: data
    list_data = []
    with open(tsv, "r") as tsv_stream:
        tsv_table = csv.reader(tsv_stream, delimiter="\t")
        for index, row in enumerate(tsv_table):
            if index == 0:
                for attr in wanted_gff_attributes:
                    row.insert(1, attr.capitalize())
                row.insert(1, 'Strand')
                row.insert(1, 'End')
                row.insert(1, 'Start')
                row.insert(1, 'Chromosome')
                row.append("Attributes")
            else:
                if row[0] in annotations:
                    for attr in wanted_gff_attributes:
                        row.insert(1, annotations[row[0]][attr])
                    row.insert(1, annotations[row[0]]['gff_strand'])
                    row.insert(1, annotations[row[0]]['gff_stop'])
                    row.insert(1, annotations[row[0]]['gff_start'])
                    row.insert(1, annotations[row[0]]['gff_chr'])
                    row.append(annotations[row[0]]['attr'])
                else:
                    row.insert(1, "-")
            list_data.append(row)
    if len(list_data) < 2:
        print('TSV file "{}" is empty or only contains a header'.format(tsv), file=sys.stderr)
        sys.exit(3)

    # get number of rows & columns
    rows = len(list_data)
    columns = len(list_data[1])

    # convert to pandas data frame, so pandas ExcelWriter is usable
    df = pd.DataFrame(list_data[1:], columns=list_data[0])
    with pd.ExcelWriter(outfile, engine='xlsxwriter', engine_kwargs={'options': {'strings_to_numbers': True}}) as writer:
        df.to_excel(writer, sheet_name=sheet_name, index=False)

        columns -= 1  # because of removing of first column
        workbook = writer.book
        worksheet = writer.sheets[sheet_name]

        for i, width in enumerate(get_col_widths(df)):
            worksheet.set_column(i, i, width + 5)

        p_value_format = {'type': '3_color_scale',
                        'min_color': "#7FFFAD",
                        'mid_color': "#EDE97E",
                        'max_color': "#FF0000",
                        'mid_type': 'num',
                        'min_type': 'num',
                        'max_type': 'num',
                        'min_value': 0.01,
                        'max_value': 1,
                        'mid_value': 0.05}

        log_fold_format = {'type': '3_color_scale',
                        'min_color': "#7FFFAD",
                        'mid_color': "#FFFFFF",
                        'mid_type': 'num',
                        'mid_value': 0,
                        'max_color': "#FF0000"}

        count_format = {'type': '3_color_scale',
                        'min_color': "#FFFFFF",
                        'mid_color': "#EDE97E",
                        'max_color': "#FF0000",
                        'mid_type': 'num',
                        'max_type': 'num',
                        'min_type': 'num',
                        'min_value': 0,
                        'mid_value': 100,
                        'max_value': 1000}

        # conditional formatting
        worksheet.conditional_format(1, 5 + len(wanted_gff_attributes), rows - 1, 2 * number_of_conditions + len(wanted_gff_attributes) + 3,
                                    p_value_format)
        worksheet.conditional_format(1, 5 + len(wanted_gff_attributes) + 2 * number_of_conditions, rows - 1,
                                    3 * number_of_conditions + len(wanted_gff_attributes) + 3, log_fold_format)
        worksheet.conditional_format(1, 5 + len(wanted_gff_attributes) + 3 * number_of_conditions, rows - 1, columns - 1, count_format)

        # freeze first row and column
        worksheet.freeze_panes(1, 1)

        # autofilter for each column
        worksheet.autofilter(0, 0, rows - 1, columns)

        # legend sheet
        legend_sheet = workbook.add_worksheet("legend")
        legend_sheet.write(0, 0, "p-values")
        legend_sheet.write(0, 1, "lfc")
        legend_sheet.write(0, 2, "counts")

        legend_sheet.write(1, 0, 0.01)
        legend_sheet.write(2, 0, 0.05)
        legend_sheet.write(3, 0, 1)
        legend_sheet.conditional_format(1, 0, 3, 0, p_value_format)

        legend_sheet.write(1, 1, "min", workbook.add_format({'bg_color': "#7FFFAD"}))
        legend_sheet.write(2, 1, 0, workbook.add_format({'bg_color': "#FFFFFF"}))
        legend_sheet.write(3, 1, "max", workbook.add_format({'bg_color': "#FF0000"}))

        legend_sheet.write(1, 2, 0)
        legend_sheet.write(2, 2, 100)
        legend_sheet.write(3, 2, 1000)
        legend_sheet.conditional_format(1, 2, 3, 2, count_format)
        

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
    main()
