"""
Network Doctor - Comprehensive Windows Network & Wi-Fi Diagnostic Tool
======================================================================
Collects deep diagnostics about Wi-Fi connection, channel congestion,
gateway latency, jitter, packet loss, DNS performance, and MTU health.
Outputs a structured JSON report for instant AI analysis.
"""

import json
import os
import platform
import re
import subprocess
import time
from datetime import datetime

REPORT_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "network_diagnostic_report.json")


def run_cmd(cmd: str) -> str:
    """Run shell command and return trimmed output."""
    try:
        res = subprocess.run(cmd, shell=True, capture_output=True, text=True, timeout=30, encoding="cp857", errors="ignore")
        return res.stdout.strip()
    except Exception as e:
        return f"ERROR: {e}"


def get_wifi_interfaces() -> dict:
    """Extract current connected Wi-Fi interface details."""
    out = run_cmd("netsh wlan show interfaces")
    data = {}
    for line in out.splitlines():
        if ":" in line:
            parts = line.split(":", 1)
            k = parts[0].strip()
            v = parts[1].strip()
            if k:
                data[k] = v
    return data


def get_neighbor_networks() -> list:
    """Scan and list all surrounding Wi-Fi networks and channels."""
    out = run_cmd("netsh wlan show networks mode=bssid")
    networks = []
    current_net = {}
    current_bssid = {}

    for line in out.splitlines():
        line = line.strip()
        if line.startswith("SSID"):
            if current_net:
                networks.append(current_net)
            ssid_name = line.split(":", 1)[1].strip() if ":" in line else "Hidden"
            current_net = {"ssid": ssid_name, "bssids": []}
        elif line.startswith("BSSID"):
            bssid_val = line.split(":", 1)[1].strip()
            current_bssid = {"bssid": bssid_val}
            if current_net:
                current_net["bssids"].append(current_bssid)
        elif line.startswith("Signal"):
            sig = line.split(":", 1)[1].strip()
            current_bssid["signal"] = sig
        elif line.startswith("Channel"):
            ch = line.split(":", 1)[1].strip()
            current_bssid["channel"] = ch
        elif line.startswith("Radio type"):
            rad = line.split(":", 1)[1].strip()
            current_bssid["radio"] = rad
        elif line.startswith("Band"):
            bnd = line.split(":", 1)[1].strip()
            current_bssid["band"] = bnd

    if current_net:
        networks.append(current_net)
    return networks


def ping_test(host: str, count: int = 5) -> dict:
    """Ping a host to measure packet loss, min/avg/max latency and jitter."""
    out = run_cmd(f"ping -n {count} {host}")
    times = []
    lost = 0
    for line in out.splitlines():
        m = re.search(r"time[<=](\d+)ms", line, re.IGNORECASE)
        if m:
            times.append(int(m.group(1)))
        if "Request timed out" in line or "zaman aşımı" in line:
            lost += 1

    packet_loss_pct = (lost / count) * 100 if count > 0 else 0
    avg_latency = sum(times) / len(times) if times else 999.0
    jitter = max(times) - min(times) if len(times) > 1 else 0

    return {
        "target": host,
        "sent": count,
        "received": len(times),
        "packet_loss_pct": packet_loss_pct,
        "min_ms": min(times) if times else None,
        "max_ms": max(times) if times else None,
        "avg_ms": round(avg_latency, 2),
        "jitter_ms": jitter,
        "samples": times,
    }


def dns_benchmark() -> dict:
    """Test resolution speed for common domains."""
    domains = ["google.com", "cloudflare.com", "borsadirekt.com", "osmanlimenkul.com.tr"]
    results = {}
    import socket
    for d in domains:
        start = time.perf_counter()
        try:
            ip = socket.gethostbyname(d)
            elapsed_ms = round((time.perf_counter() - start) * 1000, 2)
            results[d] = {"ip": ip, "resolve_time_ms": elapsed_ms, "status": "OK"}
        except Exception as e:
            results[d] = {"error": str(e), "status": "FAIL"}
    return results


