# Obsidian Sync Server
A reimplemented sync server for Obsidian based on reverse engineering.
Not affiliated with [Obsidian.md](https://obsidian.md/).

![Supported Obsidian version](https://img.shields.io/badge/dynamic/json?url=https%3A%2F%2Fraw.githubusercontent.com%2FCzBiX%2Fob-sync-server%2Fmaster%2Fob-plugin%2Fapi-server%2Fmanifest.json&query=minAppVersion&logo=obsidian&label=Obsidian&color=rebeccapurple)
[![Plugin release](https://img.shields.io/github/v/release/czbix/ob-sync-server?label=plugin)](https://github.com/CzBiX/ob-sync-server/releases)
[![Server release](https://img.shields.io/github/v/tag/czbix/ob-sync-server?filter=v*&label=server)](https://github.com/CzBiX/ob-sync-server/pkgs/container/ob-sync-server)


## What works
- [x] support mobile devices
- [x] user create, login
- [x] vault list, create, delete
- [x] vault share
- [x] live sync
- [x] history, restore

## TODO
- [ ] database/storage cleanup
- [ ] API to access vaults/documents
- [ ] publish maybe?

## Usage

1. Run the server
   ```bash
   docker run -d \
     -p 8000:8000 \
     -v /path/to/data:/app/data \
     --name ob-sync-server \
     ghcr.io/czbix/ob-sync-server
   ```
2. Create database and user
   ```bash
   docker exec -it ob-sync-server ./cli.py create-database
   docker exec -it ob-sync-server ./cli.py create-user {name} {email} {password}
   ```

3. Install *api-server* plugin

    Download the plugin from [release](https://github.com/CzBiX/ob-sync-server/releases/latest), extract and put it into your vault's `.obsidian/plugins` folder.
    Enable the plugin and set the server URL to your server, such as `http://localhost:8000/`.
    Also do the same on your other devices if needed.

4. Follow the [official guide](https://help.obsidian.md/Obsidian+Sync/Set+up+Obsidian+Sync#Log+in+with+your+Obsidian+account) to set up sync on your devices.


## Disclaimer
This implementation is based on the reverse engineering of client, and may not be the same as the official server.
Most of features are implemented, and should work as expected.
But bugs may exist, use at your own risk.