"""
Emite o cheie noua de licenta, prin serverul live.

Folosire:
    python issue_key.py NUME-CHEIE

ADMIN_TOKEN se citeste din variabila de mediu ADMIN_TOKEN, daca exista,
altfel ti-l cere la prompt (ascuns, nu apare pe ecran cand il tastezi).
"""

import getpass
import json
import os
import sys
import urllib.request

SERVER_URL = "https://facturare-license-server.onrender.com"


def main():
    if len(sys.argv) != 2:
        print("Folosire: python issue_key.py NUME-CHEIE")
        sys.exit(1)

    key = sys.argv[1]
    admin_token = os.environ.get("ADMIN_TOKEN") or getpass.getpass("ADMIN_TOKEN: ")

    payload = json.dumps({"key": key, "admin_token": admin_token}).encode("utf-8")
    req = urllib.request.Request(
        f"{SERVER_URL}/issue", data=payload,
        headers={"Content-Type": "application/json"}, method="POST",
    )
    with urllib.request.urlopen(req, timeout=15) as resp:
        result = json.loads(resp.read().decode("utf-8"))

    print(result)


if __name__ == "__main__":
    main()
