#!/usr/bin/python

# A script to find the proxy being used

import pacparser
import socket
import re
import subprocess

pac_file = 'examples/test.pac'

IP_MATCHER = re.compile(r"(\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3})")

def extract_proxies(fh):
	proxy_exception_final = ""
	proxy_exc_buffer = ""
	for line in fh:
		line = line.strip()
		match = IP_MATCHER.findall(line)
		if "return " in line:
			if "\"DIRECT" in line:
				proxy_exception_final += proxy_exc_buffer
			proxy_exc_buffer = ""
		elif len(match) == 2:
			ip, mask = match
			#print "%s/%s" % (ip, mask)
			proxy_exc_buffer += "\"%s/%s\" " % (ip, mask)
		else:
			pass
	print "/usr/sbin/networksetup -setproxybypassdomains %s" % (proxy_exception_final)


def run_command(command):
	p = subprocess.Popen(command, stdout=subprocess.PIPE, shell=isinstance(command, str))
	return iter(p.stdout.readline, b'')


if __name__ == '__main__':
	# get current IP address
	ip_addr = socket.gethostbyname(socket.getfqdn())
	print "Preferred IP Address: %s" % (ip_addr)

	# get current proxy server
	pacparser.init()

	pacparser.parse_pac('examples/test.pac')
	output = pacparser.find_proxy('http://www.manugarg.com', 'www.manugarg.com')
	proxies = output.split("; ")
	proxies = [p.replace('PROXY ', '') for p in proxies]

	# Get list of all the interfaces
	bash_command = "/usr/sbin/networksetup -listallnetworkservices"
	for linea in run_command(bash_command):
		linea = linea.strip()
		if "*" not in linea:
			print "/usr/sbin/networksetup -setwebproxy \"%s\" %s" % (linea, proxies[0])
			# see https://developer.apple.com/legacy/library/documentation/Darwin/Reference/ManPages/man8/networksetup.8.html

	# get exceptions
	with open(pac_file) as fh:
		extract_proxies(fh)
