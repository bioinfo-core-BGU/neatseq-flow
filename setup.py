#from distutils.core import setup
from setuptools import find_packages, setup

setup(
    name                = 'NeatSeq-Flow',
    version             = '1.1.0',
    author              = 'Menachem Sklarz',
    author_email        = 'sklarz@bgu.ac.il',
    maintainer          = 'Menachem Sklarz',
    maintainer_email    = 'sklarz@bgu.ac.il',
    url                 = 'http://neatseq-flow.readthedocs.io/en/latest/',
    description         = 'Package for creation of workflow scripts for execution on computer clusters',
    license             = 'Creative Commons Attribution-Noncommercial-Share Alike license',
    long_description    =  open('README').read(),
    download_url        = 'https://github.com/bioinfo-core-BGU/neatseq-flow.git',
    platforms           = ["POSIX","Windows"],
    packages            = ['neatseq_flow',
                            'neatseq_flow.modules',
                            'neatseq_flow.monitor',
                            'neatseq_flow.step_classes.Assembly',
                            'neatseq_flow.step_classes.ChIP_seq',
                            'neatseq_flow.step_classes.Generic_module',
                            'neatseq_flow.step_classes.IGVtools',
                            'neatseq_flow.step_classes.mapping',
                            'neatseq_flow.step_classes.preparing',
                            'neatseq_flow.step_classes.Reports',
                            'neatseq_flow.step_classes.RNA_seq',
                            'neatseq_flow.step_classes.searching',
                            'neatseq_flow.step_classes.UCSCtools',
                            'neatseq_flow.step_classes.variants',
                            'neatseq_flow.step_classes',],
    scripts             = ['bin/neatseq_flow_monitor.py',
                            'bin/neatseq_flow.py'],
    data_files          = [('Workflows',['Workflows/mapping.yaml']),
                            ('Workflows/Sample_sets',['Workflows/PE_tabular.nsfs'])],
    install_requires    = [
                        "pyyaml >= 3.12",
                        "bunch == 1.0.1",
                        "pandas"],
    classifiers         = [
                          'Development Status :: 4 - Beta',
                          'Environment :: Console',
                          'Intended Audience :: End Users',
                          'Intended Audience :: Developers',
                          'License :: OSI Approved :: Python Software Foundation License',
                          'Operating System :: Microsoft :: Windows',
                          'Operating System :: POSIX',
                          'Programming Language :: Python',
                          ],
    )
    

    
