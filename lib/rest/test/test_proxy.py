#
# This file is part of Python-REST. Python-REST is free software that is
# made available under the MIT license. Consult the file "LICENSE" that is
# distributed together with this file for the exact licensing terms.
#
# Python-REST is copyright (c) 2010 by the Python-REST authors. See the file
# "AUTHORS" for a complete overview.

import time
import threading
from rest.proxy import ObjectProxy


class Dict(dict):
    pass


class TestProxy(object):

    def test_access(self):
        proxy = ObjectProxy(Dict())
        proxy.test = 'foo'
        assert proxy.test == 'foo'
        del proxy.test
        assert not hasattr(proxy, 'test')
        proxy['test2'] = 'bar'
        assert proxy['test2'] == 'bar'
        assert 'test2' in proxy
        assert proxy
        assert proxy.get('test2') == 'bar'
        del proxy['test2']
        assert 'test2' not in proxy
        assert not proxy

    def _do_test_separation(self, proxy, id, result):
        proxy._register(Dict())
        proxy['test'] = id
        time.sleep(1)  # poor man's synchronization
        result.append(proxy['test'] - id)

    def test_separation(self):
        proxy = ObjectProxy(Dict())
        result = []
        t1 = threading.Thread(target=self._do_test_separation,
                              args=(proxy, 1, result))
        t2 = threading.Thread(target=self._do_test_separation,
                              args=(proxy, 2, result))
        t1.start(); t2.start()
        t1.join(); t2.join()
        assert 'test' not in proxy
        assert result == [0, 0]
