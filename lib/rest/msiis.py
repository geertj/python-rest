#
# This file is part of Python-REST. Python-REST is free software that is
# made available under the MIT license. Consult the file "LICENSE" that is
# distributed together with this file for the exact licensing terms.
#
# Python-REST is copyright (c) 2010 by the Python-REST authors. See the file
# "AUTHORS" for a complete overview.

import sys
import os
import os.path
import stat
import inspect
import py_compile

from xml.etree import ElementTree as etree
from xml.etree.ElementTree import Element, SubElement, ElementTree
from optparse import OptionParser

from win32security import (GetNamedSecurityInfo, SetNamedSecurityInfo,
                           LookupAccountName, ACL_REVISION_DS, SE_FILE_OBJECT,
                           DACL_SECURITY_INFORMATION, OBJECT_INHERIT_ACE,
                           CONTAINER_INHERIT_ACE, INHERIT_ONLY_ACE)
from win32file import CreateDirectory, FindFilesW
from win32con import FILE_ATTRIBUTE_DIRECTORY
from ntsecuritycon import (FILE_GENERIC_READ, FILE_GENERIC_WRITE,
                           FILE_ADD_SUBDIRECTORY, FILE_TRAVERSE, DELETE)
from isapi_wsgi import ISAPIThreadPoolHandler
from isapi.install import (ISAPIParameters, ScriptMapParams,
                           VirtualDirParameters, HandleCommandLine)
from pywintypes import error as WindowsError

from rest.server import re_module, program_name
from rest.util import import_module


webroot = r'C:\inetpub\wwwroot'
eggdir = r'C:\Documents and Settings\Default User\Application Data' \
         r'\Python-Eggs'


class Error(Exception):
    """ISAPI installation error."""


class Extension(ISAPIThreadPoolHandler):
    """ISAPI Extension."""

    def TerminateExtension(self, status):
        self.rootapp.shutdown()
        ISAPIThreadPoolHandler.TerminateExtension(self, status)


def create_isapi_handler(fname, opts):
    """Generate a Python script that will be out ISAPI entry point."""
    fout = open(fname, 'w')
    fout.write('## This file is auto-generated and will be overwritten\n')
    fout.write('from rest.msiis import Extension\n')
    fout.write('from rest.util import setup_logging\n')
    fout.write('from %s import %s\n' % (opts.modname, opts.classname))
    fout.write('def __ExtensionFactory__():\n')
    if opts.debug:
        fout.write('  import win32traceutil\n')
    fout.write('  setup_logging(%s)\n' % opts.debug)
    fout.write('  return Extension(%s)\n' % opts.classname)
    fout.close()
    py_compile.compile(fname)
    print 'ISAPI handler created.'


def create_egg_cache(eggdir):
    """Create egg cache."""
    # Make sure there is an egg cache that is writeable to the IUSR
    # account.
    try:
        st = os.stat(eggdir)
    except OSError:
        st = None
    if st is not None:
        if not stat.S_ISDIR(st.st_mode):
            raise Error, 'Egg cache is not a directory.'
        print 'Egg cache exists.'
    else:
        CreateDirectory(eggdir, None)
        print 'Egg cache created.'

    # Change/check the ACL
    try:
        target = LookupAccountName(None, 'IUSR')[0]  # IIS7
    except WindowsError:
        hostname = LookupAccountName(None, 'Administrator')[1]  # get host name
        target = LookupAccountName(None, 'IUSR_%s' % hostname)[0]  # IIS6
    desc = GetNamedSecurityInfo(eggdir, SE_FILE_OBJECT,
                                DACL_SECURITY_INFORMATION)
    acl = desc.GetSecurityDescriptorDacl()
    for i in range(acl.GetAceCount()):
        ace = acl.GetAce(i)
        if ace[2] == target:
            break  # assume the ACE is correct
    else:
        flags = OBJECT_INHERIT_ACE|CONTAINER_INHERIT_ACE
        access = FILE_GENERIC_READ|FILE_GENERIC_WRITE|FILE_ADD_SUBDIRECTORY| \
                 FILE_TRAVERSE|DELETE
        acl.AddAccessAllowedAceEx(ACL_REVISION_DS, flags, access, target)
        SetNamedSecurityInfo(eggdir, SE_FILE_OBJECT, DACL_SECURITY_INFORMATION,
                             None, None, acl, None)


