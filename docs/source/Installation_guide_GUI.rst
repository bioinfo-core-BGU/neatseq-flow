===============================
Installation Guide (GUI) 
===============================

.. include:: links.rst

**Author:** Menachem Sklarz

This guide is for users wishing to use NeatSeq-Flow through its Graphical User Interface.

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

NeatSeq-Flow can be installed in one of two ways:

#. Installation using **Conda** (recommended)
#. Installation without Conda.

**Conda** allows easy installation of NeatSeq-Flow in one go. For selected workflows, as well as for the NeatSeq-Flow tutorials, we also provide entire Conda environments which include NeatSeq-Flow with all necessary analysis programs.

.. Users wishing to install NeatSeq-Flow with conda need miniconda2.

.. For users wishing to install NeatSeq-Flow without conda, the requirements are: git; pip; pyyaml and bunch python packages; and the specific analysis programs needed for the desired workflow.

.. For accessing NeatSeq-Flow GUI from Windows, it is recommended to install a Windows X server such as MobaXterm.
   

.. _GUI_install_with_conda:


Install and execute NeatSeq-Flow GUI **with Conda**
===================================================

Installing Using Conda will install NeatSeq-Flow-GUI with all its dependencies [#f1]_ in one go:

Prerequisites
--------------

- The computer where the GUI is installed needs to have a web browser, preferably FireFox.
- To use the GUI from another computer having a Windows operating system, that computer needs to have a Windows X server, e.g. MobaXterm.

Install miniconda
--------------------------


For Linux 64bit, in the terminal:

.. code-block:: bash

        wget https://repo.continuum.io/miniconda/Miniconda2-latest-Linux-x86_64.sh
        sh Miniconda2-latest-Linux-x86_64.sh

**During conda’s installation: type *yes* to add conda to the PATH**

For different operating system go to `minionda downloads page <https://conda.io/miniconda.html>`_


.. Important::    If you do not have *git* installed, please install it with the following command:

       .. code-block:: bash

            conda install -c anaconda git


Install **NeatSeq-Flow**
--------------------------

2. Download the **NeatSeq Flow Tutorial** installer file:

   .. code-block:: bash

        wget http://neatseq-flow.readthedocs.io/en/latest/extra/NeatSeq_Flow_conda_env.yaml

3. Create the **NeatSeq_Flow_Tutorial** conda environment:

   .. code-block:: bash

        conda env create -f NeatSeq_Flow_conda_env.yaml

Install **NeatSeq-Flow** GUI
-----------------------------------

Then in the terminal:

#. Download the NeatSeq-Flow-GUI installer file:

   .. code-block:: bash

        wget https://raw.githubusercontent.com/bioinfo-core-BGU/NeatSeq-Flow-GUI/master/NeatSeq_Flow_GUI_installer.yaml

#. Create the NeatSeq_Flow_GUI conda environment:

   .. code-block:: bash

        conda env create -f NeatSeq_Flow_GUI_installer.yaml

#. Activate the NeatSeq_Flow_GUI conda environment:

    .. code-block:: bash

        bash
        source activate NeatSeq_Flow_GUI

#. Run NeatSeq_Flow_GUI:

    .. code-block:: bash

        NeatSeq_Flow_GUI.py


.. _GUI_install_no_conda:

Install and execute NeatSeq-Flow GUI without Conda
===============================================================

First, install **NeatSeq-Flow** as described :ref:`here <install_main_no_conda>`.

Then, make sure you have these programs installed:

- git
- python = 3.6.5
- wxpython
- pyyaml
- munch
- pandas
- Flexx
- A web-browser (Preferably firefox)

**Now, install the GUI**:

1. Clone the github repository of the GUI:

   .. code-block:: bash
   
        git clone https://github.com/bioinfo-core-BGU/NeatSeq-Flow-GUI.git

2. Execute the GUI:

   .. code-block:: bash

        python3 NeatSeq-Flow-GUI/bin/NeatSeq_Flow_GUI.py

To use the GUI from another computer having a Windows operating system, use a Windows X server such as MobaXterm.

.. rubric:: Footnotes

.. [#f1] Not including the web-browser
