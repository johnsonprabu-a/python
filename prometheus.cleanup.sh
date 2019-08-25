#!/bin/bash

pkill -9 prometheus
rm -rf /etc/prometheus/
rm /usr/local/bin/prom*
rm -rf /var/lib/prometheus/
rm -rf /opt/prometheus*
rm /etc/systemd/system/prometheus.service

