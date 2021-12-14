[![License: GPL v3](https://img.shields.io/badge/License-GPL%20v3-brightgreen.svg)](https://github.com/pblumenkamp/curare/blob/master/LICENSE.txt)
![Don't judge me](https://img.shields.io/badge/Language-Python-blue.svg)
![Don't judge me](https://img.shields.io/badge/Language-Snakemake-blue.svg)
![Release](https://img.shields.io/github/release/pblumenkamp/curare.svg)

# Curare - A Customizable and Reproducible Analysis Pipeline for RNA-Seq Experiments

## Contents
- [Description](#description)
- [Features](#features)
- [Usage](#usage)
  - [Installation](#installation)
  - [Execute Curare](#creating-a-pipeline)
- [Availability](#availability)
- [Citation](#citation)
- [FAQ](#faq)

## Description

Curare is a freely available analysis pipeline for reproducible, high-throughput, bacterial RNA-Seq experiments. Define standardized pipelines customized for your specific workflow without the necessity of installing all the tools by yourself.   
  
Curare is implemented in Python and uses the power of [Snakemake](https://snakemake.readthedocs.io/) and [Conda](https://docs.conda.io/projects/conda/en/latest/index.html) to build and execute the defined workflows. Its modulized structure and the simplicity of Snakemake enables developers to create new and advanced workflow steps. 

## Features
Curare was developed to simplify the automized execution of RNA-Seq workflows on large datasets. Each workflow can be divided into four steps: Preprocessing, Premapping, Mapping, and Analysis.

##### Available modules
+ Preprocessing
  + Trim-Galore
+ Premapping
  + FastQC
  + MultiQC
+ Mapping
  + Bowtie
  + Bowtie2
  + BWA (Backtrack)
  + BWA (Mem)
  + BWA (SW)
  + Segemehl
  + Star
+ Analysis
  + Count Table (FeatureCounts)
  + DGE Analysis (DESeq2)
  + Normalized Coverage
  + ReadXplorer

### Results Report
At the end of a Curare run, you will also get an HTML report containing the most important results and an overview of all used settings. The start page will include Curare statistics, the runtime of this analysis, sample descriptions, and all dependencies of the tools used in this pipeline. From the navigation bar at the top, you can then navigate to the specific reports of each module with detailed charts and many statistics. (Images created with Curare using the data from: Banerjee R et al., "Tailoring a Global Iron Regulon to a Uropathogen.", mBio, 2020 Mar 24;11(2))
![start_page](https://user-images.githubusercontent.com/9703726/144844060-5acc6f29-fcaf-446d-9dd8-27c92bf33269.png)

![Curare_Statistics](https://user-images.githubusercontent.com/9703726/145035029-5dd70610-10d2-45e1-8c1f-0334522c2625.png)


## Usage
### Installation
#### From sources
It is recommended to use [conda](https://docs.conda.io/projects/conda/en/latest/user-guide/install/index.html) for installing all dependencies required for Curare. 
```bash
git clone https://github.com/pblumenkamp/curare.git
cd curare
conda env create -f curare_env.yml
conda activate curare
./curare/curare.py --help
```

### Creating a pipeline
The easiest way to create a new pipeline is by using the Curare wizard. It will guide through all steps, asks what module you wish to use and creates the two necessary files (`samples.tsv` and `pipeline.yml`). These files can then be edited with a standard file editor for customizing your data and analysis.  
```bash
# Current working directory is inside of tool directory
cd curare
./curare_wizard.py --samples target_directory/samples.tsv --pipeline target_directory/pipeline.yml
```

### Samples File
The samples file (`samples.tsv`) is a tab-separated file collecting all necessary information about the used biological samples. This includes a unique identifier (`name`), a file path to the sequencing data (`forward_reads`/`reverse reads` on paired-end data, `reads` on single-end data), and depending on used modules further information like the condition. Every line starting with a # is a comment line and will be ignored by Curare. These lines are just helpful information for correctly writing this file.

**Name column**: A unique identifier used throughout the whole pipeline for this sample. To prevent any side-effects on the file system or in the used scripts, only alphanumerical characters and '_' are allowed for sample names.

**Reads columns**: Here, you define the file path to the responding sequencing data. For paired-end datasets, two columns must be set (`forward_reads` and `reverse_reads`), for single-end data only one column (`reads`). The file path can either be a relative path (relative to this file) or an absolute path (starting with '/').

**Additional columns**: Every selected module can define additional columns. The Curare wizard automatically creates a `samples.tsv` containing all required columns. So just fill out all open fields in the generated file, and everything will work. You can find a description of all additional columns in the header of the created file.

**Example**         
```tsv
# name: Unique sample name. Only use alphanumeric characters and '_'. [Value Type: String]
# forward_reads: File path to fastq file containing forward reads. Either as an absolute path or relative to this file. [Value Type: Path]
# reverse_reads: File path to fastq file containing reverse reads. Either as an absolute path or relative to this file. [Value Type: Path]
# condition: Condition name of the sequencing run. May contain [A-Z, a-z, 0-9, _;!@^(),.[]-, Whitespace]. [Value Type: String]

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
The pipeline file (`pipeline.yml`) defines the used modules and their parameters in the newly created workflow. As a typical YAML file, everything is structured in categories. There are categories for each workflow step (`preprocessing`, `premapping`, `mapping`, and `analysis`) and the main category for the whole pipeline (`pipeline`). Each of the four workflow categories has a parameter `modules` defining the used modules in this step. Since many modules need additional information, like a file path to the reference genome or a quality threshold, modules have their own block in their category for specifying these values. 

One differentiates between mandatory and optional settings. Mandatory settings follow the structure `gff_feature_type: <Insert Config Here>`. It is necessary to replace `<Insert Config Here>` with a real value, e.g. "CDS" (like in the `samples.tsv`, the file path can either be relative to this file or absolute). Optional settings are commented out with a single #. For using other values than the default value, just remove the # and write your parameter after the colon.

**Example**  
```yaml
## Curare Pipeline File
## This is an automatically created pipeline file for Curare.
## All required parameters must be set (replace <Insert Config Here> with real value).
## All optional parameters are commented out with a single '#'. For including these parameters, just remove the '#'.

pipeline:
  paired_end: true

preprocessing:
  modules: ["trimgalore"]

  trimgalore:
    ## Choose phred33 (Sanger/Illumina 1.9+ encoding) or phred64 (Illumina 1.5 encoding). [Value Type: Enum]
    #phred_score_type: "--phred33"

    ## Trim low-quality ends from reads in addition to adapter removal. (Default: 20). [Value Type: Number]
    #quality_threshold: "20"

    ## Discard reads that became shorter than length INT because of either quality or adapter trimming. (Default: 20). [Value Type: Number]
    #min_length: "20"

    ## Additional options to use in shell command. [Value Type: String]
    #additional_parameter: ""

    ## Adapter sequence to be trimmed. If not specified explicitly, Trim Galore will try to auto-detect whether the Illumina universal, Nextera transposase, or Illumina small RNA adapter sequence was used. [Value Type: String]
    #adapter_forward: ""

    ## adapter sequence to be trimmed off read 2 of paired-end files. [Value Type: String]
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

    ## Additional options to use in shell command. [Value Type: String]
    #additional_bowtie2_options: ""


analysis:
  modules: ["dge_analysis", "readxplorer"]

  dge_analysis:
    ## Used feature type, e.g. gene or exon. [Value Type: String]
    gff_feature_type: <Insert Config Here>

    ## Descriptor for gene name, e.g. ID or gene_id. [Value Type: String]
    gff_feature_name: <Insert Config Here>

    ## File path to gff file. [Value Type: File_input]
    gff_path: <Insert Config Here>

    ## Additional options to use in shell command. [Value Type: String]
    #additional_featcounts_options: ""
    
    ## Strand specificity of reads. Specifies if reads must lie on the same strand as the feature, the opposite strand, or can be on both. Options: "unstranded, stranded, reversely_stranded"
    #strand_specificity: "unstranded"

    ## GFF attributes to show in the beginning of the xlsx summary (Comma-separated list, e.g. "experiment, product, Dbxref"). [Value Type: String]
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
## All required parameters must be set (replace <Insert Config Here> with real value).
## All optional parameters are commented out with a single '#'. For including these parameters, just remove the '#'.

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

    ## Adapter sequence to be trimmed. If not specified explicitly, Trim Galore will try to auto-detect whether the Illumina universal, Nextera transposase, or Illumina small RNA adapter sequence was used. [Value Type: String]
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
  modules: ["dge_analysis", "readxplorer"]

  dge_analysis:
    ## Used feature type, e.g. gene or exon. [Value Type: String]
    gff_feature_type: "CDS"

    ## Descriptor for gene name, e.g. ID or gene_id. [Value Type: String]
    gff_feature_name: "ID"

    ## File path to gff file. [Value Type: File_input]
    gff_path: "reference/my_genome.gff"

    ## Additional options to use in shell command. [Value Type: String]
    #additional_featcounts_options: ""
  
    ## Strand specificity of reads. Specifies if reads must lie on the same strand as the feature, the opposite strand, or can be on both. Options: "unstranded, stranded, reversely_stranded"
    strand_specificity: "reversely_stranded"

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
```bash
# Current working directory inside of root tool directory
cd curare
conda activate curare
./curare.py --samples <target_directory>/samples.tsv --pipeline <target_directory>/pipeline.yml --output <results_directory> --use-conda
```

All results, including the conda environments and a final report, will be written in `results_directory`.
  
### Results
Curare structures all the results by categories and modules. This way each module can create their own structure and is independent from all other modules. For example, the mapping modules generates multiple bam files with various flag filters like unmapped or concordant reads and the differential gene expression module builds large excel files with the most important values and an R object to continue the analysis on your own. (Images: Bowtie2 mapping chart and DESeq2 summary table )
  
<div style="display: inline-flex; flex-direction: row; justify-content: space-evenly; align-items: center">
  <img src="https://user-images.githubusercontent.com/9703726/145060940-d8dda4b1-7ad5-4f3c-947d-f1381aa9614c.png" width=450>
  <img src="https://user-images.githubusercontent.com/9703726/145061206-5b01b8b7-c81f-4dc4-b893-cf8f7b2a850d.png" width=450>
 </p>
  

## Availability
Conda package in preparation.
  
## Citation
In preparation.

## FAQ
1. How can I use Curare? [Usage](#usage)
2. Contact and support: curare@computational.bio.uni-giessen.de
3. Issues: Bugs and issues can be filed [here](https://github.com/pblumenkamp/curare/issues)
