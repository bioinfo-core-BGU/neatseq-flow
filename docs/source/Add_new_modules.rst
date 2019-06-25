.. _for_the_programmer_Adding_modules:


====================================================
Adding New Modules
====================================================

.. include:: links.rst

**Author:** Menachem Sklarz



.. contents:: Page Contents:
   :depth: 2
   :local:
   :backlinks: top



.. _adding_modules:

Introduction
================

In NeatSeq-Flow, the workflow parameter file describes the steps to be performed in the workflow. Each step involves executing a command-line program on the file types managed by the workflow. The description of each step is in the form of a YAML-format block defining the program to be used and the arguments that should be passed to the program. Occasionally, steps include executing further, downstream analyses following execution of the main program. The definition block is concise and readable in that much of the nuts-and-bolts of data input and output are managed behind the scenes in the step **Module**.

However, often no module exists for a program we would like to include in our workflow. In order to incorporate analysis programs which do not yet have modules, one can proceed in two ways:

1. **Use one of the generic modules**

   This method is preferable for quickly getting a working workflow without the need to create a new module for the program. However, it requires the specification of several additional parameters in the workflow design step, and is less recommended for programs that are planned to be re-used many times, in different scenarios, in the future.  

   
2. **Create a new module**

   Creating modules is quite easy, and requires only basic Python programming knowledge. Still, please make sure a module does not already exist for the program you want to run before creating a new module.
   
   It is our hope that the community of users will provide access to a wide range of modules, making the process of developing new workflows more straightforward for non-programmers.

   This section provides detailed instructions for writing modules for analysis-programs and scripts for which no module exists.

.. The idea is to use the ``sample_data`` dictionary for input and output files while leaving as many of the other parameters as possible to the user. This will enable as much flexibility as possible while relieving the user of the need to track input and output files.
   
.. Note:: It is recommended to go over the :ref:`how_neatseqflow_works` page before writing new modules.
   

Steps in writing **NeatSeq-Flow** modules
===========================================

.. Modules are python objects which NeatSeq-Flow can find and load into it's script-generating engine. The module is loaded only if a step in the workflow uses it, *i.e.* the module name is passed via the ``module`` field in the step YAML-block.

Modules are python objects which NeatSeq-Flow can find and load into it's script-generating engine. Each step is an instance of a module, defined by passing the module name via the ``module`` field in the instance YAML-block.

.. .. Attention:: The module python classes are loaded on-the-fly when instances of the module exist. They do not

The following conditions have to be met for NeatSeq-Flow to find and load the module:

#. The module is stored in a file called ``<module_name>.py`` where ``<module_name>`` is the module name.
#. The class defined in the file is called ``Step_<module_name>``.
#. The file is located in a directory containing an empty ``__init__.py`` file.
#. This directory is in the directories list passed to **NeatSeq-Flow** through the ``module_path`` global parameter (see :ref:`parameter_file_definition`).

.. Tip:: The directory containing the ``<module_name>.py`` file can be nested within other directories to any depth, and only the upper level needs to be provided via ``module_path``, provided that each directory in the directory structure contains and empty ``__init__.py`` file.

Generally speaking, modules are called in three contexts by NeatSeq-Flow:

#. Function ``step_specific_init()`` is called when the class is constructed.
#. Function ``step_sample_initiation()`` is called when the class is exposed to the ``sample_data`` dictionary of file types available to the class.
#. Function ``build_scripts()`` is then called to actually perform the script-building.

The first two functions should be used for input checking. Making sure the user supplied all the required parameters, and giving clear error messages when not, will make it easier for the user to quickly get the module instance up-and-running.

The easiest way to write a new module is to use one of the template files and make only the analysis-program-specific modifications.

Preparing the module file
-----------------------------

#. Choose a name for the module. *e.g.* ``bowtie2_mapper``. **Make sure the name is not already in use**.
#. Decide which level the module will work on: samples or project-wide?

    - Use the |general_template| if it can work on both sample and project levels.
    - Use the |sample_template| if it works on the sample level.
    - Use the |project_template| if it works on the project level.

#. Change the name of the template file to to ``<module_name>.py``. 
#. Make sure the file is within a directory which includes an empty ``__init__.py`` file. This directory is passed to **NeatSeq-Flow** through the ``module_path`` global parameter (see :ref:`parameter_file_definition`)
#. Change the class name to ``Step_<module_name>`` in the line beginning with ``class Step_...``. Make sure ``<module_name>`` here is identical to the one you used in the filename above.


