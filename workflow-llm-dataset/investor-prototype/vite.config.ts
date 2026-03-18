import react from '@vitejs/plugin-react'
import path from 'path'
import { execFile } from 'child_process'
import { promisify } from 'util'
import { fileURLToPath } from 'url'
import fs from 'fs'
import type { Plugin } from 'vite'
import { defineConfig } from 'vite'

const execFileP = promisify(execFile)
const __dirname = path.dirname(fileURLToPath(import.meta.url))

function edgeDesktopSnapshotPlugin(): Plugin {
  return {
    name: 'edge-desktop-snapshot-api',
    configureServer(server) {
      server.middlewares.use(async (req, res, next) => {
        if (req.url?.split('?')[0] !== '/api/edge-desktop-snapshot') {
          return next()
        }
        if (req.method !== 'GET' && req.method !== 'POST') {
          return next()
        }
        const repo =
          process.env.EDGE_DESKTOP_REPO_ROOT ||
          path.resolve(__dirname, '..')
        let py =
          process.env.EDGE_DESKTOP_PYTHON ||
          path.join(repo, '.venv', 'bin', 'python')
        if (!fs.existsSync(py)) {
          py =
            process.env.EDGE_DESKTOP_PYTHON_FALLBACK ||
            (process.platform === 'win32' ? 'python' : 'python3')
        }
        const useAdapter =
          process.env.EDGE_DESKTOP_USE_ADAPTER === '1' ||
          process.env.VITE_EDGE_USE_ADAPTER === '1'
        const code = [
          'import json, pathlib, sys',
          `r = pathlib.Path(r"""${repo.replace(/\\/g, '/')}""").resolve()`,
          'sys.path.insert(0, str(r / "src"))',
          useAdapter
            ? 'from workflow_dataset.live_desktop_adapter import build_live_adapter_snapshot'
            : 'from workflow_dataset.edge_desktop.snapshot import build_edge_desktop_snapshot',
          useAdapter
            ? 'print(json.dumps(build_live_adapter_snapshot(repo_root=r), default=str))'
            : 'print(json.dumps(build_edge_desktop_snapshot(repo_root=r), default=str))',
        ].join('\n')
        try {
          const { stdout } = await execFileP(py, ['-c', code], {
            cwd: repo,
            timeout: 28_000,
            maxBuffer: 14 * 1024 * 1024,
            env: { ...process.env },
          })
          res.setHeader('Content-Type', 'application/json; charset=utf-8')
          res.end(stdout.trim())
        } catch (e: unknown) {
          const msg = e instanceof Error ? e.message : String(e)
          res.statusCode = 502
          res.setHeader('Content-Type', 'application/json; charset=utf-8')
          res.end(JSON.stringify({ error: msg, repo }))
        }
      })
    },
  }
}

// https://vite.dev/config/
export default defineConfig({
  plugins: [react(), edgeDesktopSnapshotPlugin()],
})
