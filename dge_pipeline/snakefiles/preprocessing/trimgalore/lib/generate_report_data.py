"""
Convert trim-galore results to usable data for the large report

Usage:
    generate_report_data.py --stats <stats> --output <output> [--paired-end]
    generate_report_data.py (--version | --help)

Options:
    -h --help               Show this help message and exit
    --version               Show version and exit

    -s <stats> --stats <stats>                 TSV containing the paths to all report files
    -o <output> --output <output>                              Created js containing trim-galore statistics
    --paired-end                                               Paired-End run, else Single-End
"""

import json
import re
from pathlib import Path
from typing import Any, Dict, List, Match, Pattern

import pandas as pd
from docopt import docopt


def create_trim_galore_stats_js_object_se(stats_file: Path) -> Dict[str, Any]:
    tsv_df = pd.read_csv(stats_file, sep="\t")
    stats: Dict[str, Dict[str, Dict[str, Any]]] = {}
    for index, row in tsv_df.iterrows():
        stats[row["Sample"]] = {
            "Forward": parse_stats_file(Path(row["Forward"]))
        }
    return stats


def create_trim_galore_stats_js_object_pe(stats_file: Path) -> Dict[str, Any]:
    tsv_df = pd.read_csv(stats_file, sep="\t")
    stats: Dict[str, Dict[str, Dict[str, Any]]] = {}
    for index, row in tsv_df.iterrows():
        forward, runtime_parameter = parse_stats_file(Path(row["Forward"]))
        reverse, _ = parse_stats_file(Path(row["Reverse"]))
        stats[row["Sample"]] = {
            "Runtime Parameters": runtime_parameter,
            "Forward": forward,
            "Reverse": reverse
        }
    return stats

