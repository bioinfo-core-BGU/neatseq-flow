.. neatseq_flow documentation master file, created by
   sphinx-quickstart on Sun Jan 08 15:32:48 2017.

**NeatSeq-Flow**: A Lightweight Software for Efficient Execution of High-Throughput Sequencing Workflows.
========================================================================================================================

.. figure:: figs/NeatSeq_Flow_logo.png
   :scale: 60 %
   :align: center
   :alt: NeatSeq-Flow logo

.. include:: links.rst

.. image:: https://readthedocs.org/projects/neatseq-flow/badge/?version=latest
   :target: http://neatseq-flow.readthedocs.io/en/latest/

.. image:: https://img.shields.io/badge/License-GPLv3-blue.svg
   :target: https://www.gnu.org/licenses/gpl-3.0

.. image:: https://img.shields.io/github/last-commit/sklarz-bgu/neatseq-flow.svg

.. image:: https://anaconda.org/levinl/neatseq-flow/badges/downloads.svg

.. sidebar:: **What's new**...


   * `It is now possible to run NeatSeq-Flow also on Windows and Mac using Docker <https://github.com/bioinfo-core-BGU/NeatSeq-Flow-Using-Docker>`_
   * `It is now possible to run NeatSeq-Flow also on Amazon cloud <https://github.com/bioinfo-core-BGU/NeatSeq-Flow-In-The-Cloud>`_
   * Improved GUI (press on the image)

     .. figure:: https://raw.githubusercontent.com/bioinfo-core-BGU/NeatSeq-Flow-GUI/master/doc/Static_GUI.png
        :target: https://raw.githubusercontent.com/bioinfo-core-BGU/NeatSeq-Flow-GUI/master/doc/NeatSeq-Flow-GUI.gif
        :align: left

   * `Visual report for differential expression (DESeq2), clustering and functional analyses <https://github.com/bioinfo-core-BGU/NeatSeq-Flow_Workflows/blob/master/DeSeq_Workflow/Tutorial.md>`_
   * `GATK workflow <https://neatseq-flow.readthedocs.io/projects/neatseq-flow-modules/en/latest/Workflow_docs/GATK_workflow.html>`_
   * `QIIME2 workflow <https://neatseq-flow.readthedocs.io/projects/neatseq-flow-modules/en/latest/Workflow_docs/QIIME2_workflow.html>`_
   * `Generic module tutorial <https://neatseq-flow.readthedocs.io/projects/neatseq-flow-modules/en/latest/Module_docs/Generic_module.html>`_


.. topic:: Important links


   * :ref:`quick_start` install and try NeatSeq-Flow
   * :ref:`install_on_windows_with_wsl` install and try NeatSeq-Flow on Windows using WSL
   * GitHub: `NeatSeq-Flow <https://github.com/bioinfo-core-BGU/neatseq-flow>`_
   * GitHub: `NeatSeq-Flow GUI <https://github.com/bioinfo-core-BGU/NeatSeq-Flow-GUI>`_
   * `A short movie demonstrating the GUI <https://raw.githubusercontent.com/bioinfo-core-BGU/NeatSeq-Flow-GUI/master/doc/NeatSeq-Flow-GUI.gif>`_
   * `Module and Workflow repository <http://neatseq-flow.readthedocs.io/projects/neatseq-flow-modules/en/latest/>`_
   * `Article on BioRXiv <https://www.biorxiv.org/content/early/2018/12/18/173005>`_
   * `Contact <mailto:sklarz@bgu.ac.il?subject=Inquiry\ about\ NeatSeq-Flow>`_


What is **NeatSeq-Flow**?
--------------------------

NeatSeq-Flow is a platform for modular design and execution of bioinformatics workflows on a local computer or, preferably, computer cluster.
The platform has a command-line interface as well as a fully functional graphical user interface (GUI), both used locally without the need to connect to remote servers.
Analysis programs comprising a workflow can be anything executable from the Linux command-line, either publicly available or in-house programs.
Ready-to-use workflows are available for common Bioinformatics analyses such as assembly & annotation, RNA-Seq, ChIP-Seq, variant calling, metagenomics and genomic epidemiology.
Creation and sharing of new workflows is easy and intuitive, without need for programming knowledge.
NeatSeq-Flow is general-purpose and may easily be adjusted to work on different types of analyses other than high-throughput sequencing.

