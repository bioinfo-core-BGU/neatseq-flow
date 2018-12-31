.. _gui_tutorial:

===========================
NeatSeq-Flow Tutorial (GUI)
===========================

**Author:** Liron Levin

This tutorial is for users wishing to use NeatSeq-Flow through its Graphical User Interface.

Typically, the installation of both NeatSeq-Flow and its GUI is done on a Linux operating system.
It is then possible to use the GUI from a Windows computer through a Windows X server such as MobaXterm.

**In this Tutorial we will:**

-  `Install Conda`_
-  `Install NeatSeq-Flow`_
-  `Install NeatSeq-Flow-GUI`_
-  `Learn How to Create a Work-Flow`_
-  `Configure the Used Variables in the Work-Flow`_
-  `Load a Work-Flow Parameter File`_
-  `Configure a Sample file`_
-  `Configure the Cluster information`_
-  `Run the Work-Flow`_

Prerequisites
--------------

- The computer where the GUI is installed needs to have a web browser, preferably FireFox.
- To use the GUI from another computer having a Windows operating system, that computer needs to have a Windows X server, e.g. MobaXterm.

Install Conda
-------------

-  For Linux 64bit, in the terminal:

   .. code-block:: bash

        wget https://repo.continuum.io/miniconda/Miniconda2-latest-Linux-x86_64.sh
        sh Miniconda2-latest-Linux-x86_64.sh

   **During conda’s installation: type *yes* to add conda to the PATH**

   For different operating system go to `minionda downloads page <https://conda.io/miniconda.html>`_

   If you do not have git installed, install it now with conda:

       .. code-block:: bash

            conda install -c anaconda git

Install NeatSeq-Flow
--------------------

1. Create New Directory for the Tutorial

   .. code-block:: bash
   
        mkdir Tutorial
        cd Tutorial

2. Download the **NeatSeq Flow Tutorial** installer file:

   .. code-block:: bash
   
        wget https://raw.githubusercontent.com/bioinfo-core-BGU/neatseq-flow-tutorial/master/NeatSeq_Flow_Tutorial_Install.yaml

3. Create the **NeatSeq_Flow_Tutorial** conda environment:

  .. code-block:: bash
  
        conda env create -f NeatSeq_Flow_Tutorial_Install.yaml

4. Download the **Tutorial Work-Flow Parameter file**

   .. code-block:: bash
   
      wget https://raw.githubusercontent.com/bioinfo-core-BGU/NeatSeq-Flow-GUI/master/doc/Tutorial_Parameter_file.yaml

5. Download the **Tutorial Work-Flow Sample file**

   .. code-block:: bash

      wget https://raw.githubusercontent.com/bioinfo-core-BGU/neatseq-flow-tutorial/master/Samples_conda.nsfs

Install NeatSeq-Flow-GUI
------------------------

1. Download the **NeatSeq-Flow-GUI** installer file:

   .. code-block:: bash

      wget https://raw.githubusercontent.com/bioinfo-core-BGU/NeatSeq-Flow-GUI/master/NeatSeq_Flow_GUI_installer.yaml

2. Create the **NeatSeq_Flow_GUI** conda environment:

   .. code-block:: bash
   
      conda env create -f NeatSeq_Flow_GUI_installer.yaml

3. Activate the **NeatSeq_Flow_GUI** conda environment:

   .. code-block:: bash
   
      bash
      source activate NeatSeq_Flow_GUI

4. Run **NeatSeq_Flow_GUI**:

   .. code-block:: bash
   
      NeatSeq_Flow_GUI.py

Learn How to Create a Work-Flow
-------------------------------

1. **Add New Step:**

   .. figure:: https://raw.githubusercontent.com/bioinfo-core-BGU/NeatSeq-Flow-GUI/master/doc/Add_Step.gif
      :target: https://raw.githubusercontent.com/bioinfo-core-BGU/NeatSeq-Flow-GUI/master/doc/Add_Step.gif

   In the ‘Work-Flow’ Tab choose a module template and click on the ‘Create New Step’ button.

