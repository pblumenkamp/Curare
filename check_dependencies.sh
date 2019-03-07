#!/usr/bin/env bash

RED='\033[0;31m'
GREEN='\033[0;32m'
ORANGE='\033[0;33m'
NC='\033[0m' # No Color

echo "##OS##"
command -v lsb_release >/dev/null 2>&1
if [[ $? = 0 ]]
then
    lsb_release -a 2>&1
else
    echo "OSTYPE: $OSTYPE"
fi

echo
echo "##Global##"

command -v python >/dev/null 2>&1
if [[ $? = 0 ]]
then
    VERSION=$(python --version 2>&1 | grep "Python")
    REGEX="Python (.*)"
    if [[ ${VERSION} =~ $REGEX ]]
    then
        echo -e "Python: ${GREEN}${BASH_REMATCH[1]}${NC}"
    else
        echo -e "Python: ${ORANGE}Unknown version${NC}"
    fi
else
    echo -e "Python: ${RED}Not installed${NC}"
fi

command -v python3 >/dev/null 2>&1
if [[ $? = 0 ]]
then
    VERSION=$(python3 --version 2>&1 | grep "Python")
    REGEX="Python (.*)"
    if [[ ${VERSION} =~ $REGEX ]]
    then
        echo -e "Python3: ${GREEN}${BASH_REMATCH[1]}${NC}"
    else
        echo -e "Python3: ${ORANGE}Unknown version${NC}"
    fi
else
    echo -e "Python: ${RED}Not installed${NC}"
fi

command -v R >/dev/null 2>&1
if [[ $? == 0 ]]
then
    VERSION=$(R --version | grep "R version")
    REGEX="R version (.*?) \(.*"
    if [[ ${VERSION} =~ $REGEX ]]
    then
        echo -e "R: ${GREEN}${BASH_REMATCH[1]}${NC}"
    else
        echo -e "R: ${ORANGE}Unknown version${NC}"
    fi
else
    echo -e "R: ${RED}Not installed${NC}"
fi

command -v snakemake >/dev/null 2>&1
if [[ $? == 0 ]]
then
    VERSION=$(snakemake --version)
    REGEX="([0-9]+\.?)+"
    if [[ ${VERSION} =~ $REGEX ]]
    then
        echo -e "Snakemake: ${GREEN}$VERSION${NC}"
    else
        echo -e "Snakemake: ${ORANGE}Unknown version${NC}"
    fi
else
    echo -e "Snakemake: ${RED}Not installed${NC}"
fi

echo ""
echo "##Premapping##"

command -v fastqc >/dev/null 2>&1
if [[ $? == 0 ]]
then
    VERSION=$(fastqc --version)
    REGEX="^FastQC v(.*)$"
    if [[ ${VERSION} =~ $REGEX ]]
    then
        echo -e "FastQC: ${GREEN}${BASH_REMATCH[1]}${NC}"
    else
        echo -e "FastQC: ${ORANGE}Unknown version${NC}"
    fi
else
    echo -e "FastQC: ${RED}Not installed${NC}"
fi

command -v multiqc >/dev/null 2>&1
if [[ $? == 0 ]]
then
    VERSION=$(multiqc --version)
    REGEX="^multiqc, version (.*)$"
    if [[ ${VERSION} =~ $REGEX ]]
    then
        echo -e "MultiQC: ${GREEN}${BASH_REMATCH[1]}${NC}"
    else
        echo -e "MultiQC: ${ORANGE}Unknown version${NC}"
    fi
else
    echo -e "MultiQC: ${RED}Not installed${NC}"
fi

echo ""
echo "##Mapping##"

command -v bowtie2 >/dev/null 2>&1
if [[ $? == 0 ]]
then
    VERSION=$(bowtie2 --version | grep "bowtie2-align-s version")
    REGEX=".*bowtie2-align-s version (.*)"
    if [[ ${VERSION} =~ $REGEX ]]
    then
        echo -e "Bowtie2: ${GREEN}${BASH_REMATCH[1]}${NC}"
    else
        echo -e "Bowtie2: ${ORANGE}Unknown version${NC}"
    fi
else
    echo -e "Bowtie2: ${RED}Not installed${NC}"
fi

command -v bwa >/dev/null 2>&1
if [[ $? == 0 ]]
then
    VERSION=$(bwa 2>&1 | grep "Version:")
    REGEX="Version:[[:space:]]*(.*)"
    if [[ ${VERSION} =~ $REGEX ]]
    then
        echo -e "BWA: ${GREEN}${BASH_REMATCH[1]}${NC}"
    else
        echo -e "BWA: ${ORANGE}Unknown version${NC}"
    fi
else
    echo -e "BWA: ${RED}Not installed${NC}"
fi

