import csv
import matplotlib
matplotlib.use('Agg')
matplotlib.rcParams.update({'figure.autolayout': True})
import matplotlib.pyplot as plt
import pandas as pd
import sys

from pathlib import Path
from typing import Dict, List, Union
from matplotlib.colors import ListedColormap


def get_col_widths(df: pd.DataFrame) -> List[int]:
    return [max(y) for y in [[len(col)] + [len(x) for x in df[col]] for col in df.columns]]


# function for lazy programmers. make a format white 2 black. You can change the colors (see below)
def format_w2c(min_color: str = '#FFFFFF', max_color: str = '#000000', min_value: int = 0, max_value: int = 100) -> Dict[str, Union[str, int]]:
    return {'type': '2_color_scale',
            'min_color': min_color,
            'max_color': max_color,
            'min_type': 'num',
            'max_type': 'num',
            'min_value': min_value,
            'max_value': max_value}


def create_charts(df: pd.DataFrame, output_dir: Path):
    colors = ListedColormap(['#4878d0', '#dc7ec0', '#ff7f00', '#e41a1c'])
    absolute_alignments: pd.DataFrame = df[["sample", "aligned_conc_1_time", "aligned_conc_more_than_1_times", "aligned_disconc_1_time", "pairs_aligned_0_times_conc_or_disconc"]]
    absolute_alignments = absolute_alignments.set_index("sample")
    absolute_alignments.index.names = [None]
    absolute_alignments = absolute_alignments.apply(pd.to_numeric, errors="ignore")
    absolute_alignments = absolute_alignments.rename(columns={"aligned_conc_1_time": "Aligned Conc. 1 Time",
                                                              "aligned_conc_more_than_1_times": "Aligned Conc. >1 Times",
                                                              "aligned_disconc_1_time": "Aligned Disconc.",
                                                              "pairs_aligned_0_times_conc_or_disconc": "Not Aligned Conc. Or Disconc."})
    ax = absolute_alignments.plot(kind='bar', stacked=True, colormap=colors)
    ax.legend(loc='lower center', bbox_to_anchor=(0.5, 1.01), frameon=False, ncols=2)

    ax.set_ylabel("#Read Pairs")
    plt.savefig(str(output_dir / "alignment_stats.svg"))

    relative_alignments = absolute_alignments.div(other=absolute_alignments.sum(axis=1), axis=0).mul(100)
    ax = relative_alignments.plot(kind='bar', stacked=True, colormap=colors)
    ax.legend(loc='lower center', bbox_to_anchor=(0.5, 1.01), frameon= False, ncols=2)
    ax.set_ylabel("Read Pairs [%]")
    plt.savefig(str(output_dir / "alignment_stats_relative.svg"))



def main():
    tsv_file: Path = Path(sys.argv[1]).resolve()
    output_xlsx: Path = Path(sys.argv[2]).resolve()
    output_plots: Path = Path(sys.argv[3]).resolve()
    if output_plots.exists() and not output_plots.is_dir():
        print("Path for plots must be a directory.", file=sys.stderr)
        exit(1)
    else:
        output_plots.mkdir(parents=True, exist_ok=True)

    # name of sheet
    sheet_name: str = "Mappings"

    # fill list of lists:
    # first element = 1st row: header
    # second to n-th element: data
    list_data: List[List] = []
    with tsv_file.open() as tsvin:
        tsvin = csv.reader(tsvin, delimiter="\t")
        for row in tsvin:
            list_data.append(row)

    # get number of rows & columns
    rows: int = len(list_data)
    columns: int = len(list_data[1])

    # make a pandas DataFrame (you don't have to to this with pandas. Maybe it's better to rewrite it and write the cells with a for-loop)
    # and write it to the xlsx sheet
    df: pd.DataFrame = pd.DataFrame(list_data[1:], columns=list_data[0])

    create_charts(df, output_plots)

    writer: pd.ExcelWriter = pd.ExcelWriter(str(output_xlsx),
                                            engine='xlsxwriter',
                                            engine_kwargs={'options': {'strings_to_numbers': True}})
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
    worksheet.conditional_format(1, columns, rows - 1, columns, format_w2c(max_color='#FFFFFF', min_color="#FF0000"))
    worksheet.conditional_format(1, columns - 1, rows - 1, columns - 1, format_w2c(min_color='#FFFFFF', max_color="#FF0000"))
    worksheet.conditional_format(1, columns - 3, rows - 1, columns - 3, format_w2c(max_color='#FFFFFF', min_color="#FF0000"))
    worksheet.conditional_format(1, columns - 5, rows - 1, columns - 5, format_w2c(min_color='#FFFFFF', max_color="#FF0000"))
    worksheet.conditional_format(1, columns - 10, rows - 1, columns - 10, format_w2c(max_color='#FFFFFF', min_color="#FF0000"))
    worksheet.conditional_format(1, columns - 13, rows - 1, columns - 13, format_w2c(min_color='#FFFFFF', max_color="#FF0000"))
    worksheet.conditional_format(1, columns - 15, rows - 1, columns - 15, format_w2c(max_color='#FFFFFF', min_color="#FF0000"))
    worksheet.conditional_format(1, columns - 17, rows - 1, columns - 17, format_w2c(min_color='#FFFFFF', max_color="#FF0000"))
    worksheet.conditional_format(1, columns - 20, rows - 1, columns - 20, {'type': 'data_bar', 'bar_color': "#BBCFDA", 'bar_solid': True})

    writer.close()


if __name__ == '__main__':
    main()
