# Script for easy installation of NeatSeq-Flow and it's GUI with conda
# Will install all required packages into a dedicated directory ('NeatSeq_Flow_install') inside the current directory.
# Written by Menachem Sklarz, 4/2/19

USAGE="USAGE: sh NeatSeq_Flow_install_script.sh ['temporary'|'permanent']\n\n

A script for complete installation of NeatSeq-Flow and it's GUI.\n
For the purpose, Miniconda will be installed. The location of Miniconda installation is determined by the first argument:\n\n

If 'temporary' is passed, everything is installed within a directory called 'NeatSeq_Flow_install' within the current directory.\n
If 'permanent' is passed, installation of Miniconda is done in the default location in the current user's home.\n\n
"
set -eu

if [ $# == 0 ]; then
    echo -e $USAGE
    exit
fi

if [[ $1 =~ ^te ]]; then
    # Make a directory for conda installation
    mkdir NeatSeq_Flow_install; cd NeatSeq_Flow_install;
    # Download and execute conda installer into current directory:
    wget https://repo.continuum.io/miniconda/Miniconda2-latest-Linux-x86_64.sh
    CURRENT_DIR=$(readlink -f .)
    sh Miniconda2-latest-Linux-x86_64.sh -b -f -p $CURRENT_DIR
    PREFIX="$CURRENT_DIR/bin"
elif [[ $1 =~ ^pe ]]; then
    # Add current directory to path
    PREFIX="$HOME/miniconda2/bin"

    if [[ -d $PREFIX ]]; then
        echo -e "miniconda already installed in " $PREFIX ". Using existing installation."
    else
        # Download and execute conda installer into current directory:
        wget https://repo.continuum.io/miniconda/Miniconda2-latest-Linux-x86_64.sh
        sh Miniconda2-latest-Linux-x86_64.sh -b -f
    fi

else
    echo -e $USAGE
fi

# Add current directory to path
PATH="$PREFIX:$PATH"

# Install git
conda install -y -c anaconda git

# Get NeatSeq_Flow installer and create environment:
wget http://neatseq-flow.readthedocs.io/en/latest/extra/NeatSeq_Flow_conda_env.yaml
conda env create --force -f NeatSeq_Flow_conda_env.yaml

# Get NeatSeq_Flow_GUI installer and create environment:
wget https://raw.githubusercontent.com/bioinfo-core-BGU/NeatSeq-Flow-GUI/master/NeatSeq_Flow_GUI_installer.yaml
conda env create --force -f NeatSeq_Flow_GUI_installer.yaml

echo -e "To use the GUI, run the following commands:\n-------------------"
echo -e '    PATH="'$PREFIX':$PATH"'
echo -e '    source activate NeatSeq_Flow_GUI\n\n'
echo -e 'Then, enter the GUI with the following command:'
echo -e '    NeatSeq_Flow_GUI.py\n\n'
echo -e "If you get the following or similar message when executing the GUI..."
echo -e '\tCould not detect a suitable backend...'
echo -e "...you need to either install a graphical backend or use NeatSeq-Flow's command-line version, as follows:\n\n"

echo -e "To use the NeatSeq-Flow without the GUI:\n-------------------"
echo -e '    PATH="'$PREFIX':$PATH"'
echo -e '    source activate NeatSeq_Flow'
echo -e 'Then, get usage for NeatSeq-Flow with the following command:'
echo -e '    neatseq_flow.py --help\n\n'

if [[ $1 =~ ^te ]]; then
    cd -
fi



