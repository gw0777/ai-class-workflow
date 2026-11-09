import { expect, test } from 'claude-code/testing'

test('Write: 저장할 글의 적응체육을 특수체육으로 바꾼다', async ($, on) => {
  let saved = ''
  on('tool.call', (_, e) => {
    if (e.tool === 'Write') saved = e.content
    return { result: {} }
  })
  await $.tool.call({ tool: 'Write', file_path: '/x/lesson.md', content: '적응체육 수업과 적응 체육 평가' })
  expect(saved).toBe('특수체육 수업과 특수체육 평가')
})

test('Edit: new_string만 바꾸고 old_string은 그대로 둔다', async ($, on) => {
  let oldS = ''
  let newS = ''
  on('tool.call', (_, e) => {
    if (e.tool === 'Edit') { oldS = e.old_string; newS = e.new_string }
    return { result: {} }
  })
  await $.tool.call({ tool: 'Edit', file_path: '/x/a.md', old_string: '적응체육 개론', new_string: '적응체육 개론 2판' })
  expect(oldS).toBe('적응체육 개론')
  expect(newS).toBe('특수체육 개론 2판')
})

test('해당 용어가 없으면 글을 그대로 넘긴다', async ($, on) => {
  let saved = ''
  on('tool.call', (_, e) => {
    if (e.tool === 'Write') saved = e.content
    return { result: {} }
  })
  await $.tool.call({ tool: 'Write', file_path: '/x/b.md', content: '협동학습 모형' })
  expect(saved).toBe('협동학습 모형')
})

test('Edit: 파일에 이미 특수체육으로 저장돼 있으면 old_string도 맞춘다', async ($, on) => {
  let oldS = ''
  on('fs.read', () => ({ value: '# 특수체육 수업 계획\n특수체육 교수모형: 협동학습\n' }))
  on('tool.call', (_, e) => {
    if (e.tool === 'Edit') oldS = e.old_string
    return { result: {} }
  })
  await $.tool.call({ tool: 'Edit', file_path: '/x/lesson.md', old_string: '적응 체육 교수모형: 협동학습', new_string: '적응 체육 교수모형: 협동학습\n적응체육 평가 기준' })
  expect(oldS).toBe('특수체육 교수모형: 협동학습')
})

test('바꾼 뒤에는 Claude에게 알리는 메모를 결과에 붙인다', async ($, on) => {
  on('tool.call', () => ({ result: {} }))
  const r = await $.tool.call({ tool: 'Write', file_path: '/x/c.md', content: '적응체육' })
  expect(JSON.stringify(r)).toContain('term-guard')
})
