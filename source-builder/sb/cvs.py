#
# RTEMS Tools Project (http://www.rtems.org/)
# Copyright 2010-2013 Chris Johns (chrisj@rtems.org)
# All rights reserved.
#
# This file is part of the RTEMS Tools package in 'rtems-tools'.
#
# Permission to use, copy, modify, and/or distribute this software for any
# purpose with or without fee is hereby granted, provided that the above
# copyright notice and this permission notice appear in all copies.
#
# THE SOFTWARE IS PROVIDED "AS IS" AND THE AUTHOR DISCLAIMS ALL WARRANTIES
# WITH REGARD TO THIS SOFTWARE INCLUDING ALL IMPLIED WARRANTIES OF
# MERCHANTABILITY AND FITNESS. IN NO EVENT SHALL THE AUTHOR BE LIABLE FOR
# ANY SPECIAL, DIRECT, INDIRECT, OR CONSEQUENTIAL DAMAGES OR ANY DAMAGES
# WHATSOEVER RESULTING FROM LOSS OF USE, DATA OR PROFITS, WHETHER IN AN
# ACTION OF CONTRACT, NEGLIGENCE OR OTHER TORTIOUS ACTION, ARISING OUT OF
# OR IN CONNECTION WITH THE USE OR PERFORMANCE OF THIS SOFTWARE.

#
# Provide some basic access to the cvs command.
#

import os

import error
import execute
import options
import path

class repo:
    """An object to manage a cvs repo."""

    def _cvs_exit_code(self, ec, output):
        if ec:
            print output
            raise error.general('cvs command failed (%s): %d' % (self.cvs, ec))

    def _parse_args(self, url):
        if not url.startswith('cvs://'):
            raise error.general('invalid cvs url: %s' % (url))
        opts = { 'cvsroot': ':%s' % (us[0][6:]),
                 'module':  '' }
        for o in us:
            os = o.split('=')
            if len(os) == 1:
                opts[os[0]] = True
            else:
                opts[os[0]] = os[1:]
        return opts

    def _run(self, args, check = False):
        e = execute.capture_execution()
        if path.exists(self.path):
            cwd = self.path
        else:
            cwd = None
        exit_code, proc, output = e.spawn([self.cvs, '-q'] + args, cwd = cwd)
        if check:
            self._cvs_exit_code(exit_code, output)
        return exit_code, output

    def __init__(self, _path, opts, macros = None):
        self.path = _path
        self.opts = opts
        if macros is None:
            self.macros = opts.defaults
        else:
            self.macros = macros
        self.cvs = self.macros.expand('%{__cvs}')

    def cvs_version(self):
        ec, output = self._run(['--version'], True)
        lines = output.split('\n')
        if len(lines) < 12:
            raise error.general('invalid version string from cvs: %s' % (output))
        cvs = lines[0].split(' ')
        if len(cvs) != 6:
            raise error.general('invalid version number from cvs: %s' % (lines[0]))
        vs = cvs[4].split('.')
        if len(vs) < 3:
            raise error.general('invalid version number from cvs: %s' % (cvs[4]))
        return (int(vs[0]), int(vs[1]), int(vs[2]))

    def checkout(self, root, path, module = ''):
        ec, output = self._run(['-d', root, 'co', '-N', '-d', path, module], check = True)

    def update(self):
        ec, output = self._run(['up'])

    def reset(self):
        ec, output = self._run(['up', '-C'], check = True)

    def branch(self):
        ec, output = self._run(['branch'])
        if ec == 0:
            for b in output.split('\n'):
                if b[0] == '*':
                    return b[2:]
        return None

    def status(self):
        keys = { 'U': 'modified',
                 'P': 'modified',
                 'M': 'modified',
                 'R': 'removed',
                 'C': 'conflict',
                 'A': 'added',
                 '?': 'untracked' }
        _status = {}
        if path.exists(self.path):
            ec, output = self._run(['-n', 'up'])
            if ec == 0:
                state = 'none'
                for l in output.split('\n'):
                    if len(l) > 2 and l[0] in keys:
                        if keys[l[0]] not in _status:
                            _status[keys[l[0]]] = []
                        _status[keys[l[0]]] += [l[2:]]
        return _status

    def clean(self):
        _status = self.status()
        return len(_status) == 0

    def valid(self):
        if path.exists(self.path):
            ec, output = self._run(['-n', 'up', '-l'])
            if ec == 0:
                if not output.startswith('cvs status: No CVSROOT specified'):
                    return True
        return False

if __name__ == '__main__':
    import sys
    opts = options.load(sys.argv, defaults = 'defaults.mc')
    ldir = 'cvs-test-rm-me'
    c = repo(ldir, opts)
    if not path.exists(ldir):
        c.checkout(':pserver:anoncvs@sourceware.org:/cvs/src', ldir, 'newlib')
    print c.cvs_version()
    print c.valid()
    print c.status()
    c.reset()
    print c.clean()