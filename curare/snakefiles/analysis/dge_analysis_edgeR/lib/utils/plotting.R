# Heatmap showing similarities between samples (needs a count table and conditions )
create_correlation_matrix <- function(countdata, conditiontable) {
    countdata.normalized.processed <- as.matrix(countdata)
    countdata.normalized.processed <- countdata.normalized.processed[rowSums(countdata.normalized.processed) >= 10,]
    countdata.normalized.processed <- log2(countdata.normalized.processed + 1)
    sample_cor <- cor(countdata.normalized.processed, method = 'pearson', use = 'pairwise.complete.obs')

    return(pheatmap(sample_cor, annotation_row = conditiontable, fontsize = 16))
}

# Bar charts showing the assignment of allignments to genes (featureCounts statistics)
create_feature_counts_statistics <- function(featureCountsLog) {
    colors <- c('#4878d0', '#cfcfcf', '#a6d854', '#956cb4', '#ffd92f', '#797979', '#4daf4a', '#8c613c', '#dc7ec0', '#82c6e2', '#d5bb67', '#e41a1c', '#ff9f9b', '#ff7f00')
    names(colors) <- c("Assigned", "Unassigned - Unmapped", "Unassigned - Read Type", "Unassigned - Singleton", "Unassigned - MappingQuality", "Unassigned - Chimera", "Unassigned - FragmentLength",
                       "Unassigned - Duplicate", "Unassigned - MultiMapping", "Unassigned - Secondary", "Unassigned - NonSplit", "Unassigned - NoFeatures", "Unassigned - Overlapping Length", "Unassigned - Ambiguity")
    fcColScale <- scale_fill_manual(name="Group", values=colors)
    d <- read.table(featureCountsLog, header = T, row.names = 1)
    colnames(d) <- gsub("mapping\\.(.*)\\.bam", "\\1", colnames(d))
    rownames(d) <- gsub("_", " - ", rownames(d))

    dpct <- t(t(d) / colSums(d))

    dm <- melt(t(d))
    dpctm <- melt(t(dpct))

    colnames(dm) <- c("Sample", "Group", "Reads")
    dm$Group <- factor(dm$Group, levels = rev(levels(dm$Group)[order(levels(dm$Group))]))

    count_groups <- length(unique(dm$Group))
    legend_entries_per_row <- 3
    if (legend_entries_per_row < 3) {
        legend_entries_per_row <- count_groups
    } else if (legend_entries_per_row == 4) {
        legend_entries_per_row <- 4
    }

    assignment.absolute <- ggplot(dm[dm$Reads > 0,], aes(x = Sample, y = Reads, width=0.7)) +
        geom_bar(aes(fill = Group), stat = "identity", group = 1) +
        theme_minimal() +
        scale_y_continuous(expand = expansion(mult = c(0, .05)), labels = scales::comma) +
        theme(text = element_text(size = 22), 
              axis.text.x = element_text(angle = 90, hjust = 1, vjust = 0.5), 
              axis.title.x = element_blank(), 
              axis.title.y = element_text(margin = margin(t=0, r=16, b=0, l=8)),
              legend.position = "bottom", 
              legend.title = element_blank(),
              panel.grid.major.x = element_blank()) +
        guides(fill=guide_legend(ncol=2, reverse=TRUE)) +
        labs(y = "# Assigned Reads") +
        fcColScale


    colnames(dpctm) <- c("Sample", "Group", "Reads")
    dpctm$Group = factor(dpctm$Group, levels = rev(levels(dpctm$Group)[order(levels(dpctm$Group))]))
    dpctm$Reads <- dpctm$Reads * 100
    assignment.relative <- ggplot(dpctm[dpctm$Reads > 0,], aes(x = Sample, y = Reads, width=0.6)) +
        geom_bar(aes(fill = Group), stat = "identity", group = 1) +
        theme_minimal() +
        scale_y_continuous(expand = expansion(mult = c(0, .1)), labels = scales::comma) +
        theme(text = element_text(size = 22), 
              axis.text.x = element_text(angle = 90, hjust = 1, vjust = 0.5),
              axis.title.y = element_text(margin = margin(t=0, r=16, b=0, l=8)), 
              axis.title.x = element_blank(), 
              legend.position = "bottom", 
              legend.title = element_blank(),
              panel.grid.major.x = element_blank()) +
        guides(fill=guide_legend(ncol=2, reverse=TRUE)) +
        labs(y = "Assigned Reads [%]") +
        fcColScale

    return(list(assignment.absolute, assignment.relative))
}

# Heatmap showing log fold change of one condition versus all others (TODO legend and description)
plotHeatmap2 <- function(x, name = "no_name_set.pdf", row_subset = NA, distMethod = "euclidean", clusterMethod = "complete", clrn = NA){
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

    # no observations allowed with NAs
    x <- x[complete.cases(x),]
    nCol <- 40
    mycol2 <- colorpanel(n = nCol, low = "green", mid = "black", high = "red")
    mx <- max(abs(x), na.rm = TRUE)
    pairs.breaks <- seq(-mx, mx, by = (2 * mx / nCol))

    pdf(name, width = 25, height = 25)
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

