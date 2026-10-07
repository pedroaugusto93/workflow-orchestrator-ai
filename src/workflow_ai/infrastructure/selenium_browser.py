from __future__ import annotations

import base64
import time
from pathlib import Path
from typing import Sequence

from selenium.common.exceptions import (
    ElementClickInterceptedException,
    StaleElementReferenceException,
    TimeoutException,
)
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait

from workflow_ai.ports.browser import BrowserPort, Locator


_BY = {
    "css": By.CSS_SELECTOR,
    "xpath": By.XPATH,
    "name": By.NAME,
    "id": By.ID,
    "tag": By.TAG_NAME,
}


class SeleniumBrowser(BrowserPort):
    def __init__(self, driver, *, timeout: float = 15.0) -> None:
        self.driver = driver
        self.timeout = timeout

    def _wait(self, timeout: float | None = None) -> WebDriverWait:
        return WebDriverWait(self.driver, timeout or self.timeout, poll_frequency=0.2)

    @staticmethod
    def _tuple(locator: Locator):
        return (_BY[locator.by], locator.value)

    def navigate(self, url: str) -> None:
        if not url:
            raise ValueError("URL do portal não configurada.")
        self.driver.get(url)
        self.page_ready()

    def page_ready(self) -> None:
        self._wait().until(lambda d: d.execute_script("return document.readyState") == "complete")
        try:
            self._wait(4).until(
                lambda d: not d.execute_script(
                    """
                    const sels=['.block-ui-overlay','.block-ui.active','.ngx-loading',
                                '.loading-overlay','.loading','.throbber','.spinner','#spinner'];
                    return sels.some(s => {
                      const el=document.querySelector(s); if(!el) return false;
                      const st=getComputedStyle(el), r=el.getBoundingClientRect();
                      return st.visibility!=='hidden' && st.display!=='none' && r.width>0 && r.height>0;
                    });
                    """
                )
            )
        except TimeoutException:
            pass

    def click(self, locator: Locator, *, timeout: float | None = None) -> None:
        last = None
        for _ in range(3):
            try:
                el = self._wait(timeout).until(EC.element_to_be_clickable(self._tuple(locator)))
                self.driver.execute_script("arguments[0].scrollIntoView({block:'center'});", el)
                try:
                    el.click()
                except ElementClickInterceptedException:
                    self.driver.execute_script("arguments[0].click();", el)
                return
            except (TimeoutException, StaleElementReferenceException, ElementClickInterceptedException) as exc:
                last = exc
                time.sleep(0.4)
        raise TimeoutException(f"Elemento não clicável: {locator}") from last

    def fill(self, locator: Locator, value: str, *, timeout: float | None = None) -> None:
        el = self._wait(timeout).until(EC.visibility_of_element_located(self._tuple(locator)))
        self.driver.execute_script("arguments[0].scrollIntoView({block:'center'});", el)
        try:
            el.click()
            el.clear()
        except Exception:
            pass
        try:
            el.send_keys(Keys.CONTROL, "a")
            el.send_keys(Keys.DELETE)
        except Exception:
            pass
        if value not in (None, ""):
            el.send_keys(str(value))
        self.driver.execute_script(
            "arguments[0].dispatchEvent(new Event('input',{bubbles:true}));"
            "arguments[0].dispatchEvent(new Event('change',{bubbles:true}));"
            "arguments[0].dispatchEvent(new Event('blur',{bubbles:true}));",
            el,
        )

    def select_value(self, locator: Locator, value: str, *, timeout: float | None = None) -> None:
        el = self._wait(timeout).until(EC.presence_of_element_located(self._tuple(locator)))
        self.driver.execute_script(
            "arguments[0].value=arguments[1];"
            "arguments[0].dispatchEvent(new Event('input',{bubbles:true}));"
            "arguments[0].dispatchEvent(new Event('change',{bubbles:true}));",
            el,
            str(value),
        )

    def select_first_containing_option(
        self, scope: Locator, option_value: str, *, timeout: float | None = None
    ) -> bool:
        host = self._wait(timeout).until(EC.presence_of_element_located(self._tuple(scope)))
        for select in host.find_elements(By.TAG_NAME, "select"):
            if select.find_elements(By.CSS_SELECTOR, f"option[value='{option_value}']"):
                self.driver.execute_script(
                    "arguments[0].value=arguments[1];"
                    "arguments[0].dispatchEvent(new Event('input',{bubbles:true}));"
                    "arguments[0].dispatchEvent(new Event('change',{bubbles:true}));",
                    select,
                    str(option_value),
                )
                return True
        return False

    def read_value(self, locator: Locator, *, timeout: float | None = None) -> str:
        el = self._wait(timeout).until(EC.presence_of_element_located(self._tuple(locator)))
        return (el.get_attribute("value") or "").strip()

    def exists(self, locator: Locator, *, timeout: float = 2.0) -> bool:
        try:
            self._wait(timeout).until(EC.presence_of_element_located(self._tuple(locator)))
            return True
        except TimeoutException:
            return False

    def wait_absent(self, locator: Locator, *, timeout: float | None = None) -> None:
        self._wait(timeout).until(EC.invisibility_of_element_located(self._tuple(locator)))

    def upload(self, locator: Locator, path: str | Path, *, timeout: float | None = None) -> None:
        file_path = Path(path).expanduser().resolve()
        if not file_path.is_file():
            raise FileNotFoundError(file_path)
        el = self._wait(timeout).until(EC.presence_of_element_located(self._tuple(locator)))
        el.send_keys(str(file_path))

    def confirm(self, labels: Sequence[str], *, timeout: float = 5.0) -> bool:
        try:
            self._wait(timeout).until(
                EC.visibility_of_element_located(
                    (By.CSS_SELECTOR, "div.swal2-container.swal2-shown, div.swal2-popup.swal2-modal")
                )
            )
        except TimeoutException:
            return False
        wanted = [x.strip().casefold() for x in labels if x.strip()]
        for button in self.driver.find_elements(By.CSS_SELECTOR, "button.swal2-confirm"):
            try:
                if button.is_displayed() and (
                    not wanted or any(w in (button.text or "").strip().casefold() for w in wanted)
                ):
                    self.driver.execute_script("arguments[0].click();", button)
                    return True
            except StaleElementReferenceException:
                continue
        return False

    def last_row_cells(self, table_body: Locator) -> list[str]:
        host = self.driver.find_element(*self._tuple(table_body))
        rows = [r for r in host.find_elements(By.CSS_SELECTOR, "tr") if r.find_elements(By.CSS_SELECTOR, "td")]
        if not rows:
            return []
        return [(td.text or "").strip() for td in rows[-1].find_elements(By.CSS_SELECTOR, "td")]

    def execute_script(self, script: str, *args):
        return self.driver.execute_script(script, *args)

    def window_handles(self) -> list[str]:
        return list(self.driver.window_handles)

    def current_window(self) -> str | None:
        try:
            return self.driver.current_window_handle
        except Exception:
            return None

    def switch_window(self, handle: str) -> None:
        self.driver.switch_to.window(handle)
        self.page_ready()

    def close_window(self) -> None:
        self.driver.close()

    def print_pdf(self, destination: str | Path) -> Path:
        path = Path(destination).expanduser().resolve()
        path.parent.mkdir(parents=True, exist_ok=True)
        result = self.driver.execute_cdp_cmd(
            "Page.printToPDF",
            {
                "printBackground": True,
                "preferCSSPageSize": True,
                "marginTop": 0,
                "marginBottom": 0,
                "marginLeft": 0,
                "marginRight": 0,
            },
        )
        data = result.get("data") if isinstance(result, dict) else None
        if not data:
            raise RuntimeError("Chrome não retornou dados do PDF.")
        path.write_bytes(base64.b64decode(data))
        return path
