try:
    from dns import resolver
except:
    print "Error dnspython is not installed! (http://www.dnspython.org/)"
import gevent
import os
import plugoo
from plugoo.assets import Asset
from plugoo.tests import Test
from __future__ import with_statement

__plugoo__ = "DNST"
__desc__ = "DNS censorship detection test"

class Top1MAsset(Asset):
    def __init__(self, file=None):
        self = Asset.__init__(self, file)
    
    def next_asset(self):
        with self.fh as asset:
            lines = asset.readlines()
            for line in lines:
                yield line.split(',')[1]

class DNSTAsset(Asset):
    def __init__(self, file=None):
        self = Asset.__init__(self, file)

class DNST(Test):
    def lookup(self, hostname, ns):
        res = resolver.Resolver(configure=False)
        res.nameservers = [ns]
        answer = res.query(hostname)

        ret = []

        for data in answer:
            ret.append(data.address)

        return ret

    def experiment(self, *a, **kw):
        # this is just a dirty hack
        address = kw['data'][0]
        ns = kw['data'][1]

        config = self.config

        print "ADDRESS: %s" % address
        print "NAMESERVER: %s" % ns

        exp = self.lookup(address, ns)
        control = self.lookup(address, config.tests.dns_control_server)

        if len(set(exp) & set(control)) > 0:
            print "%s : no tampering on %s" % (address, ns)
            return (address, ns, False)
        else:
            print "%s : possible tampering on %s (%s, %s)" % (address, ns, exp, control)
            return (address, ns, exp, control, True)

def run(ooni):
    """Run the test
    """
    config = ooni.config
    urls = []

    dns_experiment = DNSTAsset(os.path.join(config.main.assetdir, \
                                            config.tests.dns_experiment))
    dns_experiment_dns = DNSTAsset(os.path.join(config.main.assetdir, \
                                                config.tests.dns_experiment_dns))

    assets = [dns_experiment, dns_experiment_dns]

    dnstest = DNST(ooni)
    ooni.logger.info("starting test")
    dnstest.run(assets)
    ooni.logger.info("finished")


