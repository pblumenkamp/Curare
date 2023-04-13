#!/usr/bin/env python3
"""
Fill feature set files from "count_statistics.py" with annotation information

Usage:
    fill_feature_set_file.py --feature_set_dir <directory> --count_table_dir <directory> --output_dir <directory> --feature_suffix <suffix> --annotation <annotation> --gff_feature_name <feature_identifier>
    fill_feature_set_file.py (--version | --help)

Options:
    -h --help               Show this help message and exit
    --version               Show version and exit

    -i <directory> --feature_set_dir <directory>                Directory with feature set files
    -c <directory> --count_table_dir <directory>                Directory with featureCounts count tables
    -o <directory> --output_dir <directory>                     Output directory (output file name == input file name)
    -s <suffix> --feature_suffix <suffix>                       Suffix of files containing feature sets
    -a <annotation> --annotation <annotation>                   GFF annotation
    -t <feature_identifier> --gff_feature_name <feature_identifier>         Descriptor for gene name, e.g. ID or gene_id
"""

from dataclasses import dataclass
import os
from pathlib import Path
import sys
from typing import Dict, List, Tuple

from docopt import docopt
import xlsxwriter


@dataclass(frozen=True)
class GFFFeature:
    chromosome: str
    type: str
    start: int
    end: int
    strand: str
    annotations: Dict[str, str]


def main(feature_dir: Path, count_table_dir: Path, output_dir: Path, input_suffix: str, annotation_path: Path, feature_identifier: str):
    # Parse GFF file into gff_entries. Group by chromosomes and make it searchable by ID
    gff_entries: Dict[str, Dict[str, GFFFeature]] = {} # Chromosome: {ID: GFFFeature}
    with annotation_path.open() as annotation:
        for line in annotation:
            if line.startswith('#') or not line.strip():
                continue
            chromosome, _, feature_type, start, end, _, strand, _, annotations = line.strip().split('\t', maxsplit=8)
            start, end = int(start), int(end)
            annotations: Dict[str, str] = parse_attributes(annotations)
            if chromosome not in gff_entries: 
                gff_entries[chromosome] = {}
            gff_entries[chromosome][annotations[feature_identifier]] = GFFFeature(chromosome=chromosome,
                                                                    type=feature_type,
                                                                    start=start,
                                                                    end=end,
                                                                    strand=strand,
                                                                    annotations=annotations)

    # Do loop for each file with user-specifies suffix in user-specified input directory
    # Create feature set file with meta-information for each feature set file
    for feature_file in (filepath for filepath in os.listdir(feature_dir) if filepath.endswith(input_suffix)):
        feature_type: str = feature_file.split("_", maxsplit=1)[0]
        # get all atrributes of column 9 in GFF of this specific feature type
        feature_attributes: Dict[str, None] = {}
        for gff_entry in (entry for chromosome in gff_entries.keys() for entry in gff_entries[chromosome].values() if entry.type == feature_type):
            for attribute in gff_entry.annotations.keys():
                feature_attributes[attribute] = None
        del(feature_attributes[feature_identifier])
        # parse feature set file
        feature_sets: Dict[str, Dict[Tuple[str, str], List[str]]] = {}    # Chromosome: {id, splitted_text_line}
        with open(feature_dir / feature_file) as in_feature_set:
            feature_set_header: List[str] = next(in_feature_set).strip().split("\t")
            for line in in_feature_set:
                split_line: List[str] = line.strip().split("\t")
                feature_sets.setdefault(split_line[-1], {})[split_line[-2]] = split_line
        # parse featureCounts count table
        count_table: Dict[str, Dict[Tuple[str, str], List[str]]] = {}    # Chromosome: {id, splitted_count_entries}
        count_table_name: str = feature_file.removesuffix(input_suffix) + ".txt"
        with open(count_table_dir / count_table_name) as in_count_table:
            count_table_header: List[str] = None
            while count_table_header is None:
                next_line: str = next(in_count_table)
                if not next_line.startswith("#") and next_line.strip():
                    count_table_header: List[str] = next_line.strip().split("\t")[6:]
            for line in in_count_table:
                split_line: List[str] = line.strip().split("\t")
                count_table.setdefault(split_line[1], {})[split_line[0]] = split_line[6:]
        # write output. Start with with content of existing feature set file and add columns of GFF
        with (output_dir / feature_file).open("w") as out_tsv, (output_dir / (feature_file.rsplit(".", maxsplit=1)[0] + ".xlsx")).open("w") as out_xlsx:
            # init xlsx workbook
            workbook: xlsxwriter.Workbook = xlsxwriter.Workbook(output_dir / (feature_file.rsplit(".", maxsplit=1)[0] + ".xlsx"))
            worksheet: xlsxwriter.worksheet_class = workbook.add_worksheet()
            xlsx_row:int = 0
            
            header_row: List[str] = feature_set_header[:] + ["Start", "End", "Strand"] + list(feature_attributes.keys()) + count_table_header
            out_tsv.write("\t".join(header_row))
            for i, entry in enumerate(header_row):
                worksheet.write(xlsx_row, i, entry)
                worksheet.set_column(i, i, len(entry * 2))
            xlsx_row += 1

            for chromosome, features in feature_sets.items():
                for feature, line in features.items():
                    annotation_values: List[str] = []
                    for attribute in feature_attributes.keys():
                        if attribute in gff_entries[chromosome][feature].annotations:
                            annotation_values.append(gff_entries[chromosome][feature].annotations[attribute])
                        else:
                            annotation_values.append("-")
                    start_pos: int = gff_entries[chromosome][feature].start
                    end_pos: int = gff_entries[chromosome][feature].end
                    strand: str = gff_entries[chromosome][feature].strand
                    out_tsv.write("\t".join(line[:] + [str(start_pos), str(end_pos), strand] + annotation_values + count_table[chromosome][feature]) + "\n")
                    xlsx_row_entries: List = line[:] + [start_pos, end_pos, strand] + annotation_values
                    # Since count tables could include NAs, these entries must be converted inside of a try/except block
                    for entry in count_table[chromosome][feature]:
                        try:
                            xlsx_entry: float = float(entry)
                        except:
                            xlsx_entry = entry
                        xlsx_row_entries.append(xlsx_entry)

                    for i, entry in enumerate(xlsx_row_entries):
                        worksheet.write(xlsx_row, i, entry)
                    xlsx_row += 1

        worksheet.autofilter(0, 0, xlsx_row-1, len(header_row))
        workbook.close()

