const { createWriteStream } = require('node:fs')
const fs = require('node:fs/promises')
const os  = require('node:os')
const stream = require('node:stream/promises')
const path = require('node:path')
const zlib = require('node:zlib')

const axios = require('axios')
const asar = require('@electron/asar')
const { program } = require('commander')

const { patch } = require('./patch')

program
  .option('--beta', 'Use beta version')
  .option('--debug', 'Enable debug mode')
  .option('--dir <dir>', 'Directory to patch')
  .argument('[asarPath]')

program.parse()

const opts = program.opts()

function getAsarPath() {
  const path = program.args[0]

  return path
}

function getDistPath(asarPath) {
  return asarPath.replace('.asar', '.0.asar')
}

async function patchJs(dir) {
  const targetJS = path.join(dir, 'app.js')
  const content = await fs.readFile(targetJS, 'utf8')

  const newContent = (await patch(content)).code

  if (opts.debug) {
    const debugPath = targetJS + '.debug'
    await fs.writeFile(debugPath, newContent)
  } else {
    await fs.writeFile(targetJS, newContent)
  }
}

async function patchVersion(dir) {
  const targetJS = path.join(dir, 'package.json')
  if (!await fsExists(targetJS)) {
    return
  }

  const content = await fs.readFile(targetJS)

  const pkg = JSON.parse(content)
  pkg.version += '.repack'

  await fs.writeFile(targetJS, JSON.stringify(pkg, null, 2))
}

async function patchFiles(dir) {
  await patchJs(dir)
  await patchVersion(dir)
}

async function repackAsar(asarPath, distPath) {
  const tmpDir = await fs.mkdtemp(path.join(os.tmpdir(), 'ob-patch-'))
  console.log(`Temp dir: ${tmpDir}`)

  await asar.extractAll(asarPath, tmpDir)

  await patchFiles(tmpDir)

  const newPath = distPath ? distPath : getDistPath(asarPath)

  if (!opts.debug) {
    await asar.createPackage(tmpDir, newPath)
    await fs.rm(tmpDir, { recursive: true })
  }

  return newPath
}

async function fsExists(path) {
  try {
    await fs.access(path)
    return true
  } catch (e) {
    return false
  }
}

async function downloadFromGithub(useBeta) {
  let resp = await axios.get('https://raw.githubusercontent.com/obsidianmd/obsidian-releases/master/desktop-releases.json')
  let json = resp.data

  if (useBeta) {
    console.log('Using beta version')
    json = json['beta']
  }
  
  const minimumVersion = json['minimumVersion']
  const latestVersion = json['latestVersion']
  const url = json['downloadUrl']

  const targetPath = path.join('dist', `obsidian-${latestVersion}.asar`)

  console.log(`Minimum version: ${minimumVersion}`)
  console.log(`Latest version: ${latestVersion}`)
  console.log(`Download url: ${url}`)
  console.log(`Target path: ${targetPath}`)

  if (await fsExists(targetPath)) {
    console.log('Target file already exists')
    return targetPath
  }

  const headers = {}
  if (useBeta) {
    headers['User-Agent'] = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/86.0.4240.183 Safari/537.36'
  }

  resp = await axios.get(url, {
    headers,
    responseType: 'stream',
    onDownloadProgress: (event) => {
      const percentCompleted = Math.round((event.loaded * 100) / event.total)
      console.log(`Download progress: ${percentCompleted}%`)
    }
  })

  const tmpFile = targetPath + '.tmp'
  await stream.pipeline(
    resp.data,
    zlib.createGunzip(),
    createWriteStream(tmpFile),
  )

  await fs.rename(tmpFile, targetPath)

  return targetPath
}

async function main() {
  if (opts.dir) {
    console.log(`Patching directory: ${opts.dir}`)
    await patchFiles(opts.dir)
    return
  }

  let asarPath = getAsarPath()

  if (!asarPath) {
    asarPath = await downloadFromGithub(opts['beta'])
  }

  console.log(`Asar path: ${asarPath}`)
  const newPath = await repackAsar(asarPath)

  console.log(`Repacked asar: ${newPath}`)
}

if (require.main === module) {
  main()
}