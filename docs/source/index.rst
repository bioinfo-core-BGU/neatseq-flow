.. neatseq_flow documentation master file, created by
   sphinx-quickstart on Sun Jan 08 15:32:48 2017.

**NeatSeq-Flow**: A Lightweight Software for Efficient Execution of High Throughput Sequencing Workflows.
========================================================================================================================

.. figure:: figs/NeatSeq_Flow_logo.png
   :scale: 60 %
   :align: center
   :alt: NeatSeq-Flow logo


.. image:: https://readthedocs.org/projects/neatseq-flow/badge/?version=latest
   :target: http://neatseq-flow.readthedocs.io/en/latest/

   
.. sidebar:: **NeatSeq-Flow**...

   * is an easy-to-install python package; 
   * creates workflow scripts for high throughput sequencing data, which are executed automatically on a computer cluster, fully under control of the user while the cluster job scheduler controls execution order;
   * creates a directory structure for tidy storing of shell scripts and workflow outputs;
   * utilizes cluster parallelization capabilities;
   * is easily expandable with new modules while a generic module exists for quick incorporation of programs;
   * records information about files produced by the scripts;
   * provides documentation, version control and time & memory usage reports and
   * provides a monitor for tracking execution progress.

.. contents:: Table of Contents
   :depth: 1
   :local:
   :backlinks: top


What is **NeatSeq-Flow**?
--------------------------

* A bioinformatics workflow (WF) is a series of computer programs called sequentially, sometimes on hundreds or even thousands of samples.
* **NeatSeq-Flow** creates human readable and self explanatory shell scripts for execution on computer grids. 
* The hyrachically-organised scripts are then executed by running a master-script.
* The main benefits in using **NeatSeq-Flow** are:
	* the user has full control over the WF execution;
	* the cluster job scheduler ensures correct execution order and enforces dependencies;
	* simple, cross-platform installation; 
	* scripts and output files are neatly organized;
	* utilization of cluster parallelization capabilities;
	* documentation, version control as well as time & memory usage reports and 
	* adding modules and expanding existing WFs requires only basic python skills.
* **NeatSeq-Flow** is available on `github <https://github.com/bioinfo-core-BGU/neatseq-flow>`_ (See :ref:`installation_section`)

    

Modules
-------

While a basic number of modules come with **NeatSeq-Flow**, the main source of modules is the **NeatSeq-Flow module and workflow repository**. This repository is available on `github <https://github.com/bioinfo-core-BGU/neatseq-flow-modules>`_. Check out the `list of modules in the modules repository <http://neatseq-flow.readthedocs.io/projects/neatseq-flow-modules/en/latest/>`_.

Authors
---------

* Menachem Sklarz
* Michal Gordon
* Liron Levin
* Vered Chalifa-Caspi


.. Detailed documentation
.. -----------------------

.. toctree::
   :maxdepth: 3
   :caption: Installation

   00.getting_started

.. toctree::
   :maxdepth: 1
   :caption: Detailed documentation

   01.concept
   02.build_WF
   03.output
   06.addnew_module
   07.monitor
   
   
Indices and tables
==================

* :ref:`genindex`
* :ref:`modindex`
* :ref:`search`

