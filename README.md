# AssetPulse — Predictive Maintenance

Dashboard de manutenção preditiva industrial, com React, FastAPI, MQTT, PostgreSQL e simulador de sensores.

## Iniciar tudo com Docker

```bash
docker compose up --build
```

- **Dashboard:** http://localhost:5173
- **API Swagger:** http://localhost:8000/docs
- **Healthcheck:** http://localhost:8000/api/health

A simulação publica a cada 4 segundos mensagens no tópico `assetpulse/{asset_id}/telemetry`. O worker grava leituras no PostgreSQL; a API disponibiliza valores recentes e históricos.

## Rodar somente o dashboard

```bash
cd frontend
npm install
npm run dev
```

Sem backend, o dashboard ativa **modo demonstração** com dados locais simulados. Nesse modo, os gráficos históricos são ilustrativos. Com backend, a lista de ativos utiliza leituras da API, mas o gráfico de tendência segue demonstrativo nesta versão (a rota de histórico está pronta para integração).

## API

- `GET /api/health` — estado da API
- `GET /api/assets` — lista de ativos com últimas leituras e regras de classificação
- `GET /api/assets/{asset_id}/history?limit=100` — histórico de leituras
- `POST /api/telemetry` — ingerir uma leitura manualmente

Exemplo:

```bash
curl -X POST http://localhost:8000/api/telemetry -H 'Content-Type: application/json' -d '{"asset_id":"M-01","temp":67,"vibration":4.2,"rpm":1760,"current":13.4}'
```

## Organização

```
frontend/       React + Vite + Recharts
backend/app/    FastAPI, SQLAlchemy e consumidor MQTT
simulator/      Publicador MQTT com dados simulados
docker-compose.yml
mosquitto.conf
```

## Design tokens

| Uso | Cor |
| --- | --- |
| Fundo | `#0A0B18` |
| Superfícies | `#101023` |
| Primária | `#9E78F8` |
| Secundária | `#32C7E5` |
| Texto | `#F6F7FB` |
| Branco | `#FFFFFF` |

## Próximos passos

1. Integrar `GET /api/assets/{id}/history` ao gráfico em tempo real.
2. Adicionar autenticação, autorizações e segregação por planta industrial.
3. Treinar Isolation Forest com dados históricos rotulados, avaliar falsos positivos e publicar versão do modelo.
4. Criar ordens de serviço e notificações com confirmação dos responsáveis.
5. Parametrizar limiares por tipo de máquina conforme especificações técnicas.
6. Proteger broker MQTT (TLS, credenciais e ACL) e mover credenciais para secrets.

**Aviso:** É um MVP educacional. Índices de saúde e alertas são heurísticas demonstrativas, não um diagnóstico de falha validado. Não conectar a sistemas de parada ou segurança operacional.

Repositório sugerido: `assetpulse-predictive-maintenance`.
