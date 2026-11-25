// TEMPLATE: the per-episode render.cjs of a code-overlay serial (copy it into each episode folder).
// PURPOSE: the puppeteer canvas renderer of a code-overlay reel. The `stills` mode is the QA entry point: it renders
//   the FINAL composite (art + HUD + captions + cards) at the given seconds, full size, into stills/t0012.50.jpg.
//   Raw art in art/ is not enough - captions and cards only exist in these stills.
// NEEDS: index.html that sets window.READY, window.SIZE=[w,h], window.DUR and window.seek(t); `npm i puppeteer`.
// USAGE (inside the episode folder):
//   cat _engine.js _ep<n>.js > main.js && node render.cjs stills 0.5,2,4.2,7,...   # one time per shot, mid-shot
//   node render.cjs video --audio out/audio_final.wav                                # only after the stills pass
// node render.cjs stills 1,5,9        pictures at those seconds of the whole video, in stills/
// node render.cjs video               the video, at out/video.mp4
// node render.cjs video --audio a.mp3 the same, with that sound on it
const http = require('http'), fs = require('fs'), path = require('path'), cp = require('child_process')
let puppeteer
try { puppeteer = require('puppeteer') } catch { console.error('Run: npm i'); process.exit(1) }
const TYPES = { '.html': 'text/html', '.js': 'text/javascript', '.json': 'application/json', '.jpg': 'image/jpeg', '.png': 'image/png', '.ttf': 'font/ttf' }
const server = http.createServer((q, s) => {
  const f = path.join(__dirname, decodeURIComponent(q.url.split('?')[0]).replace(/^\/$/, '/index.html'))
  fs.readFile(f, (e, b) => { if (e) { s.writeHead(404); return s.end() } s.writeHead(200, { 'content-type': TYPES[path.extname(f)] || 'application/octet-stream' }); s.end(b) })
})
;(async () => {
  await new Promise((r) => server.listen(0, r))
  const gl = process.platform === 'darwin' ? '--use-angle=metal' : '--use-angle=swiftshader'
  const b = await puppeteer.launch({ headless: true, protocolTimeout: 300000, args: ['--enable-webgl', '--ignore-gpu-blocklist', gl, '--enable-unsafe-swiftshader'] })
  const p = await b.newPage()
  p.on('pageerror', (e) => { console.error('PAGE ERROR:', e.message); process.exit(1) })
  await p.setViewport({ width: 1920, height: 1920 })
  await p.goto(`http://localhost:${server.address().port}/index.html`, { waitUntil: 'networkidle2' })
  await p.waitForFunction(() => window.READY || window.FAILED, { timeout: 120000 })
  const failed = await p.evaluate(() => window.FAILED)
  if (failed) { console.error(failed); process.exit(1) }
  const [w, h] = await p.evaluate(() => window.SIZE)
  await p.setViewport({ width: w, height: h })
  const dur = await p.evaluate(() => window.DUR)
  const mode = process.argv[2]
  if (mode === 'stills') {
    fs.mkdirSync('stills', { recursive: true })
    for (const t of process.argv[3].split(',').map(Number)) {
      await p.evaluate((v) => window.seek(v), t)
      const file = `stills/t${t.toFixed(2).padStart(6, '0')}.jpg`
      await p.screenshot({ path: file, type: 'jpeg', quality: 88 })
      console.log(file)
    }
    console.log(`Stills in stills/. The story runs ${dur.toFixed(1)}s.`)
  } else {
    fs.mkdirSync('out', { recursive: true })
    const n = Math.round(dur * 30), audio = process.argv.indexOf('--audio')
    const args = ['-v', 'error', '-y', '-f', 'image2pipe', '-c:v', 'mjpeg', '-framerate', '30', '-i', '-']
    if (audio > 0) args.push('-i', process.argv[audio + 1], '-c:a', 'aac', '-b:a', '192k', '-shortest')
    args.push('-c:v', 'libx264', '-preset', 'medium', '-crf', '17', '-pix_fmt', 'yuv420p', '-movflags', '+faststart', 'out/video.mp4')
    const ff = cp.spawn('ffmpeg', args, { stdio: ['pipe', 'inherit', 'inherit'] })
    for (let i = 0; i < n; i++) {
      await p.evaluate((v) => window.seek(v), i / 30)
      const s = await p.screenshot({ type: 'jpeg', quality: 95 })
      if (!ff.stdin.write(s)) await new Promise((r) => ff.stdin.once('drain', r))
      if (i % 60 === 0) console.log(`frame ${i}/${n}`)
    }
    ff.stdin.end()
    await new Promise((r) => ff.on('close', r))
    console.log('Video: out/video.mp4')
  }
  await b.close(); server.close()
})().catch((e) => { console.error(e); process.exit(1) })
