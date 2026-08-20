import { execFileSync } from 'node:child_process'
import path from 'node:path'

export default function teardown() {
  const cwd = path.resolve(__dirname, '../..')
  const diff = execFileSync('git', ['diff', '--', 'web/next-env.d.ts', 'web/tsconfig.json'], {
    cwd,
    encoding: 'utf8',
  })
  if (!diff.includes('.next-rotulos-off') && !diff.includes('compras-rotulos-off')) return
  execFileSync('git', ['checkout', '--', 'web/next-env.d.ts', 'web/tsconfig.json'], { cwd })
}
