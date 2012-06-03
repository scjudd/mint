from urllib import urlencode
import cookielib
import logging
import re
import time
import urllib2

log = logging.getLogger("mint")

class Session(object):
    """Used for making authenticated requests to mint.com"""

    USER_AGENT = ("Mozilla/5.0 (X11; Linux i686) AppleWebKit/536.5 (KHTML, "
                  "like Gecko) Chrome/19.0.1084.52 Safari/536.5")
    
    def __init__(self, email, password):
        self._opener = urllib2.build_opener(urllib2.HTTPCookieProcessor())
        self._opener.addheaders = [("User-Agent", self.USER_AGENT)]
        self.log = logging.getLogger("mint.Session")

        self.is_authenticated = False
        self.login(email, password)

    def request(self, *args, **kwargs):
        """Make an authenticated request"""

        return self._opener.open(*args, **kwargs)

    def login(self, email, password):
        """Authenticate with mint.com"""

        self.email = email
        self.log.info("Logging in as %s" % email)

        url = "https://wwws.mint.com/loginUserSubmit.xevent"
        data = urlencode({
            "username": email,
            "password": password,
            "task": "L",
            "timezone": "-5",
            "nextPage": "",
            "browser": "Chrome",
            "browserVersion": "19",
            "os": "Linux"
        })

        response = self.request(url, data).read()

        token_re = re.compile(r"token&quot;:&quot;([^&].+)")
        self.token = token_re.search(response).group(1)

        # TODO: check for login error

        self.is_authenticated = True
        self.log.info("Login successful")

def get_balance(session):
    session.request("https://wwws.mint.com/refreshFILogins.xevent",
                    "token="+session.token)

    while True:
        status = session.request("https://wwws.mint.com/userStatus.xevent")
        if "true" in status.read():
            break
        time.sleep(1)

    url = "https://wwws.mint.com/htmlFragment.xevent?task=module-accounts"
    html = session.request(url).read()

    balance_re = re.compile(r"<span class='balance'>([0-9,.$]+)")
    return balance_re.search(html).group(1)
