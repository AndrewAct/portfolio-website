import { APP_BASE_HREF } from '@angular/common';
import { CommonEngine } from '@angular/ssr';
import express from 'express';
import { fileURLToPath } from 'node:url';
import { dirname, join, resolve } from 'node:path';
import bootstrap from './src/main.server';

// The Express app is exported so that it can be used by serverless Functions.
export function app(): express.Express {
  const server = express();
  const serverDistFolder = dirname(fileURLToPath(import.meta.url));
  const browserDistFolder = resolve(serverDistFolder, '../browser');
  const indexHtml = join(serverDistFolder, 'index.server.html');

  const commonEngine = new CommonEngine();

  server.set('view engine', 'html');
  server.set('views', browserDistFolder);

  // Example Express Rest API endpoints
  // server.get('/api/**', (req, res) => { });
  // Serve static files from /browser
  server.get('**', express.static(browserDistFolder, {
    maxAge: '1y',
    index: 'index.html',
  }));

  // All regular routes use the Angular engine
  server.get('**', (req, res, next) => {
    try {
      const { protocol, originalUrl, baseUrl, headers } = req;

      // Process URL and ensure it is safe
      let safeUrl;
      try {
        const host = headers.host || 'localhost';
        safeUrl = `${protocol}://${host}${originalUrl}`;
        new URL(safeUrl);
      } catch (urlError) {
        console.error('Invalid URL detected:', urlError);
        res.status(400).send('Bad Request: Invalid URL');
        return;
      }

      commonEngine
        .render({
          bootstrap,
          documentFilePath: indexHtml,
          url: safeUrl,
          publicPath: browserDistFolder,
          providers: [{ provide: APP_BASE_HREF, useValue: baseUrl }],
        })
        .then((html) => {
          res.send(html);
        })
        .catch((renderErr) => {
          console.error('SSR Render Error:', renderErr);

          // Return error information
          if (renderErr instanceof URIError) {
            res.status(400).send('Bad Request: URI malformed');
            return;
          }

          next(renderErr);
        });
    } catch (err) {
      console.error('Express route error:', err);

      // Process URI errors
      if (err instanceof URIError) {
        res.status(400).send('Bad Request: URI malformed');
        return;
      }

      next(err);
    }
  });

  return server;
}

function run(): void {
  const port = process.env['PORT'] || 4000;

  // Start up the Node server
  const server = app();
  server.listen(port, () => {
    console.log(`Node Express server listening on http://localhost:${port}`);
  });
}

run();