Places to modify in the actual code
-------------------------------------

Function ``step_specific_init()``
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

As mentioned above, this function is where the parameters the user has passed via the YAML-block are checked.

The parameters are containd in a dictionary called ``self.params``. For example, the program path is contained in ``self.params["script_path"]`` and redirected arguments are included in ``self.params["redirects"]`` dictionary.

Making sure the YAML block is correctly formatted saves the user time - the error message will be displayed before any script generation is done.

Additionally, clearly worded error messages will make it easier for the user to understand what he did wrong.

#. Set ``self.shell`` to `csh` or `bash`, depending on the shell language you want your scripts to be coded in (It is best to use ``bash`` because it will work with CONDA. See |conda|).
#. Check the user has passed all the parameters you expect him to pass. You do not have to check the general NeatSeq-Flow syntax, such as ``module`` and ``script_path`` fields. For example, if you expect the user to supply a ``type2use`` field, check ``type2use`` exists in ``self.params`` and raise an ``AssertionException`` (see :ref:`assert_and_warn`) if not.

Function ``step_sample_initiation()``
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

This function is called after previous steps have made their modifications on the file-type dictionary, ``self.sample_data``.

Here, it is recommended to put code checking the existence of all file types the module expects. *e.g.* the ``samtools`` module checks that a ``bam`` or ``sam`` file exist in the scope required by the user. NeatSeq-Flow has automatic file-type checking but having dedicated tests with clear error messages makes it easier for the user to pinpoint the problem.

For raising errors, please use the assertion-checking machinery (:ref:`assert_and_warn`) to make sure the error messages are displayed in NeatSeq-Flow fashion.

.. Function ``build_scripts()``
.. ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
..
.. is the actual place to put the step script building code. See :ref:`build_scripts_help`.



.. _build_scripts_help:

Function ``build_scripts()``
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

This is the place to put the script-building code.

Building the script is done in several stages:

#. Clear the script in ``self.script``.
#. Assemble the command(s) to be executed in ``self.script``.
#. Create the final script for execution, including the extra code added automatically by NeatSeq-Flow.
#. Modify ``sample_data`` to reflect the changes and new file produced by the command.

If the script is assembled per-sample, the three steps above should be repeated for each sample, in a loop:

  .. code-block:: python

    for sample in self.sample_data["samples"]:

.. Attention:: For modules that can operate both on project-scope and sample-scope files, you can use a single loop for both options. See |general_template| for how this is done.

Set ``self.script`` to contain the command/s executed by the script (This will go inside the ``for`` loop for sample-level steps)

1. Initialize it with ``self.script = ""``
2. Calling ``self.script += self.get_script_const()`` will add the ``setenv`` parameter, if it exists; the ``script_path`` parameter and the redirected parameters. Then all that remains is to see to input and output parameters.
3. The input parameter, typically ``-i``, is usually based on the sample data structure, *e.g.*:

   .. code-block:: python

        self.script += "-i {inp} \\\n\t".format(inp=self.sample_data[sample]["fasta.nucl"])

   .. Note:: The ``"\\\n\t"`` at the end of the string makes the final script more readable.

4. The output parameter (typicall ``-o``) should be set to a filename within ``self.base_dir``. If the step is a sample-level step, get a directory for the output files by calling ``self.make_folder_for_sample(sample)``.

   For example, the following code sets the output parameter ``-o`` to ``<sample_dir>/<sample_name>.output.bam``.

   .. code-block:: python

        sample_dir = self.make_folder_for_sample(sample)
        output_filename = sample_dir + sample + ".output.bam"
        self.script += "-o {outp} \n\n".format(outp=output_filename)

   .. Tip:: Function ``self.make_folder_for_sample(sample)`` will return ``self.base_dir`` if ``sample`` is set to ``"project_data"``.

   .. Tip:: You can add more than one command in the ``self.script`` variable if the two commands are typically executed together. See ``trinity`` module for an example.

