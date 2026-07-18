import { readdir, readFile, mkdir, writeFile } from 'node:fs/promises';
import { join, dirname } from 'node:path';
import { fileURLToPath } from 'node:url';

const __dirname = dirname(fileURLToPath(import.meta.url));
const CONTENT_ROOT = join(__dirname, '..', '..', 'content', 'roadmaps');
const DIST_ROOT = join(__dirname, '..', 'dist');
const TEMPLATE_PATH = join(DIST_ROOT, 'index.html');
const BASE_URL = 'https://retainhq.app';

// MUST sync with frontend/src/LessonView.jsx
const ROADMAP_LABEL = {
  'python-swe': 'Python',
  'sql': 'SQL',
  'aptitude': 'Aptitude',
  'core-cs': 'Core CS',
  'dsa': 'DSA',
  'ai-engineering': 'AI Engineering',
  'cpp-swe': 'C++',
  'python-backend': 'Python Backend',
  'physics-9': 'Physics (Class 9)',
  'physics-10': 'Physics (Class 10)'
};

function escapeHTML(str) {
  if (typeof str !== 'string') return '';
  return str
    .replace(/&/g, '&amp;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;')
    .replace(/"/g, '&quot;')
    .replace(/'/g, '&#039;');
}

function collapseWhitespace(str) {
  return (str || '').replace(/\s+/g, ' ').trim();
}

// --- Consolidated extractText (was duplicated: one inside renderContentBlocks, one module-level) ---
function extractText(val) {
  if (typeof val === 'string') return val;
  if (Array.isArray(val)) return val.map(extractText).filter(Boolean).join('\n');
  if (typeof val === 'object' && val !== null) {
    if (val.text) return val.text;
    if (val.content) return val.content;
    if (val.body) return val.body;
    if (val.intuition) return val.intuition;
    // mistake object {mistake, why} or {title, explanation}
    if (val.mistake) return val.mistake + (val.why ? ' — ' + val.why : '');
    if (val.title && val.explanation) return val.title + ': ' + val.explanation;
    // recall / OA object {q, a} / {question, answer}
    if (val.q) return val.q;
    if (val.question) return val.question;
    // overview object {what, why}
    if (val.what) return val.what + (val.why ? ' ' + val.why : '');
  }
  return '';
}

// --- Helper to render a string or array as <p> paragraphs ---
function renderParagraphs(val) {
  const text = typeof val === 'string' ? val : extractText(val);
  if (!text) return '';
  return text.split('\n').map(p => p.trim()).filter(Boolean)
    .map(p => `<p>${escapeHTML(p)}</p>\n`).join('');
}

// --- P0-A: Full content rendering for all lesson kinds ---
function renderContentBlocks(lesson) {
  let html = '';

  // Helper to add a section with a heading
  function section(label, content) {
    if (!content) return;
    html += `<h2>${escapeHTML(label)}</h2>\n${content}`;
  }

  // 1. Hook (scenario + question)
  const hook = lesson.hook;
  if (hook && typeof hook === 'object') {
    const scenario = hook.scenario;
    const question = hook.question;
    if (scenario) {
      html += `<h2>Scenario</h2>\n`;
      html += renderParagraphs(scenario);
      if (question) html += `<p><strong>${escapeHTML(question)}</strong></p>\n`;
    }
  }

  // 2. Overview / why_it_exists / why_learning_this
  const overview = lesson.overview;
  if (overview) {
    html += `<h2>Overview</h2>\n`;
    if (typeof overview === 'string') {
      html += renderParagraphs(overview);
    } else if (typeof overview === 'object') {
      if (overview.what) html += `<p>${escapeHTML(overview.what)}</p>\n`;
      if (overview.why) html += `<p>${escapeHTML(overview.why)}</p>\n`;
      if (Array.isArray(overview.where_used) && overview.where_used.length) {
        html += `<p><strong>Where used:</strong> ${overview.where_used.map(w => escapeHTML(w)).join(', ')}</p>\n`;
      }
    }
  }

  const whyItExists = lesson.why_it_exists;
  if (whyItExists) {
    html += `<h2>Why it exists</h2>\n`;
    if (typeof whyItExists === 'string') {
      html += renderParagraphs(whyItExists);
    } else if (typeof whyItExists === 'object') {
      if (whyItExists.problem) html += `<p><strong>Problem:</strong> ${escapeHTML(whyItExists.problem)}</p>\n`;
      if (whyItExists.naive_solution) html += `<p><strong>Naive approach:</strong> ${escapeHTML(whyItExists.naive_solution)}</p>\n`;
      if (whyItExists.better_idea) html += `<p><strong>Better idea:</strong> ${escapeHTML(whyItExists.better_idea)}</p>\n`;
    }
  }

  const whyLearning = lesson.why_learning_this;
  if (Array.isArray(whyLearning) && whyLearning.length) {
    html += `<h2>Why learn this</h2>\n<ul>\n`;
    for (const item of whyLearning) {
      if (typeof item === 'string' && item.trim()) html += `<li>${escapeHTML(item)}</li>\n`;
    }
    html += `</ul>\n`;
  }

  // 3. Mental model (intuition + description)
  const mm = lesson.mental_model;
  if (mm) {
    html += `<h2>Mental model</h2>\n`;
    if (typeof mm === 'string') {
      html += renderParagraphs(mm);
    } else if (typeof mm === 'object') {
      if (mm.intuition) html += `<p><strong>${escapeHTML(mm.intuition)}</strong></p>\n`;
      if (mm.description) html += renderParagraphs(mm.description);
      if (mm.repeated_decision) html += `<p><em>Repeated decision: ${escapeHTML(mm.repeated_decision)}</em></p>\n`;
    }
  }

  // 4. Explanation
  if (lesson.explanation) {
    html += `<h2>Explanation</h2>\n`;
    html += renderParagraphs(lesson.explanation);
  }

  // Analogy
  if (lesson.analogy) {
    html += `<h2>Analogy</h2>\n`;
    html += renderParagraphs(lesson.analogy);
  }

  // 5. Sections (body + recap) — one <h2> for the block, paragraphs inside
  const sections = lesson.sections;
  if (Array.isArray(sections) && sections.length) {
    html += `<h2>Deep dive</h2>\n`;
    for (const sec of sections) {
      if (!sec || typeof sec !== 'object') continue;
      if (sec.body) {
        const paras = sec.body.split('\n').map(p => p.trim()).filter(Boolean);
        for (const p of paras) html += `<p>${escapeHTML(p)}</p>\n`;
      }
      if (sec.recap) html += `<p><em>${escapeHTML(sec.recap)}</em></p>\n`;
    }
  }

  // 6. Method / formula / pattern_discovery / derivation
  const method = lesson.method;
  if (Array.isArray(method) && method.length) {
    html += `<h2>Method</h2>\n<ol>\n`;
    for (const step of method) {
      if (typeof step === 'string' && step.trim()) html += `<li>${escapeHTML(step)}</li>\n`;
    }
    html += `</ol>\n`;
  }

  const formula = lesson.formula;
  if (formula) {
    html += `<h2>Formula</h2>\n`;
    if (typeof formula === 'string') {
      html += renderParagraphs(formula);
    } else if (typeof formula === 'object') {
      if (formula.statement) html += `<p><strong>${escapeHTML(formula.statement)}</strong></p>\n`;
      if (formula.explain) html += renderParagraphs(formula.explain);
    }
  }

  const patternDiscovery = lesson.pattern_discovery;
  if (patternDiscovery && typeof patternDiscovery === 'object') {
    html += `<h2>Pattern discovery</h2>\n`;
    if (patternDiscovery.setup) html += `<p>${escapeHTML(patternDiscovery.setup)}</p>\n`;
    if (Array.isArray(patternDiscovery.cases) && patternDiscovery.cases.length) {
      html += `<ul>\n`;
      for (const c of patternDiscovery.cases) {
        if (typeof c === 'string') html += `<li>${escapeHTML(c)}</li>\n`;
      }
      html += `</ul>\n`;
    }
    if (patternDiscovery.prompt) html += `<p><em>${escapeHTML(patternDiscovery.prompt)}</em></p>\n`;
    if (patternDiscovery.rule) html += `<p><strong>Rule:</strong> ${escapeHTML(patternDiscovery.rule)}</p>\n`;
  }

  const derivation = lesson.derivation;
  if (Array.isArray(derivation) && derivation.length) {
    html += `<h2>Derivation</h2>\n`;
    for (const der of derivation) {
      if (!der || typeof der !== 'object') continue;
      if (der.goal) html += `<h3>${escapeHTML(der.goal)}</h3>\n`;
      if (Array.isArray(der.steps)) {
        html += `<ol>\n`;
        for (const st of der.steps) {
          if (typeof st === 'string') {
            html += `<li>${escapeHTML(st)}</li>\n`;
          } else if (typeof st === 'object' && st) {
            const parts = [st.expr, st.rule, st.why].filter(Boolean).map(s => escapeHTML(s));
            html += `<li>${parts.join(' — ')}</li>\n`;
          }
        }
        html += `</ol>\n`;
      }
    }
  }

  // 7. Code snippets
  const codeSnippets = lesson.code_snippets;
  if (Array.isArray(codeSnippets) && codeSnippets.length) {
    html += `<h2>Code examples</h2>\n`;
    for (const cs of codeSnippets) {
      if (!cs || typeof cs !== 'object') continue;
      if (cs.title) html += `<h3>${escapeHTML(cs.title)}</h3>\n`;
      if (cs.code) {
        const lang = cs.language || '';
        html += `<pre><code class="language-${escapeHTML(lang)}">${escapeHTML(cs.code)}</code></pre>\n`;
      }
      if (cs.explanation) html += `<p>${escapeHTML(cs.explanation)}</p>\n`;
    }
  }

  // 8. Code walkthrough / aha moment
  const cw = lesson.code_walkthrough;
  if (cw && typeof cw === 'object' && cw.code) {
    html += `<h2>Code walkthrough</h2>\n`;
    html += `<pre><code>${escapeHTML(cw.code)}</code></pre>\n`;
    if (cw.focus) html += `<p><em>Focus: ${escapeHTML(cw.focus)}</em></p>\n`;
  }

  // Query walkthrough (SQL lessons)
  const qw = lesson.query_walkthrough;
  if (qw && typeof qw === 'object' && qw.query) {
    html += `<h2>Query walkthrough</h2>\n`;
    html += `<pre><code class="language-sql">${escapeHTML(qw.query)}</code></pre>\n`;
    if (qw.focus) html += `<p><em>Focus: ${escapeHTML(qw.focus)}</em></p>\n`;
  }

  const aha = lesson.aha_moment;
  if (aha && typeof aha === 'object') {
    html += `<h2>Aha moment</h2>\n`;
    if (aha.code) html += `<pre><code>${escapeHTML(aha.code)}</code></pre>\n`;
    if (aha.prediction) html += `<p><strong>Prediction:</strong> ${escapeHTML(aha.prediction)}</p>\n`;
    if (aha.common_guess) html += `<p><strong>Common guess:</strong> ${escapeHTML(aha.common_guess)}</p>\n`;
    if (aha.why) html += `<p>${escapeHTML(aha.why)}</p>\n`;
  }

  // 9. Worked example
  const we = lesson.worked_example;
  if (we) {
    html += `<h2>Worked example</h2>\n`;
    const examples = Array.isArray(we) ? we : [we];
    for (const ex of examples) {
      if (!ex || typeof ex !== 'object') continue;
      if (ex.problem) html += `<p><strong>Problem:</strong> ${escapeHTML(ex.problem)}</p>\n`;
      if (Array.isArray(ex.steps) && ex.steps.length) {
        html += `<ol>\n`;
        for (const step of ex.steps) {
          if (typeof step === 'string') {
            html += `<li>${escapeHTML(step)}</li>\n`;
          } else if (typeof step === 'object' && step) {
            // Physics worked_example steps have {narration, math?}
            const text = step.narration || step.text || extractText(step);
            if (text) html += `<li>${escapeHTML(text)}</li>\n`;
          }
        }
        html += `</ol>\n`;
      }
      if (ex.answer) html += `<p><strong>Answer:</strong> ${escapeHTML(ex.answer)}</p>\n`;
    }
  }

  // 10. Key points
  const kp = lesson.key_points;
  if (Array.isArray(kp) && kp.length) {
    html += `<h2>Key points</h2>\n<ul>\n`;
    for (const item of kp) {
      if (typeof item === 'string') {
        html += `<li>${escapeHTML(item)}</li>\n`;
      } else if (typeof item === 'object' && item) {
        const title = item.title || '';
        const detail = item.detail || '';
        html += `<li><strong>${escapeHTML(title)}</strong>${detail ? ': ' + escapeHTML(detail) : ''}</li>\n`;
      }
    }
    html += `</ul>\n`;
  }

  // 11. DSA-specific: pattern, failure_signals, engineering_examples, when_not_to_use
  const pattern = lesson.pattern;
  if (pattern && typeof pattern === 'object' && pattern.name) {
    html += `<h2>Pattern: ${escapeHTML(pattern.name)}</h2>\n`;
    if (Array.isArray(pattern.recognition_cues) && pattern.recognition_cues.length) {
      html += `<p><strong>Recognition cues:</strong></p>\n<ul>\n`;
      for (const cue of pattern.recognition_cues) {
        if (typeof cue === 'string') html += `<li>${escapeHTML(cue)}</li>\n`;
      }
      html += `</ul>\n`;
    }
  }

  const failureSignals = lesson.failure_signals;
  if (Array.isArray(failureSignals) && failureSignals.length) {
    html += `<h2>Failure signals</h2>\n<ul>\n`;
    for (const fs of failureSignals) {
      if (typeof fs === 'string') html += `<li>${escapeHTML(fs)}</li>\n`;
    }
    html += `</ul>\n`;
  }

  const engExamples = lesson.engineering_examples;
  if (Array.isArray(engExamples) && engExamples.length) {
    html += `<h2>Engineering examples</h2>\n`;
    for (const ex of engExamples) {
      if (!ex || typeof ex !== 'object') continue;
      if (ex.title) html += `<h3>${escapeHTML(ex.title)}</h3>\n`;
      if (ex.problem) html += `<p>${escapeHTML(ex.problem)}</p>\n`;
      if (ex.why_this_algorithm) html += `<p><em>${escapeHTML(ex.why_this_algorithm)}</em></p>\n`;
    }
  }

  const whenNot = lesson.when_not_to_use;
  if (Array.isArray(whenNot) && whenNot.length) {
    html += `<h2>When not to use</h2>\n<ul>\n`;
    for (const wn of whenNot) {
      if (typeof wn === 'object' && wn) {
        html += `<li><strong>${escapeHTML(wn.scenario || '')}</strong>: ${escapeHTML(wn.reason || '')}</li>\n`;
      }
    }
    html += `</ul>\n`;
  }

  // 12. Shortcuts
  const shortcuts = lesson.shortcuts;
  if (Array.isArray(shortcuts) && shortcuts.length) {
    html += `<h2>Shortcuts</h2>\n<ul>\n`;
    for (const sc of shortcuts) {
      if (typeof sc === 'string') {
        html += `<li>${escapeHTML(sc)}</li>\n`;
      } else if (typeof sc === 'object' && sc) {
        html += `<li><strong>${escapeHTML(sc.title || '')}</strong>: ${escapeHTML(sc.trick || '')}`;
        if (sc.example) html += ` <em>(${escapeHTML(sc.example)})</em>`;
        html += `</li>\n`;
      }
    }
    html += `</ul>\n`;
  }

  // 13. Common mistakes
  const cm = lesson.common_mistakes || lesson.mistakes;
  if (Array.isArray(cm) && cm.length) {
    html += `<h2>Common mistakes</h2>\n<ul>\n`;
    for (const item of cm) {
      if (typeof item === 'string') {
        html += `<li>${escapeHTML(item)}</li>\n`;
      } else if (typeof item === 'object' && item) {
        if (item.title && item.explanation) {
          html += `<li><strong>${escapeHTML(item.title)}</strong>: ${escapeHTML(item.explanation)}</li>\n`;
        } else {
          const text = item.mistake || item.title || extractText(item);
          const why = item.why || item.explanation || '';
          html += `<li>${escapeHTML(text)}${why ? ' — ' + escapeHTML(why) : ''}</li>\n`;
        }
      }
    }
    html += `</ul>\n`;
  }

  // 14. Glossary
  const glossary = lesson.glossary;
  if (Array.isArray(glossary) && glossary.length) {
    html += `<h2>Glossary</h2>\n<dl>\n`;
    for (const entry of glossary) {
      if (!entry || typeof entry !== 'object') continue;
      if (entry.term) html += `<dt>${escapeHTML(entry.term)}</dt>\n`;
      if (entry.definition) html += `<dd>${escapeHTML(entry.definition)}</dd>\n`;
    }
    html += `</dl>\n`;
  }

  // 15. Recall questions (questions only)
  const rq = lesson.recall_questions || lesson.recall;
  if (Array.isArray(rq) && rq.length) {
    html += `<h2>Recall questions</h2>\n<ul>\n`;
    for (const item of rq) {
      const text = (typeof item === 'object' && item) ? (item.q || item.question || '') : (typeof item === 'string' ? item : '');
      if (text) html += `<li>${escapeHTML(text)}</li>\n`;
    }
    html += `</ul>\n`;
  }

  // 16. Understanding checks + OA questions — visible Q&A (include answers)
  const uc = lesson.understanding_checks;
  if (Array.isArray(uc) && uc.length) {
    html += `<h2>Understanding checks</h2>\n`;
    for (const check of uc) {
      if (!check || typeof check !== 'object') continue;
      if (check.question) html += `<h3>${escapeHTML(check.question)}</h3>\n`;
      if (check.answer) html += `<p>${escapeHTML(check.answer)}</p>\n`;
      if (check.why) html += `<p><em>${escapeHTML(check.why)}</em></p>\n`;
    }
  }

  const oa = lesson.oa_questions;
  if (Array.isArray(oa) && oa.length) {
    html += `<h2>Questions &amp; answers</h2>\n`;
    for (const q of oa) {
      if (!q || typeof q !== 'object') continue;
      const question = q.question || q.q || '';
      if (question) html += `<h3>${escapeHTML(question)}</h3>\n`;
      if (q.answer) html += `<p>${escapeHTML(q.answer)}</p>\n`;
      if (q.approach) html += `<p><em>Approach: ${escapeHTML(q.approach)}</em></p>\n`;
    }
  }

  // 17. Practice tasks + challenge (title + prompt only; omit solution/starter_code)
  const pt = lesson.practice_tasks;
  if (Array.isArray(pt) && pt.length) {
    html += `<h2>Practice tasks</h2>\n`;
    for (const task of pt) {
      if (!task || typeof task !== 'object') continue;
      if (task.title) html += `<h3>${escapeHTML(task.title)}</h3>\n`;
      if (task.prompt) html += `<p>${escapeHTML(task.prompt)}</p>\n`;
    }
  }

  const challenge = lesson.challenge;
  if (challenge && typeof challenge === 'object') {
    html += `<h2>Challenge</h2>\n`;
    if (challenge.title) html += `<h3>${escapeHTML(challenge.title)}</h3>\n`;
    if (challenge.prompt) html += `<p>${escapeHTML(challenge.prompt)}</p>\n`;
  }

  // 18. Interesting facts (DSA)
  const facts = lesson.interesting_facts;
  if (Array.isArray(facts) && facts.length) {
    html += `<h2>Interesting facts</h2>\n<ul>\n`;
    for (const f of facts) {
      if (typeof f === 'string') html += `<li>${escapeHTML(f)}</li>\n`;
    }
    html += `</ul>\n`;
  }

  return html;
}

function getSeoDescription(lesson) {
  let raw = '';
  if (typeof lesson.overview === 'string' && lesson.overview) {
    raw = lesson.overview;
  } else if (lesson.overview && typeof lesson.overview === 'object' && lesson.overview.what) {
    raw = lesson.overview.what;
  } else if (lesson.hook?.scenario) {
    raw = extractText(lesson.hook.scenario);
  } else if (lesson.mental_model) {
    if (typeof lesson.mental_model === 'string') raw = lesson.mental_model;
    else if (lesson.mental_model.intuition) raw = lesson.mental_model.intuition;
    else if (lesson.mental_model.text) raw = lesson.mental_model.text;
  }

  let desc = collapseWhitespace(raw);
  if (!desc) {
    desc = `Learn ${lesson.title} and lock it into long-term memory with spaced repetition and active recall on RetainHQ.`;
  }
  return desc.slice(0, 158);
}

async function main() {
  let roadmapDirs;
  try {
    roadmapDirs = await readdir(CONTENT_ROOT, { withFileTypes: true });
  } catch (err) {
    console.log('[generate-lesson-html] No content/roadmaps directory found — skipping.');
    return;
  }

  let templateHtml = '';
  try {
    templateHtml = await readFile(TEMPLATE_PATH, 'utf-8');
  } catch (err) {
    console.warn(`[generate-lesson-html] Could not read ${TEMPLATE_PATH}. Ensure this runs after vite build.`);
    return;
  }

  let generatedCount = 0;
  // roadmapKey -> [{slug, title}] — collected for the static hub pages below.
  const hubIndex = new Map();

  for (const entry of roadmapDirs) {
    if (!entry.isDirectory()) continue;
    const roadmapKey = entry.name;
    const srcDir = join(CONTENT_ROOT, roadmapKey);

    const files = await readdir(srcDir);
    const lessonFiles = files.filter(f => f.endsWith('.json'));

    // First pass: Build slug -> title index for this roadmap
    const slugMap = new Map();
    const lessons = [];
    for (const file of lessonFiles) {
      const srcPath = join(srcDir, file);
      try {
        const raw = await readFile(srcPath, 'utf-8');
        const lesson = JSON.parse(raw);
        if (!lesson.title) continue;
        const slug = lesson.slug || file.replace('.json', '');
        slugMap.set(slug, lesson.title);
        lessons.push({ slug, lesson });
      } catch (err) {
        console.warn(`[generate-lesson-html] Skipping malformed file ${file}: ${err.message}`);
      }
    }

    // Second pass: Generate HTML
    for (const { slug, lesson } of lessons) {
      const label = ROADMAP_LABEL[roadmapKey] || 'RetainHQ';
      // P0-B: prefer seo.title / seo.description if present
      const pageTitle = lesson.seo?.title ?? `${lesson.title} · ${label} | RetainHQ`;
      const pageDesc = lesson.seo?.description ?? getSeoDescription(lesson);
      const url = `${BASE_URL}/roadmaps/${roadmapKey}/learn/${slug}`;

      // 1. Replacements in <head>. NOTE: every replacement uses the function form —
      // lesson prose can contain `$&`/`$'`, which are special in string replacements.
      let html = templateHtml;

      // Replace <title>...</title>
      html = html.replace(/<title>.*?<\/title>/, () => `<title>${escapeHTML(pageTitle)}</title>`);

      // Replace <meta name="description" content="...">
      html = html.replace(/<meta[^>]*name="description"[^>]*>/i, () => `<meta name="description" content="${escapeHTML(pageDesc)}">`);

      // Replace <link rel="canonical" href="...">
      html = html.replace(/<link[^>]*rel="canonical"[^>]*>/i, () => `<link rel="canonical" href="${url}">`);

      // Replace <meta property="og:url" content="...">
      html = html.replace(/<meta[^>]*property="og:url"[^>]*>/i, () => `<meta property="og:url" content="${url}">`);

      // Optionally handle og:title and twitter:title if they exist in the template
      // Usually Vite injects these via JS, but if they are static, replace them:
      html = html.replace(/<meta[^>]*property="og:title"[^>]*>/i, () => `<meta property="og:title" content="${escapeHTML(pageTitle)}">`);
      html = html.replace(/<meta[^>]*name="twitter:title"[^>]*>/i, () => `<meta name="twitter:title" content="${escapeHTML(pageTitle)}">`);

      // 2. Append JSON-LD before </head>
      const ldJson = [
        {
          "@context": "https://schema.org",
          "@type": "LearningResource",
          "name": lesson.title,
          "description": pageDesc,
          "url": url,
          "inLanguage": "en",
          "learningResourceType": "lesson",
          "isPartOf": { "@type": "Course", "name": `${label} — RetainHQ` },
          "publisher": { "@type": "Organization", "name": "RetainHQ", "url": "https://retainhq.app" }
        },
        {
          "@context": "https://schema.org",
          "@type": "BreadcrumbList",
          "itemListElement": [
            { "@type": "ListItem", "position": 1, "name": "Roadmaps", "item": `${BASE_URL}/roadmaps` },
            { "@type": "ListItem", "position": 2, "name": label, "item": `${BASE_URL}/roadmaps/${roadmapKey}` },
            { "@type": "ListItem", "position": 3, "name": lesson.title }
          ]
        }
      ];
      
      const ldScript = `<script type="application/ld+json">${JSON.stringify(ldJson)}</script>`;
      html = html.replace(/<\/head>/, () => `${ldScript}</head>`);

      // 3. Inject readable article content into <div id="root">
      // 4. Internal links inside the article
      
      let articleHtml = `<article style="max-width: 800px; margin: 0 auto; padding: 20px; font-family: system-ui, sans-serif; color: #1a1a1a; background: #fff;">\n`;
      articleHtml += `<h1>${escapeHTML(lesson.title)}</h1>\n`;
      
      // Breadcrumb links
      articleHtml += `<div style="margin-bottom: 20px; font-size: 0.9em;">`;
      articleHtml += `<a href="/roadmaps">Roadmaps</a> › <a href="/roadmaps/${roadmapKey}">${escapeHTML(label)}</a>`;
      articleHtml += `</div>\n`;
      
      articleHtml += renderContentBlocks(lesson);
      
      // 19. Previous, Next, and Related Links
      let navHtml = '';
      const prevSlugs = lesson.metadata?.prerequisites || [];
      for (const s of prevSlugs) {
        if (slugMap.has(s)) {
          navHtml += `<p><strong>Previous:</strong> <a href="/roadmaps/${roadmapKey}/learn/${s}">${escapeHTML(slugMap.get(s))}</a></p>\n`;
        }
      }
      const nextSlugs = lesson.metadata?.unlocks || [];
      for (const s of nextSlugs) {
        if (slugMap.has(s)) {
          navHtml += `<p><strong>Next:</strong> <a href="/roadmaps/${roadmapKey}/learn/${s}">${escapeHTML(slugMap.get(s))}</a></p>\n`;
        }
      }

      const relatedSlugs = lesson.related || [];
      for (const s of relatedSlugs) {
        if (slugMap.has(s)) {
          navHtml += `<p><strong>Related:</strong> <a href="/roadmaps/${roadmapKey}/learn/${s}">${escapeHTML(slugMap.get(s))}</a></p>\n`;
        }
      }

      // Hardcoded cross-roadmap links
      if (slug === 'the-gil') {
        navHtml += `<p><strong>Related:</strong> <a href="/roadmaps/python-backend/learn/threading-vs-multiprocessing">Threading vs Multiprocessing</a></p>\n`;
      } else if (slug === 'threading-vs-multiprocessing') {
        navHtml += `<p><strong>Related:</strong> <a href="/roadmaps/python-backend/learn/the-gil">The GIL (Global Interpreter Lock)</a></p>\n`;
      }

      if (navHtml) {
        articleHtml += `<h2>Continue learning</h2>\n${navHtml}`;
      }
      
      // Link to roadmap again at the end
      articleHtml += `<p><a href="/roadmaps/${roadmapKey}">Return to ${escapeHTML(label)} Roadmap</a></p>\n`;
      articleHtml += `</article>`;

      html = html.replace(/<div id="root">[\s\S]*?(?:<\/noscript>)?\s*<\/div>/, () => `<div id="root">${articleHtml}</div>`);

      // Create output dir and write file
      const outDir = join(DIST_ROOT, 'roadmaps', roadmapKey, 'learn', slug);
      await mkdir(outDir, { recursive: true });
      await writeFile(join(outDir, 'index.html'), html);

      generatedCount++;
    }

    if (lessons.length) {
      hubIndex.set(roadmapKey, lessons.map(({ slug, lesson }) => ({ slug, title: lesson.title })));
    }
  }

  // --- Static hub pages -----------------------------------------------------
  // Lesson pages link UP to /roadmaps/<key>, but to crawlers those routes are
  // empty SPA shells — nothing links DOWN to the lessons. These hubs complete
  // the crawl graph: /roadmaps -> each roadmap hub -> every lesson.
  // (The React app mounts on top and replaces the article, same as lessons.)

  function hubPage({ path, pageTitle, pageDesc, articleHtml, ldJson }) {
    let html = templateHtml;
    const url = `${BASE_URL}${path}`;
    html = html.replace(/<title>.*?<\/title>/, () => `<title>${escapeHTML(pageTitle)}</title>`);
    html = html.replace(/<meta[^>]*name="description"[^>]*>/i, () => `<meta name="description" content="${escapeHTML(pageDesc)}">`);
    html = html.replace(/<link[^>]*rel="canonical"[^>]*>/i, () => `<link rel="canonical" href="${url}">`);
    html = html.replace(/<meta[^>]*property="og:url"[^>]*>/i, () => `<meta property="og:url" content="${url}">`);
    html = html.replace(/<meta[^>]*property="og:title"[^>]*>/i, () => `<meta property="og:title" content="${escapeHTML(pageTitle)}">`);
    html = html.replace(/<meta[^>]*name="twitter:title"[^>]*>/i, () => `<meta name="twitter:title" content="${escapeHTML(pageTitle)}">`);
    if (ldJson) {
      const ldScript = `<script type="application/ld+json">${JSON.stringify(ldJson)}</script>`;
      html = html.replace(/<\/head>/, () => `${ldScript}</head>`);
    }
    html = html.replace(/<div id="root">[\s\S]*?(?:<\/noscript>)?\s*<\/div>/, () => `<div id="root">${articleHtml}</div>`);
    return html;
  }

  const ARTICLE_STYLE = 'max-width: 800px; margin: 0 auto; padding: 20px; font-family: system-ui, sans-serif; color: #1a1a1a; background: #fff;';

  // Per-roadmap hubs: /roadmaps/<key>
  for (const [roadmapKey, lessonList] of hubIndex) {
    const label = ROADMAP_LABEL[roadmapKey] || 'RetainHQ';
    const pageTitle = `${label} Roadmap · Spaced Repetition | RetainHQ`;
    const pageDesc = `Learn ${label} step by step — ${lessonList.length} free lessons with spaced repetition and active recall on RetainHQ, so what you study actually sticks.`.slice(0, 158);

    let articleHtml = `<article style="${ARTICLE_STYLE}">\n`;
    articleHtml += `<div style="margin-bottom: 20px; font-size: 0.9em;"><a href="/roadmaps">Roadmaps</a> › ${escapeHTML(label)}</div>\n`;
    articleHtml += `<h1>${escapeHTML(label)} Roadmap</h1>\n`;
    articleHtml += `<p>${escapeHTML(pageDesc)}</p>\n<h2>Lessons</h2>\n<ul>\n`;
    for (const { slug, title } of lessonList) {
      articleHtml += `<li><a href="/roadmaps/${roadmapKey}/learn/${slug}">${escapeHTML(title)}</a></li>\n`;
    }
    articleHtml += `</ul>\n</article>`;

    const ldJson = {
      '@context': 'https://schema.org',
      '@type': 'Course',
      name: `${label} — RetainHQ`,
      description: pageDesc,
      url: `${BASE_URL}/roadmaps/${roadmapKey}`,
      inLanguage: 'en',
      provider: { '@type': 'Organization', name: 'RetainHQ', url: BASE_URL },
    };

    const outDir = join(DIST_ROOT, 'roadmaps', roadmapKey);
    await mkdir(outDir, { recursive: true });
    await writeFile(join(outDir, 'index.html'), hubPage({ path: `/roadmaps/${roadmapKey}`, pageTitle, pageDesc, articleHtml, ldJson }));
  }

  // Top hub: /roadmaps — must byte-match the client-side useSeo title in Roadmaps.jsx.
  {
    const pageTitle = 'Learning Roadmaps · DSA, System Design, Python & SQL | RetainHQ';
    const pageDesc = 'Structured learning roadmaps for DSA, system design, Python, SQL, Core CS, and aptitude — each topic tracked by spaced repetition so what you study actually sticks.';
    let articleHtml = `<article style="${ARTICLE_STYLE}">\n<h1>Learning Roadmaps</h1>\n<p>${escapeHTML(pageDesc)}</p>\n<ul>\n`;
    for (const [roadmapKey, lessonList] of hubIndex) {
      const label = ROADMAP_LABEL[roadmapKey] || roadmapKey;
      articleHtml += `<li><a href="/roadmaps/${roadmapKey}">${escapeHTML(label)}</a> — ${lessonList.length} lessons</li>\n`;
    }
    articleHtml += `</ul>\n</article>`;
    await mkdir(join(DIST_ROOT, 'roadmaps'), { recursive: true });
    await writeFile(join(DIST_ROOT, 'roadmaps', 'index.html'), hubPage({ path: '/roadmaps', pageTitle, pageDesc, articleHtml, ldJson: null }));
  }

  console.log(`[generate-lesson-html] Wrote ${generatedCount} static lesson page(s) + ${hubIndex.size + 1} hub page(s).`);
}

main().catch((err) => {
  console.error('[generate-lesson-html] Fatal:', err);
  process.exit(1);
});
