// SPDX-FileCopyrightText: 2026 maninblack
// SPDX-License-Identifier: MIT
// Rebuild only the current standalone preview; preserve its wrapper and licenses.
const fs = require('node:fs');
const path = require('node:path');
const base = path.join(__dirname, '../docs/demo/mockups/aosedge-demo-interaction-mockup-2-10');
const source = fs.readFileSync(base + '.source.html', 'utf8');
const old = fs.readFileSync(base + '.html', 'utf8');
const marker = '<!-- SPDX-FileCopyrightText: 2026 maninblack -->';
const start = old.indexOf(marker), end = old.lastIndexOf('</body>');
if (start < 0 || end < start || !source.startsWith(marker)) throw Error('Unexpected standalone boundaries');
fs.writeFileSync(base + '.html', old.slice(0, start) + source + '\n' + old.slice(end));
console.log('Built standalone 2.10 from its editable source.');
