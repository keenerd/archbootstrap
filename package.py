#!/usr/bin/env python2

from __future__ import print_function
import os, os.path
import sys
import tarfile
import time
import datetime as dt
import hashlib
import shutil
import subprocess
from collections import defaultdict

class DescParse(object):
    """
    """

    def __init__(self, desc_file):
        self.info = self.desc_load(desc_file)
        self.info = self.desc_clean(self.info)

    # bunch of stateless/static methods
    # for easier testing and modularity
    def desc_load(self, desc_file):
        "takes a file-like object, returns a messy desc"
        info = defaultdict(list)
        mode = None
        for line in desc_file:
            line = self.clean(line)
            if not line:
                continue
            if line.startswith('%'):
                mode = line.strip('%')
                continue
            info[mode].append(line)
        desc_file.close()
        return info

    def desc_clean(self, info):
        "returns a new dictionary"
        singles = 'NAME VERSION DESC URL SIZE INSTALLDATE BUILDDATE'.split()
        integers = 'SIZE INSTALLDATE BUILDDATE'.split()
        info2 = {}
        for k in singles:
            if k not in info:
                continue
            info2[k] = info[k][0]
            if k in integers:
                info2[k] = int(info2[k])
        for k,v in info.items():
            if k in info2:
                continue
            info2[k] = v
        return info2

    def clean(self, n):
        n = n.strip()
        for c in '><:=':
            n = n.partition(c)[0]
        return n


