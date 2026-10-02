"""
Browser manager module using Chrome DevTools Protocol (CDP) Attach.
Connects directly to an existing Chrome instance without triggering automation flags.
"""

from typing import Optional, Tuple
from playwright.async_api import Browser, BrowserContext, Page, async_playwright

from config import CDP_URL, DEFAULT_TIMEOUT_MS, NAVIGATION_TIMEOUT_MS
from modules.logger import log_error, log_info, log_success, log_warn


class BrowserManager:
    def __init__(self, cdp_url: str = CDP_URL):
        self.cdp_url = cdp_url
        self._playwright = None
        self._browser: Optional[Browser] = None
        self._context: Optional[BrowserContext] = None

    async def connect(self, domain_hint: str = "") -> Tuple[Browser, Page]:
        """
        Menghubungkan Playwright ke Google Chrome yang sedang berjalan via CDP port.
        Jika domain_hint diberikan, tab yang sesuai akan dicari atau dibuat baru secara terisolasi.
        Menaikkan ConnectionError jika Chrome tidak terdeteksi (TIDAK memanggil sys.exit).
        """
        log_info(f"Menghubungi Google Chrome via Remote Debugging ({self.cdp_url})...")
        self._playwright = await async_playwright().start()

        try:
            self._browser = await self._playwright.chromium.connect_over_cdp(
                self.cdp_url,
                timeout=DEFAULT_TIMEOUT_MS,
            )
        except Exception as e:
            log_error("Gagal terhubung ke Google Chrome!")
            log_warn("Pastikan Anda sudah membuka Chrome dengan Remote Debugging:")
            log_warn(" - Di Windows: Jalankan start_chrome_windows.bat atau start_gui_windows.bat")
            log_warn(" - Di Linux: Jalankan ./launchers/start_chrome_linux.sh atau ./start_gui.sh")
            log_warn(f"Detail error: {e}")
            if self._playwright:
                try:
                    await self._playwright.stop()
                except Exception:
                    pass
                self._playwright = None
            raise ConnectionError(
                f"Cannot connect to Chrome on port 9222 ({self.cdp_url}). "
                "Pastikan Chrome sudah dijalankan dengan Remote Debugging (--remote-debugging-port=9222)."
            ) from e

        contexts = self._browser.contexts
        if not contexts:
            log_error("Tidak ada browser context yang ditemukan di Chrome.")
            if self._playwright:
                try:
                    await self._playwright.stop()
                except Exception:
                    pass
                self._playwright = None
            raise ConnectionError("Tidak ada browser context yang ditemukan di Chrome.")

        self._context = contexts[0]
        self._context.set_default_timeout(DEFAULT_TIMEOUT_MS)
        self._context.set_default_navigation_timeout(NAVIGATION_TIMEOUT_MS)

        # Cari tab sesuai domain_hint, atau tab aktif pertama jika tanpa domain_hint
        page = await self.get_or_create_page(domain_hint)

        log_success(f"Berhasil menempel ke Google Chrome! (Tabs aktif: {len(self._context.pages)})")
        return self._browser, page

    async def get_or_create_page(self, domain_hint: str = "") -> Page:
        """
        Mencari tab yang sudah membuka domain_hint (misal 'carousell', 'youtube', atau 'issuu'),
        atau menggunakan tab kosong yang tersedia, atau membuat tab baru jika belum ada.
        Menjamin isolasi tab antar platform agar tidak saling menimpa.
        """
        if not self._context:
            raise RuntimeError("Browser belum terhubung. Panggil connect() terlebih dahulu.")

        if domain_hint:
            clean_hint = domain_hint.strip().lower()

            # 1. Cari tab aktif yang URL-nya memuat domain_hint
            for p in self._context.pages:
                try:
                    if not p.is_closed() and clean_hint in p.url.lower():
                        log_info(f"Menggunakan tab yang sudah terbuka untuk '{domain_hint}': {p.url}")
                        await p.bring_to_front()
                        return p
                except Exception:
                    continue

            # 2. Cek apakah ada tab kosong (about:blank atau newtab) yang bisa digunakan kembali
            for p in self._context.pages:
                try:
                    if not p.is_closed() and p.url.lower() in ("about:blank", "chrome://newtab/", ""):
                        log_info(f"Menggunakan tab kosong untuk '{domain_hint}': {p.url}")
                        await p.bring_to_front()
                        return p
                except Exception:
                    continue

        else:
            # Jika tanpa domain_hint, gunakan tab pertama yang aktif dan belum tertutup
            for p in self._context.pages:
                try:
                    if not p.is_closed():
                        await p.bring_to_front()
                        return p
                except Exception:
                    continue

        # 3. Buat tab baru jika tidak ada tab yang cocok
        page = await self._context.new_page()
        await page.bring_to_front()
        return page

    async def disconnect(self):
        """
        Memutus sambungan CDP dengan aman tanpa menutup browser asli milik user.
        """
        try:
            if self._browser:
                log_info("Memutus sambungan Playwright dari Google Chrome (Browser Anda tetap terbuka)...")
                await self._browser.close()
        except Exception as e:
            log_warn(f"Peringatan saat menutup browser CDP: {e}")
        finally:
            self._browser = None
            self._context = None

        try:
            if self._playwright:
                await self._playwright.stop()
        except Exception as e:
            log_warn(f"Peringatan saat menghentikan Playwright: {e}")
        finally:
            self._playwright = None

        log_success("Selesai.")