command -v samtools >/dev/null 2>&1
if [[ $? == 0 ]]
then
    VERSION=$(samtools 2>&1 | grep "Version")
    REGEX="Version: (.*)"
    if [[ ${VERSION} =~ $REGEX ]]
    then
        echo -e "Samtools: ${GREEN}${BASH_REMATCH[1]}${NC}"
    else
        echo -e "Samtools: ${ORANGE}Unknown version${NC}"
    fi
else
    echo -e "Samtools: ${RED}Not installed${NC}"
fi

echo ""
echo "##Analysis##"

command -v featureCounts >/dev/null 2>&1
if [[ $? == 0 ]]
then
    VERSION=$(featureCounts -v 2>&1 | grep "featureCounts")
    REGEX="featureCounts v(.*)"
    if [[ ${VERSION} =~ $REGEX ]]
    then
        echo -e "featureCounts: ${GREEN}${BASH_REMATCH[1]}${NC}"
    else
        echo -e "featureCounts: ${ORANGE}Unknown version${NC}"
    fi
else
    echo -e "featureCounts: ${RED}Not installed${NC}"
fi

echo ""
echo "##Python modules##"

python -c "import pandas" >/dev/null 2>&1
if [[ $? == 0 ]]
then
    VERSION=$(python -c "import pandas; print(pandas.__version__)")
    echo -e "Pandas: ${GREEN}${VERSION}${NC}"
else
    echo -e "Pandas: ${RED}Not installed${NC}"
fi

python -c "import snakemake" >/dev/null 2>&1
if [[ $? == 0 ]]
then
    VERSION=$(python -c "import snakemake; print(snakemake.__version__)")
    echo -e "Snakemake: ${GREEN}${VERSION}${NC}"
else
    echo -e "Snakemake: ${RED}Not installed${NC}"
fi

python -c "import xlsxwriter" >/dev/null 2>&1
if [[ $? == 0 ]]
then
    VERSION=$(python -c "import xlsxwriter; print(xlsxwriter.__version__)")
    echo -e "Xlsxwriter: ${GREEN}${VERSION}${NC}"
else
    echo -e "Xlsxwriter: ${RED}Not installed${NC}"
fi

python -c "import yaml" >/dev/null 2>&1
if [[ $? == 0 ]]
then
    VERSION=$(python -c "import yaml; print(yaml.__version__)")
    echo -e "Yaml: ${GREEN}${VERSION}${NC}"
else
    echo -e "Yaml: ${RED}Not installed${NC}"
fi

echo ""
echo "##R packages##"

R --slave --vanilla -e 'if (! "DESeq2" %in% rownames(installed.packages())) {quit(status=1)}' >/dev/null 2>&1
if [[ $? == 0 ]]
then
    VERSION=$(R --slave --vanilla -e 'cat(as.character(packageVersion("DESeq2")))')
    echo -e "DESeq2: ${GREEN}${VERSION}${NC}"
else
    echo -e "DESeq2: ${RED}Not installed${NC}"
fi

R --slave --vanilla -e 'if (! "pheatmap" %in% rownames(installed.packages())) {quit(status=1)}' >/dev/null 2>&1
if [[ $? == 0 ]]
then
    VERSION=$(R --slave --vanilla -e 'cat(as.character(packageVersion("pheatmap")))')
    echo -e "pheatmap: ${GREEN}${VERSION}${NC}"
else
    echo -e "pheatmap: ${RED}Not installed${NC}"
fi

R --slave --vanilla -e 'if (! "ggplot2" %in% rownames(installed.packages())) {quit(status=1)}' >/dev/null 2>&1
if [[ $? == 0 ]]
then
    VERSION=$(R --slave --vanilla -e 'cat(as.character(packageVersion("ggplot2")))')
    echo -e "ggplot2: ${GREEN}${VERSION}${NC}"
else
    echo -e "ggplot2: ${RED}Not installed${NC}"
fi

R --slave --vanilla -e 'if (! "reshape2" %in% rownames(installed.packages())) {quit(status=1)}' >/dev/null 2>&1
if [[ $? == 0 ]]
then
    VERSION=$(R --slave --vanilla -e 'cat(as.character(packageVersion("reshape2")))')
    echo -e "reshape2: ${GREEN}${VERSION}${NC}"
else
    echo -e "reshape2: ${RED}Not installed${NC}"
fi

R --slave --vanilla -e 'if (! "gplots" %in% rownames(installed.packages())) {quit(status=1)}' >/dev/null 2>&1
if [[ $? == 0 ]]
then
    VERSION=$(R --slave --vanilla -e 'cat(as.character(packageVersion("gplots")))')
    echo -e "gplots: ${GREEN}${VERSION}${NC}"
else
    echo -e "gplots: ${RED}Not installed${NC}"
fi