class Package:
    '''
    parse information from a pacman package
   
    member variables:
    file (string) - name of package file
    file_list (array) - list of files in the package archive
    pkginfo (dict) - package information parsed from .PKGINFO
    pkg (TarFile) -  the tarball
    '''


    def __init__ (self, file, rootpath):
        self.file = file

        if not os.path.exists(file):
            raise IOError('{} does not exist'.format(file))

        if not tarfile.is_tarfile(file):
            raise TypeError('{} is not a tar file'.format(file))

        self.pkg = tarfile.open(file)

        self.file_list = self.pkg.getnames()
        self.file_list.sort()
        if not ".PKGINFO" in self.file_list:
            raise TypeError('{} is not a package file'.format(file))

        self.__parse_pkginfo()
        self.rootpath = rootpath
        self.localname="-".join([self.pkginfo['pkgname'], self.pkginfo['pkgver']])
        self.localpath = '/'.join([rootpath, '/var/lib/pacman/local/', self.localname]) 
        self.installfile = '/'.join([self.localpath, 'install'])
        self.descfile = '/'.join([self.localpath, 'desc'])
        self.filesfile = '/'.join([self.localpath, 'files'])
        self.mtreefile = "/".join([self.localpath, "mtree"])

    def __parse_pkginfo(self):
        self.pkginfo = {}
        self.pkginfo['pkgname'] = ""
        self.pkginfo['pkgbase'] = ""
        self.pkginfo['pkgver'] = ""
        self.pkginfo['pkgdesc'] = ""
        self.pkginfo['url'] = ""
        self.pkginfo['builddate'] = ""
        self.pkginfo['installdate'] = ""
        self.pkginfo['packager'] = ""
        self.pkginfo['size'] = ""
        self.pkginfo['arch'] = ""
        self.pkginfo['force'] = ""
        self.pkginfo['validation'] = ""
        self.pkginfo['reason'] = ""
        self.pkginfo['license'] = []
        self.pkginfo['replaces'] = []
        self.pkginfo['group'] = []
        self.pkginfo['depend'] = []
        self.pkginfo['optdepend'] = []
        self.pkginfo['conflict'] = []
        self.pkginfo['provides'] = []
        self.pkginfo['backup'] = []
        self.pkginfo['makepkgopt'] = []   

        arrays = ['license', 'replaces', 'group', 'depend', 'optdepend',
                  'conflict', 'provides', 'backup', 'makepkgopt']
       
        pkginfo = self.pkg.extractfile(".PKGINFO")
        for line in pkginfo:
            if (line[0] == '#'.encode('utf-8')[0]):
                continue
            (key, value) = line.decode('utf-8').split(" = ")

            if key in arrays:
                self.pkginfo[key].append(value.strip())
            else:
                self.pkginfo[key] = value.strip()

        pkginfo.close()


    def descfile_fun(self):
        with open(self.descfile, "w") as descfile:
            print('%NAME%\n{}'.format(self.pkginfo['pkgname']), file=descfile)
            print('\n%VERSION%\n{}'.format(self.pkginfo['pkgver']), file=descfile)
            print('\n%DESC%\n{}'.format(self.pkginfo['pkgdesc']), file=descfile)
            print('\n%URL%\n{}'.format(self.pkginfo['url']), file=descfile)
            print('\n%ARCH%\n{}'.format(self.pkginfo['arch']), file=descfile)
            print('\n%BUILDDATE%\n{}'.format(self.pkginfo['builddate']), file=descfile)
            print('\n%INSTALLDATE%\n{}'.format(int(time.mktime(dt.datetime.now().timetuple()))), file=descfile)
            print('\n%PACKAGER%\n{}'.format(self.pkginfo['packager']), file=descfile)
            print('\n%SIZE%\n{}'.format(self.pkginfo['size']), file=descfile)
            if self.pkginfo['reason']:
                print('\n%REASON%\n1', file=descfile)
            if self.pkginfo['group']:
                print('\n%GROUPS%', file=descfile)
                for group in self.pkginfo['group']:
                    print("{}".format(group), file=descfile)
            print('\n%LICENSE%', file=descfile)
            for license in self.pkginfo['license']:
                print("{}".format(license), file=descfile)
            print("\n%VALIDATION%\n{}".format('gpg'), file=descfile)
            if self.pkginfo['replaces']:
                print('\n%REPLACES%', file=descfile)
                for replace in self.pkginfo['replaces']:
                    print("{}".format(replace), file=descfile)
            if self.pkginfo['depend']:
                print('\n%DEPENDS%', file=descfile)
                for depend in self.pkginfo['depend']:
                    print("{}".format(depend), file=descfile)
            if self.pkginfo['optdepend']:
                print('\n%OPTDEPENDS%', file=descfile)
                for depend in self.pkginfo['optdepend']:
                    print("{}".format(depend), file=descfile)
            if self.pkginfo['conflict']:
                print('\n%CONFLICTS%', file=descfile)
                for conflict in self.pkginfo['conflict']:
                    print("{}".format(conflict), file=descfile)
            if self.pkginfo['provides']:
                print('\n%PROVIDES%', file=descfile)
                for provide in self.pkginfo['provides']:
                    print("{}".format(provide), file=descfile)
            print(file=descfile)
            os.remove("/".join([self.rootpath, '.PKGINFO']))

    def installfile_fun(self):
        if ".INSTALL" in self.file_list:
            src = "/".join([self.rootpath, ".INSTALL"])
            shutil.move(src, self.installfile)

    def get_md5sum(self, backup_file):
        tmpfile = open("/".join([self.rootpath, backup_file]), 'rb')
        ret = hashlib.md5(tmpfile.read()).hexdigest()
        tmpfile.close()
        return ret


    def filesfile_fun(self):
        filesfile = open(self.filesfile, 'w')
        print("%FILES%", file=filesfile)
        for line in self.file_list:
            print(line, file=filesfile)
        print(file=filesfile)
        if self.pkginfo['backup']:
            print("%BACKUP%", file=filesfile)
            for line in self.pkginfo['backup']:
                print(line, self.get_md5sum(line), file=filesfile, sep='\t')
        print(file=filesfile)
        filesfile.close()

    def mtreefile_fun(self):
        if '.MTREE' in self.file_list:
            src = "/".join([self.rootpath, ".MTREE"])
            shutil.move(src, self.mtreefile)

    def extractfiles(self):
        self.pkg.extractall(path=self.rootpath)
        self.pkg.close()
        
    def post_install_fun(self):
        if os.path.isfile(self.installfile):
            with open(self.installfile, 'r') as  installfile:
                if 'post_install' in installfile.read():
                    os.chroot(self.rootpath)
                    os.putenv('BASH_ENV', self.installfile)
                    subprocess.call(["bash", '-c', 'post_install'])
        

    def installpackage(self):
        os.makedirs(self.localpath, exist_ok=1)
        self.extractfiles()
        self.descfile_fun()
        self.installfile_fun()
        self.filesfile_fun()
        self.mtreefile_fun()

if __name__ == '__main__':
    if os.path.isdir(sys.argv[2]):
        archive = Package(sys.argv[1], sys.argv[2])
        archive.installpackage()

# vim : set ts=4 sw=4 softtabstop=4 et:
