.. _for_the_programmer_Adding_modules:


====================================================
Adding New Modules
====================================================

.. include:: links.rst

**Author:** Menachem Sklarz



.. contents:: Page Contents:
   :depth: 3
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

`minimap2 <https://github.com/lh3/minimap2>`_ is *A versatile pairwise aligner for genomic and spliced nucleotide sequences*. We will use it as an example for creating a new module for an analysis program.

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

Getting ready
------------------

Before actually programming the module, we would like to prepare the files for testing our new module.

As expected, we will call our new module ``minimap2``. We will use this name repeatedly in the following sections, and it is important to be consistent with the spelling.

#. Install and activate a NeatSeq-Flow conda environment
#. Make a directory for the project:

   .. code-block:: bash

      mkdir minimap2_module
      cd minimap2_module/

#. Make a temporary python directory for the module and transfer the file into it:

   .. code-block:: bash

      mkdir module_dir
      touch module_dir/__init__.py

#. Download the |general_template|, rename it to ``minimap2.py`` and move it into the ``module_dir``:

   .. code-block:: bash

      curl -L https://raw.githubusercontent.com/bioinfo-core-BGU/neatseq-flow/master/docs/source/_extra/extra/NeatSeqFlow_ModuleTemplate.py > minimap2.py
      mv minimap2.py module_dir/

#. We need a sample file which has a project-scope fasta file as a reference and sample-scope read files, in fastq format, to align to the reference. This is the simplest use-case of minimap2. Later, we will develop the module further and enable other sample file configurations.

   Download :download:`a similar sample file from here <https://raw.githubusercontent.com/bioinfo-core-BGU/neatseq-flow-modules/master/Workflows/sample_sets/PE_tabular.nsfs>` or create your own sample file. It should look like this (make sure the fields are TAB-separated!):

   .. code-block:: bash

      Title	minimap2_devel


      #Type	Path
      Nucleotide	/path/to/nucl.fna

      #SampleID	Type	Path
      Sample1	Forward	/path/to/Sample1.Forward.fq
      Sample1	Reverse	/path/to/Sample1.Reverse.fq
      Sample2	Single	/path/to/Sample2.Single.fq

#. Finally, we need a parameter file to play around with.

   #. Copy the :download:`Basic Preparation parameter file <https://raw.githubusercontent.com/bioinfo-core-BGU/neatseq-flow-modules/master/Workflows/Basic_Preparation.yaml>` (if using the link, you have to rename the file to ``minimap2_parameters.yaml``):

   .. code-block:: bash

      curl -L https://raw.githubusercontent.com/bioinfo-core-BGU/neatseq-flow-modules/master/Workflows/Basic_Preparation.yaml > minimap2_parameters.yaml

   #. Open the ``minimap2_parameters.yaml`` file in a text editor of choice, or with the GUI.
   #. Keep the ``Global_params`` and and ``Vars`` sections. You can remove the ``Documentation`` section.
   #. In the ``Step_params`` section, keep only the ``merge1`` section.
   #. Add a YAML-block for the ``minimap2`` module parameters:

      #. The instance name is arbitrary. I will call it ``Minimap2_basic``.
      #. The module name is up to us. We will call it ``minimap2``.
      #. The base is the import step, ``merge1`` in this case.
      #. The ``script_path`` section is less important for the moment. Set it to ``/path/to/minimap2``

   .. code-block:: bash

      Minimap2_basic:
          module:         minimap2
          base:           merge1
          script_path:    /path/to/minimap2

Choosing input files
-------------------------

Usually, ``minimap2`` takes 2 arguments: The reference and the sequences to align. For paired end reads in separate files, it takes 3 arguments:

   .. code-block:: bash

      minimap2 -ax sr ref.fa read1.fq read2.fq > aln.sam     # paired-end alignment

We will not try guessing where to take the input from. The user will have to specify the source of the reference file with ``reference:`` and the source of the reads with ``scope``.

The reference is always a nucleotide fasta file, stored in ``fasta.nucl``. The reads can be either fasta or fastq files.

**Usually, the user will align sample-scope reads to a project-scope reference**, so that will be the default behaviour. The user will be able to change that behaviour by specifying the following parameters in the instance YAML-block:

* ``reference``: Can be a path for a reference external to the workflow, or ``sample`` to use a sample-scope ``fasta.nucl`` file, or ``project`` to use a project-scope ``fasta.nucl`` file (= the default).
* ``scope``: Can be set to ``sample`` to use sample-scope reads (the default) or to ``project`` to use a project-scope reads.
* ``type2use``: Will determine whether the reads are in *fasta* or *fastq* format.

The reads can be either in ``fastq`` format or in ``fasta`` format. This can cause an issue when both reference and reads are project-scope fasta file! In the advance section below, we will try solving this issue. For now, we will not allow such a configuration.

