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
feature_counts_log_file <- args[match('--featcounts-log', args) + 1]
r_data <- args[match('--r-data',args)+1]
output_folder <- args[match('--output', args) + 1]
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
for (package in c("BiocParallel", "ggplot2", "gplots")) {
    if (!(package %in% rownames(installed.packages()))) {
        stop(paste('Package "', package, '" not installed', sep=""))
    } else {
        print(paste("Import:", package))
        library(package, character.only=TRUE)
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

# Run on multiple threads
if ("BiocParallel" %in% rownames(installed.packages())) {
    register(MulticoreParam(threads))
}

# Load R state in file
# This is evil code! It overrides existing functions...
load(file = r_data)

# Create all DESeq2 comparisons
if (!file.exists(paste(output_folder, "deseq2_comparisons", sep = ""))) {
    dir.create(paste(output_folder, "deseq2_comparisons", sep = ""))
}
for (cond in combn(levels(condition), 2, simplify = FALSE)) {
    res <-
    results(deseq.results,
    addMLE = FALSE,
    contrast = c("condition", cond[1], cond[2]))
    write.table(res, file = paste(output_folder, "deseq2_comparisons/deseq2_results_", cond[1], "_Vs_", cond[2], ".csv", sep = ""), sep = "\t", row.names = TRUE, col.names = NA)
}

# Create a summary file for each condition
if (!file.exists(paste(output_folder, "summary", sep = ""))) {
    dir.create(paste(output_folder, "summary", sep = ""))
}
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

    if (length(vs_condition) >= 2) {
        fc2 <- log2foldChange[, c(1,
                                  seq(from = 3, to = length(log2foldChange), by = 6),
                                  seq(from = 7, to = length(log2foldChange), by = 6),
                                  seq(from = 6, to = length(log2foldChange), by = 6))
        ]
    } else {
        fc2 <- log2foldChange[, c(7, 2, 5, 6)]
        fc2 <- fc2[complete.cases(fc2[, 2]),]
    }

    rownames(fc2) <- fc2$gene_id
    fc2 <- merge(fc2, counts(deseqDataset, normalized = TRUE), by = 0)
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
        if ('gplots' %in% rownames(installed.packages())) {
            plotHeatmap2(m, name = paste(output_folder, 'summary/', control, ".pdf", sep = ""))
        }
    }
})
