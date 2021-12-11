from requests import Session
from typing import ClassVar
import attr, logging, re, time


@attr.s(auto_attribs=True)
class HvSession:
    # class vars
    HV_LINK: ClassVar[str] = "https://hentaiverse.org"
    LOGIN_LINK: ClassVar[str] = "https://forums.e-hentai.org/index.php?act=Login&CODE=01"
    RATE_LIMIT: ClassVar[float] = 1 # seconds btwn requests

    # init args
    user: str
    pw: str
    session: Session = attr.ib(default=attr.Factory(Session))

    # instance vars
    did_login: bool = attr.ib(default=False, init=False)
    ign: str = attr.ib(default=None, init=False)

    _last_sent: float = attr.ib(default=0, init=False)
    _seen_main: bool = attr.ib(default=False, init=False) # visited the main hv page at least once
    _seen_isk: bool = attr.ib(default=False, init=False)

    def login(self):
        invalid_string = "You have to log on to access this game."

        resp = self.session.get(self.HV_LINK)
        if invalid_string in resp.text:
            time.sleep(self.RATE_LIMIT)
            self._login()

        self.did_login = True
        self._seen_main = False
        self._seen_isk = False

        return self

    def _login(self):
        logging.debug('Logging into HV...')

        payload = dict(
            CookieDate=1,
            b='d',
            bt=6,
            UserName=self.user,
            PassWord=self.pw,
            ipb_login_submit="Login!",
        )

        resp = self.session.post(self.LOGIN_LINK, data=payload)
        resp.encoding = 'utf-8'
        assert "You are now logged in as:" in resp.text

        ign = re.search("You are now logged in as: (.*?)<br", resp.text)
        self.ign = ign.group(1)
        logging.info(f'Logged in as {ign}')

        return self.session

    def get(self, url: str, **kwargs):
        self._prep_truck(url)
        self._delay_request()

        logging.debug(f'Getting {url} -- {kwargs}')
        return self.session.get(url, **kwargs)

    def post(self, url: str, **kwargs):
        self._prep_truck(url)
        self._delay_request()

        logging.debug(f'Posting {url} -- {kwargs}')
        return self.session.post(url, **kwargs)

    def _delay_request(self):
        elapsed = time.time() - self._last_sent

        if elapsed < self.RATE_LIMIT:
            delay = self.RATE_LIMIT - elapsed
            time.sleep(delay)

        self._last_sent = time.time()
        return

    # visit hv page at least once after login to set cookies or something
    def _prep_truck(self, url: str):
        if '/isekai/' in url and not self._seen_isk:
            logging.debug(f'Doing first isekai visit')
            self._seen_isk = True
            self.get('https://hentaiverse.org/isekai/')
        elif not self._seen_main:
            logging.debug(f'Doing first main visit')
            self._seen_main = True
            self.get('https://hentaiverse.org/')