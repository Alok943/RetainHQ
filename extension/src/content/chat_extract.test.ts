// @vitest-environment jsdom
import { describe, it, expect, beforeEach } from 'vitest'
import { extractChatContent } from './chat_extract'

function setBody(html: string) {
  document.body.innerHTML = html
}

beforeEach(() => {
  document.body.innerHTML = ''
})

describe('extractChatContent — ChatGPT', () => {
  it('reads user turns in full and prefixes them U:', () => {
    setBody(`
      <div data-message-author-role="user">How do I speed up this query?</div>
      <div data-message-author-role="assistant">Add an index.</div>
    `)
    const content = extractChatContent('chatgpt.com')
    expect(content).toContain('U: How do I speed up this query?')
    expect(content).toContain('A: Add an index.')
  })

  it('truncates assistant turns to 300 chars but keeps user turns whole', () => {
    const longAnswer = 'x'.repeat(1000)
    const longQuestion = 'y'.repeat(1000)
    setBody(`
      <div data-message-author-role="user">${longQuestion}</div>
      <div data-message-author-role="assistant">${longAnswer}</div>
    `)
    const content = extractChatContent('chatgpt.com')
    expect(content).toContain(`U: ${longQuestion}`)
    expect(content).toContain(`A: ${'x'.repeat(300)}`)
    expect(content).not.toContain('x'.repeat(301))
  })

  it('strips code blocks before reading text', () => {
    setBody(`
      <div data-message-author-role="assistant">Here's the fix:<pre>const x = veryLongCodeBlock()</pre>done</div>
    `)
    const content = extractChatContent('chatgpt.com')
    expect(content).not.toContain('veryLongCodeBlock')
  })

  it('ignores nodes with an unrecognized role', () => {
    setBody(`<div data-message-author-role="system">hidden instructions</div>`)
    expect(extractChatContent('chatgpt.com')).toBe('')
  })

  it('returns empty string when nothing matches (no silent breakage)', () => {
    setBody(`<div class="totally-unrelated">hello</div>`)
    expect(extractChatContent('chatgpt.com')).toBe('')
  })

  it('keeps only the most recent MAX_TURNS turns', () => {
    const turns = Array.from({ length: 70 }, (_, i) =>
      `<div data-message-author-role="user">turn-${i}</div>`
    ).join('')
    setBody(turns)
    const content = extractChatContent('chatgpt.com')
    expect(content).not.toContain('turn-0"')
    expect(content).toContain('turn-69')
    expect(content.split('\n').length).toBe(60)
  })
})

describe('extractChatContent — ordering and caps (ChatGPT, the one verified adapter)', () => {
  it('preserves conversation order — NOT all user turns then all assistant turns', () => {
    // The regression: querying each role separately and concatenating yields
    // U,U,A,A. MAX_TOTAL_CHARS truncates from the oldest end, so that ordering
    // would strip the entire user side of a long conversation first.
    setBody(`
      <div data-message-author-role="user">first question</div>
      <div data-message-author-role="assistant">first answer</div>
      <div data-message-author-role="user">second question</div>
      <div data-message-author-role="assistant">second answer</div>
    `)
    expect(extractChatContent('chatgpt.com').split('\n')).toEqual([
      'U: first question',
      'A: first answer',
      'U: second question',
      'A: second answer',
    ])
  })

  it('counts a nested container once, not twice', () => {
    setBody(`
      <div data-message-author-role="user">q</div>
      <div data-message-author-role="assistant">outer <span data-message-author-role="assistant">inner</span></div>
    `)
    expect(extractChatContent('chatgpt.com').split('\n')).toEqual(['U: q', 'A: outer inner'])
  })

  it('keeping the most recent turns keeps BOTH sides of the recent conversation', () => {
    // With the old role-grouped ordering this kept only assistant turns.
    const html = Array.from({ length: 40 }, (_, i) =>
      `<div data-message-author-role="user">q${i}</div><div data-message-author-role="assistant">a${i}</div>`
    ).join('')
    setBody(html)
    const lines = extractChatContent('chatgpt.com').split('\n')
    expect(lines.length).toBe(60) // MAX_TURNS
    expect(lines.filter((l) => l.startsWith('U: ')).length).toBe(30)
    expect(lines.filter((l) => l.startsWith('A: ')).length).toBe(30)
    expect(lines.at(-1)).toBe('A: a39') // and it's the TAIL that survived
  })
})

