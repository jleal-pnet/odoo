#!/usr/bin/env bash

# Write the server configuration
function connect () {
	SERVER="${1}"
	CURRENT_SERVER_FILE=/home/pi/odoo-remote-server.conf
	HOSTS=/root_bypass_ramdisks/etc/hosts
	HOST_FILE=/root_bypass_ramdisks/etc/hostname
	HOSTNAME="$(hostname)"
	IOT_NAME="${2}"
	sudo mount -o remount,rw /
	sudo mount -o remount,rw /root_bypass_ramdisks
	echo "${SERVER}" > ${CURRENT_SERVER_FILE}
	sudo sed -i "s/${HOSTNAME}/${IOT_NAME}/g" ${HOSTS}
	echo "${IOT_NAME}" > /tmp/hostname
	sudo cp /tmp/hostname "${HOST_FILE}"
	sudo hostname "${IOT_NAME}"
	sudo mount -o remount,ro /
	sudo mount -o remount,ro /root_bypass_ramdisks
	sudo service odoo restart
}

connect "${1}" "${2}" &