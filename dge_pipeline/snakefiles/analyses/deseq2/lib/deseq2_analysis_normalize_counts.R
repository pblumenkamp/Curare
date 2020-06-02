# Source plotting file
initial.options <- commandArgs(trailingOnly = FALSE)
script.name <- sub(pattern = "--file=", 
                   replacement = "", 
                   x = initial.options[grep("--file=", initial.options)]
                   )
script.basename <- dirname(script.name)
utils.plotting <- file.path(script.basename,"utils/plotting.R")
source(utils.plotting)

# Parse arguments
args <- commandArgs(TRUE)
counttable_file <- args[match('--count-table', args) + 1]
condition_file <- args[match('--conditions', args) + 1]
feature_counts_log_file <- args[match('--featcounts-log', args) + 1]
r_data <- args[match('--r-data',args)+1]
output_vis <- args[match('--output-vis', args) + 1]
output_count <- args[match('--output-count', args) + 1]
threads <- args[match('--threads', args) + 1]

# Required packages
for (package in c("DESeq2")) {
    if (!(package %in% rownames(installed.packages()))) {
        library("crayon")
        stop(paste('Package "', package, '" not installed', sep=""))
    } else {
        print(paste("Import:", package))
        library(package, character.only=TRUE)
    }
}

# "Optional" packages
for (package in c("BiocParallel", "pheatmap", "ggplot2", "reshape2", "gplots")) {
    if (!(package %in% rownames(installed.packages()))) {
        stop(paste('Package "', package, '" not installed', sep=""))
    } else {
        print(paste("Import:", package))
        library(package, character.only=TRUE)
    }
}

# Run on multiple threads
if ("BiocParallel" %in% rownames(installed.packages())) {
    register(MulticoreParam(threads))
}

# Import count table (featureCounts)
countdata.raw <- read.csv(counttable_file, header = TRUE, row.names = 1, sep = "\t", comment.char = "#")
countdata <- as.matrix(countdata.raw[, c(6 : length(countdata.raw))])
colnames(countdata) <- as.vector(sapply(colnames(countdata), function(x) gsub("mapping\\.(.*)\\.bam", "\\1", x)))

# Import condition file:
#
# Sample1<tab>Condition1
# Sample2<tab>Condition1
# Sample3<tab>Condition2
# Sample4<tab>Condition2
#
conditiontable <- read.csv(condition_file, header = FALSE, row.names = 1, sep = "\t", comment.char = "#")
rownames(conditiontable) <- gsub("-", ".", rownames(conditiontable))
colnames(conditiontable) <- c('condition')
condition <- as.factor(conditiontable[, 1])

deseqDataset <- DESeqDataSetFromMatrix(countData = countdata, colData = conditiontable, design = ~ condition)

# Write normalized count table
deseqDataset <- estimateSizeFactors(deseqDataset)
countdata.normalized <- counts(deseqDataset, normalized = TRUE)
write.table(countdata.normalized, file = output_count, sep = "\t", row.names = TRUE, col.names = NA)

# Often called dds
deseq.results <- DESeq(object = deseqDataset, parallel = TRUE)

# Save R state in file
save.image(file = r_data)

# Heatmap showing similarities between samples (needs a count table and conditions )
if ("pheatmap" %in% rownames(installed.packages())) {
    pdf(paste(output_vis, 'correlation_heatmap.pdf', sep = "/"), width = 8, height = 8, onefile = FALSE)
    print(create_correlation_matrix(countdata.normalized, conditiontable))
    dev.off()
}

# Bar charts showing the assignment of allignments to genes (featureCounts statistics)
if (("ggplot2" %in% rownames(installed.packages())) && ("reshape2" %in% rownames(installed.packages()))) {
    pdf(paste(output_vis, 'counts_assignment.pdf', sep = "/"))
    invisible(lapply(create_feature_counts_statistics(feature_counts_log_file), print))
    dev.off()
}

# PCA of DESeq2 data (needs a DESeq2 dataset )
{
    rld <- rlog(deseqDataset)
    pdf(paste(output_vis, 'pca.pdf', sep = "/"), onefile = FALSE)
    print(plotPCA(rld))
    dev.off()
}
