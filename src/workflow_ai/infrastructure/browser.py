from __future__ import annotations

from selenium import webdriver
from selenium.webdriver.chrome.options import Options


def attach_to_chrome(host: str = "127.0.0.1", port: int = 9222):
    """Attach to a Chrome session already started with remote debugging."""
    options = Options()
    options.add_experimental_option("debuggerAddress", f"{host}:{port}")
    return webdriver.Chrome(options=options)
