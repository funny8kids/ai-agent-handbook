// Renders every authored *display* formula into the markup a reader's browser actually paints,
// with the same pinned KaTeX build the formula judge uses. Called only by
// check_content_overflow.py — that judge owns extraction, the version pin and the controls.
//
// throwOnError is false on purpose: a formula that throws is already owned by
// check_katex_formulas.py, and here it must come back as one defective row, not as a dead sweep.
import { createRequire } from 'module';
import { readFileSync, writeFileSync } from 'fs';

const from = process.env.KATEX_REQUIRE_FROM || `${process.cwd()}/`;
const require = createRequire(/[/\\]$/.test(from) ? from : `${from}/`);
let katex;
try {
  katex = require('katex');
} catch (err) {
  console.log(JSON.stringify({ skip: `katex not resolvable: ${err.message}` }));
  process.exit(2);
}

const items = JSON.parse(readFileSync(process.argv[2], 'utf8'));
const out = items.map((it) => {
  try {
    return { src: it.src, html: katex.renderToString(it.src, { throwOnError: false, displayMode: true }) };
  } catch (err) {
    return { src: it.src, error: String(err.message).slice(0, 160) };
  }
});
writeFileSync(process.argv[3], JSON.stringify({
  version: require('katex/package.json').version,
  count: out.length,
  items: out,
}));
console.log('ok');
