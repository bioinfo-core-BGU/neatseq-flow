==========================================
Using the generic modules
==========================================

.. include:: links.rst

**Author:** Menachem Sklarz

.. contents:: Page Contents:
   :depth: 2
   :local:
   :backlinks: top

Two generic modules are provided to enable including in workflows programs for which no dedicated module exists. Using the modules saves writing dedicated modules and can therefore be utilized by non-programmers as well; however, this comes at a cost of adding clutter to the workflow parameter definition file.

The generic modules, called ``Generic`` and ``Fillout_Generic``, do not contain a definition of input and output file types, therefore the user has to specify the input and output file types in the parameter file.

``Generic``
   is simpler to use for defining most Linux programs, and has extra file type management capacities.

   * `A general overview of the "Generic" module <https://neatseq-flow.readthedocs.io/projects/neatseq-flow-modules/en/latest/Module_docs/GenericModules.html#generic>`_.
   * `A tutorial <https://neatseq-flow.readthedocs.io/projects/neatseq-flow-modules/en/latest/Module_docs/Generic_module.html>`_.

``Fillout_Generic``
   can incorporate more than one command per step, as well as cater to irregular program calls, such as calls including complex pipes.

   * `A general overview of the "Fillout_Generic" module <https://neatseq-flow.readthedocs.io/projects/neatseq-flow-modules/en/latest/Module_docs/GenericModules.html#fillout-generic>`_.





