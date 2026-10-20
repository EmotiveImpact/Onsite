// Isolated DOM/asset fixture served by Vite for interface checks. Not in the production entry.
// It never imports Encounter or physics and cannot modify the running game's simulation.
import '../src/style.css'
import {FrontEnd, type RoundSummary} from '../src/onsite/FrontEnd'
import type {OperatorKit, PlayerSettings} from '../src/onsite/profile'
import {Input} from '../src/wwb/engine/input'

const html = new DOMParser().parseFromString(await (await fetch('/index.html')).text(), 'text/html')
html.querySelectorAll('script').forEach(script => script.remove())
document.body.replaceChildren(...Array.from(html.body.childNodes))
document.body.dataset.flow = 'title'
const mapId = new URLSearchParams(location.search).get('map') === 'heron-court' ? 'heron-court' : 'heron-reach'
let appliedSettings: PlayerSettings | undefined, appliedKit: OperatorKit | undefined, titleReturns = 0
const frontEnd = new FrontEnd({mapId, onSettings: settings => {appliedSettings = settings}, onKit: kit => {appliedKit = kit}, onReturnToTitle: () => {titleReturns++}})
// Install the actual global gameplay listeners so native menu keys cannot regress silently.
// It stays unlocked: this fixture does not claim to exercise gameplay or pointer lock.
const input = new Input(document.getElementById('game') as HTMLCanvasElement)
window.addEventListener('pagehide', () => input.dispose(), {once: true})
for (const id of ['start', 'resume', 'restart', 'restart-pause']) document.getElementById(id)!.onclick = () => frontEnd.enterGame()
frontEnd.markReady()
Object.defineProperty(window, '__frontendFixture', {value: {
  ready: true,
  pause: () => frontEnd.showPause(),
  result: (summary: RoundSummary) => frontEnd.showResult(summary),
  inspect: () => ({settings: appliedSettings, kit: appliedKit, titleReturns}),
}})