# State machine for parsing Column 9 of GFF/GTF files (Default GFF3)
def parse_attributes(attributes: str, attribute_separator: str=';', key_value_separator: str='=', quotes: str='"') -> Dict[str,str]:
    state: str = 'first_letter_key'  # first_letter_key, key, value, quotes
    splitted_attributes: Dict[str, str] = {}
    key: str = ""
    value: str = ""

    for char in attributes:
		# Ignore whitespaces, attribute and key/value separator after a separator
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


if __name__ == "__main__":
    arguments = docopt(__doc__, version='1.0')

    arguments["--feature_set_dir"] = Path(arguments["--feature_set_dir"])
    if not arguments["--feature_set_dir"].is_dir():
        print("Error: \"--feature_set_dir\" must be an directory.", file=sys.stderr)
        sys.exit(10)
    
    arguments["--count_table_dir"] = Path(arguments["--count_table_dir"])
    if not arguments["--count_table_dir"].is_dir():
        print("Error: \"--count_table_dir\" must be an directory.", file=sys.stderr)
        sys.exit(11)

    arguments["--annotation"] = Path(arguments["--annotation"])
    if not (arguments["--annotation"].exists() and arguments["--annotation"].is_file()):
        print("Annotation file does not exist: \"{}\".".format(arguments["--annotation"]), file=sys.stderr)
        sys.exit(12)

    arguments["--output_dir"] = Path(arguments["--output_dir"])

    main(arguments["--feature_set_dir"], arguments["--count_table_dir"], arguments["--output_dir"], arguments["--feature_suffix"], arguments["--annotation"], arguments["--gff_feature_name"])