It does not make sense to try aligning project-scope reads to a sample-scope reference. Therefore, we'll add a test for this scenario and stop execution if it occurs.

.. list-table:: Permitted scenarios
   :header-rows: 1

   * - Reference scope
     - Reads type
     - Reads scope
   * - External path
     - fasta/fastq
     - sample/project
   * - project
     - fasta
     - sample
   * - project
     - fastq
     - sample/project
   * - sample
     - fastq
     - sample

Add the following lines to the parameter file ``minimap2_parameters.yaml``, to suit the sample data configuration:

   .. code-block:: bash

        reference:      project
        scope:          sample
        type2use:       fastq

Determining output type
-----------------------------

According to the ``minimap2`` manual, passing a ``-a`` argument will make ``minimap2`` produce it's output in ``sam`` format, otherwise, the default, is a ``paf`` format. The ``-a`` argument can be passed by the user via the ``redirects`` YAML-block. We will have to look for it there and set the output file type appropriately!

Defining the module code
-----------------------------

Open the ``minimap2.py`` file in an editor of choice.

#. The file begins with a skeleton of a module deocumentation. Later on you can fill in the empty fields but for now just change ``MODULE_NAME`` to ``minimap2``.
#. Then, proceed to the definition of the module class. Find the line containing ``class Step_MODULENAME`` and change it to:

   .. code-block:: python

      class Step_minimap2(Step):

#. Delete the line defining ``auto_redirs``. It is not relevant for this module.
#. Finally, scroll to the definition of the ``step_specific_init()`` method.

Defining the ``step_specific_init()`` method
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. Important:: Before we proceed, let's make sure NeatSeq-Flow can find and use the ``minimap2`` module we have begun defining.

       .. code-block:: bash

          neatseq_flow.py -s sample_data.nsfs -p minimap2_parameters.yaml

    You should get the following error:

       .. code-block:: bash

            Reading files...
            WARNING: The following module paths do not exist and will be removed from search path: ../neatseq_flow_modules
            Preparing objects...
            Creating directory structure...
            Making step instances...
            Step minimap2 not found in regular path or user defined paths.
            An error has occurred. See comment above.

    The problem is that we have not told NeatSeq-Flow where to look for the new module! In line 7 of the parameter file, change the ``module_path`` definition to the full path to the ``module_dir`` you created above.

       .. code-block:: bash

          module_path:     /full/path/to/module_dir

    If you execute NeatSeq-Flow again, you should get a python ``SyntaxError``. That's great - it means the module was found!

The ``step_specific_init()`` function comes with a test on ``scope``. We'll leave it and the line defining the shell as *bash*.

Replace the section titled ``Various assertions`` with the following test:

   .. code-block:: python

        # Check type2use is defined and is fasta or fastq
        if "type2use" not in self.params:
            raise AssertionExcept("Please provide 'type2use' parameter!")
        if self.params["type2use"] not in ["fastq","fasta"]:
            raise AssertionExcept("'type2use' must be either 'fasta' or 'fastq'!")
        # Check reference is defined
        if "reference" not in self.params:
            raise AssertionExcept("Please provide 'reference' parameter!")
        # Check the various scenarios and combinations of reference, scope and type2use
        if self.params["reference"] == "project":
            if self.params["type2use"] == "fasta" and self.params["scope"] == "project":
                raise AssertionExcept("You can't have both project-scope 'reference' and project-scope reads!")
        elif self.params["reference"] == "sample":
            if self.params["scope"] == "project":
                raise AssertionExcept("You can't have sample-scope 'reference' and project-scope reads!")
            if self.params["type2use"] == "fasta":
                raise AssertionExcept("You can't have both sample-scope 'reference' and sample-scope fasta reads!")

Rerun NeatSeq-Flow and you will get a ``SyntaxError`` from a later part of the module definition. So let's fix it:

Defining the ``step_sample_initiation()`` method
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

In this function, we should check that the inputs we are expecting exist in the ``self.sample_data`` dictionary. For now, we'll use the default NeatSeq-Flow error checking mechanism. Just comment out the section titled ``# Testing a condition on each sample``.

.. Attention:: The first section in function ``step_sample_initiation()`` sets ``self.sample_list`` to a list of samples, depending on ``scope``. This is important because the ``build_scripts()`` function loops over ``self.sample_list``. Therefore, you do not need to provide a special treatment for different scopes in ``build_scripts()``. See implementation :ref:`below <build_scripts>`.

Rerun NeatSeq-Flow and you will get a NeatSeq-Flow error message as follows::

    In Minimap2_basic (project scope): Type "INPUT_FILE_TYPE" does not exists! Check scope and previous steps.
    An error has occurred. See comment above.
    Printing current JSON and exiting

