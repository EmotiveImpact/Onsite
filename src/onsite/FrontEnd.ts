// Original ONSITE player-facing flow. The existing runtime still owns simulation and pointer lock.
import {accuracy, loadProfile, recordRound, saveProfile, type MapId, type OperatorKit, type PlayerProfile, type PlayerSettings, type RoundRecord} from './profile'
import type {KitPreview} from './KitPreview'

const $ = <T extends HTMLElement = HTMLElement>(id: string) => document.getElementById(id) as T
const clock = (seconds: number) => `${Math.floor(seconds / 60).toString().padStart(2, '0')}:${Math.floor(seconds % 60).toString().padStart(2, '0')}`
const maps = {
  'heron-court': {name: 'Heron Court', bots: 3, levels: 2, seconds: 180, copy: 'Clear three opponents, then secure the court. Two stair routes connect the courtyard and upper gallery.'},
  'heron-reach': {name: 'Heron Reach', bots: 6, levels: 5, seconds: 300, copy: 'Clear six opponents across the estate, then secure The Cage. Basements, galleries and upper routes connect five levels.'},
} as const
type FrontEndOptions = {mapId: MapId; onSettings: (settings: PlayerSettings) => void; onKit: (kit: OperatorKit) => void; onReturnToTitle: () => void}
export type RoundSummary = Omit<RoundRecord, 'completedAt'>

export class FrontEnd {
  private profile: PlayerProfile
  private panel = 'play'
  private ready = false
  private preview?: KitPreview
  private previewLoading = false
  private resultRecorded = false
  private storageAvailable = true
  private readonly map

  constructor(private readonly options: FrontEndOptions) {
    this.profile = loadProfile(undefined, window.matchMedia('(prefers-reduced-motion: reduce)').matches)
    this.map = maps[options.mapId]
    $('mission-title').textContent = `${this.map.name}.`
    $('mission-copy').textContent = this.map.copy
    $('mission-bots').textContent = String(this.map.bots).padStart(2, '0')
    $('mission-levels').textContent = String(this.map.levels).padStart(2, '0')
    $('mission-time').textContent = clock(this.map.seconds)
    $('location-name').replaceChildren(...this.map.name.split(' ').flatMap((part, i) => i ? [document.createElement('br'), document.createTextNode(part.toUpperCase())] : [document.createTextNode(part.toUpperCase())]))
    $('load-status').textContent = `Preparing ${this.map.name}…`
    document.querySelectorAll<HTMLAnchorElement>('[data-map]').forEach(link => {
      const current = link.dataset.map === options.mapId
      link.classList.toggle('selected', current)
      if (current) { link.setAttribute('aria-current', 'page'); link.addEventListener('click', e => e.preventDefault()) }
      link.querySelector('.map-status')!.textContent = current ? 'SELECTED' : 'LOAD'
    })
    const tabs = [...document.querySelectorAll<HTMLButtonElement>('[data-panel]')]
    tabs.forEach((tab, index) => {
      tab.addEventListener('click', () => this.showPanel(tab.dataset.panel!))
      tab.addEventListener('keydown', event => {
        let next: number | undefined
        if (event.key === 'ArrowRight') next = (index + 1) % tabs.length
        if (event.key === 'ArrowLeft') next = (index + tabs.length - 1) % tabs.length
        if (event.key === 'Home') next = 0
        if (event.key === 'End') next = tabs.length - 1
        if (next !== undefined) { event.preventDefault(); this.showPanel(tabs[next].dataset.panel!); tabs[next].focus() }
      })
    })
    document.querySelectorAll<HTMLInputElement | HTMLSelectElement>('[data-setting]').forEach(control => {
      control.addEventListener(control instanceof HTMLInputElement && control.type === 'range' ? 'input' : 'change', () => {
        const key = control.dataset.setting as keyof PlayerSettings
        const settings = this.profile.settings
        if (key === 'quality') settings.quality = control.value === 'balanced' || control.value === 'detail' ? control.value : 'auto'
        else if (key === 'sound' || key === 'reducedMotion') settings[key] = (control as HTMLInputElement).checked
        else settings[key] = Number(control.value)
        this.syncSettings(); this.persist(); options.onSettings(this.settings)
      })
    })
    document.querySelectorAll<HTMLInputElement>('input[name="hood"], input[name="trainers"]').forEach(control => control.addEventListener('change', () => {
      if (!control.checked) return
      if (control.name === 'hood') this.profile.kit.hood = control.value === 'down' ? 'down' : 'up'
      else this.profile.kit.trainers = control.value === 'runner' || control.value === 'high' ? control.value : 'court'
      this.preview?.setKit(this.kit); this.persist(); options.onKit(this.kit)
    }))
    for (const id of ['leave-pause', 'leave-result']) $(id).addEventListener('click', () => { options.onReturnToTitle(); this.returnToTitle() })
    // Modal focus remains in the visible pause/result sheet; gameplay never traps Tab.
    document.addEventListener('keydown', event => {
      if (event.key !== 'Tab') return
      const dialog = !$('pause').hidden ? $('pause') : !$('result').hidden ? $('result') : null
      if (!dialog) return
      const focusable = [...dialog.querySelectorAll<HTMLElement>('button:not([disabled]), input, select, a[href]')]
      const first = focusable[0], last = focusable.at(-1)
      if (event.shiftKey && document.activeElement === first) { event.preventDefault(); last?.focus() }
      else if (!event.shiftKey && document.activeElement === last) { event.preventDefault(); first?.focus() }
    })
    this.syncSettings(); this.syncKit(); this.updateRecord()
    options.onSettings(this.settings); options.onKit(this.kit)
  }

  get settings(): PlayerSettings { return {...this.profile.settings} }
  get kit(): OperatorKit { return {...this.profile.kit} }