NeatSeq-Flow is fully accessible to non-programmers, without compromising power, flexibility and efficiency. The user only has to specify the location of input files and the workflow design, and need not bother with the location of intermediate and final files, nor with transferring files between workflow steps. Workflow execution is fully parallelized on the cluster, and progress can be inspected through NeatSeq-Flow “terminal monitor”. All workflow steps, parameters and order of execution are stored in one file, which together with the shell scripts produced by NeatSeq-Flow comprise a complete documentation of the workflow and enable future execution of the exact same workflow or modifications thereof.

:ref:`Read more about NeatSeq-Flow <about_neatseq_flow>`.


Available Modules and Workflows
-------------------------------

| NeatSeq-Flow comes with a basic set of modules, marked `here <https://neatseq-flow.readthedocs.io/projects/neatseq-flow-modules/en/latest/#neatseq-flow-modules>`_ with an asterisk (*).
| The complete set of currently available modules and workflows is downloadable from |github|.
| Installation and usage instructions, along with full documentation of the modules and workflows, are available at `NeatSeq-Flow's Module and Workflow Repository <https://neatseq-flow.readthedocs.io/projects/neatseq-flow-modules/en/latest/>`_.

.. _quick_start:

Quick Start:
------------

 Installing Using Conda will install NeatSeq-Flow with all its dependencies in one go: 
  - First if you don't have **Conda**, `install it! <https://conda.io/miniconda.html>`_
  - Then in the terminal:

    1. Install mamba and Create the **NeatSeq_Flow** conda environment:

    .. code-block:: bash

      bash
      conda install conda-forge::mamba
      mamba create -n NeatSeq_Flow -c bioconda -c conda-forge levinl::neatseq-flow

    2. Activate the **NeatSeq_Flow** conda environment:

    .. code-block:: bash

      bash
      source activate NeatSeq_Flow
      
      
    3. Run **NeatSeq_Flow_GUI**:

    .. code-block:: bash

      NeatSeq_Flow_GUI.py --Server

    4. Use the information in the terminal:

        .. figure:: https://github.com/bioinfo-core-BGU/NeatSeq-Flow-GUI/raw/master/doc/NeatSeq-Flow_Server.jpg
           :align: right
           :width: 350

        - Copy the IP address to a web-browser - (red line)
        - A login window should appear
        - Copy the "User Name" (blue line) from the terminal to the "User Name" form in the login window
        - Copy the "Password" (yellow line) from the terminal to the "Password" form in the login window
        - Click on the "Login" button.

    5. Managing Users:
        - It is possible to mange users using SSH, NeatSeq-Flow will try to login by ssh to a host using the provided "User Name" and "Password".
        - The ssh host can be local or remote.
        - Note: If using a remote host, NeatSeq-Flow needs to be installed on the remote host and the analysis will be run on the remote host by the user that logged-in
    
    .. code-block:: bash

      NeatSeq_Flow_GUI.py --Server --SSH_HOST 127.0.0.1


    6. For more option:

    .. code-block:: bash

      NeatSeq_Flow_GUI.py -h

.. _install_on_windows_with_wsl:

