#!/bin/sh

# get sources
git clone https://bitbucket.org/LindenbergSW/FontDocTools
git clone https://github.com/ermader/UnicodeData
git clone https://github.com/ermader/TestArguments
git clone https://github.com/ermader/PathLib

# do the installs

for dir in FontDocTools UnicodeData TestArguments PathLib ; do
  cd $dir
  # echo installing $dir
  python setup.py install
  cd ..
done

cd  RasterSamplingTools
python setup.py install
cd ..
