export interface ProjectFeature {
  label: string
  description: string
}

export interface Project {
  id: string
  name: string
  nameZh?: string
  pronunciation?: string
  partOfSpeech?: string
  originalMeaning?: string
  modernMeaning?: string
  categories: string[]
  subtitle: string
  features: ProjectFeature[]
  stack: string[]
  url: string
}

export const projects: Project[] = [
  {
    id: 'ticksense',
    name: 'TickSense',
    categories: ['Live', 'AI', 'Finance', 'Real-time'],
    subtitle: 'Real-time crypto market lakehouse, built end-to-end',
    features: [
      {
        label: 'Live market data ingestion',
        description:
          'Binance WebSocket streams real-time L2 order book data — 5M+ ticks/day across 50 trading pairs'
      },
      {
        label: 'Stateful stream processing',
        description:
          'Apache Flink computes spread, imbalance, microprice, and 1-minute OHLCV with sub-second latency'
      },
      {
        label: 'Replayable by design',
        description:
          'Apache Iceberg on MinIO + Redpanda/Kafka keeps the full event history immutable and replayable'
      },
      {
        label: 'Analytics modeling with dbt',
        description:
          'Layered transformations over Trino turn raw ticks into API-ready marts with <30s freshness'
      },
      {
        label: 'Production observability',
        description:
          'Prometheus, Grafana, and Postgres CDC via Debezium provide end-to-end pipeline visibility'
      }
    ],
    stack: ['Kafka', 'PyFlink', 'Iceberg', 'dbt', 'Trino', 'FastAPI', 'Grafana', 'Debezium', 'MinIO'],
    url: 'https://ticksense.ai'
  },
  {
    id: 'wrightsop',
    name: 'WrightSOP',
    nameZh: '图匠',
    pronunciation: 'tú jiàng · /tuː dʒjɑːŋ/',
    partOfSpeech: 'noun',
    originalMeaning:
      'A drawing craftsperson skilled in turning designs into precise technical plans.',
    modernMeaning:
      'An AI-powered engineering drawing interpreter that helps teams accurately understand CAD drawings and PDFs through traceable extraction and human review.',
    categories: ['Live', 'AI', 'Industrial', 'Bilingual'],
    subtitle: 'Engineering drawings in; safer, bilingual work cards out',
    features: [
      {
        label: 'Fidelity-aware document ingestion',
        description:
          'Routes DWG, DXF, vector or scanned PDF, and field images to the best available structural or vision extractor'
      },
      {
        label: 'A hard WHAT / HOW safety boundary',
        description:
          'Drawings supply dimensions and specs; domain-authored SOP templates supply steps, tools, torque, and safety holds'
      },
      {
        label: 'Confidence-aware bilingual output',
        description:
          'Produces Chinese and English from one extraction while flagging safety-critical and low-confidence fields for review'
      },
      {
        label: 'Evidence-led CAD engineering',
        description:
          'Benchmarked headless DWG readers against a reference baseline and preserves known discrepancies instead of hiding them'
      },
      {
        label: 'Cloud-ready service boundaries',
        description:
          'Async FastAPI, PostgreSQL migrations, a typed Vue client, and container deployment keep extraction and delivery independently evolvable'
      }
    ],
    stack: [
      'FastAPI',
      'Vue 3',
      'TypeScript',
      'Aspose.CAD',
      'ezdxf',
      'PyMuPDF',
      'PostgreSQL',
      'Supabase',
      'Google Cloud Run'
    ],
    url: 'https://tujiang.build/'
  }
]
