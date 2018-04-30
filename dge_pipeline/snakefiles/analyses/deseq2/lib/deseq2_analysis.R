library("DESeq2")
library("BiocParallel")

args <- commandArgs(TRUE)
counttable_file <- args[match('--counttable', args) + 1]
condition_file <- args[match('--conditions', args) + 1]
output_folder <- args[match('--output', args) + 1]
threads <- args[match('--threads', args) + 1]
register(MulticoreParam(threads))

d.raw <- read.csv(counttable_file, header=TRUE, row.names=1, sep = "\t", comment.char = "#")
d <- as.matrix(d.raw[, c(6:length(d.raw))])
colnames(d) <- as.vector(sapply(colnames(d), function(x) gsub("mapping\\.(.*)\\.bam", "\\1", x)))

cData <- read.csv(condition_file, header=FALSE, row.names=1, sep = "\t", comment.char = "#")
colnames(cData) <- c('condition')
condition <- as.factor(cData[,1])

dds <- DESeqDataSetFromMatrix(countData=d, colData=cData, design=~condition)
d.deseq <- DESeq(object = dds, parallel = TRUE)
resultsNames(d.deseq)
save.image(paste(output_folder, "/deseq2.RData", sep=""))


#plots <- c()
#for (cond in combn(levels(condition), 2, simplify = FALSE)){
#  res <-
#    results(d.deseq,
#            addMLE = FALSE,
#            contrast = c("condition", cond[1], cond[2]))
#  write.table(res, file=paste(output_folder, "/deseq2_results_", cond[1], "_Vs._", cond[2], ".csv", sep=""), sep="\t", row.names = TRUE)
#}