2. **Change Step Name:**

   .. figure:: https://raw.githubusercontent.com/bioinfo-core-BGU/NeatSeq-Flow-GUI/master/doc/Change_Step_Name.gif
      :target: https://raw.githubusercontent.com/bioinfo-core-BGU/NeatSeq-Flow-GUI/master/doc/Change_Step_Name.gif

   You can change the new step name by clicking on the step name and edit the key field and then click the 'Edit' button to set the change.

3. **To determine the position of the new step in the work-flow:**

   .. figure:: https://raw.githubusercontent.com/bioinfo-core-BGU/NeatSeq-Flow-GUI/master/doc/Set_base.gif
      :target: https://raw.githubusercontent.com/bioinfo-core-BGU/NeatSeq-Flow-GUI/master/doc/Set_base.gif

   - Click on the step button to see the step options
   - Click on the base option
   - Click on the 'Value options' drop-down menu
   - Choose a previous    step and click the 'Add' button. This can be repeated to choose several previous steps.
   - Click the 'Edit' button to set the changes.

4. **Add new step option:**

   .. figure:: https://raw.githubusercontent.com/bioinfo-core-BGU/NeatSeq-Flow-GUI/master/doc/New_step_option.gif
      :target: https://raw.githubusercontent.com/bioinfo-core-BGU/NeatSeq-Flow-GUI/master/doc/New_step_option.gif

   - Click on the step's name (or a step option to create a new sub option)
   - Click on the 'New' button.
   - It is possible to edit the new option name and value by editing the 'Key' field and the 'Value' field, it is also possible to choose from the 'Value options' drop-down menu.
   - Click the 'Edit' button to set the changes.

5. **Edit step's options:**

   .. figure:: https://raw.githubusercontent.com/bioinfo-core-BGU/NeatSeq-Flow-GUI/master/doc/Edit_step_option.gif
      :target: https://raw.githubusercontent.com/bioinfo-core-BGU/NeatSeq-Flow-GUI/master/doc/Edit_step_option.gif

   - Click on the step's option name and change the 'Key' field and/or the 'Value' field, it is also possible to choose from the 'Value options' drop-down menu.
   - When using the 'Value options' drop-down menu, in some cases it is possible to choose variables that are defined in the 'Vars' Tab.
     They will appear in the form of {Vars.some_field.some_sub_field} to indicate the value found in the 'Vars' Tab in the some_sub_field field ( which is a sub field of 'some_field' ).
   - It is possible to choose file location as a value to the 'Value' field by clicking on the 'Browse' button.
   - Click the 'Edit' button to set the changes.

