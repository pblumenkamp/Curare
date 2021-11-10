## 0.4

### Changed (1 change)
- All preprocessing modules will now gzip fasta files. This allows the removal of the gunzip module and 100% support of gzipped fastq files.

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