Place the output file somewhere in the ``sample_data`` structure. `e.g.`:

  .. code-block:: python

        self.sample_data[sample]["bam"] = output_filename
    
  .. Attention:: If the output is a standard file, *e.g.* BAM or fastq files, put them in the respective places in ``sample_data``. See documentation for similar modules to find out the naming scheme. Otherwise, use a concise file-type descriptor for the file and **specify the location you decided on in the module documentation**.

      .. csv-table:: Slots for commonly used files
          :header: "File type", "Scope", "Slot"

          "fastq", "Sample", ``sample_data[<sample>]['fastq.F|fastq.R|fastq.S']``
          "fasta", "Sample", ``sample_data[<sample>]['fasta.nucl|fasta.prot']``
          "fasta", "Project", ``sample_data["project_data"]['fasta.nucl|fasta.prot']``
          "SAM", "Sample", ``sample_data[<sample>]['sam']``
          "BAM", "Sample", ``sample_data[<sample>]['bam']``
          "Aligner index", "Sample", ``sample_data[<sample>][<aligner name>.index']``
          "Aligner index", "Project", ``sample_data["project_data"][<aligner name>.index']``
          "Aligner reference", "Sample", ``sample_data[<sample>]['reference']``
          "GFF", "Sample", ``sample_data[<sample>]['gff']``
          "GFF", "Project", ``sample_data["project_data"]['gff']``

Creating the final executable script is done by adding the following line (within the sample-loop, if one exists):

  .. code-block:: python

    self.create_low_level_script()

That, and a little bit of debugging, usually, is all it requires to add a module to NeatSeq-Flow.

   .. tip:: As mentioned above, module instances can be based on more than one instance. *i.e.* *i* can be based on *j,k*. It was stated that in this case, if *j* and *k* instances write to the same slot, *i* will have access only to the version created by *j*.

      However, you can write modules such that *i* has access to the same slot both in *k* and in *j*: All instance versions of the ``sample_data`` dict are available in the dictionary returned by  ``self.get_base_sample_data()`` in the module class. The dictionary is keyed by the base instance name. This can be used to access *overwridden* versions of files created by instances upstream to the present module.

      For example, if **base** contains the name of the base instance (*e.g.* **merge1**), you can access the base's sample data as follows:

         .. code-block:: python

            self.get_base_sample_data()[base]

      And accessing file ``fasta.nucl`` in sample ``sample1`` from base ``merge1`` can be done with the following command:

      .. code-block:: python

         self.get_base_sample_data()["merge1"]["sample1"]["fasta.nucl"]

.. Attention:: 
    The description above assumes you don't want to support the option of working on a local directory and transferring the finished results to the final location (see :ref:`local parameter <local_step_parameter>`). If you **do** want to support it, you have to create a temporary directory with:

    .. code-block:: python

       use_dir = self.local_start(sample_dir)
        
    or:

    .. code-block:: python

       use_dir = self.local_start(self.base_dir)

    Use ``use_dir`` when defining the script, but use ``sample_dir`` and ``self.base_dir`` when assigining to ``self.sample_data`` (see the templates for examples).
    
    Finally, add the following line before ``self.create_low_level_script()``:
    
    .. code-block:: python

       self.local_finish(use_dir,sample_dir)
        
    **Note:** The procedure above **enables the user to decide** whether to run locally by adding the ``local`` parameter to the step parameter block in the parameter file!


Function ``make_sample_file_index()``
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
This function is a place to put code that produces an index file of the files produced by this step (BLAST uses this function, so you can check it out in ``blast.py``). The index file can be used by downstream instances or by ``create_spec_wrapping_up_script()`` (see below).

Function ``create_spec_preliminary_script()``
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Here, you can create the code for a script that will be run **before all other** scripts are executed. If not defined or returns nothing, it will be ignored (i.e. you can set it to ``pass``). This is useful if you need to prepare a database, for example, before the other scripts use it.

Function ``create_spec_wrapping_up_script()``
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Here, you create the code for a script that will be run **after all other** step scripts are executed. If not defined or returns nothing, it will be ignored (i.e. you can set it to "pass"). This is the place to call ``make_sample_file_index()`` to create an index of the files produced in this step; and to call a script that takes the index file and does some kind of data agglomeration.

.. Attention:: It is highly recommended to create an instance-scope list of the redirected parameters that the user should **not** pass because they are dealt with by your module. The list should be called ``self.auto_redirs`` and you should place it directly after the class definition line (*i.e.* the line beginning with ``class Step_...``). After instance creation, the list is checked by **NeatSeq-Flow** to make sure the user did not pass forbidden parameters.

.. Tip::
   Most Linux programs separate flags and arguments with a space, *e.g.* ``head -n 20``, and this is the default behaviour for **NeatSeq-Flow**. However, some programs require a different separator, such as ``=``, for example the PICARD suite. If your module wraps such a program, set ``self.arg_separator`` to the separator symbol, *e.g.*::

      self.arg_separator = "="




.. _assert_and_warn:

Exceptions and Warnings
------------------------

When programming a module, the programmer usually has certain requirements from the user, for instance parameters that are required to be set in the parameter file, sets of parameters which the user has to choose from and parameters which can take only specific values.

This kind of condition is typically programmed in python using assertions.

In **NeatSeq-Flow**, assertions are managed with the ``AssertionExcept`` exception class. For testing the parameters, create an ``if`` condition which raises an ``AssertionExcept``. The arguments to ``AssertionExcept`` are as follows:

#. An error message to be displayed. ``AssertionExcept`` will automatically add the step name to the message.
#. Optional: The sample name, in case the condition failed for a particular sample (e.g. a particular sample does not have a BAM file defined.)

A typical condition testing code snippet:

.. code-block:: python

    for sample in self.sample_data["samples"]:
        if CONDITION:
            raise AssertionExcept(comment = "INFORMATIVE error message\n", sample = sample)

If you only want to warn the user about a certain issue, rather than failing, you can induce **NeatSeq-Flow** to produce a warning message with the same format as an ``AssertionExcept`` message, as follows:

.. code-block:: python

    for sample in self.sample_data["samples"]:
        if CONDITION:
            self.write_warning(warning = "Warning message.\n", sample = sample, admonition = "WARNING")

.. note:: As for ``AssertionExcept``, the ``sample`` argument is optional.

.. Tip:: When calling ``AssertionExcept`` and ``self.write_warning``, setting ``sample`` to ``"project_data"`` will have the same effect as not passing ``sample``.


Example: ``minimap2`` module
===========================================

:ref:`minimap2 <https://github.com/lh3/minimap2>` is *A versatile pairwise aligner for genomic and spliced nucleotide sequences*. We will use it as an example for creating a new module for an analysis program.

In the ``minimap2`` manual, it says:

   Without any options, minimap2 takes a reference database and a query sequence file as input and produce approximate mapping, without base-level alignment (i.e. no CIGAR), in the PAF format:

   .. code-block:: bash

      minimap2 ref.fa query.fq > approx-mapping.paf

Additional arguments go between the program and the arguments, *e.g*:

   .. code-block:: bash

      minimap2 -ax map-pb ref.fa pacbio.fq.gz > aln.sam

There are 5 use-cases for the program:

#. Map long noisy genomic reads
#. Map long mRNA/cDNA reads
#. Find overlaps between long reads
#. Map short accurate genomic reads
#. Full genome/assembly alignment

We will start by building a module for use cases 1, 2 and 4. Later, we will improve the module to also enable 3 and 5.


Determine input files
-------------------------

Usually, ``minimap2`` takes 2 arguments: The reference and the sequences to align. For paired end reads in separate files, it takes 3 arguments:

   .. code-block:: bash

      minimap2 -ax sr ref.fa read1.fq read2.fq > aln.sam     # paired-end alignment

We will not try guessing where to take the input from. The user will have to determine the source of the reference file with ``reference:`` and the source of the reads with ``scope``.

The reference is always a nucleotide fasta file, stored in ``fasta.nucl``. The reads can be either fasta or fastq files.

Usually, the user will align sample-scope reads to a project-scope reference, so that will be the default behaviour. The user will be able to change that behaviour by specifying the following parameters in the instance YAML-block:

* ``reference``: Can be a path for a reference external to the workflow, or ``sample`` to use a sample-scope ``fasta.nucl`` file, or ``project`` to use a project-scope ``fasta.nucl`` file (= the default).
* ``scope``: Can be set to ``sample`` to use sample-scope reads (the default) or to ``project`` to use a project-scope reads.

The reads can be either in ``fastq`` format or in ``fasta`` format.

It does not make sense to try aligning project-scope reads to
The ``reference`` can be either a path to a reference, or ``sample`` for a

Determine output file type
-------------------------------

