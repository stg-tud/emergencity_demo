#! /bin/bash

hostapd -B /etc/hostapd/hostapd.conf
hostapd -B /etc/hostapd/hostapd_MC.conf
systemctl restart dnsmasq

sudo iptables -t nat -A POSTROUTING -o eth0 -j MASQUERADE
sudo iptables -t nat -A POSTROUTING -o wlan0 -j MASQUERADE
sudo iptables -t nat -A POSTROUTING -o wlan1 -j MASQUERADE


sudo iptables -A FORWARD -i eth0 -o wlan0 -m state --state RELATED,ESTABLISHED -j ACCEPT
sudo iptables -A FORWARD -i eth0 -o wlan1 -m state --state RELATED,ESTABLISHED -j ACCEPT

sudo iptables -A FORWARD -i wlan0 -o eth0 -m state --state RELATED,ESTABLISHED -j ACCEPT
sudo iptables -A FORWARD -i wlan1 -o eth0 -m state --state RELATED,ESTABLISHED -j ACCEPT


sudo iptables -A FORWARD -i eth0 -o wlan0 -j ACCEPT
sudo iptables -A FORWARD -i eth0 -o wlan1 -j ACCEPT

sudo iptables -A FORWARD -i wlan0 -o eth0 -j ACCEPT
sudo iptables -A FORWARD -i wlan1 -o eth0 -j ACCEPT

#docker-compose up -d
