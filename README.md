[![License: GPL v3](https://img.shields.io/badge/License-GPL%20v3-brightgreen.svg)](https://github.com/pblumenkamp/curare/blob/master/LICENSE.txt)
![Don't judge me](https://img.shields.io/badge/Language-Python-blue.svg)
![Don't judge me](https://img.shields.io/badge/Language-Snakemake-blue.svg)
![Release](https://img.shields.io/github/release/pblumenkamp/curare.svg)

# Curare - A Customizable and Reproducible Analysis Pipeline for RNA-Seq Experiments

## Contents
- [Description](#description)
- [Features](#features)
- [Installation](#installation)
- [Availability](#availability)
- [Citation](#citation)
- [FAQ](#faq)

## Description

Curare is a freely available analysis pipeline for reproducible, high-throughput, bacterial RNA-Seq experiments. Define standardized pipelines customized for your specific workflow without the necessity of installing all the tools by yourself.   
  
Curare is implemented in Python and uses the power of [Snakemake](https://snakemake.readthedocs.io/) and [Conda](https://docs.conda.io/projects/conda/en/latest/index.html) to build and execute the defined workflows. Its modulized structure and the simplicity of Snakemake enables developers to create new and advanced workflow steps. 

http://curare.computational.bio

## Features
Curare was developed to simplify the automized execution of RNA-Seq workflows on large datasets. Each workflow can be divided into four steps: Preprocessing, Premapping, Mapping, and Analysis.

##### Currently available modules
+ Preprocessing
  + Trim-Galore
+ Premapping
  + FastQC
  + MultiQC
+ Mapping
  + Bowtie2
  + BWA (Backtrack)
  + BWA (Mem)
  + BWA (SW)
  + Segemehl
  + URMAP (only in separate version due to no conda support)
+ Analysis
  + Count Table (FeatureCounts)
  + DESeq2
  + ReadXplorer

## Usage
### Installation
#### From sources
It is recommended to use [conda](https://docs.conda.io/projects/conda/en/latest/user-guide/install/index.html) for installing all dependencies required for Curare. 
```commandline
git clone https://github.com/pblumenkamp/curare.git
cd curare
conda env create -f curare_env.yml
conda activate curare
```

### Creating a pipeline
The easiest way to create a new pipeline is using the Curare wizard. It will guide through all steps and create the two necessary files (`samples.tsv` and `pipeline.yml`) at the end. These files can then be edited with a standard file editor for customization to your own data and analysis.  
```commandline
# Current working directory inside of root tool directory
cd curare
python3 curare_wizard.py --samples target_directory/samples.tsv --pipeline target_directory/pipeline.yml
```

### Samples File
The samples file (`samples.tsv`) is a tab-separated file collecting all necessary information about the used biological samples. This includes a unique identifier (`name`), a file path to the sequencing data (`forward_reads`/`reverse reads` on paired-end data, `reads` on single-end data), and depending on used modules further information like the condition. Every line starting with a # is a comment line and will be ignored by Curare. These lines are just helpful information for correctly writing this file.

**Name column**: A unique identifier used throughout the whole pipeline for this sample. To prevent any side-effects on the file system or in the used scripts, only alphanumerical characters and '_' are allowed.

**Reads columns**: Here you define the file path to the responding sequencing data. For paired-end datasets two columns must be set (`forward_reads` and `reverse_reads`), for single-end data only one column (`reads`). The file path can either be a relative path (relative to this file) or an absolute path (starting with '/').

**Additional columns**: Every selected module can define additional columns. The Curare wizard automatically creates a `samples.tsv` containing all required columns. So just fill out all open fields in the created file and everything will work. You can find a description of all additional columns in the header of the created file.

**Example**         
```tsv
# name: Unique sample name. Only use alphanumeric characters and '_'. [Value Type: String]
# forward_reads: File path to fastq file containing forward reads. Either as absolute path or relative to this file. [Value Type: Path]
# reverse_reads: File path to fastq file containing reverse reads. Either as absolute path or relative to this file. [Value Type: Path]
# condition: Condition name of sequencing run. May contain [A-Z, a-z, 0-9, _;!@^(),.[]-, Whitespace]. [Value Type: String]

name    forward_reads   reverse_reads   condition
wt_1    data/wt_1_R1.fastq  data/wt_1_R2.fastq  WT
wt_2    data/wt_2_R1.fastq  data/wt_2_R2.fastq  WT
wt_3    data/wt_3_R1.fastq  data/wt_3_R2.fastq  WT
heat_1  data/wt_1_R1.fastq  data/wt_1_R2.fastq  Heat
heat_2  data/wt_2_R1.fastq  data/wt_2_R2.fastq  Heat
heat_3  data/wt_3_R1.fastq  data/wt_3_R2.fastq  Heat
starvation_1    data/wt_1_R1.fastq  data/wt_1_R2.fastq  Starvation
starvation_2    data/wt_2_R1.fastq  data/wt_2_R2.fastq  Starvation
starvation_3    data/wt_3_R1.fastq  data/wt_3_R2.fastq  Starvation
```

### Pipeline File
The pipeline file (`pipeline.yml`) defines the used modules and their parameters in the newly created workflow. As a typical YAML file everything is structured in categories. There are catergories for each workflow step (`preprocessing`, `premapping`, `mapping`, and `analysis`) and a main category for the whole pipeline (`pipeline`). Each of the four workflow categories has a parameter `modules` defining the used modules in this step. Since many modules need additional information, like a file path to the reference genome or a quality threshold, modules have their own block in their category for specifying these values. 

One differentiates between mandatory and optional settings. Mandatory settings follow the structure `gff_feature_type: <Insert Config Here>`. It is necessary to replace `<Insert Config Here>` with a real value (like in the `samples.tsv`, the file path can either be relative to this file or absolute). Optional settings are commented out with a single #. For using other values than its default value, just remove the #.         

**Example**  
```yaml
## Curare Pipeline File
## This is an automatically created pipeline file for Curare.
## All required parameters must be set (replace <Insert Config Here> with a real value).
## All optional parameters are commented out with a single '#'. For including these parameters just remove the '#'.

pipeline:
  paired_end: true

preprocessing:
  modules: ["trimgalore"]

  trimgalore:
    ## Choose phred33 (Sanger/Illumina 1.9+ encoding) or phred64 (Illumina 1.5 encoding). [Value Type: Enum
    #phred_score_type: "--phred33"

    ## Trim low-quality ends from reads in addition to adapter removal. (Default: 20). [Value Type: Number
    #quality_threshold: "20"

    ## Discard reads that became shorter than length INT because of either quality or adapter trimming. (Default: 20). [Value Type: Number
    #min_length: "20"

    ## Additional options to use in shell command. [Value Type: String
    #additional_parameter: ""

    ## Adapter sequence to be trimmed. If not specified explicitly, Trim Galore will try to auto-detect whether the Illumina universal, Nextera transposase or Illumina small RNA adapter sequence was used. [Value Type: String
    #adapter_forward: ""

    ## adapter sequence to be trimmed off read 2 of paired-end files. [Value Type: String
    #adapter_reverse: ""


premapping:
  modules: ["multiqc"]

mapping:
  modules: ["bowtie2"]

  bowtie2:
    ## Path to reference genome fasta file. [Value Type: File_input]
    genome_fasta: <Insert Config Here>

    ## Choose local or end-to-end alignment. [Value Type: Enum]
    ## Enum choices: "local", "end-to-end"
    alignment_type: <Insert Config Here>

    ## Additional options to use in shell command. [Value Type: String
    #additional_bowtie2_options: ""


analysis:
  modules: ["deseq2", "readxplorer"]

  deseq2:
    ## Used feature type, e.g. gene or exon. [Value Type: String]
    gff_feature_type: <Insert Config Here>

    ## Descriptor for gene name, e.g. ID or gene_id. [Value Type: String]
    gff_feature_name: <Insert Config Here>

    ## File path to gff file. [Value Type: File_input]
    gff_path: <Insert Config Here>

    ## Additional options to use in shell command. [Value Type: String
    #additional_featcounts_options: ""

    ## GFF attributes to show in the beginning of the xlsx summary (Comma-separated list, e.g. "experiment, product, Dbxref"). [Value Type: String
    #attribute_columns: ""


  readxplorer:
    ## Path to ReadXplorer CLI executable. [Value Type: File_input]
    readxplorer_cli_path: <Insert Config Here>

    ## Path to reference genome sequence. [Value Type: File_input]
    reference_genome: <Insert Config Here>
```
<details>
  <summary>Filled pipeline file</summary>
  
```yaml
## Curare Pipeline File
## This is an automatically created pipeline file for Curare.
## All required parameters must be set (replace <Insert Config Here> with a real value).
## All optional parameters are commented out with a single '#'. For including these parameters just remove the '#'.

pipeline:
  paired_end: true

preprocessing:
  modules: ["trimgalore"]

  trimgalore:
    ## Choose phred33 (Sanger/Illumina 1.9+ encoding) or phred64 (Illumina 1.5 encoding). [Value Type: Enum]
    phred_score_type: "--phred64"

    ## Trim low-quality ends from reads in addition to adapter removal. (Default: 20). [Value Type: Number]
    quality_threshold: "35"

    ## Discard reads that became shorter than length INT because of either quality or adapter trimming. (Default: 20). [Value Type: Number]
    #min_length: "20"

    ## Additional options to use in shell command. [Value Type: String]
    #additional_parameter: ""

    ## Adapter sequence to be trimmed. If not specified explicitly, Trim Galore will try to auto-detect whether the Illumina universal, Nextera transposase or Illumina small RNA adapter sequence was used. [Value Type: String]
    #adapter_forward: ""

    ## adapter sequence to be trimmed off read 2 of paired-end files. [Value Type: String]
    #adapter_reverse: ""


premapping:
  modules: ["multiqc"]

mapping:
  modules: ["bowtie2"]

  bowtie2:
    ## Path to reference genome fasta file. [Value Type: File_input]
    genome_fasta: "reference/my_genome.fasta"

    ## Choose local or end-to-end alignment. [Value Type: Enum]
    ## Enum choices: "local", "end-to-end"
    alignment_type: "end-to-end"

    ## Additional options to use in shell command. [Value Type: String]
    #additional_bowtie2_options: ""


analysis:
  modules: ["deseq2", "readxplorer"]

  deseq2:
    ## Used feature type, e.g. gene or exon. [Value Type: String]
    gff_feature_type: "CDS"

    ## Descriptor for gene name, e.g. ID or gene_id. [Value Type: String]
    gff_feature_name: "ID"

    ## File path to gff file. [Value Type: File_input]
    gff_path: "reference/my_genome.gff"

    ## Additional options to use in shell command. [Value Type: String]
    #additional_featcounts_options: ""

    ## GFF attributes to show in the beginning of the xlsx summary (Comma-separated list, e.g. "experiment, product, Dbxref"). [Value Type: String]
    #attribute_columns: ""


  readxplorer:
    ## Path to ReadXplorer CLI executable. [Value Type: File_input]
    readxplorer_cli_path: /usr/share/readxplorer/bin/readxplorer-cli

    ## Path to reference genome sequence. [Value Type: File_input]
    reference_genome: "reference/my_genome.fasta"
```
</details>

### Starting Curare
Curare can be started with this command: 
```commandline
# Current working directory inside of root tool directory
cd curare
conda activate curare
python3 curare.py --samples target_directory/samples.tsv --pipeline target_directory/pipeline.yml --output results_directory --use-conda 
```

All results, including the conda environments and a final report, will be written in `results_directory`.

### Results
Curare structures all the results by categories and modules. As an example, here are the top two levels of test case results (directories are surounded by *).
```
├── *analysis*
│   └── *dge_analysis*
│       ├── counts_normalized.txt
│       ├── counts.txt
│       ├── counts.txt.summary
│       ├── *count_tables*
│       ├── deseq2_comparisons
│       │   ├── deseq2_results_delta_Fur_delta_RhyB_Vs_delta_RhyB.csv
│       │   ├── deseq2_results_delta_Fur_delta_RhyB_Vs_WT.csv
│       │   ├── deseq2_results_delta_Fur_Vs_delta_Fur_delta_RhyB.csv
│       │   ├── deseq2_results_delta_Fur_Vs_delta_RhyB.csv
│       │   ├── deseq2_results_delta_Fur_Vs_WT.csv
│       │   └── deseq2_results_delta_RhyB_Vs_WT.csv
│       ├── deseq2.RData
│       ├── *logs*
│       ├── *summary*
│       │   ├── delta_Fur_delta_RhyB.pdf
│       │   ├── delta_Fur_delta_RhyB.tsv
│       │   ├── delta_Fur_delta_RhyB.xlsx
│       │   ├── delta_Fur.pdf
│       │   ├── delta_Fur.tsv
│       │   ├── delta_Fur.xlsx
│       │   ├── delta_RhyB.pdf
│       │   ├── delta_RhyB.tsv
│       │   ├── delta_RhyB.xlsx
│       │   ├── WT.pdf
│       │   ├── WT.tsv
│       │   └── WT.xlsx
│       └── *visualization*
│           ├── correlation_heatmap.svg
│           ├── counts_assignment_absolute.svg
│           ├── counts_assignment_relative.svg
│           ├── feature_assignments
│           │   ├── delta_Fur_1.svg
│           │   ├── delta_Fur_2.svg
│           │   ├── delta_Fur_3.svg
│           │   ├── delta_Fur_delta_RhyB_1.svg
│           │   ├── delta_Fur_delta_RhyB_2.svg
│           │   ├── delta_Fur_delta_RhyB_3.svg
│           │   ├── delta_RhyB_1.svg
│           │   ├── delta_RhyB_2.svg
│           │   ├── delta_RhyB_3.svg
│           │   ├── WT_1.svg
│           │   ├── WT_2.svg
│           │   └── WT_3.svg
│           └── pca.svg
├── *mapping*
│   ├── delta_Fur_1.bam
│   ├── delta_Fur_1.bam.bai
│   ├── delta_Fur_2.bam
│   ├── delta_Fur_2.bam.bai
│   ├── delta_Fur_3.bam
│   ├── delta_Fur_3.bam.bai
│   ├── delta_Fur_delta_RhyB_1.bam
│   ├── delta_Fur_delta_RhyB_1.bam.bai
│   ├── delta_Fur_delta_RhyB_2.bam
│   ├── delta_Fur_delta_RhyB_2.bam.bai
│   ├── delta_Fur_delta_RhyB_3.bam
│   ├── delta_Fur_delta_RhyB_3.bam.bai
│   ├── delta_RhyB_1.bam
│   ├── delta_RhyB_1.bam.bai
│   ├── delta_RhyB_2.bam
│   ├── delta_RhyB_2.bam.bai
│   ├── delta_RhyB_3.bam
│   ├── delta_RhyB_3.bam.bai
│   ├── *disconcordantly*
│   ├── *logs*
│   ├── *singleton*
│   ├── *stats*
│   ├── *unmapped*
│   ├── WT_1.bam
│   ├── WT_1.bam.bai
│   ├── WT_2.bam
│   ├── WT_2.bam.bai
│   ├── WT_3.bam
│   └── WT_3.bam.bai
├── premapping
│   └── multiqc
│       ├── *fastqc*
│       ├── *multiqc_data*
│       └── multiqc_report.html
├── *preprocessing*
│   ├── delta_Fur_1_R1.fastq -> trim_galore/delta_Fur_1_val_1.fq
│   ├── delta_Fur_1_R2.fastq -> trim_galore/delta_Fur_1_val_2.fq
│   ├── delta_Fur_2_R1.fastq -> trim_galore/delta_Fur_2_val_1.fq
│   ├── delta_Fur_2_R2.fastq -> trim_galore/delta_Fur_2_val_2.fq
│   ├── delta_Fur_3_R1.fastq -> trim_galore/delta_Fur_3_val_1.fq
│   ├── delta_Fur_3_R2.fastq -> trim_galore/delta_Fur_3_val_2.fq
│   ├── delta_Fur_delta_RhyB_1_R1.fastq -> trim_galore/delta_Fur_delta_RhyB_1_val_1.fq
│   ├── delta_Fur_delta_RhyB_1_R2.fastq -> trim_galore/delta_Fur_delta_RhyB_1_val_2.fq
│   ├── delta_Fur_delta_RhyB_2_R1.fastq -> trim_galore/delta_Fur_delta_RhyB_2_val_1.fq
│   ├── delta_Fur_delta_RhyB_2_R2.fastq -> trim_galore/delta_Fur_delta_RhyB_2_val_2.fq
│   ├── delta_Fur_delta_RhyB_3_R1.fastq -> trim_galore/delta_Fur_delta_RhyB_3_val_1.fq
│   ├── delta_Fur_delta_RhyB_3_R2.fastq -> trim_galore/delta_Fur_delta_RhyB_3_val_2.fq
│   ├── delta_RhyB_1_R1.fastq -> trim_galore/delta_RhyB_1_val_1.fq
│   ├── delta_RhyB_1_R2.fastq -> trim_galore/delta_RhyB_1_val_2.fq
│   ├── delta_RhyB_2_R1.fastq -> trim_galore/delta_RhyB_2_val_1.fq
│   ├── delta_RhyB_2_R2.fastq -> trim_galore/delta_RhyB_2_val_2.fq
│   ├── delta_RhyB_3_R1.fastq -> trim_galore/delta_RhyB_3_val_1.fq
│   ├── delta_RhyB_3_R2.fastq -> trim_galore/delta_RhyB_3_val_2.fq
│   ├── *trim_galore*
│   ├── WT_1_R1.fastq -> trim_galore/WT_1_val_1.fq
│   ├── WT_1_R2.fastq -> trim_galore/WT_1_val_2.fq
│   ├── WT_2_R1.fastq -> trim_galore/WT_2_val_1.fq
│   ├── WT_2_R2.fastq -> trim_galore/WT_2_val_2.fq
│   ├── WT_3_R1.fastq -> trim_galore/WT_3_val_1.fq
│   └── WT_3_R2.fastq -> trim_galore/WT_3_val_2.fq
├── report.html
├── Snakefile
└── *snakemake_lib*
    ├── *bowtie2_lib*
    ├── bowtie2.sm
    ├── *dge_analysis_lib*
    ├── dge_analysis.sm
    ├── *global_scripts*
    ├── multiqc_lib
    ├── multiqc.sm
    ├── snakefile_config.yml
    ├── *trimgalore_lib*
    └── trimgalore.sm
```

## Availability

## Citation

## FAQ
1. How can I use Curare? [Documentation](https://www.readthedocs.comn)
2. Contact and support: curare@computational.bio.uni-giessen.de
3. Issues: Bugs and issues can be filed [here](https://github.com/pblumenkamp/curare/issues)
