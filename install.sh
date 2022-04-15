#!/bin/sh

clone_if_needed(){
    local repo=$1
    local dir_name=$(basename $repo)

    if [ ! -d $dir_name ]
    then
    git clone $repo
    else
    echo "Directory $dir_name already exists."
    fi
}

install_dirs(){
    local dir
    for dir in $* ; do
        cd $dir
        python setup.py install
        cd ..
    done
}

# create the virtual environment if it doesn't exist
venv_dir="FontTools-env"
if [ ! -d $venv_dir ] ; then
    python3 -m venv $venv_dir
fi

# activate the virtual environment
source $venv_dir/bin/activate

# get sources if needed
clone_if_needed https://bitbucket.org/LindenbergSW/FontDocTools
clone_if_needed https://github.com/ermader/UnicodeData
clone_if_needed https://github.com/ermader/TestArguments
clone_if_needed https://github.com/ermader/PathLib

# It seems to work better to install the required libraries for FontDocTools before running setup.
pip install fonttools pyobjc-core pyobjc-framework-Cocoa pyobjc-framework-Quartz pyobjc-framework-CoreText

# Install FontDocTools, UnicodeData, TestArguments, PathLib
install_dirs FontDocTools UnicodeData TestArguments PathLib

# It also seems to work better to install the required libraries for RasterSamplingTools before running setup
pip install numpy statsmodels scipy openpyxl matplotlib

# Finally, install RasterSamplingTools
install_dirs RasterSamplingTools

echo
echo "Installation complete!"
echo "Remember to run the command \"source $venv_dir/bin/activate\" before running any of the scripts."
echo
