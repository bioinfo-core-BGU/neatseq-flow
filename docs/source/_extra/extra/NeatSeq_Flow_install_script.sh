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

if [[ "$1" == "-h" || "$1" == "--help" ]]; then
    echo -e $USAGE
    exit
fi


if [[ $1 =~ ^te ]]; then
    # Make a directory for conda installation
    mkdir NeatSeq_Flow_install; cd NeatSeq_Flow_install;
    # Download and execute conda installer into current directory:
    wget https://repo.continuum.io/miniconda/Miniconda3-latest-Linux-x86_64.sh
    CURRENT_DIR=$(readlink -f .)
    sh Miniconda3-latest-Linux-x86_64.sh -b -f -p $CURRENT_DIR
    PREFIX="$CURRENT_DIR/bin"
    CONDA_DIR=$CURRENT_DIR
elif [[ $1 =~ ^pe ]]; then
    # Add current directory to path
    PREFIX="$HOME/miniconda3/bin"
    CONDA_DIR="$HOME/miniconda3"

    if [[ -d $PREFIX ]]; then
        echo -e "miniconda already installed in " $PREFIX ". Using existing installation."
    else
        # Download and execute conda installer into current directory:
        wget https://repo.continuum.io/miniconda/Miniconda2-latest-Linux-x86_64.sh
        sh Miniconda2-latest-Linux-x86_64.sh -b -f
        echo "Adding miniconda to path in .bashrc"
        echo export PATH=\"$PREFIX:\$PATH\" >> $HOME/.bashrc
    fi

else
    echo -e $USAGE
fi

# Add current directory to path
PATH="$PREFIX:$PATH"

# Install git
conda install -y -c anaconda git


# Get NeatSeq_Flow installer and create environment:
# wget http://neatseq-flow.readthedocs.io/en/latest/extra/NeatSeq_Flow_conda_env.yaml
# TODO: Change to readthedocs location when hooked to neatseq-flow3!!!
wget https://raw.githubusercontent.com/bioinfo-core-BGU/neatseq-flow3/master/docs/source/_extra/extra/NeatSeq_Flow_conda_env.yaml
conda env create --force -p $CONDA_DIR/envs/NeatSeq_Flow -f NeatSeq_Flow_conda_env.yaml

## Get NeatSeq_Flow_GUI installer and create environment:
#wget https://raw.githubusercontent.com/bioinfo-core-BGU/NeatSeq-Flow-GUI/master/NeatSeq_Flow_GUI_installer.yaml
#conda env create --force -f NeatSeq_Flow_GUI_installer.yaml


cat << CONTINUE1
# Successfuly installed....
CONTINUE1

if [[ $1 =~ ^te ]]; then

cat << CONTINUE2
# Add conda to path with:

PATH="$PREFIX:\$PATH"

# You have to do this each time you want to restart the environment
CONTINUE2

fi

cat << CONTINUE3

# Activate the environment with:

source activate $CONDA_DIR/envs/NeatSeq_Flow

# Enter the GUI with:

NeatSeq_Flow_GUI.py

# If you get the following or similar message when executing the GUI...
#     'Could not detect a suitable backend...'
# ...you need to either install a graphical backend or use NeatSeq-Flow's command-line version, as follows:

neatseq_flow.py --help

# To deactivate the environment:

conda deactivate

CONTINUE3

if [[ $1 =~ ^te ]]; then

cat << CONTINUE4
# To remove the installation:

rm -rf $CURRENT_DIR/

CONTINUE4

cd -
fi



