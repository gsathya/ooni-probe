#!/usr/bin/env python
# -*- coding: UTF-8
"""
    nodes
    *****

    This contains all the code related to Nodes
    both network and code execution.

    :copyright: (c) 2012 by Arturo Filastò, Isis Lovecruft.
    :license: see LICENSE for more details.

"""

import os
from binascii import hexlify

try:
    import paramiko
except:
    print "Error: module paramiko is not installed."
from pprint import pprint
try:
    import pyXMLRPCssh
except:
    print "Error: module pyXMLRPCssh is not installed."
import sys
import socks
import xmlrpclib

class Node(object):
    def __init__(self, address, port):
        self.address = address
        self.port = port

"""
[]: node = NetworkNode("192.168.0.112", 5555, "SOCKS5")
[]: node_socket = node.wrap_socket()
"""
class NetworkNode(Node):
    def __init__(self, address, port, node_type="SOCKS5", auth_creds=None):
        self.node = Node(address,port)

        # XXX support for multiple types
        # node type (SOCKS proxy, HTTP proxy, GRE tunnel, ...)
        self.node_type = node_type
        # type-specific authentication credentials
        self.auth_creds = auth_creds

    def _get_socksipy_socket(self, proxy_type, auth_creds):
        import socks
        s = socks.socksocket()
        # auth_creds[0] -> username
        # auth_creds[1] -> password
        s.setproxy(proxy_type, self.node.address, self.node.port,
                   self.auth_creds[0], self.auth_creds[1])
        return s

    def _get_socket_wrapper(self):
        if (self.node_type.startswith("SOCKS")): # SOCKS proxies
            if (self.node_type != "SOCKS5"):
                proxy_type = socks.PROXY_TYPE_SOCKS5
            elif (self.node_type != "SOCKS4"):
                proxy_type = socks.PROXY_TYPE_SOCKS4
            else:
                print "We don't know this proxy type."
                sys.exit(1)

            return self._get_socksipy_socket(proxy_type)
        elif (self.node_type == "HTTP"): # HTTP proxies
            return self._get_socksipy_socket(PROXY_TYPE_HTTP)
        else: # Unknown proxies
            print "We don't know this proxy type."
            sys.exit(1)

    def wrap_socket(self):
        return self._get_socket_wrapper()

class CodeExecNode(Node):
    def __init__(self, address, port, node_type, auth_creds):
        self.node = Node(address,port)

        # node type (SSH proxy, etc.)
        self.node_type = node_type
        # type-specific authentication credentials
        self.auth_creds = auth_creds

    def add_unit(self):
        pass

    def get_status(self):
        pass

class PlanetLab(Node, CodeExecNode):
    def __init__(self, address, auth_creds, ooni):
        self.node = Node(address, 22)
        self.auth_creds = auth_creds

        self.config = ooni.config
        self.logger = ooni.logger
        self.name = "PlanetLab"

    def _api_auth(self):
        api_server = xmlrpclib.ServerProxy('https://www.planet-lab.org/PLCAPI/')
        auth = {}
        ## should be changed to separate node.conf file
        auth['Username'] = self.config.main.pl_username
        auth['AuthString'] = self.config.main.pl_password
        auth['AuthMethod'] = "password"
        authorized = api_server.AuthCheck(auth)

        if authorized:
            print 'We are authorized!'
            return auth
        else:
            print 'Authorization failed. Please check your settings for pl_username and pl_password in the ooni-probe.conf file.'

    def _search_for_nodes(self, node_filter=None):
        api_server = xmlrpclib.ServerProxy('https://www.planet-lab.org/PLCAPI/', allow_none=True)
        node_filter = {'hostname': '*.cert.org.cn'}
        return_fields = ['hostname', 'site_id']
        all_nodes = api_server.GetNodes(self.api_auth(), node_filter, boot_state_filter)
        pprint(all_nodes)
        return all_nodes

    def _add_nodes_to_slice(self):
        api_server = xmlrpclib.ServerProxy('https://www.planet-lab.org/PLCAPI/', allow_none=True)
        all_nodes = self.search_for_nodes()
        for node in all_nodes:
            api_server.AddNode(self.api_auth(), node['site_id'], all_nodes)
            print 'Adding nodes %s' % node['hostname']

    def _auth_login(slicename, machinename):
        """
        Attempt to authenticate to the given PL node, slicename and
        machinename, using any of the private keys in ~/.ssh/
        """

        agent = paramiko.Agent()
        agent_keys = agent.get_keys()
        if len(agent_keys) == 0:
            return

        for key in agent_keys:
            print 'Trying ssh-agent key %s' % hexlify(key.get_fingerprint()),
            try:
                paramiko.transport.auth_publickey(machinename, slicename)
                print 'Public key authentication to PlanetLab node %s successful.' % machinename,
                return
            except paramiko.SSHException:
                print 'Public key authentication to PlanetLab node %s failed.' % machinename,

    def _ssh_to_node(slicename, machinename, sshkeypasswd):
        """
        Attempt to make an SSH2 connection to added PL nodes.
        """
        
        self.hosts = []
        self.connections = []

        if slicename, machinename, sshkeypasswd:
            Node(machinename, 22)
            for node in self.node:
                self.hosts.append([slicename, machinename, sshkeypasswd])
        
        for host in self.hosts:
            client = paramiko.SSHClient()
            if (self.config.main.auto_add_new_hosts == 1):
                client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
            client.load_system_host_keys()
            client.connect(host[1], username=host[0], password=host[2])
            self.connections.append(client)

        return (self.hosts, self.connections)

    def _ssh_and_run_(slicename, machinename, sshkeypasswd, command):
        """
        Attempt to make an SSH2 connection to PL nodes, and run
        commands.
        """
        
        PlanetLab._ssh_to_node(slicename, machinename, sshkeypasswd)

        if command:
            for host, conn in zip(self.hosts, self.connections):
                stdin, stdout, stderr = conn.exec_command(command)
                stdin.close()
                for line in stdout.read().splitlines():
                    print 'host: %s: %s' % (host[0], line)

        for conn in self.connections:
            conn.close()

    def send_files_to_node(slicename, machinename, sshkeypasswd, 
                           remotefile, localfile):
        """Attempt to stfp files to the PL node."""
        
        PlanetLab._ssh_to_node(slicename, machinename, sshkeypasswd)
        
        client = paramiko.SSHClient()
        sftp = client.open_sftp()
        sftp.get(localfile, remotefile)
        sftp.close()

    def add_unit:
        pass

    def get_status:
        pass
