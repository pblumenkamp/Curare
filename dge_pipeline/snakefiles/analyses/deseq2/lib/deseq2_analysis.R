library("DESeq2")
library("BiocParallel")
library("pheatmap")
library("ggplot2")
library("reshape2")


create_correlation_matrix <- function(countdata, conditiontable, output) {
    countdata.normalized.processed <- as.matrix(countdata)
    countdata.normalized.processed <- countdata.normalized.processed[rowSums(countdata.normalized.processed) >= 10,]
    countdata.normalized.processed <- log2(countdata.normalized.processed+1)
    sample_cor <- cor(countdata.normalized.processed, method='pearson', use='pairwise.complete.obs')

    pdf(output, width=8, height=7)
    pheatmap(sample_cor, annotation_col=conditiontable, annotation_row=conditiontable)
    dev.off()
}


#create_feature_counts_statistics <- function(featureCountsLog, output) {
#    d <- read.table(featureCountsLog, header=T, row.names = 1)
#    colnames(d) <- gsub(".bam", "", colnames(d))

#    dpct <- t(t(d)/colSums(d))

#    dm <- melt(t(d))
#    dpctm <- melt(t(dpct))

#    colnames(dm) <- c("Sample", "Group", "Reads")
#    dm$Group <- factor(dm$Group, levels = rev(levels(dm$Group)[order(levels(dm$Group))]))

#    pdf(output)
#    ggplot(dm[dm$Reads > 0,], aes(x=Sample, y=Reads)) + geom_bar(aes(fill=Group), stat="identity", group=1) +
#      theme(axis.text.x = element_text(angle = 45, hjust = 1))

#    colnames(dpctm) <- c("Sample", "Group", "Reads")
#    dpctm$Group <- factor(dpctm$Group, levels = rev(levels(dpctm$Group)))
#    ggplot(dpctm[dpctm$Reads > 0,], aes(x=Sample, y=Reads)) + geom_bar(aes(fill=Group), stat="identity", group=1) +
#      theme(axis.text.x = element_text(angle = 45, hjust = 1))
#    dev.off()
#}

args <- commandArgs(TRUE)
counttable_file <- args[match('--counttable', args) + 1]
condition_file <- args[match('--conditions', args) + 1]
feature_counts_log_file <- args[match('--featcounts-log', args) + 1]
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
#create_feature_counts_statistics(feature_counts_log_file, paste(output_folder, 'count_assignment.pdf', sep=""))

d <- read.table(feature_counts_log_file, header=T, row.names = 1)
colnames(d) <- gsub(".bam", "", colnames(d))

dpct <- t(t(d)/colSums(d))

dm <- melt(t(d))
dpctm <- melt(t(dpct))

colnames(dm) <- c("Sample", "Group", "Reads")
dm$Group <- factor(dm$Group, levels = rev(levels(dm$Group)[order(levels(dm$Group))]))

pdf(paste(output_folder, 'count_assignment.pdf', sep=""))
ggplot(dm[dm$Reads > 0,], aes(x=Sample, y=Reads)) + geom_bar(aes(fill=Group), stat="identity", group=1) +
  theme(axis.text.x = element_text(angle = 45, hjust = 1))

colnames(dpctm) <- c("Sample", "Group", "Reads")
dpctm$Group <- factor(dpctm$Group, levels = rev(levels(dpctm$Group)))
ggplot(dpctm[dpctm$Reads > 0,], aes(x=Sample, y=Reads)) + geom_bar(aes(fill=Group), stat="identity", group=1) +
  theme(axis.text.x = element_text(angle = 45, hjust = 1))
dev.off()

# Create all DESeq2 comparisons
dir.create(paste(output_folder, "deseq2_comparisons", sep=""))
for (cond in combn(levels(condition), 2, simplify = FALSE)){
  res <-
    results(deseq.results,
            addMLE = FALSE,
            contrast = c("condition", cond[1], cond[2]))
  write.table(res, file=paste(output_folder, "deseq2_comparisons/deseq2_results_", cond[1], "_Vs_", cond[2], ".csv", sep=""), sep="\t", row.names = TRUE, col.names = NA)
}

