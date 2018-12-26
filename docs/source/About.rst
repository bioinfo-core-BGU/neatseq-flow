.. _about_neatseq_flow:

========================================
About NeatSeq-Flow
========================================

.. include:: links.rst

**Author:** Vered Chalifa-Caspi

.. contents:: Table of Contents
   :depth: 2
   :local:
   :backlinks: top

NeatSeq-Flow is a platform for modular design and execution of bioinformatics workflow on a local computer or, preferably, computer cluster.
The platform has a command-line interface as well as a fully functional graphical user interface (GUI), both used locally without the need to connect to remote servers.
Analysis programs comprising a workflow can be anything executable from the Linux command-line, either publicly available or in-house programs.
Ready-to-use workflows are available for common Bioinformatics analyses such as assembly & annotation, RNA-Seq, ChIP-Seq, variant calling, metagenomics and genomic epidemiology.
Creation and sharing of new workflows is easy and intuitive, without need for programming knowledge.
NeatSeq-Flow is general-purpose and may easily be adjusted to work on different types of analyses other than high-throughput sequencing.

*The main benefits in using NeatSeq-Flow:*
   * Simple, cross-platform installation.
   * All workflow components and parameters, as well as their order of execution (a.k.a workflow design), are specified in a single file which may be prepared by the user either manually (YAML format) or through the GUI. This, together with the shell scripts produced by NeatSeq-Flow and additional NeatSeq-Flow summary files, comprise a complete documentation of the executed workflow and enable future execution of the exact same workflow or modifications thereof.
   * The user is relieved from the need to know or manage the locations of intermediate or final files, or to transfer files between workflow steps.
     Workflow output file locations are determined by NeatSeq-Flow such that they are neatly organized in an intuitive directory structure.
   * NeatSeq-Flow's "Terminal Monitor" shows script execution in real time, and reports on execution errors immediately when they occur, thus facilitating user control on the workflow.
   * The platform can accommodate workflows of any degree of complexity, and efficiently executes them in a parallelized manner on the user's computer cluster.
   * Through an intuitive GUI, NeatSeq-Flow is fully accessible to non-programmers, without compromising power, flexibility and efficiency.
   * Users can easily create complex workflows from a variety of high-throughput sequencing applications made available by NeatSeq-Flow as independent modules.
     In addition, a generic module enables direct incorporation of applications without pre-built modules.
   * Advanced users can run NeatSeq-Flow through the command-line, and create their own modules using a provided template and only basic Python commands.
   * The modules and workflows are designed to be easily shared. In addition, the support for usage of CONDA environments enables easy portability and sharing of entire working environment for workflow execution.
 
*NeatSeq-Flow input and output:*
 The input for NeatSeq-Flow is high throughput sequencing raw or processed data and any other sequence data (e.g. FASTQ, FASTA, BAM, BED, VCF), or any other data defined by the user. The output is a neat directory structure with all NeatSeq-Flow-generated shell scripts, intermediate and result files of the executed analysis programs, STDERR and SDTOUT of all shell scripts, a log file, workflow documentation and a self-sustaining workflow backup for reproducibility.

*NeatSeq-Flow processing method:*
 NeatSeq-Flow operations are implemented as modules, where each module is a wrapper for one or a set of analysis programs. In addition, NeatSeq-Flow includes a generic module which can execute any analysis program.
 
 The user needs to specify the location of the workflow input files, the order of operations, and their parameters. NeatSeq-Flow then creates a hierarchy of shell scripts: a "master script" that calls all step-level scripts; step level scripts that call all sample- (or project-) level scripts; and sample- (and/or project-) level scripts that call the relevant analysis programs. The latter shell scripts contain the code for executing the analysis programs, including input and output file locations, user-defined parameters and dependency directives (i.e. which steps need to wait for previous steps before they start). Execution of the workflow takes place by running the workflow’s master shell script.
 
 Parallelization on cluster CPUs is applied both sample-wise as well as step-wise for steps that are on independent branches of the workflow. When necessary, large input files are splitted and the results merged after execution. The workflow output files are neatly organized by module, step and sample, making it easy to locate required information.
 All workflow elements necessary for its execution are copied into a dedicated backup directory, enabling reproducing the workflow at any time in the future.
 
*How NeatSeq-Flow saves time and reduces errors:*
 - NeatSeq-Flow helps to significantly reduce the time required for designing and executing multi-step analyses. Traditionally, the bioinformatician would write shell scripts that execute the different operations of his/her desired workflow, and send them sequentially to a computer cluster job scheduler for execution on distributed nodes. Creating and executing these script-based workflows is time consuming and error prone, especially when considering projects with hundreds or thousands of samples, with many steps and plenty of intermediate files, or when the same analysis has to be repeated with different combinations of programs and parameters.
 - With NeatSeq-Flow, the user only needs to specify the location of input files and the workflow design. Then, NeatSeq-Flow creates all necessary shell scripts and executes them on the cluster. The scripts contain directives enabling parallelization and ensuring sequential execution. This makes the analysis much faster than manually running scripts one after the other.
 - The user is relieved from the need to know or manage the locations of intermediate or final files, or to transfer files between workflow steps. Workflow output file locations are determined by NeatSeq-Flow such that they are neatly organized in an intuitive directory structure.
 - NeatSeq-Flow “Terminal Monitor” shows script execution in real time, and reports on execution errors immediately when they occur, thus facilitating user control on the workflow.
 - Repeating a workflow with different combinations of programs and/or with different parameters is as easy as opening the “parameter files” (either in the GUI or through a text editor) and modifying it, and then rerunning. Similarly, repeating a workflow with a different set of sample files only requires re-specifying the files in the GUI or modifying the “sample file” in Excel.
 
*NeatSeq-Flow development*
 NeatSeq-Flow, founded by Dr. Menachem Sklarz, has been developed at the Bioinformatics Core Facility of the National Institute of Biotechnology in the Negev, Ben-Gurion University of the Negev. The software is in operation since November 2014, and is still under continuous development. NeatSeq-Flow GUI has been developed by Dr. Liron Levin and is operational since June 2018.
 
 New modules and workflows are continuously added to NeatSeq-Flow, and our hope is that the growing community of NeatSeq-Flow users will help expand NeatSeq-Flow repository by contributing additional modules and workflows and extending existing ones.
   
Read more: `NeatSeq-Flow article on BioRXiv <https://www.biorxiv.org/content/early/2018/12/18/173005>`_

