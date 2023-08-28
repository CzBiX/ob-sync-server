const { Plugin, PluginSettingTab, Setting } = require('obsidian')

const ORIGIN_URL = 'https://api.obsidian.md/'

class SettingsTab extends PluginSettingTab {
  plugin = null  

  constructor(app, plugin) {
    super(app, plugin)
    this.plugin = plugin
  }

  checkUrl(url) {
    if (!url) {
      return null
    }

    url = new URL(url)

    if (!url.protocol.startsWith('http')) {
      throw 'URL must be HTTP/HTTPS'
    }

    if (!url.pathname.endsWith('/')) {
      url.pathname += '/'
    }

    return url.toJSON()
  }

  display() {
    let { containerEl } = this

    containerEl.empty()

    const s = new Setting(containerEl)
      .setName('Server URL')
      .setDesc(createSpan({
        text: 'The new URL to use for API requests. HTTPS is recommended.',
      }))
      .addText(text => text
        .setPlaceholder('http://example.com/')
        .setValue(this.plugin.settings.newUrl)
        .onChange(async (value) => {
          let url = null;
          try {
            url = this.checkUrl(value)
          } catch (e) {
            console.log('Invalid URL', e)
          }

          text.inputEl.toggleClass('input-error', !url)
          if (!url) {
            return
          }

          this.plugin.settings.newUrl = url
          await this.plugin.saveSettings()
        }))
  }
}

module.exports = class ApiServerPlugin extends Plugin {
  settings = {}

  constructor(app, manifest) {
    super(app, manifest)

    this.origAjax = window.ajax

    const syncInstance = this.getInternalPluginInstance('sync')
    this.origGetHost = syncInstance.getHost.bind(syncInstance)
  }

  getInternalPluginInstance(id) {
    return this.app.internalPlugins.getPluginById(id).instance
  }

  async onload() {
    await this.loadSettings()
    
    this.addSettingTab(new SettingsTab(this.app, this))

    window.ajax = arg => {
      if (this.settings.newUrl && arg.url.startsWith(ORIGIN_URL)) {
        arg.url = arg.url.replace(ORIGIN_URL, this.settings.newUrl)
      }

      return this.origAjax(arg)
    }

    this.getInternalPluginInstance('sync').getHost = () => {
      let url = this.origGetHost()

      if (this.settings.newUrl && this.settings.newUrl.startsWith('http:')) {
        url = url.replace('wss:', 'ws:')
      }

      return url
    }
  }

  onunload() {
    window.ajax = this.origAjax
    delete this.getInternalPluginInstance('sync').getHost
  }

  async loadSettings() {
    this.settings = Object.assign({}, await this.loadData())
  }

  async saveSettings() {
    await this.saveData(this.settings)
  }
}