def check_mtu(gateway_ip: str = "192.168.1.1") -> dict:
    """Find maximum non-fragmented MTU."""
    sizes = [1472, 1464, 1452, 1420, 1400]
    optimal_payload = None
    for size in sizes:
        out = run_cmd(f"ping -f -l {size} -n 1 {gateway_ip}")
        if "Packet needs to be fragmented" not in out and "parçalanması gerekiyor" not in out:
            optimal_payload = size
            break
    
    total_mtu = (optimal_payload + 28) if optimal_payload else 1500
    return {
        "optimal_payload": optimal_payload,
        "effective_mtu": total_mtu,
        "is_fragmentation_risk": total_mtu < 1492,
    }


def get_ip_config() -> dict:
    """Get system IP and DNS configurations."""
    ps_cmd = "powershell -Command \"Get-NetIPConfiguration | Select-Object -Property InterfaceAlias, IPv4Address, IPv4DefaultGateway, DNSServer | ConvertTo-Json -Depth 2\""
    raw_json = run_cmd(ps_cmd)
    try:
        return json.loads(raw_json)
    except Exception:
        return {"raw": raw_json}


def main():
    print("=" * 60)
    print("🩺 AĞ DOKTORU: KAPSAMLI AĞ VE Wİ-Fİ TANI TESTİ BAŞLATILIYOR...")
    print("=" * 60)

    report = {
        "timestamp": datetime.now().isoformat(),
        "os": platform.platform(),
        "computer_name": platform.node(),
    }

    print("\n[1/5] Wi-Fi kartı ve mevcut bağlantı taranıyor...")
    wifi_info = get_wifi_interfaces()
    report["wifi_connection"] = wifi_info
    print(f" -> Bağlı Ağ: {wifi_info.get('SSID', 'Bilinmiyor')}")
    print(f" -> Frekans Bandı: {wifi_info.get('Band', 'Bilinmiyor')}")
    print(f" -> Kanal: {wifi_info.get('Channel', 'Bilinmiyor')}")
    print(f" -> Bağlantı Hızı: Alış: {wifi_info.get('Receive rate (Mbps)', '?')} Mbps | İletim: {wifi_info.get('Transmit rate (Mbps)', '?')} Mbps")

    print("\n[2/5] Çevredeki komşu ağlar ve kanal kirliliği taranıyor...")
    neighbors = get_neighbor_networks()
    report["neighbor_networks_count"] = len(neighbors)
    report["neighbor_networks"] = neighbors
    print(f" -> Tespit edilen komşu Wi-Fi sayısı: {len(neighbors)}")

    print("\n[3/5] Modem ve İnternet gecikme/jitter testleri yapılıyor...")
    gateway_ping = ping_test("192.168.1.1", count=6)
    dns1_ping = ping_test("1.1.1.1", count=6)
    dns2_ping = ping_test("8.8.8.8", count=6)
    report["ping_tests"] = {
        "gateway_192.168.1.1": gateway_ping,
        "cloudflare_1.1.1.1": dns1_ping,
        "google_8.8.8.8": dns2_ping,
    }
    print(f" -> Modem (192.168.1.1) Gecikme: {gateway_ping['avg_ms']} ms (Jitter: {gateway_ping['jitter_ms']} ms)")
    print(f" -> İnternet (1.1.1.1) Gecikme: {dns1_ping['avg_ms']} ms (Jitter: {dns1_ping['jitter_ms']} ms)")

    print("\n[4/5] DNS çözümleme hızları ölçülüyor...")
    dns_res = dns_benchmark()
    report["dns_resolution"] = dns_res
    for domain, ddata in dns_res.items():
        print(f" -> {domain:20}: {ddata.get('resolve_time_ms', '?')} ms")

    print("\n[5/5] MTU paket büyüklüğü ve IP konfigürasyonu alınıyor...")
    mtu_info = check_mtu("192.168.1.1")
    report["mtu_health"] = mtu_info
    report["ip_configuration"] = get_ip_config()
    print(f" -> Efektif MTU: {mtu_info['effective_mtu']}")

    # Save to JSON
    with open(REPORT_FILE, "w", encoding="utf-8") as f:
        json.dump(report, f, indent=2, ensure_ascii=False)

    print("\n" + "=" * 60)
    print(f"✅ TANI RAPORU OLUŞTURULDU: {REPORT_FILE}")
    print("=" * 60)
    print("Bu dosya kaydedildi. Antigravity bu raporu okuyup size özel reçeteyi sunacak!")


if __name__ == "__main__":
    main()
