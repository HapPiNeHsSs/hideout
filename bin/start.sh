#! /bin/sh
APPS="hideout"

for APP in ${APPS}; do
	echo starting ${APP}...
	if twistd -y ${APP}.tac --pid ${APP}.pid; then
		echo ...done
	else
		echo ...failed
	fi
done

