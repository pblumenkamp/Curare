library("DESeq2")
library("BiocParallel")
library("pheatmap")
library("ggplot2")
library("reshape2")


create_correlation_matrix <- function(countdata, conditiontable) {
    countdata.normalized.processed <- as.matrix(countdata)
    countdata.normalized.processed <- countdata.normalized.processed[rowSums(countdata.normalized.processed) >= 10,]
    countdata.normalized.processed <- log2(countdata.normalized.processed + 1)
    sample_cor <- cor(countdata.normalized.processed, method = 'pearson', use = 'pairwise.complete.obs')

    return(pheatmap(sample_cor, annotation_col = conditiontable, annotation_row = conditiontable))
}


create_feature_counts_statistics <- function(featureCountsLog) {
    d <- read.table(featureCountsLog, header = T, row.names = 1)
    colnames(d) <- gsub(".bam", "", colnames(d))

    dpct <- t(t(d) / colSums(d))

    dm <- melt(t(d))
    dpctm <- melt(t(dpct))

    colnames(dm) <- c("Sample", "Group", "Reads")
    dm$Group <- factor(dm$Group, levels = rev(levels(dm$Group)[order(levels(dm$Group))]))

    assignment.absolute <- ggplot(dm[dm$Reads > 0,], aes(x = Sample, y = Reads)) +
        geom_bar(aes(fill = Group), stat = "identity", group = 1) +
        theme(axis.text.x = element_text(angle = 45, hjust = 1))

    colnames(dpctm) <- c("Sample", "Group", "Reads")
    dpctm$Group = factor(dpctm$Group, levels = rev(levels(dpctm$Group)[order(levels(dpctm$Group))]))
    assignment.relative <- ggplot(dpctm[dpctm$Reads > 0,], aes(x = Sample, y = Reads)) +
        geom_bar(aes(fill = Group), stat = "identity", group = 1) +
        theme(axis.text.x = element_text(angle = 45, hjust = 1))

    return(list(assignment.absolute, assignment.relative))
}

plotHeatmap2 <- function(x, name = "no_name_set.pdf", row_subset = NA, distMethod = "euclidean", clusterMethod = "complete", clrn = NA, ...){
    require('gplots')
    if (! is.na(clrn)) {
        # set the custom distance and clustering functions
        hclustfunc <- function(x) hclust(x, method = clusterMethod)
        distfunc <- function(x) dist(x, method = distMethod)
        # perform clustering on rows and columns
        cl.row <- hclustfunc(distfunc(x))
        gr.row <- cutree(cl.row, clrn)
        require(RColorBrewer)
        if (clrn < 3)clrn <- 3
        col1 <- brewer.pal(clrn, "Set1")
    }else {
        gr.row <- NA
    }

    pdf(name, width = 25, height = 25)
    nCol <- 40
    mycol2 <- colorpanel(n = nCol, low = "green", mid = "black", high = "red")
    mx <- max(abs(x))
    pairs.breaks <- seq(- mx, mx, by = (2 * mx / nCol))
    if (is.na(row_subset[1])) {
        xx <- x
    }else {
        xx <- x[row_subset,]
    }
    if (is.na(clrn)) {
        heatmap.2(xx,
        distfun = function(x) dist(x, method = distMethod),
        hclustfun = function(x) hclust(x, method = clusterMethod),
        col = mycol2,
        breaks = pairs.breaks,
        margins = c(20, 10),
        trace = "none")
    }else {
        heatmap.2(xx,
        distfun = function(x) dist(x, method = distMethod),
        hclustfun = function(x) hclust(x, method = clusterMethod),
        col = mycol2,
        breaks = pairs.breaks,
        margins = c(20, 10),
        RowSideColors = col1[gr.row],
        trace = "none")
    }
    dev.off()
    return(gr.row)
}

rotate_vector <- function(vec, n=1L){
    x <- seq(1, length(vec))
    while (n > 0) {
        x <- c(x[2 : length(x)], x[1])
        n <- n - 1
    }
    vec[x]
}


args <- commandArgs(TRUE)
counttable_file <- args[match('--counttable', args) + 1]
condition_file <- args[match('--conditions', args) + 1]
feature_counts_log_file <- args[match('--featcounts-log', args) + 1]
output_folder <- args[match('--output', args) + 1]
threads <- args[match('--threads', args) + 1]
register(MulticoreParam(threads))

countdata.raw <- read.csv(counttable_file, header = TRUE, row.names = 1, sep = "\t", comment.char = "#")
countdata <- as.matrix(countdata.raw[, c(6 : length(countdata.raw))])
colnames(countdata) <- as.vector(sapply(colnames(countdata), function(x) gsub("mapping\\.(.*)\\.bam", "\\1", x)))

