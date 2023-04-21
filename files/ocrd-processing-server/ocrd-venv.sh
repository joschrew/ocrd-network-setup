#!/usr/bin/bash -e

# Script to create a python-venv with ocrd and processors installed
#
# Script installes python3.7 and system-requirements to run ocrd and its processors. Also this
# script is supposed to be used to update the processors, but that is not working proplery yet

DEPS="python3.7 python3.7-venv python3.7-dev make parallel git wget imagemagick libgeos-dev "
DEPS+="libtesseract-dev libleptonica-dev tesseract-ocr-eng tesseract-ocr-script-frak tesseract-ocr "
DEPS+="automake xmlstarlet ca-certificates libmagick++-6.q16-dev libgraphicsmagick++1-dev libboost-dev"
VENV="$HOME/venv-ocrd"
REPOS="$HOME/repos"

# update processor repositories (maybe later this can be used as a script parameter)
UPDATE=0

# read cmd opts
while getopts ":u" param; do
	case "${param}" in
		u) UPDATE=1;;
	esac
done
shift $((OPTIND -1))

# Install all dependencies for OCR-D with apt
function install_dependencies() {
	# add deadsnakes ppa to install python3.7
	add_deadsnakes=0
	find /etc/apt/ -name *.list | xargs cat | grep  "^[[:space:]]*deb" | grep "deadsnakes/ppa" -q || add_deadsnakes=1
	if test $add_deadsnakes -ne 0; then
		sudo add-apt-repository -y ppa:deadsnakes/ppa
	fi
	# add alex-p ppa to install tesseract-stuff
	add_alexp=0
	find /etc/apt/ -name *.list | xargs cat | grep  "^[[:space:]]*deb" | grep "alex-p/tesseract-ocr" -q || add_alexp=1
	if test $add_alexp -ne 0; then
		sudo add-apt-repository -y ppa:alex-p/tesseract-ocr
	fi

	# Install requierements(DEPS)
	for package in $DEPS; do
		is_installed=1
		dpkg -s $package || is_installed=0
		if test $is_installed -eq 0; then
			sudo apt install -y $package
		fi
	done
}

# Create venv if not existing
function create_venv() {
	if ! test -d $VENV; then
		python3.7 -m venv $VENV
	fi

	mkdir -p $REPOS
}

# Clone and optional update github repo
#
# param1: destination dir-name of repo
# param2: git-clone-url
# param3: update (pull) repo (not yet implemented)
# param4: optional. Branch to checkout. Needed to get the PR
function pull_package {
	# clone repo
	if ! test -d $REPOS/$1; then
		git clone $2 $REPOS/$1
	fi

	# checkout specific branch
	if test $# -gt 3 && ! test -z $4; then
		cd $REPOS/$1
		git checkout $4
		cd -
	fi

	if test $3 -ne 0; then
		cd $REPOS/$1
		echo "try to git pull repo: $1"
		output=$(git pull --ff-only)
		cd -
		if grep -q "Already up to date" <<< $output; then
			return 1
		fi
	fi
	return 0
}

# Install procesors: Clone / update core and all processors and then (re)install
function install_processors() {
	# clone processors
	update_core=0
	pull_package ocrd_core https://github.com/OCR-D/core.git $UPDATE dev-processing-broker || update_core=$?

	# this script has set -e so fails on errors. this `pull_package ... || update_x=$?` is to make
	# return nonzero possible. pipefail is of so only last exit code (when using pipe or `||`) has to be
	# zero
	update_cis=0
	pull_package ocrd_cis https://github.com/cisocrgroup/ocrd_cis $UPDATE || update_cis=$?
	update_anybaseocr=0
	pull_package ocrd_anybaseocr https://github.com/OCR-D/ocrd_anybaseocr.git $UPDATE || update_anybaseocr=$?
	update_wrap=0
	pull_package ocrd_wrap https://github.com/bertsky/ocrd_wrap.git $UPDATE || update_wrap=$?
	update_tesserocr=0
	pull_package ocrd_tesserocr https://github.com/OCR-D/ocrd_tesserocr.git $UPDATE || update_tesserocr=$?
	update_calamari=0
	pull_package ocrd_calamari https://github.com/OCR-D/ocrd_calamari.git $UPDATE || update_calamari=$?
	update_fileformat=0
	pull_package ocrd_fileformat https://github.com/OCR-D/ocrd_fileformat.git $UPDATE || update_fileformat=$?
	update_olena=0
	pull_package ocrd_olena https://github.com/OCR-D/ocrd_olena.git $UPDATE || update_olena=$?
	update_segment=0
	pull_package ocrd_segment https://github.com/OCR-D/ocrd_segment.git $UPDATE || update_segment=$?

	# install processors
	# for updating the installation is simply run again, maybe that is not ideal?
	. $VENV/bin/activate

	cd $REPOS/ocrd_core
	if ! test -f $VENV/bin/ocrd || test $update_core -ne 0; then
		make install-dev  # TODO: change for after development phase?!
	fi

	cd $REPOS/ocrd_cis
	if ! test -f $VENV/bin/ocrd-cis-ocropy-binarize || test $update_cis -ne 0; then
		make install
	fi
	cd $REPOS/ocrd_anybaseocr
	if ! test -f $VENV/bin/ocrd-anybaseocr-crop || test $update_anybaseocr -ne 0; then
		make install
	fi
	cd $REPOS/ocrd_wrap
	if ! test -f $VENV/bin/ocrd-skimage-binarize || test $update_wrap -ne 0; then
		make install
	fi
	cd $REPOS/ocrd_tesserocr
	if ! test -f $VENV/bin/ocrd-tesserocr-deskew || test $update_tesserocr -ne 0; then
		make install
	fi
	cd $REPOS/ocrd_calamari
	if ! test -f $VENV/bin/ocrd-calamari-recognize || test $update_calamari -ne 0; then
		make install
	fi
	cd $REPOS/ocrd_fileformat
	if ! test -f $VENV/bin/ocrd-fileformat-transform || test $update_fileformat -ne 0; then
		git submodule update --init --recursive
		# make install reinstalls ocrd-core which would be redundant
		make install-fileformat install-tools
	fi
	cd $REPOS/ocrd_olena
	if ! test -f $VENV/bin/ocrd-olena-binarize || test $update_olena -ne 0; then
		make install
	fi
	cd $REPOS/ocrd_segment
	if ! test -f $VENV/bin/ocrd-segment-repair || test $update_segment -ne 0; then
		pip install .
	fi

	deactivate
}


install_dependencies
create_venv
install_processors
