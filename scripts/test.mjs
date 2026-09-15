import fs from 'node:fs';import path from 'node:path';import assert from 'node:assert/strict';import {execFileSync} from 'node:child_process';
const root=process.cwd(),dist=path.join(root,'dist');
const walk=d=>fs.readdirSync(d,{withFileTypes:true}).flatMap(e=>e.isDirectory()?walk(path.join(d,e.name)):[path.join(d,e.name)]);
const files=walk(dist),html=files.filter(f=>f.endsWith('.html'));let refs=0;
for(const f of html){const s=fs.readFileSync(f,'utf8');assert(s.includes('name="viewport"'),f+' missing viewport');assert(/<html lang="(en|mk|sq)"/.test(s),f+' missing language');for(const m of s.matchAll(/(?:href|src)="(\/(?!\/)[^"?#]*)(?:[^" ]*)"/g)){let p=decodeURIComponent(m[1]);const target=path.join(dist,p);assert(fs.existsSync(target),f+' missing target '+p);refs++}for(const m of s.matchAll(/<script type="application\/ld\+json">(.*?)<\/script>/g))JSON.parse(m[1]);if(f.includes('/products/')&&!f.endsWith('/products/index.html'))assert(s.includes('mailto:artinkstudio.2026@gmail.com?subject='),f+' quote');}
execFileSync(process.execPath,['--check','public/assets/app.js']);execFileSync(process.execPath,['--check','scripts/ignore-build.cjs']);
const cfg=JSON.parse(fs.readFileSync(path.join(dist,'admin/cms/config.yml')));assert.equal(cfg.backend.repo,'ArtanSulejmani/artink-studio-site');assert.equal(cfg.collections[0].create,true);assert.equal(cfg.collections[0].delete,true);assert.equal(cfg.collections.at(-1).name,'release');
for(const l of ['en','mk','sq'])assert(fs.existsSync(path.join(dist,l,'privacy/index.html')));
console.log(`PASS: ${html.length} HTML pages; ${refs} internal references; JSON-LD; 3 languages; mail links; CMS CRUD/release schema; JS syntax.`);
