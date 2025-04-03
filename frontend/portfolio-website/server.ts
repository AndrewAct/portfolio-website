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

      // 安全处理 URL - 避免 URI 解码错误
      let safeUrl;
      try {
        // 确保 URL 是安全的
        const host = headers.host || 'localhost';
        safeUrl = `${protocol}://${host}${originalUrl}`;
        // 验证 URL 的有效性
        new URL(safeUrl);
      } catch (urlError) {
        console.error('Invalid URL detected:', urlError);
        res.status(400).send('Bad Request: Invalid URL');
        return; // 添加 return 语句
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
          // 不需要 return，因为 res.send() 已经结束了请求
        })
        .catch((renderErr) => {
          console.error('SSR Render Error:', renderErr);

          // 如果是 URI 错误，返回适当的响应
          if (renderErr instanceof URIError) {
            res.status(400).send('Bad Request: URI malformed');
            return; // 添加 return 语句
          }

          // 对于其他错误，继续到下一个中间件
          next(renderErr);
          // 不需要 return，因为 next() 将控制权传递给下一个中间件
        });
    } catch (err) {
      console.error('Express route error:', err);

      // 处理 URI 错误
      if (err instanceof URIError) {
        res.status(400).send('Bad Request: URI malformed');
        return; // 添加 return 语句
      }

      next(err);
      // 不需要 return，因为 next() 将控制权传递给下一个中间件
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
