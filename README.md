# 📶 WiFi Speed Tray

> Lightweight, real-time Windows System Tray monitor displaying **Physical Wi-Fi Link Speed (Mbps)** and **Live Network Throughput (Download & Upload in KB/s & MB/s)**.

---

## ✨ Features

* **⚡ Physical Link Speed:** Shows current negotiated Wi-Fi transmit/receive rate (e.g. `263.3 Mbps`, `433 Mbps`, `866 Mbps`).
* **🔻 Live Internet Throughput:** Real-time download (`↓ 1.4 MB/s`) and upload (`↑ 120 KB/s`) speed calculation with microsecond precision.
* **🎯 Rich Hover Tooltip:**
  ```text
  📶 Ağ: Hg_5 (5 GHz - Kanal 48)
  ⚡ Fiziksel Link: 263.3 Mbps (Alış) / 263.3 Mbps (Veriş) | 802.11ac
  🔻 Anlık İndirme: 1.4 MB/s
  🔺 Anlık Yükleme: 120 KB/s
  📶 Sinyal Gücü: %78
  ```
* **🎨 Modern Dynamic Icon:** Renders a 64x64 high-DPI icon directly in the system tray displaying download speed (`↓1.4M`) and link speed (`263M`).
* **🪶 Zero Bloat:** Built with Python, `pystray`, `Pillow`, and `psutil`. Uses virtually zero CPU and ~15MB RAM.
* **🩺 Built-in Network Doctor:** Includes `network_doctor.py` for comprehensive Wi-Fi, MTU, DNS, and channel congestion diagnostics.

---

## 🚀 Quick Start

### 1. Requirements
Ensure Python 3.9+ is installed, then install dependencies:
```bash
pip install -r requirements.txt
```

### 2. Run
Double-click **`start_wifi_speed_tray.bat`** or run:
```bash
pythonw wifi_speed_tray.py
```
The icon will appear silently in your Windows System Tray (next to the clock).

### 3. Start with Windows (Automatic)
Double-click **`add_to_startup.bat`** to enable running automatically on Windows boot.

---

## 🛠️ Diagnostics (Network Doctor)
Run the built-in diagnostic tool to analyze Wi-Fi channel overlaps, DNS resolution latency, and MTU:
```bash
python network_doctor.py
```

---

## 📄 License
MIT License © 2026 Habil Gür
