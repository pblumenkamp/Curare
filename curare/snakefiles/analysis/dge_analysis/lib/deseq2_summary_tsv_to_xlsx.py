#!/usr/bin/env python3

"""
Converts the TSV output of the DESeq2 module of the dge pipeline to XLSX

Exit codes:
    0: Program finished successful
    1: Error while reading GFF file
    2: GFF file does not contain specified identifier (--identifier)
    3: TSV file is empty or only contains a header (or one row and no header)
    4: Python module is missing
"""

import importlib.util
import sys
import csv
import argparse
import gzip

from importlib import util

missing_modules = []
for module in ['pandas', 'xlsxwriter']:
    if importlib.util.find_spec(module) is None:
        missing_modules.append(module)
if len(missing_modules) != 0:
    for module in missing_modules:
        print('Python module "{}" is missing'.format(module), file=sys.stderr)
    sys.exit(4)

import pandas as pd


def parse_arguments():
    parser = argparse.ArgumentParser()
    parser.add_argument('--tsv', help="TSV file to convert. File must contain a header in the first row and must not have any comments.")
    parser.add_argument('--conditions', dest='number_of_conditions', type=int, help="Number of Conditions in TSV minus 1 (#Cond - 1)")
    parser.add_argument('--gff', help="GFF file used for creating the TSV")
    parser.add_argument('--identifier', help="GFF identifier, e.g. ID")
    parser.add_argument('--feature', help="Used GFF feature, e.g. gene or CDS")
    parser.add_argument('--attributes', type=str, default="",
                        help="Comma-seperated GFF attributes (e.g product,locus_tag) to show as columns at the beginning of the XLSX file")
    parser.add_argument('--output', help="Output path for XLSX file")
    return parser.parse_args()


def get_col_widths(df):
    return [max(y) for y in [[len(col)] + [len(x) for x in df[col]] for col in df.columns]]


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
    feature = args.feature
    wanted_gff_attributes = [arg.upper() for arg in args.attributes.split(",")]

    annotations = {}
    if gff_file.endswith(".gz"):
        gff = gzip.open(gff_file, "rt")
    else:
        gff = open(gff_file, "r")
    for line in gff:
        try:
            if line.startswith("#"):
                continue
            columns = line.strip().split("\t")
            if len(columns) != 9:
                continue
            if columns[2] == feature:
                attributes_string = columns[8]
                attributes = {a.upper(): b for a, b in [att.split("=", maxsplit=1) for att in attributes_string.split(";")] if
                              a.upper() in wanted_gff_attributes + [identifier]}
                annotations[attributes[identifier]] = {}
                annotations[attributes[identifier]]['attr'] = attributes_string.replace(';', '; ')
                annotations[attributes[identifier]]['gff_start'] = columns[3]
                annotations[attributes[identifier]]['gff_stop'] = columns[4]
                annotations[attributes[identifier]]['gff_strand'] = columns[6]
                for attr in wanted_gff_attributes:
                    if attr in attributes:
                        annotations[attributes[identifier]][attr] = attributes[attr]
                    else:
                        annotations[attributes[identifier]][attr] = "-"
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
                row.append("Attributes")
            else:
                if row[0] in annotations:
                    for attr in wanted_gff_attributes:
                        row.insert(1, annotations[row[0]][attr])
                    row.insert(1, annotations[row[0]]['gff_strand'])
                    row.insert(1, annotations[row[0]]['gff_stop'])
                    row.insert(1, annotations[row[0]]['gff_start'])
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
    writer = pd.ExcelWriter(outfile,
                            engine='xlsxwriter',
                            options={'strings_to_numbers': True}
                            )
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
                      'min_value': 0.001,
                      'max_value': 1,
                      'mid_value': 0.01}

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
    worksheet.conditional_format(1, 4 + len(wanted_gff_attributes), rows - 1, 2 * number_of_conditions + len(wanted_gff_attributes) + 3,
                                 p_value_format)
    worksheet.conditional_format(1, 4 + len(wanted_gff_attributes) + 2 * number_of_conditions, rows - 1,
                                 3 * number_of_conditions + len(wanted_gff_attributes) + 3, log_fold_format)
    worksheet.conditional_format(1, 4 + len(wanted_gff_attributes) + 3 * number_of_conditions, rows - 1, columns - 1, count_format)

    # freeze first row and column
    worksheet.freeze_panes(1, 1)

    # autofilter for each column
    worksheet.autofilter(0, 0, rows - 1, columns)

    # legend sheet
    legend_sheet = workbook.add_worksheet("legend")
    legend_sheet.write(0, 0, "p-values")
    legend_sheet.write(0, 1, "lfc")
    legend_sheet.write(0, 2, "counts")

    legend_sheet.write(1, 0, 0.001)
    legend_sheet.write(2, 0, 0.01)
    legend_sheet.write(3, 0, 1)
    legend_sheet.conditional_format(1, 0, 3, 0, p_value_format)

    legend_sheet.write(1, 1, "min", workbook.add_format({'bg_color': "#7FFFAD"}))
    legend_sheet.write(2, 1, 0, workbook.add_format({'bg_color': "#FFFFFF"}))
    legend_sheet.write(3, 1, "max", workbook.add_format({'bg_color': "#FF0000"}))

    legend_sheet.write(1, 2, 0)
    legend_sheet.write(2, 2, 100)
    legend_sheet.write(3, 2, 1000)
    legend_sheet.conditional_format(1, 2, 3, 2, count_format)

    writer.save()


if __name__ == '__main__':
    main()
