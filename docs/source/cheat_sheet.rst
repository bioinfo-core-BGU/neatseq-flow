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
Input Files
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

.. list-table:: Global parameters
   :widths: 50 50
   :header-rows: 1

   * - Parameter
     - Description
   * - ``Executor``
     - SGE, Local or SLURM. (Default: SGE)
   * - ``Qsub_q``
     - The cluster queue (or *partition*) to use. Default value for *qsub* ``–q`` parameter. **Required**
   * - ``Qsub_nodes``
     - Default nodes on which to execute jobs (Default: All nodes in queue)
   * - ``Qsub_opts``
     - Other parameters to pass to qsub
   * - ``Qsub_path``
     - The full path to qsub. Obtain by running ``which qsub`` (default: qsub is in path)
   * - ``Default_wait``
     - Default: 10. Leave as is
   * - ``module_path``
     - List of paths to repositories of additional modules. (Must be a **python** directory, containing ``__init__.py``
   * - ``job_limit``
     - Path to a file, defining parameters for limiting number of concurrent jobs, with the following line::
                     limit=1000 sleep=60
   * - ``conda``
     - ``path`` and ``env``, defining the path to the environment you want to use and its name (:ref:`see here <conda_param_definition>`).
   * - ``setenv``
     - Setting in global parameters is equivalent to setting ``setenv`` in all steps (see section `Additional parameters`_.
   * - ``export``
     - Synonymous with ``setenv``. Has the same effect.

.. Attention:: The default executor is SGE. For SLURM, ``sbatch`` is used instead of ``qsub``, *e.g.*  ``Qsub_nodes`` defines the nodes to be used by sbatch.

.. Attention:: If NeatSeq-Flow is executed from within a conda environment with both NeatSeq-Flow and it's modules installed, ``module_path`` will automatically include the modules repo. If not, you will have to give the path to the location where the modules were installed.


Vars section
--------------

Replacements to be made in the parameter file. In YAML format. Referred to in other sections by the dot-notification.

Example::

   Vars:
     paths:
       bwa:        /path/to/bwa
       samtools:   /path/to/samtools
     genome:       /path/to/genomeDir

In parameter section:


.. list-table:: Variables
   :header-rows: 1

   * - This...
     - Becomes this...
   * - ``{Vars.paths.bwa}``
     - /path/to/bwa
   * - ``{Vars.paths.samtools}``
     - /path/to/samtools
   * - ``{Vars.genome}``
     - /path/to/genomeDir



Step-wise parameters
-------------------------

A series of YAML blocks, one per workflow step to perform. Each block takes the following form::

   fqc_trimgal:
     module:         fastqc_html
     base:           trim_gal
     script_path:    {Vars.paths.fastqc}

Types of step parameters:

Required parameters
~~~~~~~~~~~~~~~~~~~~

.. list-table:: Required parameters
   :header-rows: 1

   * - Parameter
     - Description
   * - ``module``
     - The name of the module of which this step is an instance.
   * - ``base``
     - The name of the step(s) on which the current step is based (not required for the merge step, which is always first and single)
   * - ``script_path``
     - The full path to the script executed by this step.

Cluster parameters
~~~~~~~~~~~~~~~~~~~~~~

Passed in a ``qsub_params`` block.

.. list-table:: Cluster parameters
   :header-rows: 1

   * - Parameter
     - Description
   * - ``node``
     - A node or YAML list of nodes on which to run the step scripts (overrides global parameter Qsub_nodes)
   * - ``queue`` or ``-q``
     - Will limit the execution of the step’s scripts to this queue (overrides global parameter Qsub_q)
   * - ``-pe``
     - Will set the -pe parameter for all scripts for this module (see SGE qsub manual).
   * - ``-XXX: YYY``
     - Set the value of qsub parameter -XXX to YYY. This is a way to define other SGE parameters for all step scripts.


Additional parameters
~~~~~~~~~~~~~~~~~~~~~~

.. list-table:: Additional parameters
   :header-rows: 1

   * - Parameter
     - Description
   * - ``tag``
     - All instances downstream to the tagged instance will have the same tag. All steps with the same tag can be executed with one master script
   * - ``intermediate``
     - Will add a line to scripts/95.remove_intermediates.sh for deleting the results of this step
   * - ``setenv``
     - Set various environment variables for the duration of script execution. A string with format ``ENV="value for env1" ENV2="new value for env2"``
   * - ``export``
     - Is equivalent to setting ``setenv``. You can't set them both.
   * - ``precode``
     - Additional code to be added before the actual script. Rarely used
   * - ``scope``
     - Use sample- or project-wise files. Check per-module documentation for whether and how this parameter is defined
   * - ``sample_list``
     - Limit this step to a subset of the samples. See section `Sample list`_.
   * - ``conda``
     - Is used to define step specific conda parameters. The syntax is the same as for the global conda definition (see here).
   * - ``arg_separator``
     - Set the delimiter between program argument and value, *e.g.* '=' (Default: ‘ ‘)
   * - ``local``
     - Use a local directory for intermediate files before copying results to final destination in data dir.


Redirected parameters
~~~~~~~~~~~~~~~~~~~~~~~~~~~

Parameters to be redirected to the actual program executed by the step.

Redirected parameters are specified within a ``redirects:`` block. The parameter name must include the ``-`` or ``--`` required by the program defined in script_path.


Sample list
~~~~~~~~~~~~~~

The sample list enables limiting the instance scripts to a subset of the samples. It can be expressed in two ways:

1. A YAML list or a comma-separated list of sample names:

   .. code-block:: bash

      sample_list: [sample1, sample2]


2. By levels of a category (see section `Mapping file`_):

   .. code-block:: bash

      sample_list:
          category:  Category1
          levels:     [level1,level2]

For using all but a subset of samples, use ``exclude_sample_list`` instead of ``sample_list``.


Mapping file
===============

Passed to NeatSeq-Flow with ``--mapping``.

A tab-separated table with at least two columns:

1. Sample ID
2. First category name
3. Additional categories…

Example::

   #SampleID	Category1	Category2
   Sample1	A	C
   Sample2	A	D
   Sample3	B	C
   Sample4	B	D


-------------
Flow control
-------------

``merge``
============

Basic mode
--------------

NeatSeq-Flow will attempt to guess all the parameters it requires.

Example::

    Merge_files:
        module:         merge
        script_path:

Advanced mode
----------------

Define source and target slots and how to merge the files. Attempts to guess information left out by the user.

.. list-table:: ``merge`` parameters
   :header-rows: 1

   * - Parameter
     - Description
   * - ``src``
     - source slot.
   * - ``trg``
     - target slot
   * - ``ext``
     - merged file extension.
   * - ``scope``
     - the scope of the file
   * - ``script_path``
     - the code to use for merging, or one of the following values:
   * - ``pipe``
     - a command through which to pipe the file before storing.


.. list-table:: Special values
   :header-rows: 1

   * - Value
     - Description
   * - ``..guess..``
     - Guess (script_path, trg and ext)
   * - ``..import..``
     - Do not copy the file, just import it into its slot (only if one file defined for src).
   * - ``..skip..``
     - Do not import the file type.

Example::

    merge_data:
        module:         merge
        src:            [Forward,    Reverse, Nucl]
        trg:            [fastq.F,    fastq.R, fasta.nucl]
        script_path:    [..import.., cat,     'curl -L']
        ext:            [null,       null,    txt]
        scope:          [sample,     sample,  project]


``manage_types``
====================

Import raw data files into the data/ directory.

.. list-table:: ``manage_types`` values
   :header-rows: 1

   * - Value
     - Possible values
     - Description
   * - operation
     - add | del | mv | cp
     - The operation to perform on the file type.
   * - scope
     - project|sample
     - The scope on which to perform the operation. (For ‘mv’ and ‘cp’ this is the source scope)
   * - type
     -
     - The file type on which to perform the operation. (For ‘mv’ and ‘cp’ this is the source type)
   * - scope_trg
     - project|sample
     - The destination scope for ‘mv’ and ‘cp’ operations
   * - type_trg
     -
     - The destination type for ‘mv’ and ‘cp’ operations.
   * - Path
     -
     - For ``add`` operation, the value to insert in the file type.

Example::

   manage_types1:
     module:   manage_types
     base:   trinity1
     script_path:
     scope:[project, sample, sample, project]
     operation: [mv,del,cp,add]
     type: [fasta.nucl, fasta.nucl, fastq.F, bam]
     type_trg:   [transcripts.nucl, None ,fastq.main, None]
     scope_trg:   sample
     path:   [None, None, None, /path/to/mapping.bam]

``merge_table``
=====================

Used for concatenating tables from samples into one project table, or for concatenating tables from sample sub-samples, according to a mapping file. Any text file can be merged in this way.

.. list-table:: ``merge_table`` parameters
   :header-rows: 1

   * - Parameter
     - Description
   * - header
     -  The number of header lines the files contain.
   * - add_filename
     -  Set to append  the source filename to each line in the resulting file.
   * - ext
     -  The extension to use in the resulting file. If not specified, uses merged file exts.
   * - scope
     -  project or group, if group, you must also specify category.


Example::

   merge_blast_tables:
       module:  merge_table
       base:      merge1
       script_path:
       type:  [blast.prot,fasta.nucl]
       header: 0
       ext:  [out,fna]
