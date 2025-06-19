/backend/
│
├── docker-compose.yml
├── .env.template
│
├── services/
│   ├── history/
│   │── ├── app/
│   │   │   ├── schemas.py
│   │   │   ├── router.py
│   │   │   ├── service.py
│   ├── main.py
│   ├── Dockerfile
│   └── requirements.txt
│   │ 
│   ├── url-shortener/
│   │   ├── app/
│   │   ├── main.py
│   │   ├── Dockerfile
│   │   └── requirements.txt
│   │ 
│   └── horoscope/
│       ├── app/
│       ├── main.py
│       ├── Dockerfile
│       └── requirements.txt
│
├── libs/
│   └── shared/
│       ├── config.py
│       ├── logger.py
│       ├── exceptions.py
│       ├── monitoring/
│       └── __init__.py
├── __init__.py
│
└── tests/
    └── integration/
