# coding=utf-8
import ast
import json
import logging
import logging.handlers
import os
import socket
import time
import requests


def check_url(url, timeout=None, retry_count=0, retry_period=5, logger=None):
    """
    Checking if an HTTP is up and running.

    Args:
        url (str): URL
        timeout (float): Timeout value in seconds.
        retry_count (int): Number of tries
        retry_period (float): Period between retries in seconds.
        logger (logging.Logger): Logger

    Returns:
        bool: True if success, False elsewhere
    """
    if not url:
        if logger:
            logger.error("Invalid url: %s", str(url))
        return False
    default_timeout = socket.getdefaulttimeout()
    miss_count = 0
    try:
        if timeout is not None:
            socket.setdefaulttimeout(timeout)  # timeout in seconds
        while miss_count <= retry_count:
            try:
                if logger:
                    logger.debug("Check URL server: %s...", url)
                status_code = requests.get(url).status_code
                if status_code == 200:
                    if logger:
                        logger.debug("... hit!")
                    return True
            except Exception:
                if logger:
                    logger.debug("... miss")
                miss_count += 1
                time.sleep(retry_period)
        if logger:
            logger.error("Cannot reach url '%s' after %d attempts", url, retry_count)
        return False

    # Set back to default value
    finally:
        socket.setdefaulttimeout(default_timeout)


def https_session(max_retries=2):
    """
    Instantiate HTTPS session

    Args:
        max_retries (int): The maximum number of retries each connection should attempt

    Returns:
        requests.Session: Https session
    """
    session = requests.Session()
    session.mount('https://', requests.adapters.HTTPAdapter(max_retries=max_retries))
    return session


def get_host_public_ip(logger=None):
    """
    Find current host IP address.

    Args:
        logger (logging.Logger): Logger

    Returns:
        str: IP address

    Raises:
        OSError: Fail to get IP address
    """
    for url, section in (('http://ipinfo.io/ip', ''),
                         ('http://ip-api.com/xml', 'query'),
                         ('http://freegeoip.net/xml', 'IP')):

        # Try to get response
        if logger is not None:
            logger.debug("Get public IP answer using: %s", url)
        session = https_session(max_retries=1)
        response = session.get(url)
        try:
            response.raise_for_status()
        except requests.exceptions.RequestException:
            if logger is not None:
                logger.exception("Caught following exception with '%s':" % url)
        else:
            # Parse IP from response
            if section:
                # XML parser lazy import since not always used
                try:
                    # Use lxml if available
                    import lxml.etree as ET
                except ImportError:
                    # Else use standard library
                    import xml.etree.ElementTree as ET

                root = ET.fromstring(response.text.encode('utf-8'))
                ip_address = str(root.findall(section)[0].text)
            else:
                ip_address = str(response.text)

            if logger is not None:
                logger.debug("Public IP answer: %s", ip_address)
            return "/32%s" % ip_address.strip()

    raise OSError("Failed to find your external IP address. Your internet connection might be broken.")


def pretty_dict(obj):
    """
    Format dictionary to text.

    Args:
        obj (dict): Dict to format.

    Returns:
        str: formatted dict
    """
    return json.dumps(ast.literal_eval(str(obj)), indent=4)


class APILogger(logging.Logger):
    """
    Custom logger that:
    - Forwards records to parent logger if not an exception (but save it into the log file)
    - Force the level to DEBUG for the file handler.
    """

    _level_request = logging.WARNING
    ref_name = ''
    filename = ''

    def setLevel(self, level):
        """
        Set logger level

        Args:
            level (int): Logger level
        """
        self._level_request = level
        super(APILogger, self).setLevel(
            level if self.name != self.ref_name else logging.DEBUG)

    def handle(self, record):
        """
        Conditionally emit the specified logging record.

        Args:
            record: Logging record
        """
        for handler in self.handlers:
            handler.emit(record)

        if record.name == self.ref_name and record.levelno < self._level_request:
            return

        if record.name == self.ref_name and record.exc_info is not None:
            record.msg = record.exc_info[1].message
            record.exc_text = None
            record.exc_info = None
        self.parent.handle(record)


def init_logger(name, filename):
    """
    Initialize logger

    Args:
        name (str): Logger name
        filename (str): Script filename to use as base for logger filename

    Returns:
       APILogger: logger instance
    """

    # Register our logger class and create local logger object
    ref_logger_class = logging.getLoggerClass()
    try:
        logging.setLoggerClass(APILogger)
        logger = logging.getLogger(name)
        logger.ref_name = name
        logger.setLevel(logging.WARNING)

    # Use the original Logger class for the others
    finally:
        logging.setLoggerClass(ref_logger_class)

    # Rotating file handler
    file_handler = logging.handlers.RotatingFileHandler(
        os.path.join(os.path.dirname(filename), '%s.log' % name),
        maxBytes=100 * 1024 * 1024, backupCount=5)
    file_handler.setLevel(logging.DEBUG)
    file_handler.setFormatter(
        logging.Formatter("%(asctime)s - %(levelname)-8s: %(filename)-20s, %(funcName)-28s, %(lineno)-4d: %(message)s"))
    logger.addHandler(file_handler)

    # Save filename inside logger for future use
    logger.filename = file_handler.baseFilename

    return logger
