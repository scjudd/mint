#!/usr/bin/env python2

from urllib import urlencode
import cookielib
import logging
import lxml.html
import re
import urllib2

log = logging.getLogger("mint")

class MintError(Exception):
    pass

class LoginError(MintError):
    pass

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
        self.log.debug("Logging in as %s" % email)

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

        if "password were incorrect" in response:
            raise LoginError

        token_re = re.compile(r"token&quot;:&quot;([^&].+)")
        self.token = token_re.search(response).group(1)

        self.is_authenticated = True
        self.log.debug("Login successful")

def refreshFILogins(session):
    """Request mint.com to refresh Financial Institution (FI) data"""

    log.debug("POST /refreshFILogins.xevent")
    url = "https://wwws.mint.com/refreshFILogins.xevent"
    return session.request(url, "token="+session.token).read()

def userStatus(session):
    """Check if mint.com is currently refreshing FI data"""

    log.debug("GET /userStatus.xevent")
    url = "https://wwws.mint.com/userStatus.xevent"
    return session.request(url).read()

def htmlFragment(session, task="module-accounts"):
    """Request an html fragment from mint.com"""

    log.debug("GET /htmlFragment.xevent?task="+task)
    url = "https://wwws.mint.com/htmlFragment.xevent?task="+task
    return session.request(url).read()

def get_balances(session):
    """Get current FI account balances from mint.com"""

    attempts = 0
    refreshFILogins(session)

    while True:
        attempts += 1

        if attempts % 5 == 0: # every 5 attempts
            refreshFILogins(session)

        if "true" in userStatus(session):
            break

    def account(e):
        return e.xpath("span/a/text()")[0], e.xpath("span/text()")[0]

    tree = lxml.html.fromstring(htmlFragment(session))
    total = tree.xpath("//*[@class='balance']/text()")[0].replace("Cash","")
    accounts = map(account, tree.xpath("//h4"))
    accounts.append(("TOTAL", total))

    return accounts

if __name__ == "__main__":
    from getpass import getpass
    import ConfigParser as configparser
    import os

    log.setLevel(logging.INFO)
    log.addHandler(logging.StreamHandler())

    path = os.path.expanduser(os.path.join("~",".mintrc"))
    config = configparser.ConfigParser()

    if not os.path.exists(path):
        log.info("No ~/.mintrc found. Creating one.")

        print "\n=== Login Information ==="
        email = raw_input("Email:    ")
        password = getpass()
        print

        config.add_section("user")
        config.set("user", "email", email)
        config.set("user", "password", password)

        with open(path, "w") as f:
            config.write(f)

        os.chmod(path, 0600)

    config.read(path)

    email = config.get("user", "email")
    password = config.get("user", "password")

    session = Session(email, password)
    for acct in get_balances(session):
        print "%s: %s" % (acct[0], acct[1])
