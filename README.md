# **NeatSeq-Flow**: A Lightweight Software for Efficient Execution of High Throughput Sequencing Workflows.


What is NeatSeq-Flow and why use it?
-----------------------------
* A bioinformatics workflow (WF) is a series of computer programs called sequentially, sometimes on hundreds or even thousands of samples.
* NeatSeq-flow creates human readable and self explanatory shell scripts for execution on computer grids. 
* The hyrachically-organised scripts are then executed by running a master-script.
* The main benefits in using NeatSeq-flow are:
	* the user has full control over the WF execution;
	* the cluster job scheduler ensures correct execution order and enforces dependencies;
	* simple, cross-platform installation; 
	* scripts and output files are neatly organized;
	* utilization of cluster parallelization capabilities;
	* documentation, version control as well as time & memory usage reports and 
	* adding modules and expanding existing WFs requires only basic python skills.


Brief description
-----------------
* NeatSeq-Flow is a cross-platform, easy-to-install, no-dependency python package.
* It creates workflow scripts for high throughput sequencing data, which are executed automatically on a computer cluster, fully under control of the user.
* The cluster job scheduler controls execution order.
* NeatSeq-Flow:
	* creates a directory structure for tidy storing of shell scripts and workflow outputs;
	* utilizes cluster parallelization capabilities;
	* is easily expandable with new modules;
	* records information about files produced by the scripts and
	* provides documentation, version control and time & memory usage reports.



**[See full documentation on RTD.](http://NeatSeq-Flow.readthedocs.io/en/latest/)**

Installation & Execution
----------------------------

The easiest way to install is by cloning the github repository:

	git clone https://github.com/bioinfo-core-BGU/neatseq-flow.git

Execution is then done as follows:

	mkdir workflow_dirs
	python neatseq_flow/ -s parameter_sets/sample_sets/PE.nsfs \
		-p parameter_sets/PL.Parameters_mapping.nsfp \
		-m "my first neatseq_flow mapping workflow" \
		-d workflow_dirs/

Check out `workflow_dirs` for the workflow directories and scripts.

Citation
----------
Sklarz, Menachem, et al. **NeatSeq-Flow: A Lightweight Software for Efficient Execution of High Throughput Sequencing Workflows**. Submitted for publication.