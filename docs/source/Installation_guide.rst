===============================
Installation Guide
===============================

.. include:: links.rst

**Author:** Menachem Sklarz


.. contents:: Page Contents:
   :depth: 2
   :local:
   :backlinks: top


.. _General_section_GUI:

General
=======

Since most high-throughput sequencing analysis programs are Linux based, NeatSeq-Flow is typically used on a Linux operating system, preferably (but not necessarily) on a computer cluster.
However, the workflow design and script generation steps can be run on any operating system that has Phyton installed.

NeatSeq-Flow GUI is also installed on the Linux computer/cluster, but it is possible to access it from a Windows computer through a Windows X server.

NeatSeq-Flow can be installed in one of the following ways:

#. :ref:`install_with_script` (recommended)
#. :ref:`install_with_conda`
#. :ref:`install_no_conda`


**Conda** allows easy installation of NeatSeq-Flow in one go. For selected workflows, as well as for the NeatSeq-Flow tutorial, we also provide entire Conda environments which include NeatSeq-Flow with all necessary analysis programs (see `NeatSeq-Flow Workflows <https://neatseq-flow.readthedocs.io/projects/neatseq-flow-modules/en/latest/#neatseq-flow-workflows>`_.



.. _install_with_script:


Install NeatSeq-Flow with **installation script**
=================================================================

You can install NeatSeq-Flow and all it's dependencies in one go with a provided bash script.

The script performs the following:

* Miniconda installation
* ``git`` installation
* NeatSeq-Flow conda environment creation

Installing
--------------

**Temporary installation**
   Everything will be installed in a directory called ``NeatSeq_Flow_install``. **To uninstall NeatSeq-Flow**, just delete the directory.

   .. code-block:: bash

      curl -sl https://raw.githubusercontent.com/bioinfo-core-BGU/neatseq-flow/master/docs/source/_extra/extra/NeatSeq_Flow_install_script.sh | bash -s -- temp

**Permanent installation**
   Miniconda will be installed in the default location. If it already exists, the installed version will be used.

   The NeatSeq-Flow environment will be created in the default conda environments directory ("$HOME/miniconda3/envs").

   .. code-block:: bash

      curl -sl https://raw.githubusercontent.com/bioinfo-core-BGU/neatseq-flow/master/docs/source/_extra/extra/NeatSeq_Flow_install_script.sh | bash -s -- perm

Running **NeatSeq-Flow**
--------------------------

Follow the instructions given by the installation script when complete. Briefly:

#. Add conda to the PATH (copy-paste the command from the terminal)
#. Activate the environment and tell **NeatSeq-Flow** where the base conda installation is located:

   .. code-block:: bash

      source activate NeatSeq_Flow
      export CONDA_BASE=$(conda info --root)

#. Run NeatSeq_Flow_GUI:

   .. code-block:: bash

      NeatSeq_Flow_GUI.py

#. Alternatively, run NeatSeq_Flow command-line version:

   .. code-block:: bash

      neatseq_flow.py --help

#. When done, deactivate the environment:

   .. code-block:: bash

      source deactivate

.. _install_with_conda:

Install and execute NeatSeq-Flow **with Conda**
===================================================

Installing Using Conda will install NeatSeq-Flow with all its dependencies [#f1]_ in one go:

Prerequisites
--------------

- The computer where the GUI is installed needs to have a web browser, preferably FireFox.
- To use the GUI from another computer having a Windows operating system, that computer needs to have a Windows X server, e.g. MobaXterm.

Install miniconda
--------------------------

For Linux 64bit, in the terminal:

.. code-block:: bash

        wget https://repo.continuum.io/miniconda/Miniconda3-latest-Linux-x86_64.sh
        sh Miniconda3-latest-Linux-x86_64.sh

**During conda’s installation: type *yes* to add conda to the PATH**

.. Note:: For different operating system go to `minionda downloads page <https://conda.io/miniconda.html>`_
   NeatSeq-Flow uses python version>=3.5. Make sure you download an appropriate version.

.. Important::    If you do not have *git* installed, please install it with the following command:

       .. code-block:: bash

            conda install -c anaconda git


Install **NeatSeq-Flow**
--------------------------

#. Download the **NeatSeq Flow** installer file:

   .. code-block:: bash

        wget http://neatseq-flow.readthedocs.io/en/latest/extra/NeatSeq_Flow_conda_env.yaml

#. Create the **NeatSeq_Flow** conda environment:

   .. code-block:: bash

        conda env create -n NeatSeq_Flow -f NeatSeq_Flow_conda_env.yaml

Running **NeatSeq-Flow**
--------------------------

#. Activate the NeatSeq_Flow conda environment:

    .. code-block:: bash

        bash
        source activate NeatSeq_Flow

#. Execute the following command to tell **NeatSeq-Flow** where the base conda installation is located:

   .. code-block:: bash

      export CONDA_BASE=$(conda info --root)

#. Make a directory for your project and change into it:

   .. code-block:: bash

      mkdir first_neatseq_flow_proj; cd first_neatseq_flow_proj

#. Run NeatSeq_Flow_GUI:

    .. code-block:: bash

        NeatSeq_Flow_GUI.py

#. Alternatively, run NeatSeq_Flow command-line version:

   .. code-block:: bash

      neatseq_flow.py \
         --sample_file $CONDA_PREFIX/NeatSeq-Flow-Workflows/Sample_sets/PE_tabular.nsfs \
         --param_file $CONDA_PREFIX/NeatSeq-Flow-Workflows/RNA_seq_Trinity.yaml \
         --message "My first NeatSeq-Flow WF using conda"

#. When done, deactivate the environment:

   .. code-block:: bash

      source deactivate

.. Note:: You don't need to have the environment activated in order to execute the scripts!

.. Attention:: See the |tutorial| for a full example of how to use **NeatSeq-Flow**


.. _install_no_conda:

Install and execute NeatSeq-Flow without Conda
===============================================================

First, install **NeatSeq-Flow** as described :ref:`here <install_main_no_conda>`.

Then, make sure you have these programs installed:

- git
- pip
- python = 3.6.5
- wxpython [#f2]_
- pyyaml
- munch
- pandas [#f2]_
- Flexx [#f2]_
- A web-browser (Preferably firefox) [#f2]_

**Now, install the GUI**:

#. Clone the package from github:

   .. code-block:: bash

       git clone https://github.com/bioinfo-core-BGU/neatseq-flow.git

#. You may have to install the dependencies. This can be done with:

   .. code-block:: bash

       pip install wxpython pyyaml munch pandas Flexx

#. Clone the package of modules from github:

   .. code-block:: bash

       git clone https://github.com/bioinfo-core-BGU/neatseq-flow-modules.git


#. Clone the github repository of the GUI:

   .. code-block:: bash
   
        git clone https://github.com/bioinfo-core-BGU/NeatSeq-Flow-GUI.git

#. Execute the GUI:

   .. code-block:: bash

        python3 NeatSeq-Flow-GUI/bin/NeatSeq_Flow_GUI.py

#. Alternatively, execute the CLI version of NeatSeq-Flow:

    Create a new directory anywhere, `cd` into it and execute the following commands (``$NSF_main`` is the directory where **NeatSeq-Flow** is installed):

   .. code-block:: bash

       python $NSF_main/bin/neatseq_flow.py                         \
           --sample_file $NSF_main/Workflows/Sample_sets/PE_tabular.nsfs    \
           --param_file  $NSF_main/Workflows/mapping.yaml       \
           --message     "My first NeatSeq-Flow WF"



To use the GUI from another computer having a Windows operating system, use a Windows X server such as MobaXterm.

.. rubric:: Footnotes

.. [#f1] Not including the web-browser
.. [#f2] Required for the GUI only
