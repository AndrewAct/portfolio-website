# Portfolio Website of Andrew Chen 

v0.0.1 

* Homepage

![image info](./images/homepage.png)

* Medium Articles 

![image info](./images/medium_posts.png)

* URL Shortener

![image info](./images/url_shortener.png)

### Memo 

In current stage of refactoring, when building backend Docker images, need to follow these steps:
1. Redirect to `/backend`
2. Run build command with the full path of the Dockerfile

    `docker build -f services/history/Dockerfile -t history_test:0.0.3 .`

If we can put all shared files in all services (config.py, logger.py...), we can bypass this step. 
However, this violates "DRY" principle.

I didn't find a better solution yet, so will stick with method for now.


### Weather report 

To run weather report, direct to `backend` directory.
Then: run:
   `uvicorn services.weather_report.main:app --reload`

Note:

Although we have `mcp.py` in `weather_report` now, it is not a real MCP service.
Will update soon...

### Roadmap
- [ ] Weather report frontend (TBD)
- [ ] Weather report MCP (expected by July 13, 2025)
- [x] New feature: weather report
- [ ] Refactor: microservices (expected by June 22, 2025)
- [x] New feature: Horoscope
- [x] Frontend: Support URL Shortener functionality 
- [x] Deploy on AWS Elastic Lightsail
- [ ] Integrate GitHub Actions and workflow (TBD)
- [x] Utilities and other functionalities
- [x] Backend backbone: uses FastAPI and Python (Expected: Nov 5, 2024)
- [x] Retrieve articles from Medium (https://andrewact.medium.com/) 
- [x] Frontend (raw): uses Angular and TypeScript (Expected: Nov 6, 2024)
- [x] Domain name service (andrewcee.io) (Expected: Nov 7, 2024)

#### Weather Report To Do List

- [ ] Update the schemas
- [ ] Include more meaningful metrics 
- [ ] Support language switch (refer to Open Weather API doc)
- [ ] Support metric switch (Imperial, Metrics, Standard)

