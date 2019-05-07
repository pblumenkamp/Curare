let jsonData = {"mapping": {"groupName": "mapping", "modules": [{"name": "bwa-sw", "installed": true, "settings": {"required": [{"name": "genome_fasta", "value": "", "description": "Path to genome fasta file", "type": "file"}], "optional": [{"name": "additional_bwa_options", "value": "", "description": "Additional options to use in shell command", "type": "string"}]}}, {"name": "bwa-mem", "installed": true, "settings": {"required": [{"name": "genome_fasta", "value": "", "description": "Path to genome fasta file", "type": "file"}], "optional": [{"name": "additional_bwa_options", "value": "", "description": "Additional options to use in shell command", "type": "string"}]}}, {"name": "bowtie2", "installed": false, "settings": {"required": [{"name": "genome_fasta", "value": "", "description": "Path to genome fasta file", "type": "file"}, {"name": "alignment_type", "value": "", "description": "Choose local or end-to-end alignment", "type": "enum", "choices": {"local": "--very-sensitive-local", "end-to-end": "--very-sensitive"}}], "optional": [{"name": "additional_bowtie2_options", "value": "", "description": "Additional options to use in shell command", "type": "string"}]}}, {"name": "bwa-backtrack", "installed": true, "settings": {"required": [{"name": "genome_fasta", "value": "", "description": "Path to genome fasta file", "type": "file"}], "optional": [{"name": "additional_bwa_options", "value": "", "description": "Additional options to use in shell command", "type": "string"}]}}]}, "premapping": {"groupName": "premapping", "modules": [{"name": "fastqc", "installed": true}, {"name": "multiqc", "installed": true}]}, "preprocessing": {"groupName": "preprocessing", "modules": [{"name": "none", "installed": true}, {"name": "gunzip", "installed": true}]}, "analyses": {"groupName": "analyses", "modules": [{"name": "deseq2", "installed": true, "settings": {"required": [{"name": "gff_feature_type", "value": "", "description": "Used feature type, e.g. gene or exon", "type": "string"}, {"name": "gff_feature_name", "value": "", "description": "Descriptor for gene name, e.g. ID or gene_id", "type": "string"}, {"name": "gff_path", "value": "", "description": "File path to gff file", "type": "file"}], "optional": [{"name": "additional_featcounts_options", "value": "", "description": "Additional options to use in shell command", "type": "string"}, {"name": "attribute_columns", "value": "", "description": "GFF attributes to show in the beginning of the xlsx summary", "type": "string"}]}}, {"name": "count_table", "installed": true, "settings": {"required": [{"name": "gff_feature_type", "value": "", "description": "Used feature type, e.g. gene or exon", "type": "string"}, {"name": "gff_feature_name", "value": "", "description": "Descriptor for gene name, e.g. ID or gene_id", "type": "string"}, {"name": "gff_path", "value": "", "description": "File path to gff file", "type": "file"}], "optional": [{"name": "additional_options", "value": "", "description": "Additional options to use in shell command", "type": "string"}]}}, {"name": "readxplorer", "installed": true, "settings": {"required": [{"name": "readxplorer_cli_path", "value": "", "description": "Path to ReadXplorer-CLI execution path", "type": "file"}, {"name": "reference_genome", "value": "", "description": "Path to reference genome to use", "type": "file"}]}}]}}