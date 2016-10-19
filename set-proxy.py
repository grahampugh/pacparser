#!/usr/bin/python

# A script to find the proxy being used in a pac file and set the proxy and exceptions accordingly.
# see https://developer.apple.com/legacy/library/documentation/Darwin/Reference/ManPages/man8/networksetup.8.html for networksetup commands


import pacparser
import socket
import re
import subprocess

pac_file = '../proxy/g.pac'
location_name = 'Work'

# bash commands
list_locations_cmd = "sudo /usr/sbin/networksetup -listlocations"
delete_location_cmd = "sudo /usr/sbin/networksetup -deletelocation %s" % (location_name)
create_location_cmd = "sudo /usr/sbin/networksetup -createlocation %s populate" % (location_name)
switch_location_cmd = "sudo /usr/sbin/networksetup -switchlocation %s" % (location_name)
list_interfaces_cmd = "sudo /usr/sbin/networksetup -listallnetworkservices"

def extract_proxies(fh):
	proxy_exception_final = ""
	proxy_exc_buffer = ""
	for line in fh:
		line = line.strip()
		if "shExpMatch" in line or "dnsDomainIs" in line or "localHostOrDomainIs" in line or "url.substring" in line:
			byPassUrl = line.partition('"')[-1].rpartition('"')[0]
			proxy_exc_buffer += "\"%s\" " % (byPassUrl)
			#print "proxy_exc_buffer: %s" % (proxy_exc_buffer)
		if "return noproxy;" in line:
			#print "return: %s" % (proxy_exc_buffer)
			proxy_exception_final += proxy_exc_buffer
			proxy_exc_buffer = ""
		elif "return proxy" in line:
			proxy_exc_buffer = ""
	return proxy_exception_final


def run_command(command):
	#print "bash: %s" % command
	p = subprocess.Popen(command, stdout=subprocess.PIPE, shell=isinstance(command, str))
	return iter(p.stdout.readline, b'')


if __name__ == '__main__':
	# get current proxy server
	pacparser.init()

	pacparser.parse_pac(pac_file)
	output = pacparser.find_proxy('http://captive.apple.com', 'captive.apple.com')
	proxies = output.split("; ")
	proxies = [p.replace('PROXY ', '') for p in proxies]
	(main_proxy_url, main_proxy_port) = proxies[0].split(":")
	print "### Proxy set to: %s, port %s" % (main_proxy_url, main_proxy_port)

	# Create a new network location so we don't break existing settings
	if location_name in run_command(list_locations_cmd):
		run_command(delete_location_cmd)
	run_command(create_location_cmd)
	run_command(switch_location_cmd)

	# Get list of all the interfaces
	list_network_services = run_command(list_interfaces_cmd)
	for net_service in list_network_services:
		net_service = net_service.strip()

		# bash commands we couldn't set globally
		turnoff_autoproxy_cmd = "sudo /usr/sbin/networksetup -setautoproxystate \"%s\" off" % (net_service)
		remove_autoproxy_discovery_cmd = "sudo /usr/sbin/networksetup -setproxyautodiscovery \"%s\" off" % (net_service)
		remove_autoproxy_url_cmd = "sudo /usr/sbin/networksetup -setautoproxyurl \"%s\" \"\"" % (net_service)
		set_webproxy_cmd = "sudo /usr/sbin/networksetup -setwebproxy \"%s\" %s %s" % (net_service, main_proxy_url, main_proxy_port)
		set_securewebproxy_cmd = "sudo /usr/sbin/networksetup -setsecurewebproxy \"%s\" %s %s" % (net_service, main_proxy_url, main_proxy_port)
		with open(pac_file) as fh:
			set_proxybypass_cmd = "sudo /usr/sbin/networksetup -setproxybypassdomains \"%s\" %s" % (net_service, extract_proxies(fh))

		if "*" not in net_service:
			# Clear the autoproxy settings
			run_command(turnoff_autoproxy_cmd)
			run_command(remove_autoproxy_discovery_cmd)
			run_command(remove_autoproxy_url_cmd)
			# set the proxy
			run_command(set_webproxy_cmd)
			run_command(set_securewebproxy_cmd)
			run_command(set_proxybypass_cmd)
			# get exceptions