conditiontable <- read.csv(condition_file, header = FALSE, row.names = 1, sep = "\t", comment.char = "#")
colnames(conditiontable) <- c('condition')
condition <- as.factor(conditiontable[, 1])

deseqDataset <- DESeqDataSetFromMatrix(countData = countdata, colData = conditiontable, design = ~ condition)
deseqDataset <- estimateSizeFactors(deseqDataset)
countdata.normalized <- counts(deseqDataset, normalized = TRUE)
write.table(countdata.normalized, file = paste(output_folder, "counts_normalized.txt", sep = ""), sep = "\t", row.names = TRUE, col.names = NA)

deseq.results <- DESeq(object = deseqDataset, parallel = TRUE)
save.image(paste(output_folder, "/deseq2.RData", sep = ""))

pdf(paste(output_folder, 'correlation_heatmap.pdf', sep = ""), width = 8, height = 8, onefile = FALSE)
print(create_correlation_matrix(countdata.normalized, conditiontable))
dev.off()

pdf(paste(output_folder, 'counts_assignment.pdf', sep = ""))
invisible(lapply(create_feature_counts_statistics(feature_counts_log_file), print))
dev.off()


# Create all DESeq2 comparisons
dir.create(paste(output_folder, "deseq2_comparisons", sep = ""))
for (cond in combn(levels(condition), 2, simplify = FALSE)) {
    res <-
    results(deseq.results,
    addMLE = FALSE,
    contrast = c("condition", cond[1], cond[2]))
    write.table(res, file = paste(output_folder, "deseq2_comparisons/deseq2_results_", cond[1], "_Vs_", cond[2], ".csv", sep = ""), sep = "\t", row.names = TRUE, col.names = NA)
}

dir.create(paste(output_folder, "summary", sep = ""))
write.table(data.frame(), file='keep_summary.txt', col.names=FALSE)
sapply(1 : length(levels(condition)), function(control_i) {
    control = levels(condition)[control_i]
    vs_condition <- levels(condition)[-control_i]

    log2foldChange <- Reduce(
        function(d1, d2){
            merge(d1, d2, by = "gene_id", all = TRUE)
        },
        lapply(
            lapply(vs_condition, function(x) c(control, x)),
            function(y){
                df <- as.data.frame(results(deseq.results, addMLE = FALSE, contrast = c("condition", y[1], y[2])));
                colnames(df) <- paste(y[2], colnames(df), sep = ".");
                df$gene_id <- rownames(df);
                df
            }
        )
    )

    if (length(vs_condition) > 2) {
        log2foldChangeOnly <- log2foldChange[, c(1,
                                                 seq(from = 3, to = length(log2foldChange), by = 6),
                                                 seq(from = 7, to = length(log2foldChange), by = 6),
                                                 seq(from = 6, to = length(log2foldChange), by = 6))
                                            ]
        log2foldChangeOnly$minFC <- apply(log2foldChangeOnly[, 2:(length(vs_condition) + 1)], 1, min, na.rm = T)
        log2foldChangeOnly$maxFC <- apply(log2foldChangeOnly[, 2:(length(vs_condition) + 1)], 1, max, na.rm = T)
        fc2 <- log2foldChangeOnly[log2foldChangeOnly$minFC <= -2 | log2foldChangeOnly$maxFC >= 2,]
        fc2$minFC <- NULL
        fc2$maxFC <- NULL
    } else {
        log2foldChangeOnly <- log2foldChange[, c(7, 2, 5, 6)]
        fc2 <- log2foldChangeOnly[log2foldChangeOnly[, 3] <= - 2 | log2foldChangeOnly[, 3] >= 2,]
        fc2 <- fc2[complete.cases(fc2[, 3]),]
    }

    rownames(fc2) <- fc2$gene_id
    fc2 <- merge(fc2, counts(deseqDataset), by = 0)
    fc2$Row.names <- NULL
    rownames(fc2) <- fc2$gene_id
    write.table(x = fc2[, c(1,
                            rotate_vector(2:(1 + (length(vs_condition) * 3)), length(vs_condition)),
                            (length(vs_condition) * 3 + 2):length(fc2))],
                paste(output_folder, 'summary/', control, ".tsv", sep = ""),
                row.names = F, col.names = T, sep = "\t")
    if (length(vs_condition) > 2) {
        m <- as.matrix(fc2[, 2 : (length(vs_condition) + 1)])
        colnames(m) <- sapply(colnames(m), function(x) gsub("\\..{1,}$", '', x))
        plotHeatmap2(m, name = paste(output_folder, 'summary/', control, ".pdf", sep = ""))
    }
})
