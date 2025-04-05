import { APP_BASE_HREF } from '@angular/common';
import { CommonEngine } from '@angular/ssr';
import express, { Request, Response, NextFunction } from 'express';
import { fileURLToPath } from 'node:url';
import { dirname, join, resolve } from 'node:path';
import * as fs from 'node:fs';
import bootstrap from './src/main.server';

// The Express app is exported so that it can be used by serverless Functions.
export function app(): express.Express {
  const server = express();

  const projectRoot = dirname(fileURLToPath(import.meta.url));
  const srcFolder = join(projectRoot, 'src');
  const indexHtml = join(srcFolder, 'index.html');

  // Check ./index.html file
  if (!fs.existsSync(indexHtml)) {
    console.warn(`Warning: index.html not found at ${indexHtml}`);
  }

  const commonEngine = new CommonEngine();

  server.set('view engine', 'html');
  server.set('views', srcFolder);

  // Middleware to log requests for debugging URI errors
  server.use((req: Request, res: Response, next: NextFunction) => {
    // Log basic request information
    console.log(`[${new Date().toISOString()}] ${req.method} ${req.originalUrl}`);
    next();
  });

  // Serve static files from the src folder
  server.get('*.*', express.static(srcFolder, {
    maxAge: '1y'
  }));

  // Explicitly serve index.html for root and /index.html requests
  server.get('/', (req: Request, res: Response) => {
    res.sendFile(indexHtml);
  });

  server.get('/index.html', (req: Request, res: Response) => {
    res.sendFile(indexHtml);
  });

  // Serve assets folder
  server.use('/assets', express.static(join(srcFolder, 'assets')));

  // All regular routes use the Angular engine
  server.get('*', (req: Request, res: Response, next: NextFunction) => {
    try {
      const { protocol, originalUrl, baseUrl, headers } = req;

      // Skip processing for favicon.ico and other common browser requests
      if (originalUrl.match(/\.(ico|png|jpg|jpeg|gif|svg|webp)$/i)) {
        next();
        return;
      }

      // Log the original request URL for debugging
      console.log('Processing request:', originalUrl);

      // Process URL and ensure it is safe by properly encoding components
      let safeUrl: string;
      try {
        // First decode to avoid double-encoding
        const decodedUrl = decodeURI(originalUrl);

        // Split URL into path and query parts
        const urlParts = decodedUrl.split('?');
        const path = urlParts[0];
        const query = urlParts.length > 1 ? urlParts[1] : '';

        // Encode each path segment separately
        const safePath = path.split('/')
          .map(segment => segment ? encodeURIComponent(segment) : '')
          .join('/');

        // Reconstruct URL with encoded path and original query
        const safeOriginalUrl = safePath + (query ? '?' + query : '');

        // Log the transformation for debugging
        console.log('Original URL:', originalUrl);
        console.log('Safe URL path:', safeOriginalUrl);

        const host = headers.host || 'localhost';
        safeUrl = `${protocol}://${host}${safeOriginalUrl}`;

        // Validate the final URL
        new URL(safeUrl);
        console.log('Final URL to render:', safeUrl);
      } catch (urlError) {
        // Enhanced error logging for URL processing issues
        console.error('Invalid URL detected:', urlError);
        console.error('Original URL:', originalUrl);

        // Try to identify problematic segments in the URL
        try {
          const segments = originalUrl.split('/');
          console.log('URL segments:');
          segments.forEach((segment, index) => {
            try {
              if (segment) decodeURIComponent(segment);
              console.log(`  Segment ${index}: "${segment}" - Valid`);
            } catch (error) {
              // Type-safe error handling
              const errorMessage = error instanceof Error ? error.message : 'Unknown error';
              console.error(`  Segment ${index}: "${segment}" - INVALID: ${errorMessage}`);
            }
          });
        } catch (segmentError) {
          console.error('Error analyzing URL segments:', segmentError);
        }

        res.status(400).send('Bad Request: Invalid URL');
        return;
      }

      commonEngine
        .render({
          bootstrap,
          documentFilePath: indexHtml,
          url: safeUrl,
          publicPath: srcFolder,
          providers: [{ provide: APP_BASE_HREF, useValue: baseUrl }],
        })
        .then((html) => {
          res.send(html);
        })
        .catch((renderErr) => {
          // Enhanced error logging for SSR errors
          console.error('SSR Render Error:', renderErr);
          console.error('For URL:', safeUrl);

          // If this is a request for index.html that failed SSR, serve the static version
          if (originalUrl === '/' || originalUrl === '/index.html') {
            console.log('Falling back to static index.html');
            res.sendFile(indexHtml);
            return;
          }

          // Specific handling for URI errors
          if (renderErr instanceof URIError) {
            console.error('URI Error Details:', {
              message: renderErr.message,
              url: safeUrl,
              originalUrl: originalUrl
            });

            res.status(400).send('Bad Request: URI malformed');
            return;
          }

          next(renderErr);
        });
    } catch (err) {
      // Enhanced general error logging
      console.error('Express route error:', err);
      console.error('For request:', req.originalUrl);

      // Process URI errors
      if (err instanceof URIError) {
        console.error('URI Error in main handler:', {
          message: err.message,
          url: req.originalUrl
        });
        res.status(400).send('Bad Request: URI malformed');
        return;
      }

      next(err);
    }
  });

  // Global error handler for uncaught errors
  server.use((err: unknown, req: express.Request, res: express.Response, next: express.NextFunction) => {
    console.error('Unhandled server error:', err);

    // Special handling for Vite-specific errors
    if (err instanceof Error && err.message && err.message.includes('URI malformed')) {
      console.error('Vite URI malformed error detected');
      console.error('Request URL:', req.originalUrl);
      console.error('Request headers:', req.headers);

      // For home page, try to serve static index.html
      if (req.originalUrl === '/' || req.originalUrl === '/index.html') {
        res.sendFile(indexHtml);
        return;
      }

      res.status(400).send('Bad Request: URI malformed in Vite processing');
      return;
    }

    res.status(500).send('Internal Server Error');
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
