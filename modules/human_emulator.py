"""
Human interaction emulator to mimic realistic human behavior and prevent anti-bot detection.
"""

import asyncio
import random
import time
from typing import Optional

from config import (
    MIN_TYPING_DELAY,
    MAX_TYPING_DELAY,
    MIN_ACTION_DELAY,
    MAX_ACTION_DELAY,
)
from modules.logger import log_info, console


async def human_type(
    locator,
    text: str,
    min_delay: float = MIN_TYPING_DELAY,
    max_delay: float = MAX_TYPING_DELAY,
):
    """
    Ketik teks karakter per karakter dengan variasi delay acak,
    seperti manusia asli yang sedang mengetik di keyboard.
    """
    await locator.focus()
    # Beri jeda sejenak setelah fokus sebelum mengetik
    await asyncio.sleep(random.uniform(0.3, 0.8))

    for char in text:
        # Delay acak per karakter
        delay = random.uniform(min_delay, max_delay)
        
        # Manusia sering berhenti sejenak setelah spasi atau tanda baca
        if char in " ,.!?-\n":
            delay += random.uniform(0.1, 0.25)
            
        await locator.press_sequentially(char, delay=int(delay * 1000))
        await asyncio.sleep(random.uniform(0.01, 0.05))


async def random_delay(
    min_sec: float = MIN_ACTION_DELAY,
    max_sec: float = MAX_ACTION_DELAY,
    reason: str = "Tindakan acak",
):
    """
    Jeda singkat antar aksi mikro (misal klik tombol, scroll, buka modal).
    """
    wait_time = random.uniform(min_sec, max_sec)
    await asyncio.sleep(wait_time)


async def countdown_delay(seconds: int, message: str = "Menunggu sebelum posting berikutnya"):
    """
    Menampilkan countdown mundur di terminal untuk jeda panjang antar postingan.
    """
    log_info(f"{message}: {seconds} detik...")
    for remaining in range(seconds, 0, -1):
        if remaining % 15 == 0 or remaining <= 5:
            log_info(f"⏳ Jeda aman tersisa: {remaining}s...")
        await asyncio.sleep(1)


async def human_click(locator):
    """
    Klik elemen dengan sedikit pergerakan kursor dan micro-delay realistis.
    """
    await locator.scroll_into_view_if_needed()
    await random_delay(0.2, 0.6)
    box = await locator.bounding_box()
    if box:
        # Sedikit geser titik klik ke area dalam elemen agar tidak selalu persis di tengah
        offset_x = random.uniform(box["width"] * 0.2, box["width"] * 0.8)
        offset_y = random.uniform(box["height"] * 0.2, box["height"] * 0.8)
        await locator.page.mouse.move(box["x"] + offset_x, box["y"] + offset_y)
        await asyncio.sleep(random.uniform(0.1, 0.3))
    await locator.click()
    await random_delay(0.5, 1.2)


async def human_scroll(page, steps: int = 3, min_dist: int = 200, max_dist: int = 500):
    """
    Scroll halaman secara bertahap menyerupai pergerakan mouse wheel manusia.
    """
    for _ in range(steps):
        distance = random.randint(min_dist, max_dist)
        direction = 1 if random.random() > 0.15 else -1 # Mayoritas scroll ke bawah
        await page.mouse.wheel(0, distance * direction)
        await asyncio.sleep(random.uniform(0.4, 0.9))
