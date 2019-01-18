# Electrum SV - lightweight Bitcoin SV client
# Copyright (C) 2019 The Electrum SV Developers
# Copyright (C) 2012 thomasv@gitorious
#
# Permission is hereby granted, free of charge, to any person
# obtaining a copy of this software and associated documentation files
# (the "Software"), to deal in the Software without restriction,
# including without limitation the rights to use, copy, modify, merge,
# publish, distribute, sublicense, and/or sell copies of the Software,
# and to permit persons to whom the Software is furnished to do so,
# subject to the following conditions:
#
# The above copyright notice and this permission notice shall be
# included in all copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND,
# EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF
# MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND
# NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT HOLDERS
# BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER IN AN
# ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN
# CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
# SOFTWARE.

'''Global application state.   Use as follows:

from electrumsv.app_sate import app_state

app_state.config
app_state.daemon
app_state.plugins
app_state.func()

etc.
'''

import threading

from electrumsv.dnssec import resolve_openalias


class AppStateProxy(object):

    base_units = ['BSV', 'mBSV', 'bits']    # large to small

    def __init__(self, config, gui_kind):
        from electrumsv.device import DeviceMgr
        from electrumsv.plugin import Plugins

        self.config = config
        self.device_manager = DeviceMgr()
        self.gui_kind = gui_kind
        self.fx = None
        self.plugins = Plugins()
        # Not entirely sure these are worth caching, but preserving existing method for now
        self.decimal_point = config.get('decimal_point', 8)
        self.num_zeros = config.get('num_zeros', 0)

    # It would be nice to lose this
    def start(self):
        self.plugins.add_jobs(self.device_manager.thread_jobs())
        self.plugins.start()
        self.fetch_alias()

    def base_unit(self):
        index = (8 - self.decimal_point) // 3
        return self.base_units[index]

    def set_base_unit(self, base_unit):
        prior = self.decimal_point
        index = self.base_units.index(base_unit)
        self.decimal_point = 8 - index * 3
        if self.decimal_point != prior:
            self.config.set_key('decimal_point', self.decimal_point, True)
        return self.decimal_point != prior

    def set_alias(self, alias):
        self.config.set_key('alias', alias, True)
        if alias:
            self.fetch_alias()

    def fetch_alias(self):
        self.alias_info = None
        alias = self.config.get('alias')
        if alias:
            alias = str(alias)
            def f():
                self.alias_info = resolve_openalias(alias)
                self.alias_resolved()
            t = threading.Thread(target=f)
            t.setDaemon(True)
            t.start()

    def alias_resolved(self):
        '''Derived classes can hook into this.'''
        pass


class _AppStateMeta(type):

    def __getattr__(cls, attr):
        return getattr(cls._proxy, attr)

    def __setattr__(cls, attr, value):
        if attr == '_proxy':
            super().__setattr__(attr, value)
        return setattr(cls._proxy, attr, value)


class AppState(metaclass=_AppStateMeta):

    _proxy = None

    @classmethod
    def set_proxy(cls, proxy):
        cls._proxy = proxy


app_state = AppState