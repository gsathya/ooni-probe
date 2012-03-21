"""
    Squid Proxy Detector
    ********************

"""
import os
import httplib
import urllib2
from urlparse import urlparse

from plugoo import gen_headers
from plugoo.assets import Asset
from plugoo.tests import Test

try:
    from BeautifulSoup import BeautifulSoup
except:
    pass

__plugoo__ = "SquidProxy"
__desc__ = "This Test aims at detecting the squid transparent proxy"

class SquidAsset(Asset):
    """
    This is the asset that should be used by the Test. It will
    contain all the code responsible for parsing the asset file
    and should be passed on instantiation to the test.
    """
    def __init__(self, file=None):
        self = Asset.__init__(self, file)


class Squid(Test):
    """
    Squid Proxy testing class.
    """
    def _http_request(self, method, url,
                      path=None, headers=None):
        """
        Perform an HTTP Request.
        XXX move this function to the core OONI
        code.
        """
        url = urlparse(url)
        host = url.netloc

        conn = httplib.HTTPConnection(host, 80)
        conn.connect()

        if path is None:
            path = purl.path

        conn.putrequest(method, path)

        for h in gen_headers():
            conn.putheaders(h[0], h[1])
        conn.endheaders()

        response = conn.getresponse()

        headers = dict(response.getheaders())

        self.headers = headers
        self.data = response.read()
        return True


    def random_bad_request(self, url):
        r_str = ''.join(random.choice(string.ascii_uppercase + string.digits) for x in range(random.randint(5,20)))
        if self._http_request(self, r_str, url):
            return True
        else:
            return None

    def invalid_request(self, url):
        """
        This will trigger squids "Invalid Request" error.
        """

        test_name = "squid bad request"
        self.logger.info("RUNNING %s test" % test_name)
        if self.random_bad_request(url):
            s_headers = {'X-Squid-Error' : 'ERR_INVALID_REQ 0'}
            for i in s_headers.items():
                if i[0] in self.headers:
                    self.logger.info("the %s test returned False" % test_name)
                    return False
            self.logger.info("the %s test returned True" % test_name)
            return True
        else:
            self.logger.warning("the %s test returned failed" % test_name)
            return None


    def cache_object(self, url):
        """
        This attempts to do a GET cache_object://localhost/info on
        any destination and checks to see if the response contains
        is that of Squid.
        """
        test_name = "squid cacheobject"
        self.logger.info("RUNNING %s test" % test_name)
        if self._http_request(self, "GET", url, "cache_object://localhost/info"):
            soup = BeautifulSoup(self.data)
            if soup.find('strong') and soup.find('strong').string == "Access Denied.":
                self.logger.info("the %s test returned False" % test_name)
                return False
            else:
                self.logger.info("the %s test returned True" % test_name) 
                return True
        else:
            self.logger.warning("the %s test failed" % test_name)
            return None
    
    def experiment(self, *a, **kw):
        """
        Fill this up with the tasks that should be performed
        on the "dirty" network and should be compared with the
        control.
        """


    def control(self):
        """
        Fill this up with the control related code.
        """
        return True

def run(ooni):
    """
    This is the function that will be called by OONI
    and it is responsible for instantiating and passing
    the arguments to the Test class.
    """
    config = ooni.config

    # This the assets array to be passed to the run function of
    # the test
    assets = [TestTemplateAsset(os.path.join(config.main.assetdir, \
                                            "someasset.txt"))]

    # Instantiate the Test
    thetest = TestTemplate(ooni)
    ooni.logger.info("starting SquidProxyTest...")
    # Run the test with argument assets
    thetest.run(assets)
    ooni.logger.info("finished.")


