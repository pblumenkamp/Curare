## 0.2.1


### Added (1 change)

- Added conditions file for GenExVis (DGE-Analysis).


### Fixed (1 change)

- Fixed missing column name for Gene IDs in normalized count table (DGE-Analysis).

## 0.2.0


### Added (9 changes)

- Added a Wizard (curare_wizard.py) for creating samples and pipeline file.
- Added a cluster mode for send long-running steps to a cluster node as a job (--cluster-comand, --cluster-config-file, --cluster-nodes). If using cluster mode, the latency-wait parameter should be increased (--latency-wait in seconds).
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



