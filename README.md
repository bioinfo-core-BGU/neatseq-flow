# **NeatSeq-Flow**: A Lightweight Software for Efficient Execution of High Throughput Sequencing Workflows.
![NeatSeq-Flow Logo](docs/source/figs/NeatSeq_Flow_logo.png "NeatSeq-Flow")


[![Documentation Status](https://readthedocs.org/projects/neatseq-flow/badge/?version=latest)](http://neatseq-flow.readthedocs.io/en/latest/?badge=latest)
[![License: GPL v3](https://img.shields.io/badge/License-GPLv3-blue.svg)](https://www.gnu.org/licenses/gpl-3.0)
![GitHub release](https://img.shields.io/github/release-pre/sklarz-bgu/neatseq-flow.svg)
>>>>>>> devel
![GitHub repo size](https://img.shields.io/github/repo-size/sklarz-bgu/neatseq-flow.svg)
![GitHub top language](https://img.shields.io/github/languages/top/sklarz-bgu/neatseq-flow.svg)
![GitHub last commit](https://img.shields.io/github/last-commit/sklarz-bgu/neatseq-flow.svg)

<!--- [![Github All Releases](https://img.shields.io/github/downloads/sklarz-bgu/neatseq-flow/total.svg)]() -->


# Background

**[See full documentation on RTD.](http://NeatSeq-Flow.readthedocs.io/en/latest/)**

## Brief description

* NeatSeq-Flow is a platform for modular design and execution of bioinformatics workflows on a local computer or, preferably, computer cluster. 
* The platform has a command-line interface as well as a fully functional graphical user interface (GUI), both used locally without the need to connect to remote servers. 
* Analysis programs comprising a workflow can be anything executable from the Linux command-line, either publicly available or in-house programs. 
* Ready-to-use workflows are available for common Bioinformatics analyses such as assembly & annotation, RNA-Seq, ChIP-Seq, variant calling, metagenomics and genomic epidemiology. 
* Creation and sharing of new workflows is easy and intuitive, without need for programming knowledge. 
* NeatSeq-Flow is general-purpose and may easily be adjusted to work on different types of analyses other than high-throughput sequencing.


## The main benefits in using NeatSeq-Flow

* Simple, cross-platform installation.
* All workflow components and parameters, as well as their order of execution (a.k.a workflow design), are specified in a single file which may be prepared by the user either manually (YAML format) or through the GUI. This, together with the shell scripts produced by NeatSeq-Flow and additional NeatSeq-Flow summary files, comprise a complete documentation of the executed workflow and enable future execution of the exact same workflow or modifications thereof.
* The user is relieved from the need to know or manage the locations of intermediate or final files, or to transfer files between workflow steps. Workflow output file locations are determined by NeatSeq-Flow such that they are neatly organized in an intuitive directory structure.
* NeatSeq-Flow’s “Terminal Monitor” shows script execution in real time, and reports on execution errors immediately when they occur, thus facilitating user control on the workflow.
* The platform can accommodate workflows of any degree of complexity, and efficiently executes them in a parallelized manner on the user’s computer cluster.
* Through an intuitive GUI, NeatSeq-Flow is fully accessible to non-programmers, without compromising power, flexibility and efficiency.
* Users can easily create complex workflows from a variety of high-throughput sequencing applications made available by NeatSeq-Flow as independent modules. In addition, a generic module enables direct incorporation of applications without pre-built modules.
* Advanced users can run NeatSeq-Flow through the command-line, and create their own modules using a provided template and only basic Python commands.
* The modules and workflows are designed to be easily shared. In addition, the support for usage of CONDA environments enables easy portability and sharing of entire working environment for workflow execution.




# Installation & Execution

## Quick start

Check out the [Tutorial](http://neatseq-flow.readthedocs.io/en/latest/Example_WF.html) .

## Installing NeatSeq-Flow

The easiest way to install is using **Conda**, Conda will install NeatSeq-Flow and NeatSeq-Flow-GUI with all its dependencies **in one go**: 

  - First if you don't have **Conda**, [install it!](https://conda.io/miniconda.html) 
  - Then in the terminal:
    1. Create the **NeatSeq_Flow** conda environment:
    ```Bash
      conda env create levinl/neatseq_flow
    ```  


## Executing NeatSeq-Flow

1. Activate the environment

   1. Activate the **NeatSeq_Flow** conda environment:
    ```Bash
      bash
      source activate NeatSeq_Flow
      export CONDA_BASE=$(conda info --root)
    ```
    2. Run **NeatSeq_Flow_GUI**:
    ```Bash 
       NeatSeq_Flow_GUI.py
    ```
    3. For more option:
    ```Bash 
        NeatSeq_Flow_GUI.py -h
        usage: NeatSeq_Flow_GUI.py [-h] [--Server] [--PORT CHAR] [--HOST CHAR] [--SSL]
                           [--SSH_HOST CHAR] [--SSH_PORT CHAR] [--USER CHAR]
                           [--PASSW CHAR] [--USERSFILE CHAR]
                           [--UNLOCK_USER_DIR] [--WOKFLOW_DIR CHAR]
                           [--CONDA_BIN CHAR] [--LOG_DIR CHAR]

        NeatSeq-Flow GUI By Liron Levin

        optional arguments:
          -h, --help          show this help message and exit
          --Server            Run as Server
          --PORT CHAR         Use this port in which to run the app, If not set will
                              search for open port (Works only When --Server is set)
          --HOST CHAR         The host name/ip to serve the app, If not set, will try
                              to identify automatically (Works only When --Server is
                              set)
          --SSL               Use SSL (Only When --Server is set)
          --SSH_HOST CHAR     Connect using SSH to a remote host, NeatSeq-Flow needs
                              to be installed on the remote host (Works only When
                              --Server is set)
          --SSH_PORT CHAR     When --SSH_HOST is set use this ssh port to connect to a
                              remote host.
          --USER CHAR         User Name For This Serve (Works only When --Server is
                              set)
          --PASSW CHAR        Password For This Serve (Works only When --Server is
                              set)
          --USERSFILE CHAR    The location of a Users file in which a list of users,
                              E-mails addresses and Users directories are separated by
                              one space (as:USER user@example.com /USER/DIR). The
                              login password will be send to the user e-mail after
                              filling its user name and the password generated at the
                              beginning of the run (Works only When --Server is set).
                              You will need a Gmail account to send the password to
                              the users (you will be prompt to type in your Gmail
                              address and password)
          --UNLOCK_USER_DIR   Don't Lock Users to their Directory Or to the Current
                              Working Directory
          --WOKFLOW_DIR CHAR  A Path to a Directory containing work-flow files to
                              choose from at log-in. Works only When --Server is set.
                              If --SSH_HOST is set, the Path needs to be in the remote
                              host.
          --CONDA_BIN CHAR    A path to a the CONDA bin location. If --SSH_HOST is
                              set, the Path needs to be in the remote host.
          --LOG_DIR CHAR      A path to a directory to save log files about users
                              statistics. Only woks If --Server is set. In any way the
                              path needs to be at the local host.
    ```

1. Alternatively, run NeatSeq_Flow command-line version:

    ```Bash 
       neatseq_flow.py --help
    ``` 


# Additional repositories

The installation process described above installs the following three NeatSeq-Flow repositories:

1. [The main NeatSeq-Flow repository](https://github.com/bioinfo-core-BGU/neatseq-flow)
1. [NeatSeq-Flow's GUI repository](https://github.com/bioinfo-core-BGU/NeatSeq-Flow-GUI)
1. [NeatSeq-Flow's module repository](https://github.com/bioinfo-core-BGU/neatseq-flow-modules)


# Customers

[The National Knowledge Center for Rare / Orphan Diseases](http://in.bgu.ac.il/en/rod/Pages/default.aspx)

# Contact

Please contact 

Liron Levin at:     [levinl@bgu.ac.il](mailto:levinl@bgu.ac.il)

Menachem Sklarz at: [sklarz@bgu.ac.il](mailto:sklarz@bgu.ac.il)

# Citation

Sklarz, Menachem, et al. (2017) **NeatSeq-Flow: A Lightweight Software for Efficient Execution of High Throughput Sequencing Workflows**. [bioRxiv doi: 10.1101/173005](http://www.biorxiv.org/content/early/2017/08/08/173005)
