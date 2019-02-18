#from distutils.core import setup
from setuptools import find_packages, setup

setup(
    name                = 'NeatSeq-Flow',
    version             = '1.6.0',
    author              = 'Menachem Sklarz',
    author_email        = 'sklarz@bgu.ac.il',
    maintainer          = 'Menachem Sklarz',
    maintainer_email    = 'sklarz@bgu.ac.il',
    url                 = 'http://neatseq-flow.readthedocs.io/en/latest/',
    description         = 'Package for creation of workflow scripts for execution on computer clusters',
    license             = 'Creative Commons Attribution-Noncommercial-Share Alike license',
    long_description    =  open('README').read(),
    download_url        = 'https://github.com/bioinfo-core-BGU/neatseq-flow3.git',
    platforms           = ["POSIX","Windows"],
    packages            = find_packages(),
    include_package_data= True,  # See  MANIFEST.in
    scripts             = ['bin/neatseq_flow_monitor.py',
                            'bin/neatseq_flow.py'],
                            # 'etc/activate.d/env_vars.sh',
                            # 'etc/deactivate.d/env_vars.sh'],
    data_files          = [('NeatSeq-Flow-Workflows',['Workflows/mapping.yaml']),
                            ('NeatSeq-Flow-Workflows/Sample_sets',['Workflows/PE_tabular.nsfs'])],
    install_requires    = [
                        "pyyaml >= 3.12",
                        "munch >= 1.0.1",
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
    

    
