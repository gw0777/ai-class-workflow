import type { Register, EngineInterface } from 'claude-code'

// 특수체육 용어 가드
// Claude가 Write/Edit로 파일을 저장하기 직전에 끼어들어,
// 새로 쓰는 글(content, new_string)의 '적응체육'·'적응 체육'을 '특수체육'으로 바꾼다.
// 바꾼 사실은 도구 결과 뒤에 Claude만 읽는 메모(context)로 알려, 이후 Edit가 옛 표현을 찾다 실패하지 않게 한다.

const OLD_TERM = /적응\s*체육/g
const NEW_TERM = '특수체육'
const NOTE =
  `term-guard: 저장된 파일에서는 '적응체육'이 '${NEW_TERM}'으로 바뀌어 있습니다. ` +
  `이 파일을 다시 Edit할 때 old_string에는 '${NEW_TERM}'을 쓰세요.`

function fix(text: string): { text: string; count: number } {
  const count = (text.match(OLD_TERM) ?? []).length
  return { text: count ? text.replace(OLD_TERM, NEW_TERM) : text, count }
}

function baseName(path: string): string {
  return path.split('/').pop() ?? path
}

// 바꾼 곳이 있으면 알림을 띄우고 상태 줄 누계를 올린다.
function announce($: EngineInterface, path: string, count: number, total: number): void {
  $.ui.toast(`용어 가드: ${baseName(path)}에서 '적응체육' ${count}곳 → '${NEW_TERM}'`)
  $.ui.status(`용어 가드 ${total}곳 교정`)
}

// Edit의 old_string이 옛 표현인데 파일에는 바뀐 표현만 있으면, old_string도 바뀐 표현으로 맞춘다.
async function alignOld($: EngineInterface, path: string, old: string): Promise<string> {
  const fixed = fix(old)
  if (!fixed.count) return old
  try {
    const body = await $.fs.read(path)
    if (!body.includes(old) && body.includes(fixed.text)) return fixed.text
  } catch {
    // 읽지 못하면 원래대로 둔다
  }
  return old
}

export const register: Register = on => {
  let total = 0

  on('tool.call', { tool: 'Write' }, async ($, e, next) => {
    const { text, count } = fix(e.content)
    if (!count) return next(e)
    total += count
    announce($, e.file_path, count, total)
    const r = await next({ ...e, content: text })
    return r.deny === undefined && r.isError === undefined ? { ...r, context: [...(r.context ?? []), NOTE] } : r
  }).catch(($, e, next) => next(e))

  on('tool.call', { tool: 'Edit' }, async ($, e, next) => {
    const old = await alignOld($, e.file_path, e.old_string)
    const { text, count } = fix(e.new_string)
    if (!count && old === e.old_string) return next(e)
    if (count) {
      total += count
      announce($, e.file_path, count, total)
    }
    const r = await next({ ...e, old_string: old, new_string: text })
    return count && r.deny === undefined && r.isError === undefined ? { ...r, context: [...(r.context ?? []), NOTE] } : r
  }).catch(($, e, next) => next(e))
}
