# 見光鼠 RatSight

RatSight 是面向臺北市的證據導向都市鼠類活動模擬與市政決策支援專案。此儲存庫目前只提供可執行的開發基礎與合成資料示範，不提供真實鼠類遷移路徑或臺北市風險預測。

## 資料與科學界線

每項資料與輸出須標示為 `OBSERVED`（直接觀測）、`INFERRED`（明確假設推導）、`SIMULATED`（模型產生）或 `UNVERIFIED`（證據不足）。合成網路僅供測試；任何模擬軌跡都不是動物實際遷移紀錄。未知參數保持未知，不杜撰統計、常數或準確度。

## 架構

- `apps/web/`：Next.js、TypeScript、Tailwind CSS、MapLibre、TanStack Query 分析儀表板。
- `services/api/`：FastAPI、Pydantic、SQLAlchemy、Alembic API。
- `packages/geo/`：獨立 GeoPandas/Shapely CRS、幾何與空間圖工具。
- `packages/simulation/`：獨立 NetworkX/NumPy/SciPy 合成加權隨機漫步。
- `infra/`：提供本機 PostgreSQL/PostGIS 與隔離的地理資料整合 smoke harness。
- `openspec/`：以本機 `evidence-driven` schema 建立 OpenSpec 變更流程。
- `rig.yaml`、`.openrig/`、`guidance/`：OpenRig rat-team 與角色規範。

詳見 [架構概覽](docs/architecture/overview.md)、[研究路線圖](docs/research/research-roadmap.md)、[模型路線圖](docs/modeling/model-roadmap.md)、[資料來源政策](docs/infrastructure/data-sources.md)、[行政區界匯入指令](docs/infrastructure/administrative-boundaries-import.md)、[雨水下水道管線匯入指令](docs/infrastructure/stormwater-pipelines-import.md) 與 [full-local 資料匯入](docs/infrastructure/full-local-data-bootstrap.md)。系統提供本機檔案匯入的官方臺北行政區界、雨水管線基礎設施參考層，以及受抑制的 250 公尺公民通報彙整；合成鼠類通報圖層已移除。這些資料均不是鼠類觀測，且管線連通性仍為 `UNVERIFIED`。

## 本機開發

需求：Node.js 26、uv、Python 3.12 或 3.13、Docker Compose。套件版本以 lockfile 固定。

```sh
make install
cp .env.example .env
make db-up
make migrate
# terminal 1
make api
# terminal 2
make web
```

Web：<http://localhost:3000>。API：<http://127.0.0.1:8000>；OpenAPI：`/docs`。PostGIS 綁定 `127.0.0.1:54329`，僅限本機開發。Compose volume 持久保存；不要用 `down -v` 清除資料。

### 隔離瀏覽器驗證（不碰共享服務）

使用既有 smoke harness 執行可重現的 populated workflow；它會先檢查 Docker、端口是否空閒，再建立以專案名稱隔離的 disposable PostGIS volume、migration、fixture、API/Web、health check 與 Playwright browser checks，結束時只清理由自身啟動的程序與 volume：

```sh
# 行政區界 + 雨水管線：isolated PostGIS → API → Next.js → browser checks
make geospatial-smoke
```

需要手動檢查時，先確認 `127.0.0.1:8010` 與 `127.0.0.1:3010` 未被佔用並確認程序所有者；不可停止或重啟其他專案程序，也不可使用共享 PostGIS volume。API 必須以 `--host 127.0.0.1 --port <free-api-port>` 啟動，Web 必須以 `NEXT_PUBLIC_API_URL=http://127.0.0.1:<api-port> pnpm dev --hostname 127.0.0.1 --port <free-web-port>` 啟動；確認 `/health` 回傳 200，再以瀏覽器點擊圖層或日期控制並確認 API 請求。若端口或所有者檢查失敗，停止並記錄為未驗證。

免費、無金鑰的 CARTO Positron style 為本機預設底圖；style URL 可由 `NEXT_PUBLIC_MAP_STYLE_URL` 設定。地圖會保留 provider attribution。遵守各 provider 的使用條款、速率限制與 attribution 規定；示範底圖不可視為官方資料。

## 測試與檢查

```sh
make test
make lint
make typecheck
make build
pnpm test:e2e
make validate
```

PostGIS migration 驗證需要 Docker daemon 和可用映像。Playwright 首次使用可能需執行 `pnpm --filter @ratsight/web exec playwright install chromium`。

## OpenSpec 與團隊

變更依 OpenSpec `evidence-driven` (fork 自已安裝的 `spec-driven`) 流程管理。核心 schema 僅支援其原生 artifact lifecycle；證據蒐集、對抗式審查、獨立審查、模型驗證與 traceability 透過 `guidance/lead.md` 和明確檢查點協調，不宣稱 schema 強制不存在的階段。

OpenRig `rat-team` 有五個 pods、九個 Pi seats。`scripts/setup-pi-seats.sh --dry-run` 預覽每個 seat 的設定連結；需明確加 `--apply` 才會建立 seat 目錄/連結。憑證以 symlink 使用、不複製入 repo；不共享 session history、可寫入 memory 或 role guidance。尚未啟動 agents。

## 目前限制

已有官方行政區界與雨水管線作為地理／基礎設施參考資料，但沒有臺北真實鼠類觀測；沒有生物參數、校準或驗證結果。雨水管線標示為 `INFRASTRUCTURE_REFERENCE` / `UNVERIFIED`，不代表已驗證的地下連通性、可通行性或風險。行政區界與雨水管線都不是鼠類觀測或風險預測。模擬是 deterministic synthetic weighted random walk。Pi model catalog 已註冊指定模型 `openai-codex/gpt-5.6-luna`；實際 provider 認證與 seat 執行尚未驗證。`opencode-go/deepseek-v4.1-flash` 在本機 catalog 可見，但 seats 未啟動、憑證未驗證。
