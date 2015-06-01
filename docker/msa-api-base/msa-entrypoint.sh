#!/bin/sh
set -e

PYTHON_VERSION=3.4
PYTHON=python$PYTHON_VERSION
PYVENV=pyvenv-$PYTHON_VERSION
PIP=pip3

MSA_DATA=/data
MSA_TMP=/data/.msa-tmp
MSA_DIST=$MSA_DATA/dist
MSA_DEPLOY=$MSA_DATA/deploy

install_etc () {
	echo "Installing etc..."
	if [ ! -d "$MSA_DIST/etc" ]; then
		echo "ERROR: $MSA_DIST/etc does not exist."
		exit 1
	fi

	if [ -d "$MSA_DEPLOY/etc" ]; then
		echo "WARNING: $MSA_DEPLOY/etc already exists. Skip installing etc."
	fi
	cp -r $MSA_DIST/etc $MSA_DEPLOY/
}

source_msa_env () {
	if [ ! -f $MSA_DEPLOY/etc/msa-env ]; then
		echo "ERROR: $MSA_DEPLOY/etc/msa-env does not exist."
		exit 1
	fi
	. $MSA_DEPLOY/etc/msa-env

	if [ -z "$MSA_APP_NAME" ]; then
		echo "ERROR: MSA_APP_NAME must be set to a non-empty value in $MSA_DEPLOY/etc/msa-env."
		exit 1
	fi
}

create_pyvenv () {
	echo "Creating Python venv in $MSA_DEPLOY/env..."
	$PYVENV $MSA_DEPLOY/env
}

enter_pyvenv() {
	echo "Entering Python venv in $MSA_DEPLOY/env..."
	. $MSA_DEPLOY/env/bin/activate
}

install_python_packages () {
	if [ ! -d "$MSA_DIST/packages" ]; then
		echo "WARNING: $MSA_DIST/packages does not exist. No Python packages will be installed."
		return 0
	fi

	echo "Installing Python packages..."
	for PACKAGE in `ls $MSA_DIST/packages/`; do
		echo "Installing $PACKAGE..."
		$PIP install $MSA_DIST/packages/$PACKAGE
	done
}

copy_application () {
	if [ -d "$MSA_DEPLOY/$MSA_APP_NAME" ]; then
		echo "WARNING: $MSA_DEPLOY/$MSA_APP_NAME already exists. Skip copying application from $MSA_DIST/$MSA_APP_NAME.tar.gz"
		return 0
	fi

	echo "Extracting $MSA_DIST/$MSA_APP_NAME.tar.gz to $MSA_TMP/"
	cd $MSA_TMP && tar zxvf $MSA_DIST/$MSA_APP_NAME.tar.gz
	echo "Moving $MSA_TMP/$MSA_APP_NAME to $MSA_DIST/$MSA_APP_NAME"
	mv $MSA_TMP/$MSA_APP_NAME $MSA_DEPLOY
}

init_application () {
	if [ ! -e "$MSA_DEPLOY/django-static" ]; then
		echo "Generating static files for the django application..."
		cd $MSA_DEPLOY/$MSA_APP_NAME && $PYTHON manage.py collectstatic
	fi

	echo "Creating $MSA_DATA/db and $MSA_DATA/log..."
	mkdir -p $MSA_DATA/db
	mkdir -p $MSA_DATA/log

	if [ -f "$MSA_DEPLOY/$MSA_APP_NAME/db.sqlite3" ] && \
	    [ ! -e "$MSA_DATA/db/db.sqlite3" ]; then
		echo "Copying $MSA_DEPLOY/$MSA_APP_NAME/db.sqlite3 to $MSA_DATA/db/db.sqlite3"
		cp $MSA_DEPLOY/$MSA_APP_NAME/db.sqlite3 $MSA_DATA/db/
	fi
}

setup () {
	mkdir -p $MSA_DEPLOY
	install_etc
	source_msa_env
	create_pyvenv
	enter_pyvenv
	install_python_packages
	copy_application
	init_application
}

if [ "$1" = "setup" ]; then
	echo "Setup api server."
	setup
	exec /bin/true
elif [ "$1" = "start" ]; then
	echo "Start api server."
	exec /bin/true
elif [ "$1" = "exec" ]; then
	shift
	echo "Exec $@."
	exec $@
else
	echo "ERROR: Cannot recognize task $@."
	echo "Usage: entrypoint.sh setup|exec"
	exit 1
fi

echo "ERROR: Should not see this message!"
exit 1