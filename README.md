# Transaction Dashboard — Evaluación Técnica
 
Sistema full-stack de transacciones financieras con API REST idempotente, procesamiento asíncrono vía Celery, actualizaciones en tiempo real por WebSocket, resumen de texto con OpenAI y un bot RPA con Playwright.
 
**Stack:** FastAPI · PostgreSQL · Redis · Celery · WebSockets · React 18 · TypeScript · Zustand · React Query · TailwindCSS · OpenAI · Playwright · Docker
 
---
 
## Tabla de contenidos
 
- [Arquitectura](#arquitectura)
- [Instrucciones para ejecutar el proyecto](#instrucciones-para-ejecutar-el-proyecto)
- [Estructura del proyecto](#estructura-del-proyecto)
- [Referencia de la API](#referencia-de-la-api)
- [Eventos de WebSocket](#eventos-de-websocket)
- [Pruebas](#pruebas)
- [RPA — Scraper de Wikipedia](#rpa--scraper-de-wikipedia)
- [Decisiones técnicas clave](#decisiones-técnicas-clave)
- [Estrategia de despliegue](#estrategia-de-despliegue)
- [Solución de problemas](#solución-de-problemas)
---
 
## Arquitectura
 
```
┌─────────────┐     HTTP/WS      ┌──────────────┐      ┌─────────────┐
│   React     │ ───────────────▶ │   FastAPI    │ ───▶ │ PostgreSQL  │
│  Frontend   │ ◀─────────────── │   Backend    │      └─────────────┘
└─────────────┘    Eventos en    └──────┬───────┘
                    vivo                │                ┌─────────────┐
                                         ├───────────────▶│    Redis    │
                                         │                │ (broker +   │
                                  ┌──────▼───────┐        │ idempotencia)│
                                  │Celery Worker │ ◀──────┴─────────────┘
                                  └──────────────┘
                                         │
                                  ┌──────▼───────┐
                                  │   OpenAI /   │
                                  │     Mock     │
                                  └──────────────┘
 
┌─────────────┐
│  Playwright  │ ──▶ scrapea Wikipedia ──▶ POST /assistant/summarize
│     RPA      │
└─────────────┘
```
 
**Capas de Clean Architecture** (backend): `core/` (transversal) → `infrastructure/` (BD, cache, servicios externos) → `services/` (lógica de negocio) → `api/` (presentación HTTP/WS). Las dependencias apuntan solo hacia adentro — `core/` no depende de nada interno; `services/` nunca importa desde `api/`.
 
---
 
## Instrucciones para ejecutar el proyecto
 
Esta sección documenta el proceso real y completo para levantar el proyecto desde cero, incluyendo los pasos de depuración necesarios la primera vez que se ejecuta (healthcheck, migraciones de Alembic, etc.).
 
### Requisitos previos
 
- Docker y Docker Compose v2+
- (Opcional) Node 20+ y Python 3.12+ para desarrollo local sin Docker
### 1. Clonar y configurar
 
**Linux / macOS:**
```bash
git clone <repo-url>
cd transaction-orchestrator-app
cp .env.example .env
```
 
**Windows (PowerShell):**
```powershell
git clone <repo-url>
cd transaction-orchestrator-app
copy .env.example .env
```
 
Deja `OPENAI_API_KEY` vacío en `.env` para usar el mock automático — no se necesita API key para correr la demo completa.
 
### 2. Construir y levantar los contenedores
 
**Linux / macOS / Windows (mismo comando):**
```bash
docker compose up --build
```
 
Esto construye y levanta: PostgreSQL, Redis, FastAPI (`:8000`), Celery worker, Flower (`:5555`) y el frontend de React (`:5173`).
 
> **Nota:** si es la primera vez que levantas el proyecto en tu máquina, es posible que la API se marque como `unhealthy` y el frontend no arranque. Esto ya está resuelto en el `docker-compose.yml` de este repo (el healthcheck usa Python en vez de `curl`, que no viene incluido en la imagen `python:3.12-slim`), pero si ves ese error, revisa la sección [Solución de problemas](#solución-de-problemas).
 
### 3. Generar y aplicar las migraciones de la base de datos
 
El servicio `api` corre `alembic upgrade head` automáticamente al arrancar (ver `command` en `docker-compose.yml`). Sin embargo, si es la **primera vez** que se configura el proyecto y la carpeta `backend/migrations/versions/` está vacía, no hay ninguna migración que aplicar y las tablas nunca se crean. Pasos para generarla desde cero:
 
**Linux / macOS / Windows (mismo comando, con los contenedores ya levantados):**
```bash
# Crear el directorio de versiones si no existe
docker compose exec api mkdir -p /app/migrations/versions
 
# Generar la migración inicial a partir de los modelos SQLAlchemy
docker compose exec api alembic revision --autogenerate -m "create initial tables"
 
# Aplicarla contra la base de datos
docker compose exec api alembic upgrade head
```
 
Verifica que las tablas se crearon correctamente:
 
```bash
docker compose exec postgres psql -U postgres -d transactions_db -c "\dt"
```
 
Deberías ver `ai_logs`, `alembic_version` y `transactions`.
 
> Una vez generada, la migración queda en `backend/migrations/versions/` y debe **commitearse al repositorio** — es un artefacto versionado, no algo que se regenera en cada máquina.
 
### 4. Abrir la aplicación
 
| Servicio | URL |
|---|---|
| Dashboard (Frontend) | http://localhost:5173 |
| Documentación API (Swagger) | http://localhost:8000/docs |
| Documentación API (ReDoc) | http://localhost:8000/redoc |
| Flower (monitor de Celery) | http://localhost:5555 |
 
### 5. Verificación rápida de salud
 
```bash
curl http://localhost:8000/health
curl http://localhost:8000/transactions?limit=10&offset=0
```
 
La primera debe devolver `{"status": "ok", ...}`; la segunda, `{"total": 0, "items": []}` (o tus transacciones si ya sembraste datos).
 
### 6. Detener y reanudar el proyecto
 
**Detener sin perder datos** (recomendado para el día a día — no reconstruye nada al volver a iniciar):
 
```bash
docker compose stop
```
 
**Reanudar:**
 
```bash
docker compose start
```
 
**Bajar los contenedores** (los elimina, pero conserva los volúmenes con nombre — `postgres_data`, `redis_data` — así que los datos persisten):
 
```bash
docker compose down
```
 
**Reset completo** (elimina también los volúmenes — pierdes todos los datos, útil si la base quedó en un estado inconsistente):
 
```bash
docker compose down -v
```
 
> ⚠️ Después de un `down -v`, al volver a levantar con `docker compose up --build` la base de datos estará vacía. Si la carpeta `backend/migrations/versions/` ya tiene la migración inicial commiteada, `alembic upgrade head` la aplicará automáticamente sin pasos manuales. Solo repite el proceso del paso 3 si esa carpeta está vacía.
 
### 7. (Opcional) Desarrollo del frontend fuera de Docker
 
Para iterar más rápido en el frontend con hot reload instantáneo, puedes correrlo localmente en vez de dentro del contenedor, mientras el backend sigue en Docker:
 
**Linux / macOS:**
```bash
cd frontend
npm install
npm run dev
```
 
**Windows (PowerShell):**
```powershell
cd frontend
npm install
npm run dev
```
 
Asegúrate de que `VITE_API_URL=http://localhost:8000` y `VITE_WS_URL=ws://localhost:8000` estén configurados (en `.env` o como variables de entorno) y que el backend esté corriendo en Docker (`docker compose ps` → `api` en estado `healthy`).
 
### 8. (Opcional) Correr el bot RPA
 
```bash
make rpa TERM="Python programming language"
```
 
---
 
## Estructura del proyecto
 
```
backend/app/
├── core/               # excepciones, logger, constantes, proveedores DI
├── schemas/            # DTOs globales de Pydantic
├── api/
│   ├── routes/          # endpoints HTTP
│   └── websocket/        # endpoint WS (ciclo de vida separado)
├── services/             # orquestación de lógica de negocio
├── workers/              # app de Celery + tareas
└── infrastructure/
    ├── database/          # engine, sesión, modelos ORM
    ├── repositories/       # acceso a datos
    ├── events/             # publicador de eventos WS
    ├── integrations/       # adaptador de OpenAI
    ├── cache/              # Redis + idempotencia
    └── ws/                 # gestor de conexiones
 
frontend/src/
├── components/{atoms,molecules,organisms}/
├── hooks/                 # useTransactions, useWebSocket, useAssistant
├── services/               # api.ts, websocket.ts
├── store/                  # slices de Zustand
└── pages/
 
rpa/
├── base_scraper.py         # clase base reutilizable de Playwright
└── wikipedia_scraper.py    # Wikipedia → /assistant/summarize
```
 
El detalle completo de las decisiones detrás de esta estructura está en la sección de decisiones técnicas más abajo.
 
---
 
## Referencia de la API
 
### `POST /transactions/create`
 
Creación idempotente de transacciones. Incluye el header `Idempotency-Key` para que los reintentos sean seguros.
 
```bash
curl -X POST http://localhost:8000/transactions/create \
  -H "Content-Type: application/json" \
  -H "Idempotency-Key: order-2024-001" \
  -d '{"user_id": "user_alice", "amount": "150.00", "type": "credit"}'
```
 
**Respuesta `201`:**
```json
{
  "id": "a1b2c3d4-...",
  "user_id": "user_alice",
  "amount": "150.00",
  "type": "credit",
  "status": "pending",
  "idempotency_key": "order-2024-001",
  "task_id": null,
  "error_message": null,
  "created_at": "2024-01-15T10:30:00Z",
  "updated_at": "2024-01-15T10:30:00Z"
}
```
 
Repetir la misma solicitud con el mismo `Idempotency-Key` devuelve la respuesta idéntica sin crear una fila duplicada.
 
### `POST /transactions/async-process`
 
Encola una transacción existente para procesamiento en segundo plano.
 
```bash
curl -X POST http://localhost:8000/transactions/async-process \
  -H "Content-Type: application/json" \
  -d '{"transaction_id": "a1b2c3d4-..."}'
```
 
**Respuesta `202`:**
```json
{
  "transaction_id": "a1b2c3d4-...",
  "task_id": "celery-task-uuid",
  "status": "pending",
  "message": "Transaction enqueued for async processing."
}
```
 
### `GET /transactions`
 
Listado paginado. Parámetros de query: `limit` (por defecto 20, máximo 100), `offset`.
 
### `GET /transactions/{id}`
 
Búsqueda de una transacción individual. Devuelve `404` si no existe.
 
### `POST /assistant/summarize`
 
```bash
curl -X POST http://localhost:8000/assistant/summarize \
  -H "Content-Type: application/json" \
  -d '{"text": "Tu texto aquí, mínimo 10 caracteres..."}'
```
 
Sin `OPENAI_API_KEY` configurada, devuelve una respuesta mock claramente etiquetada (`is_mock: true`). Cada par solicitud/respuesta se persiste en la tabla `ai_logs` para auditoría y control de costos.
 
---
 
## Eventos de WebSocket
 
Conexión: `ws://localhost:8000/transactions/stream`
 
| Evento | Disparador | Payload |
|---|---|---|
| `connected` | Al establecer la conexión | `{ message, active_connections }` |
| `transaction.created` | Nueva transacción guardada | `{ id, user_id, amount, status }` |
| `transaction.status_changed` | Celery actualiza el estado | `{ id, old_status, new_status, task_id, error_message }` |
| `ping` | Cada 30s | keepalive — sin payload |
 
El hook `useWebSocket` del frontend se reconecta automáticamente con backoff exponencial (1s → 2s → 4s … máximo 30s, ±20% de jitter) e invalida la cache de React Query en cada evento relevante.
 
---
 
## Pruebas
 
```bash
make test                   # suite completa con cobertura
make test-unit               # solo pruebas unitarias (~15 casos)
make test-integration         # solo pruebas de integración (~15 casos)
```
 
**Cobertura por capa:**
- `test_idempotency.py` — hit/miss/delete de cache en Redis
- `test_transaction_service.py` — creación, replay idempotente, no encontrado, paginación
- `test_ai_service.py` — resumen mock, persistencia de logs
- `test_connection_manager.py` — broadcast, limpieza de conexiones muertas, múltiples clientes
- `test_transaction_tasks.py` — camino exitoso de Celery, agotamiento de reintentos → failed
- `test_transactions_api.py` / `test_assistant_api.py` — ciclo completo de solicitud/respuesta HTTP
- `test_websocket.py` — handshake, limpieza al desconectar, broadcast end-to-end al crear una transacción
Las pruebas usan SQLite en memoria + un doble falso de Redis — no se necesita Docker para correr `pytest` localmente si las dependencias están instaladas.
 
---

## Pruebas de la API (Postman)

La colección de Postman y el archivo de entorno se encuentran en la carpeta:

`/postman`

Para probar los endpoints:

1. Importa el archivo de entorno:
   `Transaction-Dashboard.postman_environment.json`

2. Importa la colección:
   `Transaction-Dashboard.postman_collection.json`

3. Verifica que la URL base configurada sea:

`http://localhost:8000`

La colección incluye cobertura de los principales flujos de la API, incluyendo:

* Verificación de estado (`health check`)
* Creación de transacciones con idempotencia
* Procesamiento asíncrono de transacciones
* Listado paginado de transacciones
* Consulta de transacciones por ID
* Validaciones y manejo de errores
* Integración con el asistente de resumen (OpenAI)

**Nota:** asegúrate de que el backend esté ejecutándose antes de realizar las pruebas.

---
 
## RPA — Scraper de Wikipedia
 
```bash
make rpa TERM="FastAPI"
# o directamente:
docker compose --profile rpa run --rm rpa "Celery task queue"
```
 
Flujo: navega al artículo de Wikipedia → maneja páginas de desambiguación automáticamente → extrae el primer párrafo con ≥80 caracteres (omite texto de stub/navegación) → elimina marcadores de nota al pie tipo `[1]` → hace POST a `/assistant/summarize` → imprime el resumen generado por IA.
 
Para ver el navegador en acción en vez de correr en modo headless (útil para el video de demo):
 
```bash
cd rpa
RPA_HEADLESS=false RPA_SLOW_MO=500 python wikipedia_scraper.py "Python programming language"
```
 
---
 
## Decisiones técnicas clave
 
| Decisión | Justificación |
|---|---|
| Gate de idempotencia en Redis antes de escribir en BD | Búsqueda O(1), TTL nativo, evita SQL innecesario en solicitudes duplicadas |
| Celery `acks_late=True` + backoff exponencial con jitter | Entrega at-least-once; el jitter evita el "thundering herd" en reintentos masivos |
| División en carpetas de Clean Architecture (`core/infrastructure/services/api`) | La regla de dependencias hacia adentro mantiene la lógica de negocio testeable sin mocks de HTTP o BD |
| `infrastructure/events/publisher.py` separado de `services/` | Publicar eventos es un efecto secundario de I/O, no lógica de negocio — los servicios permanecen agnósticos al broker |
| Zustand en vez de Redux | React Query gestiona el estado del servidor; Zustand solo necesita estado de UI — sin boilerplate |
| WebSocket en vez de SSE | Canal bidireccional que deja espacio para filtrado de suscripciones del lado del cliente a futuro |
| gpt-4o-mini en vez de gpt-4o | Calidad suficiente para resumir a ~15x menor costo; intercambiable con una sola constante |
| SQLite en memoria para pruebas | Las pruebas corren en milisegundos sin Docker; las de integración igual validan comportamiento SQL real |
 
---
 
## Estrategia de despliegue
 
**Configuración actual (este repo):** Docker Compose — adecuada para demos, evaluaciones técnicas y despliegues a pequeña escala.
 
**Ruta hacia producción:**
 
1. **Registro de contenedores:** subir imágenes a ECR/GCR/Docker Hub vía CI en cada merge a `main`.
2. **Base de datos:** PostgreSQL administrado (RDS/Cloud SQL) en vez de la instancia en contenedor; correr `alembic upgrade head` como un job de migración en tiempo de despliegue, no dentro del `command` del contenedor de la app.
3. **Redis:** Redis administrado (ElastiCache/Memorystore) dividido en dos instancias lógicas — una para broker/resultados de Celery, otra para cache de idempotencia — para aislar dominios de falla.
4. **API:** desplegar detrás de un load balancer con 2+ réplicas; el escalado horizontal es seguro porque la API es stateless salvo por el `ConnectionManager` en proceso.
5. **WebSocket a escala:** el `ConnectionManager` actual es en proceso y no transmite entre réplicas. Para WS multi-réplica, cambiar el transporte de broadcast a Redis Pub/Sub — cada réplica se suscribe a un canal y reenvía a sus conexiones locales. La interfaz `EventPublisher` no cambia, solo su implementación interna.
6. **Workers de Celery:** escalar horizontalmente según la profundidad de la cola (Flower expone esta métrica); usar `--autoscale=10,2` para concurrencia elástica.
7. **Secretos:** mover `OPENAI_API_KEY` y credenciales de BD a un gestor de secretos (AWS Secrets Manager / Vault) en vez de `.env`.
8. **Observabilidad:** la salida JSON de `structlog` ya es enviable a Datadog/Loki sin cambios de código (`JSON_LOGS=true`). Agregar trazado con OpenTelemetry a nivel de middleware de FastAPI para trazabilidad de requests entre servicios.
9. **Frontend:** el build estático servido por `nginx` se despliega limpiamente en cualquier CDN/hosting estático (Vercel, S3+CloudFront) — apuntar `VITE_API_URL`/`VITE_WS_URL` al dominio de la API de producción en tiempo de build.
---
 
## Solución de problemas
 
**`docker compose up` falla en el healthcheck de `api`** — Postgres tarda unos segundos en aceptar conexiones en el primer arranque; `depends_on: condition: service_healthy` maneja esto, pero si sigue fallando, aumenta `start_period` en el healthcheck. Si el healthcheck usa `curl` y la imagen es `python:3.12-slim`, ten en cuenta que `curl` no viene incluido por defecto — usa el healthcheck basado en Python que ya trae este repo, o instala `curl` en el Dockerfile.
 
**Error `relation "transactions" does not exist`** — significa que las migraciones de Alembic no se aplicaron (probablemente porque `backend/migrations/versions/` está vacía). Sigue el paso 3 de [Instrucciones para ejecutar el proyecto](#instrucciones-para-ejecutar-el-proyecto) para generarlas y aplicarlas.
 
**El WebSocket no conecta desde el frontend** — verifica que `VITE_WS_URL` coincida con el host de tu API; los navegadores bloquean contenido mixto (una página `https://`/`wss://` no puede conectar a `ws://`). Si ves reconexiones constantes con backoff exponencial en la consola, confirma primero que el backend esté corriendo (`docker compose ps`, `curl http://localhost:8000/health`) antes de asumir un bug en el frontend.
 
**Error de React "Maximum update depth exceeded" / Minified React error #185** — normalmente indica un selector de estado (por ejemplo, un selector de Zustand) que devuelve una nueva referencia de array/objeto en cada llamada, en vez de una cacheada. Corre el frontend en modo desarrollo (`npm run dev`) para ver el nombre del componente y la advertencia completa (`The result of getSnapshot should be cached to avoid an infinite loop`), y envuelve la derivación con `useMemo` o usa `useShallow` de Zustand.
 
**El script de RPA se cuelga en Wikipedia** — aumenta `RPA_TIMEOUT_MS` en `rpa/.env`; algunos términos con redirecciones necesitan más tiempo en conexiones lentas.
 
**Las tareas de Celery se quedan en `pending`** — revisa `make logs-worker`; verifica que Redis sea alcanzable desde el contenedor del worker (`CELERY_BROKER_URL`).