This is OK. We have to work on the actual script building part!

.. _build_scripts:

Defining the ``build_scripts()`` method
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

The template comes with:

#. a loop on samples (as mentioned above, the sample list depends on the definition of ``scope``!)
#. a definition of ``sample_dir`` containing a directory path for the sample output files.
#. a call to ``set_spec_script_name()`` which must be there. An explanation is beyond the scope of this tutorial.
#. a call to ``local_start()``, which defines a ``use_dir`` which is a directory path in which the outputs will actually be written (see explanation on ``local_start()`` elsewhere)
#. finall, it also initializes ``self.script`` with ``self.script = ""``

Now, we will define three variables:

* ``referenece`` containing the path to the reference.
* ``reads`` containing a path (or paths) to the reads files.
* ``output`` containing the name of the output file.

In the section beginning with the comment ``# Define location and prefix for output files``, add the following lines to define the output file name (pay attention to indentation!):

   .. code-block:: python

        output_prefix = sample + ".minimap2"
        output_suffix = "sam" if "-a" in self.params["redir_params"] else "paf"
        output = ".".join([output_prefix,output_suffix])

**Note**:

* We decide on ``output_suffix`` based on the existence of ``-a`` in the ``self.params["redir_params"]`` dictionary keys!
* ``output`` is the filename without the directory path. That part is added later, by context.

**Defining the reference:**

Add these lines after the definition of the ``output``:

   .. code-block:: python

        # Define reference
        if self.params["reference"] == "project":
            reference = self.sample_data["project_data"]["fasta.nucl"]
        elif self.params["reference"] == "sample":
            reference = self.sample_data[sample]["fasta.nucl"]
        else:
            reference = self.params["reference"]

We set ``reference`` to the project fasta file, sample fasta file or path passed in the parameters, depending on the value of the ``reference`` parameter in ``self.params``.

**Defining the reads:**

The following lines will set the ``reads`` variable, depending on the value of ``type2use`` and on the types of reads files defined for the sample:

   .. code-block:: python

        # Define reads:
        if self.params["type2use"]=="fasta":
            reads = self.sample_data[sample]["fasta.nucl"]
        else: # self.params["type2use"]=="fastq":
            if "fastq.S" in self.sample_data[sample]:
                reads = self.sample_data[sample]["fastq.S"]
            else:
                reads = "{F} {R}".format(F=self.sample_data[sample]["fastq.F"],
                                         R=self.sample_data[sample]["fastq.R"])

If you want to check everything is alright, you can add the following lines and execute NeatSeq-Flow:

   .. code-block:: python

        print("reference: "+reference)
        print("reads: "+reads)
        print("output: "+use_dir+output)
        sys.exit()

You should get the definition of ``reference``, ``reads`` and ``output`` for the first sample. You can check various combinations of parameters in the parameter file and their effects on the output. When done, comment out the ``sys.exit()`` line.

**Building the script**

This can be done in to python flavours. It depends on your personal taste, so I will show both:

The following lines should replace the section after the comment ``# Get constant part of script:`` (line of code beginning with ``self.script +=``).

   .. code-block:: python

        self.script += self.get_script_const()
        self.script += "%s \\\n\t" % reference
        self.script += "%s \\\n\t" % reads
        self.script += "> %s \n\n" % (use_dir+output)

What this does is to add the following strings to ``self.script``:

#. The constant part including environment variable definition, ``script_path`` and ``redirects``.
#. the reference
#. the reads
#. the full path to the output file.

Alternatively, the same can be achieved with the following code:

   .. code-block:: python

        self.script += """
        {const} {reference} \\
            {reads} \\
            > {outp}
                    """.format(const=self.get_script_const(),
                               reference=reference,
                               reads=reads,
                               outp=use_dir+output)

**Putting output file ``sample_data``**

Finally, we need to place the output file in the ``sample_data`` dictionary so that downstream module instances can get the path and do further work on it.

After the ``# Put the output file/s in the sample_data dictionary`` comment, replace the two lines of code with the following lines:

   .. code-block:: python

        self.sample_data[sample][output_suffix] = sample_dir + output
        self.stamp_file(self.sample_data[sample][output_suffix])

We set the ``output_suffix`` slot for ``sample`` to the output file within ``sample_dir``. Remember that ``output_suffix`` is either ``sam`` or ``paf``. The ``sam`` slot is recognized by other modules, ``samtools`` for instance. So you can now put a ``samtools`` module instance downstream to your ``minimap2`` instance to perform sorting and indexing on the ``sam`` file, *e.g.*.

The second command makes the bash script record the resulting files md5 checksum in the workflow's ``logs/file_registration.txt`` file.

That's it. We're done with the basic version of the new ``minimap2`` module!!


