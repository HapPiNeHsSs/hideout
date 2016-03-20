#! /bin/sh

APPS="hideout"

for APP in ${APPS}; do
	echo killing ${APP}...
	if kill `cat ${APP}.pid`; then
		echo ...done
	else
		echo ...failed
	fi
done

