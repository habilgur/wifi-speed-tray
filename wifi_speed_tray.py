"""
WiFi Speed Tray - Real-Time Windows System Tray Network Monitor
===============================================================
Displays:
1. Physical Wi-Fi Link Speed (Mbps, Band, Channel, Signal)
2. Live Network Throughput (Download & Upload in KB/s or MB/s)
3. Instant Hover Tooltip with rich details
4. Lightweight, low CPU/RAM consumption
"""

import os
import subprocess
import threading
import time
from typing import Dict, Tuple
from PIL import Image, ImageDraw, ImageFont
import psutil
import pystray


def format_bytes(b: float) -> str:
    """Format bytes per second into human-readable string."""
    if b >= 1024 * 1024 * 1024:
        return f"{b / (1024 * 1024 * 1024):.2f} GB/s"
    elif b >= 1024 * 1024:
        return f"{b / (1024 * 1024):.1f} MB/s"
    elif b >= 1024:
        return f"{b / 1024:.0f} KB/s"
    else:
        return f"{b:.0f} B/s"


def get_wifi_details() -> Dict[str, str]:
    """Parse netsh wlan show interfaces for link speed, SSID, band and signal."""
    try:
        res = subprocess.run(
            "netsh wlan show interfaces",
            shell=True,
            capture_output=True,
            text=True,
            timeout=4,
            encoding="cp857",
            errors="ignore",
        )
        data = {}
        for line in res.stdout.splitlines():
            if ":" in line:
                k, v = line.split(":", 1)
                data[k.strip()] = v.strip()

        return {
            "ssid": data.get("SSID", "Bağlı Değil"),
            "band": data.get("Band", ""),
            "channel": data.get("Channel", ""),
            "rx_mbps": data.get("Receive rate (Mbps)", "0"),
            "tx_mbps": data.get("Transmit rate (Mbps)", "0"),
            "signal": data.get("Signal", "0%"),
            "radio": data.get("Radio type", ""),
        }
    except Exception:
        return {"ssid": "Bilinmiyor", "rx_mbps": "0", "tx_mbps": "0", "signal": "0%"}


def create_tray_icon_image(down_str: str, link_mbps: str) -> Image.Image:
    """
    Renders a crisp 64x64 tray icon displaying live throughput and link speed.
    """
    img = Image.new("RGBA", (64, 64), color=(0, 0, 0, 0))
    draw = ImageDraw.Draw(img)

    # Rounded background badge (Dark modern slate/cyan gradient style)
    draw.rounded_rectangle([2, 2, 62, 62], radius=12, fill=(15, 23, 42, 240), outline=(56, 189, 248, 255), width=2)

    # Extract display text for download
    # e.g., "1.2 MB/s" -> "1.2M", "240 KB/s" -> "240K", "0 B/s" -> "0K"
    d_clean = down_str.replace("/s", "").replace(" ", "")
    if "MB" in d_clean:
        d_val = d_clean.replace("MB", "M")
    elif "KB" in d_clean:
        d_val = d_clean.replace("KB", "K")
    else:
        d_val = "0K"

    # Link speed integer
    link_clean = link_mbps.split(".")[0] if "." in link_mbps else link_mbps

    # Draw Download speed (top line)
    draw.text((32, 18), f"↓{d_val}", fill=(56, 189, 248, 255), anchor="mm")

    # Draw Link speed in Mbps (bottom line)
    draw.text((32, 44), f"{link_clean}M", fill=(74, 222, 128, 255), anchor="mm")

    return img


class WifiSpeedTrayApp:
    def __init__(self):
        self.running = True
        self.icon: pystray.Icon = None
        self.wifi_info = get_wifi_details()
        self.down_speed = "0 B/s"
        self.up_speed = "0 B/s"
        self.prev_time = time.time()
        self.prev_io = psutil.net_io_counters()

    def update_throughput(self) -> Tuple[str, str]:
        """Calculate bytes per second difference using psutil."""
        now = time.time()
        current_io = psutil.net_io_counters()

        dt = now - self.prev_time
        if dt <= 0:
            return self.down_speed, self.up_speed

        rx_bytes = (current_io.bytes_recv - self.prev_io.bytes_recv) / dt
        tx_bytes = (current_io.bytes_sent - self.prev_io.bytes_sent) / dt

        self.prev_time = now
        self.prev_io = current_io

        self.down_speed = format_bytes(rx_bytes)
        self.up_speed = format_bytes(tx_bytes)
        return self.down_speed, self.up_speed

    def build_tooltip(self) -> str:
        """Create a rich, multi-line status tooltip."""
        ssid = self.wifi_info.get("ssid", "Bağlı Değil")
        band = self.wifi_info.get("band", "")
        ch = self.wifi_info.get("channel", "")
        radio = self.wifi_info.get("radio", "")
        rx_rate = self.wifi_info.get("rx_mbps", "0")
        tx_rate = self.wifi_info.get("tx_mbps", "0")
        sig = self.wifi_info.get("signal", "0%")

        band_str = f" ({band} - Kanal {ch})" if band else ""
        radio_str = f" | {radio}" if radio else ""

        lines = [
            f"📶 Ağ: {ssid}{band_str}",
            f"⚡ Fiziksel Link: {rx_rate} Mbps (Alış) / {tx_rate} Mbps (Veriş){radio_str}",
            f"🔻 Anlık İndirme: {self.down_speed}",
            f"🔺 Anlık Yükleme: {self.up_speed}",
            f"📶 Sinyal Gücü: {sig}",
        ]
        return "\n".join(lines)

    def monitor_loop(self):
        """Background worker thread updating throughput every 1s and wifi details every 3s."""
        wifi_tick = 0
        while self.running:
            time.sleep(1.0)
            wifi_tick += 1

            self.update_throughput()

            if wifi_tick >= 3:
                wifi_tick = 0
                self.wifi_info = get_wifi_details()

            if self.icon:
                link_mbps = self.wifi_info.get("rx_mbps", "0")
                self.icon.title = self.build_tooltip()
                self.icon.icon = create_tray_icon_image(self.down_speed, link_mbps)

    def on_refresh(self, icon, item):
        """Force refresh Wi-Fi parameters."""
        self.wifi_info = get_wifi_details()
        self.update_throughput()
        if self.icon:
            self.icon.title = self.build_tooltip()

    def on_quit(self, icon, item):
        """Cleanly terminate application."""
        self.running = False
        if self.icon:
            self.icon.stop()

    def run(self):
        """Initialize system tray icon and start event loop."""
        self.update_throughput()
        self.wifi_info = get_wifi_details()

        link_mbps = self.wifi_info.get("rx_mbps", "0")
        img = create_tray_icon_image(self.down_speed, link_mbps)
        tooltip = self.build_tooltip()

        menu = pystray.Menu(
            pystray.MenuItem(lambda item: f"Ağ: {self.wifi_info.get('ssid')}", lambda icon, item: None, enabled=False),
            pystray.MenuItem(lambda item: f"Link: {self.wifi_info.get('rx_mbps')} Mbps", lambda icon, item: None, enabled=False),
            pystray.Menu.SEPARATOR,
            pystray.MenuItem("Şimdi Yenile", self.on_refresh),
            pystray.MenuItem("Çıkış", self.on_quit),
        )

        self.icon = pystray.Icon("WiFiSpeedTray", img, tooltip, menu)

        worker = threading.Thread(target=self.monitor_loop, daemon=True)
        worker.start()

        self.icon.run()


if __name__ == "__main__":
    app = WifiSpeedTrayApp()
    app.run()