describe('extractChatContent — Claude', () => {
  // Markup mirrors the live claude.ai ancestor chain captured 2026-07-27:
  // <div class="standard-markdown"> > <p class="font-claude-response-body">
  const reply = (paras: string[]) =>
    `<div class="standard-markdown grid-cols-1 grid">${paras
      .map((p) => `<p class="font-claude-response-body break-words">${p}</p>`)
      .join('')}</div>`

  it('reads the reply body, interleaved with user turns', () => {
    setBody(`
      <div data-testid="user-message">What is DP?</div>
      ${reply(['Dynamic Programming is...'])}
    `)
    expect(extractChatContent('claude.ai').split('\n')).toEqual([
      'U: What is DP?',
      'A: Dynamic Programming is...',
    ])
  })

  it('keeps a multi-paragraph reply as ONE turn, not one per paragraph', () => {
    // Why the selector is `.standard-markdown` and not
    // `.font-claude-response-body`: the latter is a single <p>, so this reply
    // would have become three separate turns and burned the MAX_TURNS budget.
    setBody(`
      <div data-testid="user-message">explain</div>
      ${reply(['First para.', 'Second para.', 'Third para.'])}
    `)
    const lines = extractChatContent('claude.ai').split('\n')
    expect(lines.length).toBe(2)
    expect(lines[1]).toBe('A: First para.Second para.Third para.')
  })

  it('does NOT match thinking-block summaries', () => {
    // The original bug: `.font-claude-response` is a different class token
    // from `.font-claude-response-body`, and matched only these.
    setBody(`
      <div data-testid="user-message">q</div>
      <div class="font-claude-response">Pinpointed off-by-one loop initialization error</div>
      <div class="font-claude-response">DSA_COACHING</div>
      ${reply(['the actual answer'])}
    `)
    expect(extractChatContent('claude.ai').split('\n')).toEqual(['U: q', 'A: the actual answer'])
  })

  it('never counts a user message as an assistant turn, even if it renders markdown', () => {
    setBody(`
      <div data-testid="user-message"><div class="standard-markdown">my question</div></div>
      ${reply(['my answer'])}
    `)
    expect(extractChatContent('claude.ai').split('\n')).toEqual(['U: my question', 'A: my answer'])
  })
})

describe('extractChatContent — Gemini', () => {
  it('reads both turns, interleaved', () => {
    setBody(`
      <user-query>Explain closures</user-query>
      <model-response>A closure is...</model-response>
    `)
    expect(extractChatContent('gemini.google.com').split('\n')).toEqual([
      'U: Explain closures',
      'A: A closure is...',
    ])
  })

  it('strips the cdk-visually-hidden "You said"/"Gemini said" a11y label', () => {
    // Confirmed live 2026-07-27: without this, every turn came back prefixed
    // "You said"/"Gemini said" — real DOM text, invisible on screen, read
    // like anything else by textContent.
    setBody(`
      <user-query><span class="cdk-visually-hidden">You said</span>hii, lets learn sql</user-query>
      <model-response><span class="cdk-visually-hidden">Gemini said</span>Hello! I'd love to help.</model-response>
    `)
    expect(extractChatContent('gemini.google.com').split('\n')).toEqual([
      'U: hii, lets learn sql',
      "A: Hello! I'd love to help.",
    ])
  })
})

describe('extractChatContent — sr-only labels stripped on every site', () => {
  // Only confirmed live on Gemini's cdk-visually-hidden, but the same
  // failure mode (an invisible label polluting textContent) is generic
  // enough to guard everywhere rather than only where it's been caught once.
  it('ChatGPT', () => {
    setBody(`<div data-message-author-role="assistant"><span class="sr-only">ChatGPT said:</span>the real answer</div>`)
    expect(extractChatContent('chatgpt.com')).toBe('A: the real answer')
  })

  it('Claude', () => {
    setBody(`
      <div class="standard-markdown"><p class="font-claude-response-body"><span class="visually-hidden">Claude said:</span>the real answer</p></div>
    `)
    expect(extractChatContent('claude.ai')).toBe('A: the real answer')
  })
})

describe('extractChatContent — unknown host', () => {
  it('returns empty string rather than guessing', () => {
    setBody(`<div data-message-author-role="user">hi</div>`)
    expect(extractChatContent('example.com')).toBe('')
  })
})
