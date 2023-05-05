#!/usr/bin/bash
#
# Purpose of this script is to update core in the venv with an arbitrary branch of core.
#
# In addition to  pull and `make install` further adjustments are necessary regarding numpy and
# shapely dependencies
BRANCH="processor-server"

cd ~/repos/ocrd_all/core
git pull origin $BRANCH
git switch $BRANCH
. ~/repos/ocrd_all/venv/bin/activate
make install
pip install -Iv numpy==1.23.5
pip install -Iv shapely==1.8.5
deactivate
. ~/repos/ocrd_all/venv/sub-venv/headless-tf1/bin/activate
make install
pip install -Iv numpy==1.23.5
deactivate
