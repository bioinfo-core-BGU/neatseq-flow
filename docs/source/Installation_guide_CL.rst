=================================
Installation Guide (Command Line)
=================================

.. include:: links.rst

**Author:** Menachem Sklarz

This guide is for users wishing to use NeatSeq-Flow through the Linux command line.

.. contents:: Page Contents:
   :depth: 2
   :local:
   :backlinks: top


.. _General_section_install:

General
=======

Since most high-throughput sequencing analysis programs are Linux based, NeatSeq-Flow is typically used on a Linux operating system, preferably (but not necessarily) on a computer cluster.
However, the workflow design and script generation steps can be run on any operating system that has Phyton installed.

NeatSeq-Flow can be installed in one of two ways:

#. Installation using **Conda** (recommended)
#. Installation without Conda.

**Conda** allows easy installation of NeatSeq-Flow in one go. For selected workflows, as well as for the NeatSeq-Flow tutorials, we also provide entire Conda environments which include NeatSeq-Flow with all necessary analysis programs.

.. Users wishing to install NeatSeq-Flow with conda need miniconda2.

.. For users wishing to install NeatSeq-Flow without conda, the requirements are: git; pip; pyyaml and bunch python packages; and the specific analysis programs needed for the desired workflow.

   
.. _install_with_conda:


Install and execute NeatSeq-Flow **with Conda**
==============================================================

.. Attention:: The following instructions are for use with the ``bash`` shell!

#. Install `Miniconda`_ (for python version 2.7).

.. Important::    **If you do not have git installed**, please install it with the following command:

       .. code-block:: bash

            conda install -c anaconda git

#. Download the **NeatSeq-Flow** |conda_env| using `curl` or `wget`:

   .. code-block:: bash

      curl http://neatseq-flow.readthedocs.io/en/latest/extra/NeatSeq_Flow_conda_env.yaml > NeatSeq_Flow_conda_env.yaml

   .. code-block:: bash

      wget http://neatseq-flow.readthedocs.io/en/latest/extra/NeatSeq_Flow_conda_env.yaml

#. Create an environment:

   .. code-block:: bash

      conda  env create -f NeatSeq_Flow_conda_env.yaml

   .. Note:: For some versions of conda, you might have to replace ``conda env`` with ``conda-env``. If the command above does not work, try the following command:

        .. code-block:: bash

            conda-env create -f  NeatSeq_Flow_Tutorial_Install.yaml

#. Activate the environment:

   .. code-block:: bash

      source activate NeatSeq_Flow

#. Execute the following command to tell **NeatSeq-Flow** where the base conda installation is located:

   .. code-block:: bash

      export CONDA_BASE=$(conda info --root)

#. Make a directory for your project and change into it:

   .. code-block:: bash

      mkdir first_neatseq_flow_proj; cd first_neatseq_flow_proj

#. Execute **NeatSeq-Flow**:

   .. code-block:: bash

      neatseq_flow.py \
         --sample_file $CONDA_PREFIX/NeatSeq-Flow-Workflows/Sample_sets/PE_tabular.nsfs \
         --param_file $CONDA_PREFIX/NeatSeq-Flow-Workflows/mapping.yaml \
         --message "My first NeatSeq-Flow WF using conda"

#. When done, deactivate the environment:

   .. code-block:: bash

      source deactivate

.. Note:: You don't need to have the environment activated in order to execute the scripts!

.. Attention:: See the |tutorial| for a full example of how to use **NeatSeq-Flow**

.. _install_main_no_conda:

Install and execute NeatSeq-Flow without Conda
=============================================================

#. Prerequisites:

   You will need to have `git <https://git-scm.com/downloads>`_ and pip installed for the following installation procedure.

#. Clone the package from github:

   .. code-block:: bash

       git clone https://github.com/bioinfo-core-BGU/neatseq-flow.git

#. You may have to install two `python` dependencies: `yaml` and `bunch`. This can be done with:

   .. code-block:: bash

       pip install pyyaml bunch

#. Clone the package of modules from github:

   .. code-block:: bash

       git clone https://github.com/bioinfo-core-BGU/neatseq-flow-modules.git
    

.. Note:: You can also download the repository code from the following links:

   * Main **NeatSeq-Flow** source code: https://github.com/bioinfo-core-BGU/neatseq-flow/archive/master.zip
   * Module and workflow repository: https://github.com/bioinfo-core-BGU/neatseq-flow-modules/archive/master.zip

.. _Execution_section:

#. Execute NeatSeq-Flow:

Create a new directory anywhere, `cd` into it and execute the following commands (``$NSF_main`` is the directory where **NeatSeq-Flow** is installed):

   .. code-block:: bash

       python $NSF_main/bin/neatseq_flow.py                         \
           --sample_file $NSF_main/Workflows/Sample_sets/PE_tabular.nsfs    \
           --param_file  $NSF_main/Workflows/mapping.yaml       \
           --message     "My first NeatSeq-Flow WF"