6. **Remove field or step:**

   .. figure:: https://raw.githubusercontent.com/bioinfo-core-BGU/NeatSeq-Flow-GUI/master/doc/Remove_field_or_step.gif
      :target: https://raw.githubusercontent.com/bioinfo-core-BGU/NeatSeq-Flow-GUI/master/doc/Remove_field_or_step.gif

   - Click on the step's name (to remove the step) or on a step's option name (to remove the option and it's sub fields)
   - Click the 'Remove' button

Configure the Used Variables in the Work-Flow
---------------------------------------------

1. **Edit Variables:**

   .. figure:: https://raw.githubusercontent.com/bioinfo-core-BGU/NeatSeq-Flow-GUI/master/doc/Edit_Var.gif
      :target: https://raw.githubusercontent.com/bioinfo-core-BGU/NeatSeq-Flow-GUI/master/doc/Edit_Var.gif

   In the 'Vars' Tab choose a variable name to edit, change the key or value and then click on the 'Edit' button.

2. **Create New Variable:**

   .. figure:: https://raw.githubusercontent.com/bioinfo-core-BGU/NeatSeq-Flow-GUI/master/doc/Create_New_variable.gif
      :target: https://raw.githubusercontent.com/bioinfo-core-BGU/NeatSeq-Flow-GUI/master/doc/Create_New_variable.gif

   - You can create new variable by clicking on some existing variable name and then click the 'New Field' button.
   - You can create new sub variable by clicking on the existing variable to which you want to create a sub variable and then click the 'New Sub Field' button.

        
Load a Work-Flow Parameter File
-------------------------------

1. **Load a Sample file:**

   .. figure:: https://raw.githubusercontent.com/bioinfo-core-BGU/NeatSeq-Flow-GUI/master/doc/Load_WorkFlow_parameter_file.gif
      :target: https://raw.githubusercontent.com/bioinfo-core-BGU/NeatSeq-Flow-GUI/master/doc/Load_WorkFlow_parameter_file.gif

   - In the 'Work-Flow' Tab click on the 'Load WorkFlow' button, then choose the work-flow's parameter file 'Tutorial_Parameter_file.yaml' and click open.

        
Configure a Sample file
-----------------------

In the 'Samples' Tab:

1. **Edit The Project Title Name:**

   - You can edit the project title name by clicking on the Project Title name.

2. **Add a Sample/Project File:**

   - You can add a sample/project file by clicking the 'Add Sample File' or 'Add project File' button and choose a file/s.

3. **Load a Sample file:**

   .. figure:: https://raw.githubusercontent.com/bioinfo-core-BGU/NeatSeq-Flow-GUI/master/doc/Load_Sample_file.gif
      :target: https://raw.githubusercontent.com/bioinfo-core-BGU/NeatSeq-Flow-GUI/master/doc/Load_Sample_file.gif

   - Click on the 'Load Sample File' button, then choose the work-flow's sample file 'Samples_conda.nsfs' and click open.
   - You can edit the names of the samples by clicking on the sample name.
   - You can remove a sample/project file by clicking the 'Remove' button.
   - You can change a sample/project file type by clicking the drop-down menu or by editing the type name.

        
Configure the Cluster information
---------------------------------

1. **Edit Field:**

   In the 'Cluster' Tab choose a field name to edit, change the key or value and then click on the 'Edit' button.

2. **Create New Field:**

   - You can create new field by clicking on some existing field name and then click the 'New Field' button.
   - You can create new sub field by clicking on the existing field to which you want to create a sub field and then click the 'New Sub Field' button.
        
Run the Work-Flow
-----------------

.. figure:: https://raw.githubusercontent.com/bioinfo-core-BGU/NeatSeq-Flow-GUI/master/doc/Generate_scripts.gif
   :target: https://raw.githubusercontent.com/bioinfo-core-BGU/NeatSeq-Flow-GUI/master/doc/Generate_scripts.gif

**If NeatSeq-Flow is installed using conda (as in this Tutorial):** Choose the conda environment of which NeatSeq-Flow installed in.

**If NeatSeq-Flow is installed Locally:** Choose the neatseq_flow.py script location.

**In order to Generate the Work-Flow scripts:**

1. Select the Sample file.
2. Select the Work-Flow parameter-file.
3. Choose the Project Directory to generate the Work-Flow scripts in (the default is to use the Current Working Directory )
4. Click on the 'Generate scripts' button.

**To run the Work-Flow click on the 'Run scripts' button**

.. figure:: https://raw.githubusercontent.com/bioinfo-core-BGU/NeatSeq-Flow-GUI/master/doc/Run_scripts.gif
   :target: https://raw.githubusercontent.com/bioinfo-core-BGU/NeatSeq-Flow-GUI/master/doc/Run_scripts.gif

**It is possible to monitor the Work-Flow progress by clicking the 'Run Monitor' button**

.. figure:: https://raw.githubusercontent.com/bioinfo-core-BGU/NeatSeq-Flow-GUI/master/doc/Run_Monitor.gif
   :target: https://raw.githubusercontent.com/bioinfo-core-BGU/NeatSeq-Flow-GUI/master/doc/Run_Monitor.gif
  
Contact
-------

Please contact Liron Levin at: `levinl@post.bgu.ac.il <mailto:levinl@post.bgu.ac.il>`_
