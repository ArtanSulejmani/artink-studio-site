const {execFileSync} = require('node:child_process');
// Content edits are saved in Git without publishing. Increment release.version
// in the CMS to publish all saved changes in one production deployment.
if (!process.env.CACHED_COMMIT_REF || !process.env.COMMIT_REF) process.exit(1);
try {
 const changed=execFileSync('git',['diff','--name-only',process.env.CACHED_COMMIT_REF,process.env.COMMIT_REF],{encoding:'utf8'}).trim().split('\n').filter(Boolean);
 const contentOnly=changed.every(p=>p.startsWith('content/products/')||p.startsWith('public/images/')||p==='content/settings.json');
 process.exit(contentOnly ? 0 : 1);
} catch { process.exit(1); }