  markReady(): void {
    this.ready = true
    $('start').removeAttribute('disabled')
    $('start').innerHTML = 'ENTER THE ESTATE <span aria-hidden="true">↗</span>'
    $('load-status').textContent = `${this.map.name} ready · Keyboard & mouse required`
  }
  markLoadError(message: string): void {
    $('start').setAttribute('disabled', '')
    $('load-status').textContent = `The estate could not load. ${message}`
  }
  enterGame(): void {
    this.resultRecorded = false
    $('menu').hidden = true; $('pause').hidden = true; $('result').hidden = true; $('hud').hidden = false
    document.body.dataset.flow = 'game'
    this.preview?.setActive(false)
    if (document.activeElement instanceof HTMLElement) document.activeElement.blur()
  }
  showPause(): void {
    $('pause').hidden = false; $('result').hidden = true
    document.body.dataset.flow = 'pause'
    $('resume').focus({preventScroll: true})
  }
  showResult(summary: RoundSummary): void {
    if (!this.resultRecorded) {
      this.profile = recordRound(this.profile, this.options.mapId, {...summary, completedAt: Date.now()})
      this.resultRecorded = true; this.persist(); this.updateRecord()
    }
    const won = summary.outcome === 'won', best = this.profile.records[this.options.mapId].best
    $('pause').hidden = true; $('result').hidden = false
    document.body.dataset.flow = 'result'
    $('result-eyebrow').textContent = `ONSITE / ${this.map.name.toUpperCase()}`
    $('result-title').textContent = won ? 'Site secured.' : 'Not this time.'
    $('result-detail').textContent = won ? `All ${this.map.bots} opponents cleared. Capture complete.` : `${summary.kills} of ${this.map.bots} opponents cleared. Regroup and go again.`
    $('result-time').textContent = clock(summary.seconds)
    $('result-accuracy').textContent = `${accuracy(summary)}%`
    $('result-kills').textContent = `${summary.kills} / ${this.map.bots}`
    $('result-record').textContent = best ? `BEST CAPTURE ${clock(best.seconds)} · ${accuracy(best)}% accuracy` : 'Complete a capture to set your first record.'
    $('restart').focus({preventScroll: true})
  }
  returnToTitle(): void {
    $('menu').hidden = false; $('pause').hidden = true; $('result').hidden = true; $('hud').hidden = true
    document.body.dataset.flow = 'title'
    this.showPanel('play'); this.updateRecord()
    ;(this.ready ? $('start') : $('tab-play')).focus({preventScroll: true})
  }
  private showPanel(panel: string): void {
    this.panel = panel
    document.querySelectorAll<HTMLButtonElement>('[data-panel]').forEach(tab => {
      const selected = tab.dataset.panel === panel
      tab.setAttribute('aria-selected', String(selected)); tab.tabIndex = selected ? 0 : -1
      $(`panel-${tab.dataset.panel}`).hidden = !selected
    })
    $('kit-stage').hidden = panel !== 'kit'; $('menu-location').hidden = panel === 'kit'
    this.preview?.setActive(panel === 'kit' && !$('menu').hidden)
    if (panel === 'kit') void this.loadPreview()
  }
  private async loadPreview(): Promise<void> {
    if (this.preview || this.previewLoading) return
    this.previewLoading = true
    try {
      const {KitPreview} = await import('./KitPreview')
      this.preview = new KitPreview($('operator-preview'))
      await this.preview.ready
      this.preview.setKit(this.kit)
      this.preview.setActive(this.panel === 'kit' && !$('menu').hidden)
      $('kit-preview-status').textContent = ''
    } catch {
      this.preview?.dispose(); this.preview = undefined; this.previewLoading = false
      $('kit-preview-status').textContent = 'Kit preview is unavailable. Your selections are still saved.'
    }
  }
  private syncSettings(): void {
    document.body.classList.toggle('reduced-motion', this.profile.settings.reducedMotion)
    document.querySelectorAll<HTMLInputElement | HTMLSelectElement>('[data-setting]').forEach(control => {
      const value = this.profile.settings[control.dataset.setting as keyof PlayerSettings]
      if (typeof value === 'boolean') (control as HTMLInputElement).checked = value
      else control.value = String(value)
    })
    document.querySelectorAll('[data-value="sensitivity"]').forEach(output => {output.textContent = `${this.profile.settings.sensitivity.toFixed(1)}×`})
    document.querySelectorAll('[data-value="volume"]').forEach(output => {output.textContent = `${Math.round(this.profile.settings.volume * 100)}%`})
  }
  private syncKit(): void {
    for (const [name, value] of Object.entries(this.kit)) {
      const input = document.querySelector<HTMLInputElement>(`input[name="${name}"][value="${value}"]`)
      if (input) input.checked = true
    }
  }
  private persist(): void {
    this.storageAvailable = saveProfile(this.profile)
    $('save-status').textContent = this.storageAvailable ? 'Saved on this device.' : 'Storage is unavailable. Preferences apply until this page closes.'
    $('result-storage').textContent = this.storageAvailable ? 'Encounter records are stored on this device only.' : 'Storage is unavailable. This record lasts until the page closes.'
  }
  private updateRecord(): void {
    const record = this.profile.records[this.options.mapId]
    $('record-summary').textContent = record.best ? `BEST CAPTURE ${clock(record.best.seconds)} · ${accuracy(record.best)}% accuracy · ${record.secured} secured` : record.last ? `LAST ATTEMPT ${clock(record.last.seconds)} · ${record.last.kills}/${this.map.bots} opponents · Capture to set a record.` : 'No completed runs yet. Your records stay on this device.'
    if (!this.storageAvailable) $('record-summary').textContent += ' Session only.'
  }
}
