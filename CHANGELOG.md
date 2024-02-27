## 0.6.0

## Changed
- `--cores` option is now mandatory
- DESeq2 fold changes are now inversed, so that edgeR and DESeq2 results are comparable
- Count tables for DESeq2 get rounded, so `--fraction` of featureCounts will work with DESeq2

## Added
- New modules
  - HISAT2
  - Differential gene expression with edgeR
- Curare wizard now supports download of RefSeq genomes and annotations
- STAR index and STAR mapping now have threads options. These can be used to control how many mappings can run in parallel
- DESeq2 and edgeR modules also visualize the gene body coverage (using RSeQC)

## Fixed
- Fixed STAR index bug: Errors during STAR index building could lead to a state where Curare thought that the index was build properly
- A chromosome column was missing in DGE summary xlsx files

## 0.5.1

## Fixed (1 change)
- Fixed error during version parsing with newer conda/mamba versions


## 0.5.0

## Changed (7 changes)
- Curare uses conda/mamba by default and "--use-conda" is changed to "--no-conda"
- Update of all tool versions
- Update Snakemake to 7.32.3
- All Curare modules now use fixed versions (Conda dependencies use '=', not '>=')
- Tidied up correlation heatmap in 'dge_analysis'
- Reworked 'dge_analysis' parameters: Options for using 'Parent' in GFFs as ID (useful when working with exons)
- All modules will now generate csi files instead of bai files (This allows Curare to work with large plant genomes)

## Added (5 changes)
- New modules
  - bwa-mem2
  - minimap2
  - fastp
- Curare wizards now warns if target files already exist
- "--keep-going" option: If a module throws an error, independent modules will still finish

## Fixed (5 changes)
- Fixed wrong mapped reads counting in STAR
- Fixed error with xgzipped files
- Fixed 'multiqc' error when Curare was rerun in same directory
- Fixed clustering bug in 'dge_analysis' for cases with >65,536 genes
- Standardized order of samples in all visualization


## 0.4.5

### Fixed (1 change)
- Fixed bug in dge_analysis xlsx converter

## 0.4.4

### Fixed (1 change)
- Fixed broken PyPI build (snakefiles and report folder will now also be installed)


## 0.4.3

### Added (1 change)
- Made Curare PyPI and Bioconda ready
  - All executives are now also found under ./bin and can this way be easliy added to your PATH

### Changed (1 change)
- Renamed "curare_env.yml" to "conda_environment.yaml" for a more meaningful name


## 0.4.2

### Added (1 change)
- Add "Normalized Coverage" module to Analysis

### Fixed (1 change)
- Fix broken "Normalized Coverage" added by mistake last release

## 0.4.1

### Fixed (1 change)
- Fix old heading "Groups" to "Samples" in report (Report)

## 0.4.0

### Added (2 change)
- Curare now supports new mapping modules:
  - STAR
  - Bowtie

### Changed (1 change)
- All preprocessing modules will now gzip fasta files. This allows the removal of the gunzip module and 100% support of gzipped fastq files.

### Fixed (1 change)
- Min/Max values in the setting should be inclusive: min <= value <= max (Pipeline)

## 0.3.1

### Added (1 change)
- Added option for strand specificity of reads to features (DGE Analysis)

### Changed (1 change)
- Bowtie2 alignment mode (local/end-to-end) is now optional and by default "end-to-end"

### Fixed (1 change)
- Fixed incorrect usage of local alignment mode with paired-end datasets (Bowtie2)
  
## 0.3.0

### Added (5 change)

- Added main GFF feature to assignment chart title (Report - DGE Analysis & Count Table)
- Added button for opening the original count table (Report - DGE Analysis & Count Table)
- Added button for opening the DESeq2 comparison directory (Report - DGE Analysis)
- Added pagination on tables (Report)
- Added summary about mapping tool parameters (Report - Mapping)

### Changed (3 changes)

- Allowlist for GFF feature was created. If another feature is required, use 'ADDITIONAL_FEATCOUNTS_FEATURES' (DGE Analysis Module).
  - Allowlist: "CDS", "exon", "intron", "gene", "mRNA", "tRNA", "rRNA", "ncRNA", "operon", "snRNA", "snoRNA", "miRNA", "pseudogene", "small regulatory ncRNA", "rasiRNA", "guide RNA", "siRNA", "stRNA", "sRNA"
- Tabs were replaced with dropdown menus (Report)
- Runtime notation on overview page now in hours, minutes and seconds (Report)

### Fixed (3 change)
- Fixed broken header anchors on overview page (Report)
- Fixed incorrect curare dependencies
- Fixed unused Segemehl parameters

## 0.2.2

### Added (3 changes)

- Added mamba support and made mamba default when using conda
- Added support of gff.gz files (DGE Analysis Module)
- Added 'N' (None) option at module selection (Curare Wizard)

### Fixed (4 changes)

- Fixed bug when all options in a module are optional
- Fixed parsing errors of pipeline and samples file
- Check and create missing output folders
- Use curare snakefiles folder as a default (Curare Wizard)

### Changed (1 change)

- Changed '--attribute' list from space-separated to comma-separated (DGE Analysis Module)

## 0.2.1


### Added (1 change)

- Added conditions file for GenExVis (DGE-Analysis).


### Fixed (1 change)

- Fixed missing column name for Gene IDs in normalized count table (DGE-Analysis).

## 0.2.0


### Added (9 changes)

- Added a Wizard (curare_wizard.py) for creating samples and pipeline file.
- Added a cluster mode for send long-running steps to a cluster node as a job (--cluster-command, --cluster-config-file, --cluster-nodes). If using cluster mode, the latency-wait parameter should be increased (--latency-wait in seconds).
- Added a final report summarizing all used software and the most important results.
- Added bwa (http://bio-bwa.sourceforge.net/) as a mapping module. This includes the bwa-backtrack bwa-mem and bwa-sw algorithm.
- Added conda support for automatically installing all dependencies for each module.
- Added more detailed error messages when DESeq2 analyses terminate. Now, the module prints if and which R package is missing.
- Added new visualizations to differential expression analysis.
- Added Segemehl as an additional mapping module.
- Added Trim Galore for data preprocessing.


### Fixed (2 changes)

- Fixed a bug in which the DESeq2 R script would crash if exactly three conditions were present.
- Moved the sam files containing all unmapped reads into a seperate directory. This was done to prevent a bug if the sample names end with '_unmapped'.


### Changed (3 changes)

- Renamed category analyses in analysis.
- Renamed deseq2 module to dge-analysis.
- Renamed groups file in samples file.

## 0.1.1


### Removed (1 change)

- removed unneeded keep file in DESeq2 summary.


### Changed (1 change)

- switched from not normalized to normalized counts in DESeq2 summary.



