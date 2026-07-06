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
  'python-backend': 'Python Backend'
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

function renderContentBlocks(lesson) {
  const fields = [
    { key: 'hook.scenario', label: 'Scenario' },
    { key: 'overview', label: 'Overview' },
    { key: 'why', label: 'Why' },
    { key: 'why_it_matters', label: 'Why it matters' },
    { key: 'mental_model', label: 'Mental model' },
    { key: 'explanation', label: 'Explanation' },
    { key: 'analogy', label: 'Analogy' },
    { key: 'method', label: 'Method' },
    { key: 'formula', label: 'Formula' },
    { key: 'key_points', label: 'Key points', isList: true },
    { key: 'shortcuts', label: 'Shortcuts', isList: true },
    { key: 'common_mistakes', label: 'Common mistakes', isList: true, isMistake: true },
    { key: 'mistakes', label: 'Mistakes', isList: true, isMistake: true },
    { key: 'recall_questions', label: 'Recall questions', isRecall: true },
    { key: 'recall', label: 'Recall questions', isRecall: true }
  ];

  function getField(obj, path) {
    return path.split('.').reduce((o, p) => (o ? o[p] : undefined), obj);
  }

  function extractText(val) {
    if (typeof val === 'string') return val;
    if (Array.isArray(val)) return val.map(extractText).filter(Boolean).join('n');
    if (typeof val === 'object' && val !== null) {
      if (val.text) return val.text;
      if (val.content) return val.content;
      if (val.body) return val.body;
      // Also might be a mistake object {mistake, why}
      if (val.mistake) return val.mistake + (val.why ? ' - ' + val.why : '');
      // Or a recall object {q, a}
      if (val.q) return val.q;
    }
    return '';
  }

  let html = '';
  for (const field of fields) {
    const val = getField(lesson, field.key);
    if (!val) continue;

    html += `<h2>${escapeHTML(field.label)}</h2>\n`;

    if (field.isList) {
      const arr = Array.isArray(val) ? val : [val];
      html += `<ul>\n`;
      for (const item of arr) {
        const text = extractText(item);
        if (text) {
          html += `<li>${escapeHTML(text)}</li>\n`;
        }
      }
      html += `</ul>\n`;
    } else if (field.isRecall) {
      const arr = Array.isArray(val) ? val : [val];
      html += `<ul>\n`;
      for (const item of arr) {
        const text = item.q || extractText(item);
        if (text) {
          html += `<li>${escapeHTML(text)}</li>\n`;
        }
      }
      html += `</ul>\n`;
    } else {
      const text = extractText(val);
      if (text) {
        // Split by paragraphs
        const paras = text.split('\n').map(p => p.trim()).filter(Boolean);
        for (const p of paras) {
          html += `<p>${escapeHTML(p)}</p>\n`;
        }
      }
    }
  }
  return html;
}

function getSeoDescription(lesson) {
  let raw = '';
  if (typeof lesson.overview === 'string' && lesson.overview) {
    raw = lesson.overview;
  } else if (lesson.hook?.scenario) {
    raw = extractText(lesson.hook.scenario);
  } else if (lesson.mental_model) {
    if (typeof lesson.mental_model === 'string') raw = lesson.mental_model;
    else if (lesson.mental_model.text) raw = lesson.mental_model.text;
  }

  let desc = collapseWhitespace(raw);
  if (!desc) {
    desc = `Learn ${lesson.title} and lock it into long-term memory with spaced repetition and active recall on RetainHQ.`;
  }
  return desc.slice(0, 158);
}

