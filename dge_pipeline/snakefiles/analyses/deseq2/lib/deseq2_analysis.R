library("DESeq2")
library("BiocParallel")
library("pheatmap")

create_correlation_matrix <- function(countdata, conditiontable, output) {
    countdata.normalized.processed <- as.matrix(countdata)
    countdata.normalized.processed <- countdata.normalized.processed[rowSums(countdata.normalized.processed) >= 10,]
    countdata.normalized.processed <- log2(countdata.normalized.processed+1)
    sample_cor <- cor(countdata.normalized.processed, method='pearson', use='pairwise.complete.obs')

    pdf(output, width=8, height=7)
    pheatmap(sample_cor, annotation_col=conditiontable, annotation_row=conditiontable)
    dev.off()
}

args <- commandArgs(TRUE)
counttable_file <- args[match('--counttable', args) + 1]
condition_file <- args[match('--conditions', args) + 1]
output_folder <- args[match('--output', args) + 1]
threads <- args[match('--threads', args) + 1]
register(MulticoreParam(threads))

countdata.raw <- read.csv(counttable_file, header=TRUE, row.names=1, sep = "\t", comment.char = "#")
countdata <- as.matrix(countdata.raw[, c(6:length(countdata.raw))])
colnames(countdata) <- as.vector(sapply(colnames(countdata), function(x) gsub("mapping\\.(.*)\\.bam", "\\1", x)))

conditiontable <- read.csv(condition_file, header=FALSE, row.names=1, sep = "\t", comment.char = "#")
colnames(conditiontable) <- c('condition')
condition <- as.factor(conditiontable[,1])

deseqDataset <- DESeqDataSetFromMatrix(countData=countdata, colData=conditiontable, design=~condition)
deseqDataset <- estimateSizeFactors(deseqDataset)
countdata.normalized <- counts(deseqDataset, normalized = TRUE)
write.table(countdata.normalized, file = paste(output_folder, "counts_normalized.txt", sep=""), sep="\t", row.names = TRUE, col.names = NA)

deseq.results <- DESeq(object = deseqDataset, parallel = TRUE)
save.image(paste(output_folder, "/deseq2.RData", sep=""))

create_correlation_matrix(countdata.normalized, conditiontable, paste(output_folder, 'correlation_heatmap.pdf', sep=""))

# Create all DESeq2 comparisons
dir.create(paste(output_folder, "deseq2_comparisons", sep=""))
for (cond in combn(levels(condition), 2, simplify = FALSE)){
  res <-
    results(deseq.results,
            addMLE = FALSE,
            contrast = c("condition", cond[1], cond[2]))
  write.table(res, file=paste(output_folder, "deseq2_comparisons/deseq2_results_", cond[1], "_Vs_", cond[2], ".csv", sep=""), sep="\t", row.names = TRUE, col.names = NA)
}