Install on Windows with WSL:
------------------------------
 On Windows 10 version 2004 and higher (Build 19041 and higher) or Windows 11 it is possible to use both Windows and Linux at the same time on a Windows machine.
 NeatSeq-Flow can be install on the Windows Subsystem for Linux (WSL):
  - First install `Linux <https://learn.microsoft.com/en-us/windows/wsl/install>`_ on Windows: 
  - Open the **Windows** PowerShell Terminal as **administrator**:
    
    .. code-block:: bash

      wsl --install
  
  - Open the Ubuntu app/terminal:  [it is possible to use the *Microsoft Store* to install `Ubuntu <https://www.microsoft.com/store/productId/9PDXGNCFSCZV?ocid=pdpshare>`_]
 
    1. Install Conda, Make sure to type **YES** for "Do you wish the installer to initialize Miniconda3 by running conda init?":

    .. code-block:: bash

      wget https://repo.anaconda.com/miniconda/Miniconda3-latest-Linux-x86_64.sh
      sh Miniconda3-latest-Linux-x86_64.sh

    2. Install mamba and Create the **NeatSeq_Flow** conda environment:

    .. code-block:: bash
       
      bash
      conda install conda-forge::mamba
      mamba create -n NeatSeq_Flow -c bioconda -c conda-forge levinl::neatseq-flow

    3. Activate the **NeatSeq_Flow** conda environment:

    .. code-block:: bash

      bash
      source activate NeatSeq_Flow
      
      
    4. Activate SSH service:

    .. code-block:: bash
      
      sudo apt install openssh-server
      sudo ssh-keygen -A
      sudo service ssh start

    5. Run **NeatSeq_Flow_GUI**:

    .. code-block:: bash

      export WSL_IP=$(ip addr show eth0 | grep inet | awk '{ print $2; }' | sed 's/\/.*$//' | head -n 1)
      echo $WSL_IP
      NeatSeq_Flow_GUI.py --Server --HOST $WSL_IP

  - Open the **Windows** PowerShell Terminal as **administrator**:
    

    6. Run this command in the terminal while **WSL_IP** needs to be replaced with the Linux IP identified in previous step [the "echo $WSL_IP" result]:

    .. code-block:: bash

      netsh interface portproxy add v4tov4 listenaddress=127.0.0.1 listenport=49190 connectaddress=WSL_IP connectport=49190

    7. Open a web-browser and in the address bar type localhost:49190 
        - A login window should appear

    8. Use the information in the **Linux** terminal:

        .. figure:: https://github.com/bioinfo-core-BGU/NeatSeq-Flow-GUI/raw/master/doc/NeatSeq-Flow_Server.jpg
           :align: right
           :width: 350

        - Copy the "User Name" (blue line) from the terminal to the "User Name" form in the login window
        - Copy the "Password" (yellow line) from the terminal to the "Password" form in the login window
        - Click on the "Login" button.

    9. Managing Users:
        - It is possible to mange users using SSH, NeatSeq-Flow will try to login by ssh to a host using the provided "User Name" and "Password".
        - The ssh host can be local or remote.
        - Note: If using a remote host, NeatSeq-Flow needs to be installed on the remote host and the analysis will be run on the remote host by the user that logged-in
    



Authors
---------

* Menachem Sklarz
* Liron Levin
* Michal Gordon
* Vered Chalifa-Caspi

`Bioinformatics Core Facility`_, llse Katz Institute for Nanoscale Science and Technology, Ben-Gurion University of the Negev, Beer-Sheva, Israel


Cite NeatSeq-Flow
-----------------

`NeatSeq-Flow article on BioRXiv <https://www.biorxiv.org/content/early/2018/12/18/173005>`_

Contact Us
----------

| Liron Levin
| Email: `levinl@bgu.ac.il <mailto:levinl@bgu.ac.il?subject=Inquiry\ about\ NeatSeq-Flow>`_




Web Site Contents:
-------------------

.. toctree::
   :maxdepth: 1
   :caption: First Steps

   About
   Tutorial

Next Step:
-----------
   * `Generic Module Tutorial <https://neatseq-flow.readthedocs.io/projects/neatseq-flow-modules/en/latest/Module_docs/Generic_module.html>`_
  
  
.. toctree::
   :maxdepth: 1
   :caption: Detailed Documentation

   User_Manual
   Repository_links
   Add_new_modules
   cheat_sheet
   glossary


.. sphinx-build -b html source build



.. .. toctree::
..    :maxdepth: 1
..    :caption: Getting Started: Install and Try
..
..    Tutorial
.. ..   Tutorial_GUI
.. ..   Tutorial_CL
..
.. .. toctree::
..    :maxdepth: 1
..    :caption: Installation
..
..    Installation_guide
.. ..   Installation_guide_GUI
.. ..   Installation_guide_CL
