import http from 'node:http';
import { readFile } from 'node:fs/promises';
import path from 'node:path';

const directory = path.resolve(import.meta.dirname, '../dist');
const port = Number(process.env.PORT || 4173);
const types = {'.html':'text/html; charset=utf-8','.css':'text/css; charset=utf-8','.js':'text/javascript; charset=utf-8','.json':'application/json','.svg':'image/svg+xml','.xml':'application/xml','.txt':'text/plain; charset=utf-8','.webp':'image/webp','.png':'image/png','.jpg':'image/jpeg'};

http.createServer(async (request,response) => {
  try {
    const pathname = decodeURIComponent(new URL(request.url, 'http://localhost').pathname);
    const file = path.resolve(directory, '.' + pathname, pathname.endsWith('/') ? 'index.html' : '');
    if (file !== directory && !file.startsWith(directory + path.sep)) throw new Error('Invalid path');
    let data;
    try { data = await readFile(file); }
    catch { data = await readFile(path.join(file, 'index.html')); }
    response.writeHead(200, {'Content-Type':types[path.extname(file)] || types[path.extname(file + '/index.html')] || 'application/octet-stream'});
    response.end(data);
  } catch {
    response.writeHead(404, {'Content-Type':'text/plain; charset=utf-8'});
    response.end('Page not found. Run npm run build after changing products.');
  }
}).listen(port, '127.0.0.1', () => console.log(`ArtInk preview: http://localhost:${port}/\nPress Ctrl+C to stop.`));
