library("DESeq2")
library("BiocParallel")
register(MulticoreParam($$THREADS$$))

d.raw <- read.csv("$$COUNT_TABLE$$", header=TRUE, row.names=1, sep = "\t", comment.char = "#")
d <- as.matrix(d.raw[, c(6:length(d.raw))])
colnames(d) <- c($$SAMPLE_NAMES$$)

condition <- as.factor(c($$CONDITIONS$$))

cData <- data.frame(row.names=colnames(d), condition)
rownames(cData) <- colnames(d)
dds <- DESeqDataSetFromMatrix(countData=d, colData=cData, design=~condition)
d.deseq <- DESeq(object = dds, parallel = TRUE)
resultsNames(d.deseq)


plots <- c()
for (cond in combn(levels(condition), 2, simplify = FALSE)){
  res <-
    results(d.deseq,
            addMLE = FALSE,
            contrast = c("condition", cond[1], cond[2]))
  write.table(res, file=paste("$$RESULT_FOLDER$$/deseq2_results_", cond[1], "_Vs._", cond[2], ".csv", sep=""), sep="\t", row.names = TRUE)
}

