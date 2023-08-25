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

    if (url.protocol !== 'https:') {
      if (url.protocol !== 'http:' && url.hostname !== 'localhost' && url.hostname !== '127.0.0.1') {
        throw 'URL must be HTTPS'
      }
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
      .setName('New URL')
      .setDesc('Must be HTTPS, unless it\'s localhost')
      .addText(text => text
        .setPlaceholder('https://example.com/')
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
  origAjax = window.ajax
  settings = {}

  async onload() {
    await this.loadSettings()
    
    this.addSettingTab(new SettingsTab(this.app, this))

    window.ajax = arg => {
      if (arg.url.startsWith(ORIGIN_URL) && this.settings.newUrl) {
        arg.url = arg.url.replace(ORIGIN_URL, this.ettings.newUrl)
      }

      return this.origAjax(arg)
    }
  }

  onunload() {
    window.ajax = this.origAjax
  }

  async loadSettings() {
    this.settings = Object.assign({}, await this.loadData())
  }

  async saveSettings() {
    await this.saveData(this.settings)
  }
}