function extractText(val) {
  if (typeof val === 'string') return val;
  if (Array.isArray(val)) return val.map(extractText).filter(Boolean).join(' ');
  if (typeof val === 'object' && val !== null) {
    if (val.text) return val.text;
    if (val.content) return val.content;
    if (val.body) return val.body;
  }
  return '';
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
      const pageTitle = `${lesson.title} · ${label} | RetainHQ`;
      const pageDesc = getSeoDescription(lesson);
      const url = `${BASE_URL}/roadmaps/${roadmapKey}/learn/${slug}`;

      // 1. Replacements in <head>
      let html = templateHtml;
      
      // Replace <title>...</title>
      html = html.replace(/<title>.*?<\/title>/, `<title>${escapeHTML(pageTitle)}</title>`);
      
      // Replace <meta name="description" content="...">
      html = html.replace(/<meta[^>]*name="description"[^>]*>/i, `<meta name="description" content="${escapeHTML(pageDesc)}">`);
      
      // Replace <link rel="canonical" href="...">
      html = html.replace(/<link[^>]*rel="canonical"[^>]*>/i, `<link rel="canonical" href="${url}">`);
      
      // Replace <meta property="og:url" content="...">
      html = html.replace(/<meta[^>]*property="og:url"[^>]*>/i, `<meta property="og:url" content="${url}">`);
      
      // Optionally handle og:title and twitter:title if they exist in the template
      // Usually Vite injects these via JS, but if they are static, replace them:
      html = html.replace(/<meta[^>]*property="og:title"[^>]*>/i, `<meta property="og:title" content="${escapeHTML(pageTitle)}">`);
      html = html.replace(/<meta[^>]*name="twitter:title"[^>]*>/i, `<meta name="twitter:title" content="${escapeHTML(pageTitle)}">`);

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
      html = html.replace(/<\/head>/, `${ldScript}</head>`);

      // 3. Inject readable article content into <div id="root">
      // 4. Internal links inside the article
      
      let articleHtml = `<article style="max-width: 800px; margin: 0 auto; padding: 20px; font-family: system-ui, sans-serif; color: #1a1a1a; background: #fff;">\n`;
      articleHtml += `<h1>${escapeHTML(lesson.title)}</h1>\n`;
      
      // Breadcrumb links
      articleHtml += `<div style="margin-bottom: 20px; font-size: 0.9em;">`;
      articleHtml += `<a href="/roadmaps">Roadmaps</a> › <a href="/roadmaps/${roadmapKey}">${escapeHTML(label)}</a>`;
      articleHtml += `</div>\n`;
      
      articleHtml += renderContentBlocks(lesson);
      
      // Continue learning list
      const continueSlugs = new Set();
      if (lesson.metadata) {
        if (Array.isArray(lesson.metadata.prerequisites)) {
          lesson.metadata.prerequisites.forEach(s => continueSlugs.add(s));
        }
        if (Array.isArray(lesson.metadata.unlocks)) {
          lesson.metadata.unlocks.forEach(s => continueSlugs.add(s));
        }
      }
      
      const relatedLinks = [];
      for (const reqSlug of continueSlugs) {
        if (slugMap.has(reqSlug)) {
          relatedLinks.push({ slug: reqSlug, title: slugMap.get(reqSlug) });
        }
      }
      
      if (relatedLinks.length > 0) {
        articleHtml += `<h2>Continue learning</h2>\n<ul>\n`;
        for (const rel of relatedLinks) {
          articleHtml += `<li><a href="/roadmaps/${roadmapKey}/learn/${rel.slug}">${escapeHTML(rel.title)}</a></li>\n`;
        }
        articleHtml += `</ul>\n`;
      }
      
      // Link to roadmap again at the end
      articleHtml += `<p><a href="/roadmaps/${roadmapKey}">Return to ${escapeHTML(label)} Roadmap</a></p>\n`;
      articleHtml += `</article>`;

      html = html.replace(/<div id="root">[\s\S]*?(?:<\/noscript>)?\s*<\/div>/, `<div id="root">${articleHtml}</div>`);

      // Create output dir and write file
      const outDir = join(DIST_ROOT, 'roadmaps', roadmapKey, 'learn', slug);
      await mkdir(outDir, { recursive: true });
      await writeFile(join(outDir, 'index.html'), html);
      
      generatedCount++;
    }
  }

  console.log(`[generate-lesson-html] Wrote ${generatedCount} static lesson page(s).`);
}

main().catch((err) => {
  console.error('[generate-lesson-html] Fatal:', err);
  process.exit(1);
});
