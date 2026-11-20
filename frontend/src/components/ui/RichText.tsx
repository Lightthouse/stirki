import { useEffect, useState } from 'react'
import type { ReactNode } from 'react'
import { getSiteText } from '../../api'

/*
 * Текст из админки «Тексты сайта» с простой разметкой (без HTML — сотрудник не сломает вёрстку):
 *   «## Заголовок» — раздел, «- пункт» — список, **жирный**, остальные строки — абзацы.
 * Адреса сайтов и email становятся ссылками.
 */

type Block = { kind: 'p'; text: string } | { kind: 'ul'; items: string[] }
type Section = { title: string | null; blocks: Block[] }

function parse(body: string): Section[] {
  const sections: Section[] = [{ title: null, blocks: [] }]
  for (const raw of body.split('\n')) {
    const line = raw.trim()
    if (!line) continue
    const current = sections[sections.length - 1]
    if (line.startsWith('## ')) {
      sections.push({ title: line.slice(3).trim(), blocks: [] })
    } else if (line.startsWith('- ')) {
      const last = current.blocks[current.blocks.length - 1]
      if (last?.kind === 'ul') last.items.push(line.slice(2).trim())
      else current.blocks.push({ kind: 'ul', items: [line.slice(2).trim()] })
    } else {
      current.blocks.push({ kind: 'p', text: line })
    }
  }
  return sections.filter((s) => s.title !== null || s.blocks.length > 0)
}

const INLINE_RE = /(\*\*[^*]+\*\*|https?:\/\/[^\s,;)«»]+|[\w.+-]+@[\w-]+(?:\.[\w-]+)+)/g

function inline(text: string): ReactNode[] {
  const out: ReactNode[] = []
  text.split(INLINE_RE).forEach((part, i) => {
    if (!part) return
    if (part.startsWith('**') && part.endsWith('**') && part.length > 4) {
      out.push(<b key={i}>{part.slice(2, -2)}</b>)
      return
    }
    // Точка или запятая в конце адреса — конец предложения, а не часть ссылки.
    const m = part.match(/^(https?:\/\/\S+?|[\w.+-]+@[\w-]+(?:\.[\w-]+)+?)([.,:]*)$/)
    if (m && (m[1].startsWith('http') || m[1].includes('@'))) {
      const href = m[1].startsWith('http') ? m[1] : `mailto:${m[1]}`
      out.push(<a key={i} href={href} target={href.startsWith('http') ? '_blank' : undefined} rel="noreferrer">{m[1]}</a>)
      if (m[2]) out.push(m[2])
      return
    }
    out.push(part)
  })
  return out
}

export function RichText({ body }: { body: string }) {
  return (
    <>
      {parse(body).map((section, si) => (
        <section key={si}>
          {section.title && <h4>{inline(section.title)}</h4>}
          {section.blocks.map((b, bi) =>
            b.kind === 'p'
              ? <p key={bi}>{inline(b.text)}</p>
              : <ul key={bi}>{b.items.map((item, ii) => <li key={ii}>{inline(item)}</li>)}</ul>,
          )}
        </section>
      ))}
    </>
  )
}

/** Загружает текст окна из админки. null — ещё грузится; false — не удалось. */
export function useSiteText(slug: 'offer' | 'about' | 'privacy') {
  const [text, setText] = useState<{ title: string; body: string } | null | false>(null)
  useEffect(() => {
    getSiteText(slug).then(setText).catch(() => setText(false))
  }, [slug])
  return text
}

export function SiteTextBody({ text }: { text: { title: string; body: string } | null | false }) {
  if (text === null) return <p>Загрузка…</p>
  if (text === false) return <p>Не удалось загрузить текст. Проверьте интернет и откройте окно ещё раз.</p>
  return <RichText body={text.body} />
}
