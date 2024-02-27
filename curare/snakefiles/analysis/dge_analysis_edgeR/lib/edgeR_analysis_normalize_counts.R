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
threads <- args[match('--threads', args) + 1]
output_folder <- args[match('--output', args) + 1]

if (!file.exists(paste(output_folder, "edgeR_comparisons", sep="/"))) {
    dir.create(paste(output_folder, "edgeR_comparisons", sep="/"))
}
if (!file.exists(paste(output_folder, "visualization", sep="/"))) {
    dir.create(paste(output_folder, "visualization", sep="/"))
}
if (!file.exists(paste(output_folder, "summary", sep="/"))) {
    dir.create(paste(output_folder, "summary", sep="/"))
}

output_vis <- paste(output_folder, "visualization", sep="/")
output_rpkm <- paste(output_folder, "counts_rpkm.txt", sep="/")
output_cpm <- paste(output_folder, "counts_cpm.txt", sep="/")

# Required packages
for (package in c("edgeR", "BiocParallel", "pheatmap", "ggplot2", "reshape2", "gplots", "svglite")) {
    if (!(package %in% rownames(installed.packages()))) {
        library("crayon")
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
conditiontable$condition <- factor(conditiontable$condition, levels = unique(conditiontable$condition))
condition <- as.factor(conditiontable$condition)

edgeRDataset <- DGEList(counts=countdata, group=factor(condition), genes=data.frame(Length=countdata.raw$Length))

#Filter low features
keep <- filterByExpr(edgeRDataset)
edgeRDataset <- edgeRDataset[keep,keep.lib.sizes=FALSE]

# Normalization and write normalized count table
edgeRDataset <- normLibSizes(edgeRDataset)
countdata.rpkm <- rpkm(edgeRDataset)
write.table(data.frame("geneid"=rownames(countdata.rpkm), countdata.rpkm, check.names=FALSE), file = output_rpkm, sep = "\t", row.names = FALSE)
countdata.cpm <- rpkm(edgeRDataset)
write.table(data.frame("geneid"=rownames(countdata.cpm),countdata.cpm, check.names=FALSE), file = output_cpm, sep = "\t", row.names = FALSE)

# calculate dispersions
edgeRDataset <- estimateDisp(edgeRDataset)

# Save R state in file
save.image(file = r_data)

# Heatmap showing similarities between samples (needs a count table and conditions )
if ("pheatmap" %in% rownames(installed.packages())) {
    svglite(paste(output_vis, 'correlation_heatmap.svg', sep = "/"))
    print(create_correlation_matrix(countdata.cpm, conditiontable))
    dev.off()
}

# Bar charts showing the assignment of allignments to genes (featureCounts statistics)
if (("ggplot2" %in% rownames(installed.packages())) && ("reshape2" %in% rownames(installed.packages())) && ("svglite" %in% rownames(installed.packages()))) {
    plots <- create_feature_counts_statistics(feature_counts_log_file)
    svglite(paste(output_vis, 'counts_assignment_absolute.svg', sep = "/"))
    print(plots[1])
    dev.off()
    svglite(paste(output_vis, 'counts_assignment_relative.svg', sep = "/"))
    print(plots[2])
    dev.off()
}

# MDS of edgeR data
colors <- c('#4878d0', '#cfcfcf', '#a6d854', '#956cb4', '#ffd92f', '#797979', '#4daf4a', '#8c613c', '#dc7ec0', '#82c6e2', '#d5bb67', '#e41a1c', '#ff9f9b', '#ff7f00')
colorsNecessary <- length(levels(conditiontable$condition))
colorPalette <- rep(colors, length.out = colorsNecessary)
colConditions <- colorPalette[match(conditiontable$condition,
                                     levels(conditiontable$condition))]

{
    svglite(paste(output_vis, 'mds.svg', sep = "/"))
    par(mfrow=c(2,2))
    print(plotMDS(edgeRDataset, dim.plot = c(1,2), col = colConditions, gene.selection = "common"))
    print(plotMDS(edgeRDataset, dim.plot = c(2,3), col = colConditions, gene.selection = "common"))
    print(plotMDS(edgeRDataset, dim.plot = c(3,4), col = colConditions, gene.selection = "common"))
    print(plotMDS(edgeRDataset, dim.plot = c(4,5), col = colConditions, gene.selection = "common"))
    dev.off()
    for (i in 1:4){
        svglite(paste(output_vis, '/mds_c', i, '_vs_c', i+1, '.svg', sep = ""))
        print(plotMDS(edgeRDataset, dim.plot = c(i,i+1), col = colConditions, gene.selection = "common"))
        dev.off()
    }
}

rotate_vector <- function(vec, n=1L){
    x <- seq(1, length(vec))
    while (n > 0) {
        x <- c(x[2 : length(x)], x[1])
        n <- n - 1
    }
    vec[x]
}

# Create all edgeR comparisons
for (cond in combn(levels(condition), 2, simplify = FALSE)) {
    et <- exactTest(edgeRDataset, pair = c(cond[1], cond[2]))
    res <- as.data.frame(topTags(et, nrow(et)))
    write.table(res, file = paste(output_folder, "edgeR_comparisons/edgeR_results_", cond[1], "_Vs_", cond[2], ".csv", sep = ""), sep = "\t", row.names = TRUE, col.names = NA)
}

# Create a summary file for each condition
sapply(1 : length(levels(condition)), function(control_i) {
    control = levels(condition)[control_i]
    vs_condition <- levels(condition)[-control_i]

    mergedFullResults <- Reduce(
        function(d1, d2){
            merge(d1, d2, by = "gene_id", all = TRUE)
        },
        lapply(
            lapply(vs_condition, function(x) c(control, x)),
            function(y){
                et <- exactTest(edgeRDataset, pair = c(y[1], y[2]));
                df <- as.data.frame(topTags(et, nrow(et)));
                colnames(df) <- paste(y[2], colnames(df), sep = ".");
                df$gene_id <- rownames(df);
                df
            }
        )
    )

    if (length(vs_condition) >= 2) {
        summaryResults <- mergedFullResults[, c(1, #gene_id entries
                                  seq(from = 3, to = length(mergedFullResults), by = 5),    #logFC entries
                                  seq(from = 6, to = length(mergedFullResults), by = 5))    #FDR entries
        ]
    } else {
        summaryResults <- mergedFullResults[, c(6, 2, 5)]  #gene_id at pos 6 when nothin is merged
    }

    colnames(summaryResults) <- as.vector(sapply(colnames(summaryResults), function(x) gsub("(.*\\.)logFC", "\\1log2FC", x)))
    rownames(summaryResults) <- summaryResults$gene_id
    cpm.edgeRDataset <- cpm(edgeRDataset)
    colnames(cpm.edgeRDataset)<-paste(colnames(cpm.edgeRDataset),"CPM",sep=".")
    summaryResults <- merge(summaryResults, cpm.edgeRDataset, by = 0)
    summaryResults$Row.names <- NULL
    rownames(summaryResults) <- summaryResults$gene_id
    write.table(x = summaryResults[, c(1,
                            rotate_vector(2:(1 + (length(vs_condition) * 2)), length(vs_condition)),
                            (length(vs_condition) * 2 + 2):length(summaryResults))],
                paste(output_folder, 'summary/', control, ".tsv", sep = ""),
                row.names = F, col.names = T, sep = "\t")
    if (length(vs_condition) >= 2) {
        m <- as.matrix(summaryResults[, 2 : (length(vs_condition) + 1)])
        colnames(m) <- sapply(colnames(m), function(x) gsub("\\..{1,}$", '', x))
        if ('gplots' %in% rownames(installed.packages())) {
            plotHeatmap2(m, name = paste(output_folder, 'summary/', control, "_log2fc.pdf", sep = ""))
        }
    }
})
