# ob-sync-server
A reimplemented sync server for Obsidian via reverse engineering.

![Supported Obsidian version](https://img.shields.io/badge/dynamic/json?url=https%3A%2F%2Fraw.githubusercontent.com%2FCzBiX%2Fob-sync-server%2Fmaster%2Fob-plugin%2Fapi-server%2Fmanifest.json&query=minAppVersion&logo=obsidian&label=Obsidian&color=rebeccapurple)


> [!WARNING]
> Some behavior may be different from the official server.

## What works
- [x] user login
- [x] vault listing, creation, and deletion
- [x] document live syncing
- [x] document history, restore

## TODO
- [ ] database/storage cleaning
- [ ] API to access vaults/documents
- [ ] share vault
- [ ] publish maybe?

## Usage

1. Run the server
   ```bash
   docker run -d \
     -p 8000:8000 \
     -v /path/to/data:/app/data \
     --name ob-sync-server \
     ghcr.io/czbix/ob-sync-server:master
   ```
2. Create user
   ```bash
   docker exec -it ob-sync-server python3 -m src.cli create-user {name} {email} {password}
   ```

3. Install api-servr plugin

    Copy the `ob-plugin/api-server` folder to your vault's `.obsidian/plugins` directory.

    Enable the plugin and set the server URL to `http://localhost:8000`.

4. Login and enjoy
