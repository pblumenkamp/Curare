findCluster <- function(id, previd) {
  if (id-1 != previd)
    colourBool <<- !colourBool
  colourBool
}

getNextClusterChange <- function(data, start) {
  thisCluster <- data$cluster[start]
  if (nrow(data) <= start) {
    nrow(data)+1
  } else if ( thisCluster == data$cluster[start+1]) {
    getNextClusterChange(data, start+1)
  } else {
    start+1
  }
}

#result data
save.genecluster <- function(deseq2Data, directory, cond) {
  library(ggplot2)
  
  if (!dir.exists(directory)){
    dir.create(path=directory)
  }
  
  neededPlots <- ceiling(nrow(deseq2Data) / 60)
  rowsPerPlot <- ceiling(nrow(deseq2Data)/neededPlots)
  
  maxY <- max(deseq2Data$log2FoldChange)
  minY <- min(deseq2Data$log2FoldChange)
  
  startPoint  <- 1
  endPoint <- getNextClusterChange(deseq2Data, rowsPerPlot)-1
  i <- 1
  while (startPoint < nrow(deseq2Data)){
    plots <- ggplot(deseq2Data[startPoint:endPoint,], aes(x = gene, y = log2FoldChange, fill=cluster)) +
      geom_bar(stat = 'identity', 
               position = 'identity', 
               colour = 'black',        # contour around each bar
               size = 0.5               # width of the contour line
      )+
      scale_fill_manual(
        values = c("#66A5AD", "#003B46"), # bar colours 
        guide = FALSE                       # disables legend
      ) +
      ylim(minY, maxY) +
      ggtitle(paste(cond[1], "Vs.", cond[2])) + # title
      theme(plot.title = element_text(lineheight=.5, face="bold"), axis.text.x = element_text(angle=90, hjust = 1, size=8))
    
    ggsave(filename = file.path(directory, paste("genecluster_",cond[1],"Vs",cond[2],"_",i,".svg", sep="")), plot = plots)
    
    startPoint <- endPoint+1
    endPoint <- getNextClusterChange(deseq2Data, startPoint+rowsPerPlot)-1
    i <- i+1
  }
  
  deseq2Data$Start1 <- as.character(deseq2Data$Start1)
  deseq2Data$Stop1 <- as.character(deseq2Data$Stop1)
  write.table(deseq2Data[,1:(ncol(deseq2Data)-4)], file =file.path(directory, paste("genecluster_", cond[1],"Vs",cond[2],".csv", sep="")), sep="\t", row.names = FALSE)
}

#result data
save.maplot <- function(deseq2Data, svgfile, allData = FALSE, title="MA plot") {
  svg(svgfile)
  maxLog2Change <- max(deseq2Data$log2FoldChange[!is.na(deseq2Data$log2FoldChange)])
  minLog2Change <- min(deseq2Data$log2FoldChange[!is.na(deseq2Data$log2FoldChange)])
  if (allData){
    plotMA(deseq2Data, MLE=TRUE, main=title, ylim=c(minLog2Change,maxLog2Change))
  } else {
    plotMA(deseq2Data, main=title, ylim=c(minLog2Change,maxLog2Change))
  }
  dev.off()
}

#result data
save.phistogram <- function(deseq2Data, svgfile, title = "Distribution of p values") {
  svg(svgfile)
  hist(deseq2Data$padj[deseq2Data$baseMean > 1], breaks=0:40/40, col="#66A5AD", border="white", main=title, xaxt='n')
  axis(side=1, at=0:10/10, labels=0:10/10)
  dev.off()
}

