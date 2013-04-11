#!/usr/bin/python

import sys
import os
try:
    import json
except:
    from django.utils import simplejson as json
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), os.pardir)))
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), os.pardir, os.pardir)))
import manage
os.environ['DJANGO_SETTINGS_MODULE'] = 'settings.base'

from settings import DHCP_CONFIG_OUTPUT_DIRECTORY
from dhcp.models import DHCPFile
always_push_svn = True
from libs.DHCPHelper import DHCPHelper
from dhcp.DHCP import DHCP as DHCPInterface
from systems.models import ScheduledTask
def main():
    dh = DHCPHelper()
    dhcp_scopes = []
    dhcp_scopes = dh.get_scopes_to_generate()
    print dhcp_scopes
    output_dir = DHCP_CONFIG_OUTPUT_DIRECTORY
    for scope in dhcp_scopes:
        dhcp_scope = scope.task
        try:
            dir = dhcp_scope.split("-")[0]
            output_file = '-'.join(dhcp_scope.split("-")[1:])
            final_destination_file = "%s/%s/%s_generated_hosts.conf" % (output_dir,dir, output_file)
            systems = dh.systems_by_scope(dhcp_scope)
            adapters = []
            for host in systems:
                hostname = host['hostname']
                adapters.append(dh.adapters_by_system_and_scope(hostname, dhcp_scope))
            output_text = DHCPInterface([], adapters).get_hosts()
            try:
                f = open(final_destination_file,"w")
                f.write(output_text)
                f.close()
                print "Wrote config to {0}".format(final_destination_file)
            except IOError:
                pass
            try:
                DHCPFile.objects.filter(dhcp_scope=dhcp_scope).delete()
            except:
                pass
            d = DHCPFile(dhcp_scope=dhcp_scope,file_text=output_text)
            d.save()
            scope.delete()
        except IndexError:
            scope.delete()
    if len(dhcp_scopes) > 0 or always_push_svn:
        os.chdir(output_dir)
        os.system('/usr/bin/svn update')
        os.system('/usr/bin/svn add * --force')
        os.system('/usr/bin/svn commit -m "Autogenerated addition from inventory"')
    #os.system('/usr/bin/git push origin master')


if __name__ == '__main__':
    main()

