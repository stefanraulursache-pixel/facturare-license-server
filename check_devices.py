"""
Arata pe ce device-uri a fost folosita o cheie de licenta (pentru detectia
partajarii aceleiasi chei pe mai multe masini).

Folosire:
    python check_devices.py NUME-CHEIE

ADMIN_TOKEN se citeste din variabila de mediu ADMIN_TOKEN, daca exista,
altfel ti-l cere la prompt (ascuns, nu apare pe ecran cand il tastezi).
"""

import getpass
import json
import os
import sys
import urllib.parse
import urllib.request

SERVER_URL = "https://facturare-license-server.onrender.com"


def main():
    if len(sys.argv) != 2:
        print("Folosire: python check_devices.py NUME-CHEIE")
        sys.exit(1)

    key = sys.argv[1]
    admin_token = os.environ.get("ADMIN_TOKEN") or getpass.getpass("ADMIN_TOKEN: ")

    query = urllib.parse.urlencode({"admin_token": admin_token})
    url = f"{SERVER_URL}/devices/{urllib.parse.quote(key)}?{query}"

    with urllib.request.urlopen(url, timeout=15) as resp:
        result = json.loads(resp.read().decode("utf-8"))

    devices = result.get("devices", [])
    if not devices:
        print(f"Cheia '{key}' nu a fost folosita inca pe niciun device.")
        return

    print(f"Cheia '{key}' a fost folosita pe {len(devices)} device(uri):\n")
    for d in devices:
        print(f"  - {d['device_id']}  (vazut ultima oara: {d['seen_at']})")

    unique_devices = {d["device_id"] for d in devices}
    if len(unique_devices) > 1:
        print(f"\nATENTIE: cheia a fost vazuta pe {len(unique_devices)} device-uri DIFERITE - posibila partajare.")


if __name__ == "__main__":
    main()
