# PocketBase Setup

Simple scripts to download, install, and run PocketBase.

## Quick Start

```bash
cd pocketbase
chmod +x start.sh stop.sh
./start.sh
```

## What start.sh Does

1. ✅ Checks if PocketBase is already downloaded
2. ⬇️ Downloads PocketBase if not found
3. 📦 Unzips the binary
4. 🚀 Starts PocketBase server on port 8090
5. 🔄 Runs in background (survives SSH disconnect)

## Commands

```bash
./start.sh    # Start PocketBase
./stop.sh     # Stop PocketBase
```

## Accessing PocketBase

- **Admin UI**: http://YOUR_VM_IP:8090/_/
- **API**: http://YOUR_VM_IP:8090/api/

## Firewall

Don't forget to open port 8090:

```bash
# GCP Console: Add firewall rule for tcp:8090
# Or via gcloud:
gcloud compute firewall-rules create allow-pocketbase --allow=tcp:8090
```

## Logs

```bash
tail -f pocketbase/pb_log.txt
```

## Features

- Auto-download on first run
- Skip download if already exists
- Process check before starting
- Background execution with nohup
- Clean up zip files after extraction

## Version

Current version: v0.22.8

To update, delete the `pocketbase` binary and run `./start.sh` again.
