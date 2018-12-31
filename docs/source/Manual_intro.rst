============
Introduction
============

.. include:: links.rst

**Author:** Menachem Sklarz

.. contents:: Page Contents:
   :depth: 2
   :local:
   :backlinks: top

The following sections provide a detailed description of **NeatSeq-Flow** usage.

**NeatSeq-Flow** is executed in 3 steps:

1. Specification of workflow design and the input files
2. Generation of shell scripts
3. Workflow execution

In the first step, the workflow design and the input file specifications are written to a "parameter" and a "sample" file, respectively. These files can be created manually (in YAML format), or through the GUI.

In the script generation step, NeatSeq-Flow creates a set of directories in the workflow main directory (described in the following pages) with all necessary shell scripts for the workflow execution, and with dedicated directories for result files and additional information.

NeatSeq-Flow's "Terminal Monitor" enables tracking the execution process in real time, and reports on execution errors immediately when they occur. The monitor, too, is descibed in the pages below.

NeatSeq-Flow can be used in two ways: with the GUI or from the command line. The pages in this section describe usage of both methods.