def parse_stats_file(stats_file: Path) -> Dict[str, Any]:
    re_summary_run_parameters: Dict[str, Pattern] = {
        "trimming_mode": re.compile("Trimming mode:\s+(.*)"),
        "trim_galore_version": re.compile("Trim Galore version:\s+(.*)"),
        "cutadapt_version": re.compile("Cutadapt version:\s+(.*)"),
        "phred_score_cutoff": re.compile("Quality Phred score cutoff:\s+(.*)"),
        "encoding_type_selected": re.compile("Quality encoding type selected:\s+(.*)"),
        "adapter_sequence_forward": re.compile("Adapter sequence:\s+'(.*)'"),
        "adapter_sequence_reverse": re.compile("Optional adapter 2 sequence \(only used for read 2 of paired-end files\):\s+'(.*)'"),
        "max_trimming_error_rate": re.compile("Maximum trimming error rate:\s+(.*)"),
        "min_adapter_overlap": re.compile("Minimum required adapter overlap \(stringency\):\s+(.*)"),
        "min_sequence_length": re.compile("Minimum required sequence length for both reads before a sequence pair gets removed:\s+(.*)"),
        "length_cutoff_forward": re.compile("Length cut-off for read 1:\s+(.*)"),
        "length_cutoff_reverse": re.compile("Length cut-off for read 2:\s+(.*)")
    }
    re_summary: Dict[str, Pattern] = {
        "total_reads_processed": re.compile("Total reads processed:\s+(.*)"),
        "reads_with_adapters": re.compile("Reads with adapters:\s+(.*) \(.*%\)"),
        "reads_passing_filters": re.compile("Reads written \(passing filters\):\s+(.*) \(.*%\)"),
        "total_basepairs_processed": re.compile("Total basepairs processed:\s+(.*) bp"),
        "basepairs_quality_trimmed": re.compile("Quality-trimmed:\s+(.*) bp \(.*%\)"),
        "basepairs_passing_filters": re.compile("Total written \(filtered\):\s+(.*) bp \(.*%\)"),
    }

    re_adapter: Dict[str, Pattern] = {
        "adapter_overview": re.compile("Sequence: (.*); Type: (.*); Length: (.*); Trimmed: (.*) times"),
        "allowed_errors_start": re.compile("No. of allowed errors:"),
        "bases_preceding_removed_adapters_start": re.compile("Bases preceding removed adapters:"),
        "removed_sequences_start": re.compile("Overview of removed sequences"),

    }

    runtime_parameter_stats: Dict[str, Any] = {}
    sample_stats: Dict[str, Any] = {}
    in_allowed_errors_block: bool = False
    in_bases_preceding_removed_adapters_block: bool = False
    in_removed_sequences_block: bool = False
    with stats_file.open() as file:
        run_parameter_block_done: bool = False
        summary_block_done: bool = False
        adapter_block_done: bool = False
        for line in file:
            if not line.strip():
                continue
            if line.strip() == "=== Summary ===":
                run_parameter_block_done = True
                continue
            if line.strip() == "=== Adapter 1 ===":
                summary_block_done = True
                continue

            if not run_parameter_block_done:
                for key, pattern in re_summary_run_parameters.items():
                    match: Match = pattern.search(line)
                    if match:
                        runtime_parameter_stats[key] = match.group(1)
                        del re_summary_run_parameters[key]
                        break
            elif not summary_block_done:
                for key, pattern in re_summary.items():
                    match: Match = pattern.search(line)
                    if match:
                        sample_stats[key] = match.group(1)
                        del re_summary[key]
                        break
            elif not adapter_block_done:
                if "adapter_overview" in re_adapter:
                    match: Match = re_adapter["adapter_overview"].search(line)
                    if match:
                        sample_stats["adapter_overview"] = {
                            "sequence": match.group(1),
                            "type": match.group(2),
                            "length": match.group(3),
                            "trimmed": match.group(4),
                        }
                        del re_adapter["adapter_overview"]
                        continue
                elif re_adapter["allowed_errors_start"].search(line):
                    in_allowed_errors_block = True
                elif in_allowed_errors_block:
                    allowed_errors: List[Dict[str, str]] = []  # should stay in the same order
                    splitted_line: List[str] = line.strip().split(";")
                    for entry in splitted_line:
                        bp_range, count = entry.split(":")
                        allowed_errors.append({"range": bp_range.strip(), "count": count.strip()})
                    sample_stats["allowed_errors"] = allowed_errors
                    in_allowed_errors_block = False
                elif re_adapter["bases_preceding_removed_adapters_start"].search(line):
                    in_bases_preceding_removed_adapters_block = True
                elif in_bases_preceding_removed_adapters_block:
                    bases_preceding: Dict[str, str] = {}
                    for i in range(5):
                        base, percent = line.strip().split(":")
                        bases_preceding[base.strip()] = percent.strip()
                        line = next(file)
                    sample_stats["bases_preceding_adapter"] = bases_preceding
                    in_bases_preceding_removed_adapters_block = False
                elif re_adapter["removed_sequences_start"].search(line):
                    in_removed_sequences_block = True
                elif in_removed_sequences_block:
                    header: List[str] = line.strip().split("\t")
                    line = next(file).strip()
                    removed_sequences: List[Dict[str, str]] = []
                    while line:
                        entry: Dict[str, str] = {}
                        for label, value in zip(header, line.split("\t")):
                            entry[label] = value
                        removed_sequences.append(entry)
                        line = next(file).strip()
                    sample_stats["removed_sequences"] = removed_sequences
                    in_removed_sequences_block = False
                    break

    return sample_stats, runtime_parameter_stats


def generate_report_data(output_file: Path, stats_file: Path, is_paired_end: bool):
    if is_paired_end:
        stats = create_trim_galore_stats_js_object_pe(stats_file)
    else:
        stats = create_trim_galore_stats_js_object_se(stats_file)

    with output_file.open('w') as f:
        f.write('window.Curare.trim_galore = (function() {\n')
        f.write('  const paired_end = {}\n'.format("true" if is_paired_end else "false"))
        f.write('  const stats = ')

        f.write(json.dumps(stats, indent=2).replace('\n', '\n  '))
        f.write('\n')

        f.write('  return {paired_end: paired_end, stats: stats};\n')
        f.write('}());')


def main():
    args = docopt(__doc__, version='1.0')
    stats_file = Path(args["--stats"]).resolve()
    output_file = Path(args["--output"]).resolve()

    generate_report_data(output_file, stats_file, args["--paired-end"])


if __name__ == '__main__':
    main()
