import sys
import csv
import pandas as pd


def get_col_widths(df):
    return [max(y) for y in [[len(col)] + [len(x) for x in df[col]] for col in df.columns]]


# function for lazy programmers. Only works for cells with values between 0 and 100: make a format white 2 black. You can change the colors (see below)
def format_w2c(min_color='#FFFFFF', max_color='#000000'):
    return {'type': '2_color_scale',
            'min_color': min_color,
            'max_color': max_color,
            'min_type': 'num',
            'max_type': 'num',
            'min_value': 0,
            'max_value': 100}


def main():
    tsv_file = sys.argv[1]
    output = sys.argv[2]
    # name of sheet
    sheet_name = "Mappings"

    # fill list of lists:
    # first element = 1st row: header
    # second to n-th element: data
    list_data = []
    with open(tsv_file, "r") as tsvin:
        tsvin = csv.reader(tsvin, delimiter="\t")
        for row in tsvin:
            list_data.append(row)

    # get number of rows & columns
    rows = len(list_data)
    columns = len(list_data[1])

    # make a pandas DataFrame (you don't have to to this with pandas. Maybe it's better to rewrite it and write the cells with a for-loop)
    # and write it to the xlsx sheet
    df = pd.DataFrame(list_data[1:], columns=list_data[0])

    writer = pd.ExcelWriter(output,
                            engine='xlsxwriter',
                            engine_kwargs={'options': {'strings_to_numbers': True}}
                            )
    df.to_excel(writer, sheet_name=sheet_name, index=False)

    columns -= 1  # because of the removing of first column
    workbook = writer.book
    worksheet = writer.sheets[sheet_name]

    # set first column to right-aligned
    right_aligned = workbook.add_format({'align': 'right'})
    worksheet.set_column('A:A', None, right_aligned)

    for i, width in enumerate(get_col_widths(df)):
        worksheet.set_column(i, i, width + 5)

    # legend
    super_good = workbook.add_format({'bg_color': '#FFFFFF', "right": 1, "left": 1, "top": 1})
    good = workbook.add_format({'bg_color': '#FFBFBF', "right": 1, "left": 1})
    mid = workbook.add_format({'bg_color': '#FF7F7F', "right": 1, "left": 1})
    bad = workbook.add_format({'bg_color': '#FF3F3F', "right": 1, "left": 1})
    super_bad = workbook.add_format({'bg_color': '#FF0000', "right": 1, "left": 1, "bottom": 1})

    worksheet.write(0, columns + 2, "legend")
    worksheet.write(1, columns + 2, "good", super_good)
    worksheet.write(2, columns + 2, "", good)
    worksheet.write(3, columns + 2, "", mid)
    worksheet.write(4, columns + 2, "", bad)
    worksheet.write(5, columns + 2, "bad", super_bad)

    # conditional formatting
    worksheet.conditional_format(1, columns, rows - 1, columns, format_w2c(min_color='#FFFFFF', max_color="#FF0000"))
    worksheet.conditional_format(1, columns - 2, rows - 1, columns - 2, format_w2c(min_color='#FFFFFF', max_color="#FF0000"))
    worksheet.conditional_format(1, columns - 4, rows - 1, columns - 4, format_w2c(min_color='#FF0000', max_color="#FFFFFF"))
    worksheet.conditional_format(1, columns - 6, rows - 1, columns - 6, format_w2c(min_color='#FFFFFF', max_color="#FF0000"))
    worksheet.conditional_format(1, columns - 8, rows - 1, columns - 8, {'type': 'data_bar', 'bar_color': "#BBCFDA", 'bar_solid': True})

    writer.close()


if __name__ == '__main__':
    main()