def fix_egg_permissions(dir):
    """Fixup egg file permissions."""
    # On Windows 2003, it appears that *.egg files do not get an ACE that
    # gives READ access to "Users". *.egg directories seem to be OK, as well
    # as egg files under Windows 2008.
    glob = os.path.join(dir, '*.egg')
    result = FindFilesW(glob)
    nfixup = 0
    target = LookupAccountName(None, 'Users')[0]
    for res in result:
        if res[0] & FILE_ATTRIBUTE_DIRECTORY:
            continue
        fname = os.path.join(dir, res[8])
        desc = GetNamedSecurityInfo(fname, SE_FILE_OBJECT,
                                    DACL_SECURITY_INFORMATION)
        acl = desc.GetSecurityDescriptorDacl()
        for i in range(acl.GetAceCount()):
            ace = acl.GetAce(i)
            if ace[2] == target:
                break  # assume the ACE is correct
        else:
            access = FILE_GENERIC_READ
            acl.AddAccessAllowedAce(ACL_REVISION_DS, access, target)
            SetNamedSecurityInfo(fname, SE_FILE_OBJECT, DACL_SECURITY_INFORMATION,
                                 None, None, acl, None)
            nfixup += 1
    if nfixup:
        print 'Fixed %d eggs with wrong permissions.' % nfixup
    else:
        print 'All eggs have correct permissions.'


def update_web_config(webroot):
    fname = os.path.join(webroot, 'web.config')
    try:
        fin = open(fname, 'r')
        tree = ElementTree()
        tree.parse(fin)
        fin.close()
    except OSError:
        config = Element('configuration')
        tree = ElementTree(node)
    config = tree.getroot()
    webserver = config.find('./system.webServer')
    if webserver is None:
        webserver = SubElement(root, 'system.webServer')
    errors = webserver.find('./httpErrors')
    if errors is None:
        errors = SubElement(webserver, 'httpErrors')
    errors.attrib['errorMode'] = 'Custom'
    errors.attrib['existingResponse'] = 'PassThrough'
    errors.tail = '\n' + ' '*4
    static = webserver.find('./staticContent')
    if static is not None:
        for node in static:
            if node.tag == 'mimeMap':
                static.remove(node)
        if len(static) == 0:
            webserver.remove(static)
    fout = open(fname, 'w')
    tree.write(fout)
    fout.close()
    print 'Updated web.config.'


def main():
    parser = OptionParser(usage='%prog [options] install | remove',
                          prog=program_name())
    parser.add_option('-d', '--debug', action='store_true')
    parser.add_option('-m', '--module', dest='module',
                      help='use application module:classname')
    parser.set_default('debug', False)
    opts, args = parser.parse_args()
    sys.argv[1:] = args
    if not opts.module:
        parser.error('you need to specify --module')
    mobj = re_module.match(opts.module)
    if not mobj:
        parser.error('specify --module as module:classname')
    opts.modname = mobj.group(1)
    opts.classname = mobj.group(2)
    module = import_module(opts.modname)
    if module is None:
        parser.error('could not load module %s' % modname)
    if not hasattr(module, opts.classname):
        parser.error('could not load class %s from module' % opts.classname)
    params = ISAPIParameters()
    sm = ScriptMapParams(Extension='*', Flags=0)
    vd = VirtualDirParameters(Name='api', Headers=None,
                    Description='python-rest',
                    ScriptMaps=[sm], ScriptMapUpdate='replace')
    params.VirtualDirs = [vd]
    # A DLL with the name _filename.dll is installed in the same directory as
    # the handler file.
    fname = inspect.getfile(module)
    dname, fname = os.path.split(fname)
    fname, ext = os.path.splitext(fname)
    fname = os.path.join(dname, '_%s_isapi.py' % fname)
    create_isapi_handler(fname, opts)
    HandleCommandLine(params, conf_module_name=fname)
    # Fix up some common errors
    create_egg_cache(eggdir)
    dir = os.path.join(sys.exec_prefix, 'Lib', 'site-packages')
    fix_egg_permissions(dir)
    update_web_config(webroot)
