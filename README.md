# Obsidian Sync Server
A reimplemented sync server for Obsidian based on reverse engineering.
Not affiliated with Obsidian.md.

![Supported Obsidian version](https://img.shields.io/badge/dynamic/json?url=https%3A%2F%2Fraw.githubusercontent.com%2FCzBiX%2Fob-sync-server%2Fmaster%2Fob-plugin%2Fapi-server%2Fmanifest.json&query=minAppVersion&logo=obsidian&label=Obsidian&color=rebeccapurple)

## Disclaimer
This implementation is based on the reverse engineering of client, and may not be the same as the official server.
Most of features are implemented, and should work as expected.
But bugs may exist, use at your own risk.

## What works
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
   docker exec -it ob-sync-server \
     python3 -m src.cli create-database
   docker exec -it ob-sync-server \
     python3 -m src.cli create-user {name} {email} {password}
   ```

3. Install api-server plugin

    Copy the `ob-plugin/api-server` folder to your vault's `.obsidian/plugins` directory.

    Enable the plugin and set the server URL to your server, such as `http://localhost:8000/`.

4. Login and enjoy

   Also do the same on your phone if needed.