#result data
save.volcanoplot <- function(deseq2CountData, deseq2ResultData, directory, cond, title="Volcano Plot", withLabels=TRUE) {
  if (withLabels)
    library(calibrate)
  if (!dir.exists(directory)){
    dir.create(path=directory)
  }
  svg(file.path(directory, paste("volcanoplot_", cond[1], "Vs", cond[2], ".svg", sep="")))
  # #Volcano plot
  # plot(res$log2FoldChange, -log(res$padj), pch=15)
  # points(sig$log2FoldChange, -log(sig$padj), col="grey", pch=15)
  # library("calibrate")
  # textxy(sig$log2FoldChange, -log(sig$padj), rownames(sig), cex=0.9)
  # #nicer plot
  xminVal <- min(deseq2ResultData$log2FoldChange[!is.na(deseq2ResultData$log2FoldChange)])
  xmaxVal <- max(deseq2ResultData$log2FoldChange[!is.na(deseq2ResultData$log2FoldChange)])
  with(deseq2ResultData, plot(log2FoldChange, -log10(padj), pch=20, main=title, xlim=c(xminVal-1,xmaxVal+1)))
  # Add colored points: red if padj<0.05, orange of log2FC>1, green if both)
  with(subset(deseq2ResultData, padj<.05 ), points(log2FoldChange, -log10(padj), pch=20, col="red"))
  with(subset(deseq2ResultData, abs(log2FoldChange)>1), points(log2FoldChange, -log10(padj), pch=20, col="orange"))
  with(subset(deseq2ResultData, padj<.05 & abs(log2FoldChange)>1), points(log2FoldChange, -log10(padj), pch=20, col="green"))
  
  if (withLabels){
    # Label points with the textxy function from the calibrate plot
    deseq2ResultData$gene <- rownames(deseq2ResultData)
    with(subset(deseq2ResultData, padj<.05 & abs(log2FoldChange)>1), textxy(log2FoldChange, -log10(padj), labs=gene, cex=.7))
  }
  dev.off()
  
  tabledata <- assay(deseq2CountData)[rownames(subset(deseq2ResultData, padj<.05 & abs(log2FoldChange)>1)),]
  write.table(tabledata, file = file.path(directory, paste("volcanoplot_", cond[1],"Vs",cond[2],".csv", sep="")), sep="\t", row.names = TRUE, col.names = NA)
}

#result data
save.plotcounts <- function(deseq2CompleteData, deseq2ResultData, directory, cond, maxNValues = 1) {
  if (!dir.exists(directory))
    dir.create(directory)
  orderPAdj <- order(deseq2ResultData$padj)
  
  for (i in 0:(maxNValues-1)) {
    #customized plot
    plotCountsData <- plotCounts(deseq2CompleteData, gene=orderPAdj[i+1], intgroup = "condition", returnData = TRUE)
    library("ggplot2")
    p <- ggplot(plotCountsData, aes(x=condition, y=count)) +
      geom_point(position = position_jitter(w=0.1,h=0)) +
      scale_y_log10(limits=c(1,100000)) +
      ggtitle(paste(cond[1], " Vs ", cond[2], " - #", i+1, sep = "" ), 
              subtitle = paste("Top ", maxNValues, " - Gene: ", rownames(deseq2ResultData)[orderPAdj[i+1]], 
                               " - adjusted p-value: ", format(deseq2ResultData$padj[orderPAdj[i+1]], scientific = TRUE), sep=""))
    ggsave(filename = file.path(directory, paste("plotcounts_", cond[1], "Vs", cond[2], "_", i+1, ".svg", sep="")), plot = p)
  }
}

#result data
save.resulttable <- function(deseq2Data, csvfile, sep = "\t"){
  write.table(deseq2Data, file = csvfile, sep=sep, row.names = FALSE)
}

#deseq2 data
save.heatmap <- function(deseq2Data, svgfile){
  svg(svgfile)
  vsd <- getVarianceStabilizedData(deseq2Data)
  plot <- heatmap(cor(vsd), cexCol = 0.4, cexRow = 0.6)
  dev.off()
}

#deseq2 data
save.heatmap2 <- function(dds, pngfile){
  library("pheatmap")
  library("RColorBrewer")
  
  dds <- dds[ rowSums(counts(dds)) > 1, ]
  rld <- rlog(dds, blind=FALSE)
  sampleDists <- dist( t( assay(rld) ) )
  
  sampleDistMatrix <- as.matrix( sampleDists )
  #rownames(sampleDistMatrix) <- paste( rld$dex, rld$cell, sep="-" )
  rownames(sampleDistMatrix) <- colnames(sampleDistMatrix)
  colnames(sampleDistMatrix) <- NULL
  colors <- colorRampPalette( rev(brewer.pal(9, "Blues")) )(255)
  pheatmap(sampleDistMatrix,
           clustering_distance_rows=sampleDists,
           clustering_distance_cols=sampleDists,
           col=colors,
           filename=pngfile)
}

#deseq2 data
save.pca <- function(deseq2Data, svgfile, withArrow=FALSE){
  svg(svgfile)
  vsd <- getVarianceStabilizedData(deseq2Data)
  pr <- prcomp(t(vsd))
  if (withArrow){
    biplot(pr, cex=c(1,0.5), main="Biplot", col=c("black", "grey"))
  } else {
    plot(pr$x, col="white", main="PC plot", xlim=c(-22,15))
    text(pr$x[,1],pr$x[,2], labels=colnames(vsd), cex=0.7)
  }
  dev.off()
}