#!/usr/bin/env python

from __future__ import print_function, generators, with_statement
import argparse
from time import sleep
import os, re, tarfile
from subprocess import call
from package import *

try:
    from urllib.request import urlretrieve
except ImportError:
    from urllib import urlretrieve

pj = os.path.join

def base_system(mirror, rootpath='/mnt/', devel=False):
    installed_packages = []
    arch = os.uname()[-1]
    if os.path.isfile(mirror):
        db = Repo(mirror)
    else:
        coredb = pj(mirror, 'core', 'os', arch, 'core.db')
        urlretrieve(coredb, '/tmp/coredb')
        db = Repo('/tmp/coredb')
    base_packages = db.group_members('base')
    if devel:
        base_packages |= db.group_members('base-devel')
    base_packages = set(remove_v_r(p) for p in base_packages)
    base_depends = db.depends(base_packages)
    print('\n'.join(base_packages | base_depends))
    return
    
    cache_location = pj(rootpath, 'var/cache/pacman/pkg/')
    # exist_ok is not in py2
    os.makedirs(cache_location, exist_ok=1)

    for pkg in base_packages | base_depends:
        filename = '{}-{}-{}.pkg.tar.xz'.format(db[pkg]['NAME'], db[pkg]['VERSION'], db[pkg]['ARCH'])

        downloadfile = pj(cache_location, filename)
        url = pj(mirror, 'core', 'os', arch, filename)
        print(url)
        continue
        urlretrieve(url, downloadfile)
        thispkg = Package(downloadfile, rootpath)
        if pkg in base_depends:
            thispkg.pkginfo['reason'] = 1
        thispkg.installpackage()
        installed_packages.append(thispkg)

    return

    call(['mount', '-R', '/dev/', pj(rootpath, 'dev/')])
    call(['mount', '-R', '/sys/', pj(rootpath, 'sys/')])
    call(['mount', '-R', '/proc/', pj(rootpath, 'proc/')])
    shutil.copyfile('/etc/resolv.conf', pj(rootpath, '/etc/resolv.conf'))
    os.chroot(rootpath)
    shutil.copyfile('./all_post_install', '/all_post_install')
    subprocess.call(["bash", '/all_post_install'])
    os.remove('/all_post_install')



if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Basic commands')
    parser.add_argument( '-m',  '--mirror', nargs=1, required=True,
                        help='Mirror to download from')
    parser.add_argument( '-r', '--root', nargs=1, required=True,
                        help='Destination to install to')
    parser.add_argument( '-d', '--devel', action='store_true', 
                         default=False, help='And base-devel')
    args = parser.parse_args()
    base_system(args.mirror[0], args.root[0], args.devel)


# vime: set ts=4 ws=4 et
