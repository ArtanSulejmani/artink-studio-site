import fs from 'node:fs';import os from 'node:os';import path from 'node:path';import {execFileSync,spawnSync} from 'node:child_process';import assert from 'node:assert/strict';
// Isolated fixture. Never changes the project or any remote repository.
const tmp=fs.mkdtempSync(path.join(os.tmpdir(),'artink-release-test-'));
const git=(...args)=>execFileSync('git',args,{cwd:tmp,encoding:'utf8'}).trim();
const write=(p,s)=>{fs.mkdirSync(path.dirname(path.join(tmp,p)),{recursive:true});fs.writeFileSync(path.join(tmp,p),s)};
git('init','-q');git('config','user.name','Local Test');git('config','user.email','test@example.invalid');
write('content/products/test.json','{}');write('content/release.json','{"version":1}');git('add','.');git('commit','-qm','initial');const cached=git('rev-parse','HEAD');
const ignore=path.resolve('scripts/ignore-build.cjs');
function check(label,expected){const result=spawnSync(process.execPath,[ignore],{cwd:tmp,env:{...process.env,CACHED_COMMIT_REF:cached,COMMIT_REF:git('rev-parse','HEAD')}});assert.equal(result.status,expected,label);console.log('PASS:',label)}
write('content/products/test.json','{"name":"edit"}');git('add','.');git('commit','-qm','save product');check('product-only save skips deployment',0);
write('public/images/test.webp','image fixture');git('add','.');git('commit','-qm','save image');check('image and product saves skip deployment',0);
write('content/settings.json','{}');git('add','.');git('commit','-qm','save settings');check('settings save skips deployment',0);
write('content/categories/new.json','{}');git('add','.');git('commit','-qm','save category');check('category save skips deployment',0);
write('content/imports/batch.json','{}');git('add','.');git('commit','-qm','save import request');check('import processing skips deployment',0);
write('content/release.json','{"version":2}');git('add','.');git('commit','-qm','release all');check('release triggers one build including accumulated changes',1);
// Empty catalogue build remains valid when the owner hides/deletes all products.
const app=path.join(tmp,'empty-app');for(const dir of ['src','scripts','public','content'])fs.cpSync(path.resolve(dir),path.join(app,dir),{recursive:true});
for(const file of fs.readdirSync(path.join(app,'content/products')))fs.unlinkSync(path.join(app,'content/products',file));
execFileSync(process.execPath,['scripts/build.mjs'],{cwd:app});assert(fs.existsSync(path.join(app,'dist/en/products/index.html')));console.log('PASS: empty catalogue builds safely');
console.log('Temporary fixture:',tmp);
