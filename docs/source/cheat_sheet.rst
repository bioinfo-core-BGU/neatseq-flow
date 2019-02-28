==========================================
NeatSeq-Flow Cheat-Sheet
==========================================

.. include:: links.rst

**Author:** Menachem Sklarz

.. contents:: Page Contents:
   :depth: 5
   :local:
   :backlinks: top


-------------
Files
-------------

Sample file
============

Passed to NeatSeq-Flow with the ``-s`` argument.

Includes four sections:


Title
-----------

A title for the project::

   Title	Project_title

Project file information
------------------------------

Two tab-separated columns:

1. File type
2. File path

::

   #Type	Path
   Nucleotide	/path/to/genome.fasta

Samples file information
---------------------------

Three tab-separated columns:

1. Sample ID
2. File type
3. File path

Additional columns will be ignored::

   #SampleID	Type	Path	lane
   Sample1	Forward	/path/to/Sample1_F1.fastq.gz	1
   Sample1	Forward	/path/to/Sample1_F2.fastq.gz	2
   Sample1	Reverse	/path/to/Sample1_R1.fastq.gz	1
   Sample1	Reverse	/path/to/Sample1_R2.fastq.gz	2


ChIP-seq
-----------------

Define ChIP and Control ('input') pairs::

    Sample_Control	anti_sample1:input_sample1
    Sample_Control	anti_sample2:input_sample2



Parameter file
===================

Passed to NeatSeq-Flow with the ``-p`` argument.

YAML-formatted file with the following three sections.

.. Tip:: The ``Vars`` section is recommended but not compulsory.

Global parameters section
------------------------------

.. csv-table:: Global parameters
   :header: "Parameter", "Description"

   "Executor","SGE, Local or SLURM. (Default: SGE)"
   "Qsub_q","Default value for qsub ``–q`` parameter"
   "Qsub_nodes","Default nodes on which to execute jobs"
   "Qsub_opts","Other parameters to pass to qsub"
   "Qsub_path","The full path to qsub. Obtain by running ``which qsub`` (default: qsub is in path)"
   "Default_wait","Default: 10. Leave as is"
   "module_path","List of paths to repositories of additional modules."
   "job_limit","Path to a file, defining parameters for limiting number of concurrent jobs, with the following line::
                  limit=1000 sleep=60"
   "conda","``path`` and ``env``, defining the path to the environment you want to use and its name."

.. Attention:: The default executor is SGE. For SLURM, ``sbatch`` is used instead of ``qsub``, *e.g.*  ``Qsub_nodes`` defines the nodes to be used by sbatch.


.. list-table:: Frozen Delights!
   :widths: 15 10 30
   :header-rows: 1

   * - Treat
     - Quantity
     - Description
   * - Albatross
     - 2.99
     - On a stick!
   * - Crunchy Frog
     - 1.49
     - If we took the bones out, it wouldn't be |
         crunchy, now would it?
   * - Gannet Ripple
     - 1.99
     - On a stick!

Vars section
~~~~~~~~~~~~~~~~~~~
Step-wise parameters
~~~~~~~~~~~~~~~~~~~~~

Mapping file
-------------

A tab-separated table with at least two columns:

1. Sample ID
2. First category name
3. Additional categories…

::

   #SampleID	Category1	Category2
   Sample1	A	C
   Sample2	A	D
   Sample3	B	C
   Sample4	B	D


Flow control
====================================
