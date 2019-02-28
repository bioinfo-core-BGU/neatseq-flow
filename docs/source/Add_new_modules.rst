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

In order to incorporate in a wrokflow analysis programs which do not yet have modules, one can proceed in two ways:

1. **Use the generic module**

   This method is preferable for quickly getting a working workflow without the need to create a new module for the program. However, it requires the specification of several additional parameters in the workflow design step, and is less recommended for programs that are planned to be re-used many times, in different scenarios, in the future.  

   
2. **Create a new module**

   Creating modules is quite easy, and requires only basic Python programming knowledge. Still, please make sure a module does not already exist for the program you want to run before creating a new module.
   
   It is our hope that the community of users will provide access to a wide range of modules, making the process of developing new workflows more straightforward for non-programmers.

   This section provides detailed instructions for writing modules. The idea is to use the ``sample_data`` dictionary for input and output files while leaving as many of the other parameters as possible to the user. This will enable as much flexibility as possible while relieving the user of the need to track input and output files.
   
.. Note:: It is recommended to go over the :ref:`how_neatseqflow_works` page before writing new modules.
   

Steps in writing **NeatSeq-Flow** modules
===========================================

Preparing the module file
-----------------------------

#. Choose a name for the module. *e.g.* ``bowtie2_mapper``
#. Decide which level the module will work on: samples or project-wide?

    - Use the |sample_template| if it works on the sample level.
    - Use the |project_template| if it works on the project level.

#. Change the name of the template file to to ``<module_name>.py``. 
#. Make sure the file is within a directory which includes an empty ``__init__.py`` file. This directory is passed to **NeatSeq-Flow** through the ``module_path`` global parameter (see :ref:`parameter_file_definition`)
#. Change the class name to ``Step_<module_name>`` in the line beginning with ``class Step_...``. Make sure ``<module_name>`` here is identical to the one you used in the filename above.


Things to modify in the actual code
-------------------------------------

#. In ``step_specific_init()``, set ``self.shell`` to `csh` or `bash`, depending on the shell language you want your scripts to be coded in (It is best to use ``bash`` because it will work with CONDA. See |conda|).
#. In ``step_sample_initiation()`` method, you can do things on the ``sample_data`` structure before actual script preparing, such as assertion checking (:ref:`assert_and_warn`) to make sure the data the step requires exists in the ``sample_data`` structure.
#. ``build_scripts()`` is the actual place to put the step script building code. See :ref:`build_scripts_help`.
#. ``make_sample_file_index()`` is a place to put code that produces an index file of the files produced by this step (BLAST uses this function, so you can check it out in ``blast.py``)
#. In ``create_spec_preliminary_script()`` you create the code for a script that will be run before all other step scripts are executed. If not defined or returns nothing, it will be ignored (i.e. you can set it to ``pass``). This is useful if you need to prepare a database, for example, before the other scripts use it.
#. In ``create_spec_wrapping_up_script()`` you create the code for a script that will be run after all other step scripts are executed. If not defined or returns nothing, it will be ignored (i.e. you can set it to "pass"). This is the place to call ``make_sample_file_index()`` to create an index of the files produced in this step; and to call a script that takes the index file and does some kind of data agglomeration.
#. It is highly recommended to create an instance-scope list of the redirected parameters that the user should **not** pass because they are dealt with by your module. The list should be called ``self.auto_redirs`` and you should place it directly after the class definition line (*i.e.* the line beginning with ``class Step_...``). After instance creation, the list is checked by **NeatSeq-Flow** to make sure the user did not pass forbidden parameters.

.. Tip::
    Most Linux programs separate flags and arguments with a space, *e.g.* ``head -n 20``, and this is the default behaviour for **NeatSeq-Flow**. However, some programs require a different separator, such as ``=``, for example the PICARD suite. If your module wraps such a program, set ``self.arg_separator`` to the separator symbol, *e.g.*::

        self.arg_separator = "="


.. _build_scripts_help:

Instructions for ``build_scripts()`` function
------------------------------------------------

- If sample-level scripts are required, the function should contain a loop:

  .. code-block:: python

    for sample in self.sample_data["samples"]:

- Set ``self.script`` to contain the command/s executed by the script (This will go inside the ``for`` loop for sample-level steps)

    1. Initialize it with ``self.script = ""``
    2. Calling ``self.script += self.get_script_const()`` will add the ``setenv`` parameter, if it exists; the ``script_path`` parameter and the redirected parameters. Then all that remains is to see to input and output parameters.
    3. The input parameter, typically ``-i``, is usually based on the sample data structure, *e.g.*:

       .. code-block:: python

            self.script += "-i {inp} \\\n\t".format(inp=self.sample_data[sample]["fasta.nucl"])

       .. Note:: The ``"\\\n\t"`` at the end of the string makes the final script more readable.


       .. tip:: As mentioned above, module instances can be based on more than one instance. *i.e.* *i* can be based on *j,k*. It was stated that in this case, if *j* and *k* instances write to the same slot, *i* will have access only to the version created by *j*.

          However, you can write modules such that *i* has access to the same slot both in *k* and in *j*: Previous versions of the ``sample_data`` dict are available in the dictionary returned by  ``self.get_base_sample_data()`` in the module class. The dictionary is keyed by the base instance name. This can be used to access *overwridden* versions of files created by instances upstream to the present module.

          For example, if **base** contains the name of the base instance (*e.g.* **merge1**), you can access the base's sample data as follows:

          .. code-block:: python

              self.get_base_sample_data()[base]

          And accessing file ``fasta.nucl`` in sample ``sample1`` from base ``merge1`` can be done with the following command:

          .. code-block:: python

              self.get_base_sample_data()["merge1"]["sample1"]["fasta.nucl"]


    4. The output parameter (typicall ``-o``) should be set to a filename within ``self.base_dir``. If the step is a sample-level step, get a directory for the output files by calling ``self.make_folder_for_sample(sample)``.

       The following code sets the output parameter ``-o`` to ``<sample_dir>/<sample_name>.output.bam``.

       .. code-block:: python

            sample_dir = self.make_folder_for_sample(sample)
            output_filename = sample_dir + sample + ".output.bam"
            self.script += "-o {outp} \n\n".format(outp=output_filename)

       .. Tip:: Function ``self.make_folder_for_sample(sample)`` will return ``self.base_dir`` if ``sample`` is set to ``"project_data"``.

- Place the output file somewhere in the ``sample_data`` structure. `e.g.`:

  .. code-block:: python

        self.sample_data[sample]["bam"] = output_filename
    
- If the output is a standard file, *e.g.* BAM or fastq files, put them in the respective places in ``sample_data``. See documentation for similar modules to find out the naming scheme. Otherwise, use a concise file-type descriptor for the file and specify the location you decided on in the module documentation.

  For standard file types, you should use the appropriate slots (check out similar modules for proper slots to use).

  .. csv-table:: Slots for commonly used files
      :header: "File type", "Scope", "Slot"

      "f  astq", "Sample", ``sample_data[<sample>]['fastq.F|fastq.R|fastq.S']``
      "fasta", "Sample", ``sample_data[<sample>]['fasta.nucl|fasta.prot']``
      "fasta", "Project", ``sample_data["project_data"]['fasta.nucl|fasta.prot']``
      "SAM", "Sample", ``sample_data[<sample>]['sam']``
      "BAM", "Sample", ``sample_data[<sample>]['bam']``
      "Aligner index", "Sample", ``sample_data[<sample>][<aligner name>_index']``
      "Aligner index", "Project", ``sample_data["project_data"][<aligner name>_index']``
      "Aligner reference", "Sample", ``sample_data[<sample>]['reference']``
      "GFF", "Sample", ``sample_data[<sample>]['gff']``
      "GFF", "Project", ``sample_data["project_data"]['gff']``



- You can add more than one command in the ``self.script`` variable if the two commands are typically executed together. See ``samtools`` module for an example.
 
- The function should end with the following line (within the sample-loop, if one exists):

  .. code-block:: python

    self.create_low_level_script()

- That, and a little bit of debugging, usually, is all it requires to add a module to the pipeline. 

.. Attention:: 
    The steps above assume you don't want to support the option of working on a local directory and transferring the finished results to the final location (see :ref:`local parameter <local_step_parameter>`). If you **do** want to support it, you have to create a temporary directory with:

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

.. Tip:: When calling ``AssertionExcept`` and ``self.write_warning``, setting ``sample`` to ``"project_data"`` will have the same effect as not passing ``sample``. See the

