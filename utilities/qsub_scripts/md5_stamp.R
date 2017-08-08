# A script that adds a file signature to a NeatSeq-Flow file-registration file
# Get: 
# 1. md5 path (if not)
# 2. file-registration path
# 3. file-to-add path

# Return:
# 1. If file does not exist - return md5sum output
# 2. if file exists - return error state


# AUTHOR: Menachem Sklarz & Michal Gordon

library(magrittr)
library(plyr )
library(optparse)
library(tools)



# paste("Rscript",
#       "md5_stamp.R",
#       "--blast",           "MLST/SAH1503/SAH1503.blast.out",
#       "--dbtable",         "MLST/MLST_scheme.tab",
# ) %>% system

# paste("Rscript","parse_blast_general.R","-h") %>% system


args    = commandArgs(trailingOnly = F) 
filepos = args %>% grep("--file=",x = .)
curfile = sub(pattern     = "--file=",
              replacement = "",
              x           = args[filepos]) %>% file_path_as_absolute
print(curfile)


args = commandArgs(trailingOnly=TRUE)

option_list = list(
    make_option(c("-m", "--md5path"), type="character", default="md5sum", 
                help="Path to md5sum (default: md5sum with no path)", metavar="character"),
    make_option(c("-f", "--regist_file"), type="character", default=NULL, 
                help="Path to file-registration file.", metavar="character"),
    make_option(c("-r", "--result_file"), type="character", default=NULL, 
                help="Path to file to register", metavar="character"),

); 



opt_parser = optparse::OptionParser(usage = "usage: %prog [options]", 
                                    option_list=option_list,
                                    epilogue="\n\nAuthor: Menachem Sklarz");
opt = optparse::parse_args(opt_parser);

regist_file <- read.delim(opt$regist_file)

md5_sig <- system(sprintf("%s %s", opt$md5path,opt$result_file))

split()



