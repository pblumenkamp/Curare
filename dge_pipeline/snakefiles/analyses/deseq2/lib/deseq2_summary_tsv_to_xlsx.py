#!/usr/bin/env python3

import csv
import pandas as pd
import argparse


def parse_arguments():
    parser = argparse.ArgumentParser()
    parser.add_argument('--tsv', help="tsv")
    parser.add_argument('--conditions', dest='number_of_conditions', type=int)
    parser.add_argument('--gff')
    parser.add_argument('--identifier')
    parser.add_argument('--feature')
    parser.add_argument('--attributes', nargs='*', type=str, default=[])
    parser.add_argument('--output')
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
    # gff
    gff_file = args.gff
    # e.g. ID
    identifier = args.identifier.upper()
    feature = args.feature
    wanted_gff_attributes = [arg.upper() for arg in args.attributes]

    annotations = {}
    with open(gff_file, "r") as gff:
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
                print(e)
                print(line)
                raise e

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


    # get number of rows & columns
    rows = len(list_data)
    columns = len(list_data[1])

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
    worksheet.conditional_format(1, 4 + len(wanted_gff_attributes), rows - 1, 2 * number_of_conditions + len(wanted_gff_attributes) + 3, p_value_format)
    worksheet.conditional_format(1, 4 + len(wanted_gff_attributes) + 2 * number_of_conditions, rows - 1, 3 * number_of_conditions + len(wanted_gff_attributes) + 3, log_fold_format)
    worksheet.conditional_format(1, 4 + len(wanted_gff_attributes) + 3 * number_of_conditions, rows - 1, columns - 1, count_format)

    # freeze first row and column
    worksheet.freeze_panes(1, 1)

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
