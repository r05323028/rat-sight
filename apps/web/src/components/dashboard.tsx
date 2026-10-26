"use client";

import { useMutation, useQuery } from "@tanstack/react-query";
import { Fragment, useEffect, useMemo, useState } from "react";

import { LayerGlyph } from "@/components/layer-glyph";
import { MapView } from "@/components/map-view";
import { Button } from "@/components/ui/button";
import {
  BBOX_MAX_SPAN_DEGREES,
  fetchAdministrativeDistricts,
  fetchCitizenReportAggregates,
  fetchLayers,
  fetchRodentReports,
  fetchStormwaterPipelines,
  isBboxTooBroad,
  isReportedRangeInvalid,
  isSourceNetworkUnavailable,
  requestPreview,
  taipeiLocalToUtc,
  type AdministrativeDistrictProperties,
  type Bbox,
  type Layer,
  type RodentReportProperties,
  type SimulationPreview,
  type StormwaterProperties,
} from "@/lib/api";

const DEFAULT_LAYERS: Layer[] = [
  ["rodent_observations", "鼠類觀測"],
  ["sewer_networks", "污水下水道"],
  ["surface_corridors", "地表移動廊道"],
  ["human_activity", "人類活動"],
  ["environmental_conditions", "環境條件"],
  ["simulated_paths", "模擬移動路徑"],
].map(([id, label]) => ({
  id,
  label,
  available: false,
  classification: id === "simulated_paths" ? "SIMULATED" : null,
  message:
    id === "simulated_paths"
      ? "執行合成預覽後可用。"
      : id === "rodent_observations"
        ? "尚未載入觀測資料集。"
        : "尚未載入資料集。",
}));

// Canonical layer ids map to Chinese labels; unknown ids stay generic so API text cannot leak into UI.
const LAYER_LABEL_OVERRIDES: Record<string, string> = {
  rodent_observations: "鼠類觀測",
  sewer_networks: "污水下水道",
  surface_corridors: "地表移動廊道",
  human_activity: "人類活動",
  environmental_conditions: "環境條件",
  simulated_paths: "模擬移動路徑",
};

// Unavailable-row copy is owned by the UI, so API payload language never leaks.
const LAYER_UNAVAILABLE_MESSAGES: Record<string, string> = {
  rodent_observations: "尚未載入觀測資料集。",
  simulated_paths: "執行合成預覽後可用。",
};
const DEFAULT_UNAVAILABLE_MESSAGE = "尚未載入資料集。";
const CLASSIFICATION_LABELS: Record<string, string> = {
  OBSERVED: "OBSERVED · 已觀測",
  INFERRED: "INFERRED · 推論",
  SIMULATED: "SIMULATED · 模擬",
  UNVERIFIED: "UNVERIFIED · 未驗證",
};

function isSafeExternalUrl(value: string): boolean {
  return /^https?:\/\//i.test(value);
}

// Approximates the initial map center until MapView reports the real viewport bbox.
const DEFAULT_STORMWATER_BBOX: Bbox = [121.5, 24.98, 121.63, 25.09];
const MAX_VISIBLE_PIPELINE_LIST_ITEMS = 100;
const INFRASTRUCTURE_GUIDES_URL =
  "https://github.com/r05323028/rat-sight/blob/main/docs/infrastructure";

const STORMWATER_ATTRIBUTE_LABELS: [keyof StormwaterProperties, string][] = [
  ["segment_id", "管段 ID"],
  ["category_code", "類別代碼"],
  ["pipe_number", "管號"],
  ["start_node_id", "起點節點（發布機關屬性）"],
  ["end_node_id", "終點節點（發布機關屬性）"],
  ["managing_unit", "管理單位"],
  ["work_category", "工程類別"],
  ["installation_date", "安裝日期"],
  ["dimension_unit", "尺寸單位"],
  ["diameter_width", "直徑／寬"],
  ["diameter_height", "直徑／高"],
  ["conduit_count", "管孔數"],
  ["material", "材質"],
  ["start_burial_depth", "起點埋深"],
  ["end_burial_depth", "終點埋深"],
  ["length", "長度"],
  ["pipe_type", "管種"],
  ["use_status", "使用狀態"],
  ["data_status", "資料狀態"],
  ["notes", "備註"],
];

function zHandlingText(zHandling: "dropped" | "retained" | "not_present"): string {
  if (zHandling === "dropped") return "來源 Z 已捨棄 — 無文件化的垂直坐標參考系統";
  if (zHandling === "retained") return "保留來源 Z";
  return "來源無 Z 值";
}

function stormwaterQualitySummary(quality: {
  missing_pipe_number_count: number;
  duplicate_pipe_number_value_count: number;
  missing_start_endpoint_count: number;
  missing_end_endpoint_count: number;
  missing_notes_count: number;
}): string {
  return [
    `缺少管號： ${quality.missing_pipe_number_count}`,
    `重複管號值： ${quality.duplicate_pipe_number_value_count}`,
    `缺少起點： ${quality.missing_start_endpoint_count}`,
    `缺少終點： ${quality.missing_end_endpoint_count}`,
    `缺少備註： ${quality.missing_notes_count}`,
  ].join(" · ");
}

const RODENT_REPORT_DETAIL_LABELS: [keyof RodentReportProperties, string][] = [
  ["report_id", "回報 ID"],
  ["source", "來源"],
  ["report_type", "回報類型"],
  ["reported_at", "回報時間"],
  ["location_precision", "位置精度"],
  ["review_status", "審核狀態"],
  ["municipal_status", "市府狀態"],
  ["action_status", "處理狀態"],
  ["data_class", "資料類別"],
  ["classification", "分類"],
];

const RODENT_REPORT_DISCLAIMER =
  "合成回報格式的測試資料。非經查證的觀測、盛行率、族群、移動或風險證據。";

// Keep the auxiliary button list bounded; every feature stays selectable on the map.
const RODENT_REPORT_LIST_LIMIT = 100;

const STUDY_AREA_LABELS: Record<string, string> = {
  taipei_synthetic_demo: "示意合成網路",
  taipei_osm_songshan: "松山 OSM 來源網路",
};

// Only metadata the API actually returns is shown; absent fields are stated as such.
const SIMULATION_PROVENANCE_FIELDS: [keyof SimulationPreview["provenance"], string][] = [
  ["source_type", "來源類型"],
  ["source_id", "來源 ID"],
  ["source_sha256", "內容 SHA-256"],
  ["source_url", "來源 URL"],
  ["source_crs", "坐標參考系統"],
  ["coverage", "範圍 / bbox"],
  ["network_type", "網路類型"],
  ["license", "授權條款"],
  ["attribution", "姓名標示"],
  ["resource_version", "資源版本"],
];

type DatePreset = "today" | "7d" | "30d" | "all";

const DATE_PRESETS: [DatePreset, string][] = [
  ["today", "今天"],
  ["7d", "近 7 天"],
  ["30d", "近 30 天"],
  ["all", "全部"],
];

const TAIPEI_TIME_ZONE = "Asia/Taipei";

// Formats an instant as the Asia/Taipei wall-clock value a datetime-local input expects.
function taipeiDateTimeValue(date: Date): string {
  const parts = new Intl.DateTimeFormat("en-CA", {
    timeZone: TAIPEI_TIME_ZONE,
    year: "numeric",
    month: "2-digit",
    day: "2-digit",
    hour: "2-digit",
    minute: "2-digit",
    hourCycle: "h23",
  }).formatToParts(date);
  const part = (type: Intl.DateTimeFormatPartTypes) =>
    parts.find((entry) => entry.type === type)?.value ?? "00";
  return `${part("year")}-${part("month")}-${part("day")}T${part("hour")}:${part("minute")}`;
}

// Inclusive Asia/Taipei wall-clock range for a preset; null clears the filter.
function presetRange(preset: DatePreset, now: Date): { from: string; to: string } | null {
  if (preset === "all") return null;
  const days = preset === "today" ? 1 : preset === "7d" ? 7 : 30;
  const wallClock = new Date(`${taipeiDateTimeValue(now)}:00Z`);
  const from = new Date(wallClock.getTime() - (days - 1) * 24 * 60 * 60 * 1000);
  return { from: `${taipeiDateTimeValue(from).slice(0, 10)}T00:00`, to: taipeiDateTimeValue(now) };
}

// Derived from the returned graph, not from observation: the API returns every model node (0 visit
// nodes included) and every model edge, so a BFS from the echoed origin is exact for that payload.
function reachabilityFromOrigin(
  preview: SimulationPreview,
): { total: number; reachable: number; unsampled: number } | null {
  const origin = preview.origin?.node_id;
  if (!origin) return null;
  const outgoing = new Map<string, string[]>();
  for (const edge of preview.edges) {
    const targets = outgoing.get(edge.source);
    if (targets) targets.push(edge.target);
    else outgoing.set(edge.source, [edge.target]);
  }
  const reachable = new Set([origin]);
  const queue = [origin];
  while (queue.length > 0) {
    for (const next of outgoing.get(queue.pop()!) ?? []) {
      if (!reachable.has(next)) {
        reachable.add(next);
        queue.push(next);
      }
    }
  }
  return {
    total: preview.nodes.length,
    reachable: reachable.size,
    unsampled: preview.nodes.filter((node) => reachable.has(node.id) && node.visits === 0).length,
  };
}

type TerminationReason = "completed" | "dead_end" | "no_eligible_transition";

const TERMINATION_REASON_LABELS: Record<Exclude<TerminationReason, "completed">, string> = {
  dead_end: "模型網路死路（無可用出邊）終止",
  no_eligible_transition: "模型步驟規則下無合格轉移終止",
};

// `terminated_early` alone merges structural dead ends with step-rule refusals, so the fallback
// wording must hold for both when an older API omits termination_reason.
function terminationLabel(reason: TerminationReason | null | undefined): string {
  return reason && reason !== "completed"
    ? TERMINATION_REASON_LABELS[reason]
    : "模型規則下無可用轉移而提前終止";
}

export function Dashboard() {
  const layersQuery = useQuery({ queryKey: ["layers"], queryFn: fetchLayers });
  const districtsQuery = useQuery({
    queryKey: ["administrative-districts"],
    queryFn: fetchAdministrativeDistricts,
  });
  const [viewportBbox, setViewportBbox] = useState<Bbox>(DEFAULT_STORMWATER_BBOX);
  const bboxTooBroad = isBboxTooBroad(viewportBbox);
  const stormwaterQuery = useQuery({
    queryKey: ["stormwater-pipelines", viewportBbox],
    queryFn: () => fetchStormwaterPipelines(viewportBbox),
    enabled: !bboxTooBroad,
  });
  const [rodentFrom, setRodentFrom] = useState("");
  const [rodentTo, setRodentTo] = useState("");
  const [datePreset, setDatePreset] = useState<DatePreset | null>(null);
  const rodentFromUtc = taipeiLocalToUtc(rodentFrom);
  const rodentToUtc = taipeiLocalToUtc(rodentTo);
  const rodentRangeInvalid = isReportedRangeInvalid(rodentFromUtc, rodentToUtc);
  const rodentQuery = useQuery({
    queryKey: ["rodent-reports", viewportBbox, rodentFromUtc, rodentToUtc],
    queryFn: () =>
      fetchRodentReports({
        bbox: viewportBbox,
        reportedFrom: rodentFromUtc,
        reportedTo: rodentToUtc,
      }),
    enabled: !bboxTooBroad && !rodentRangeInvalid,
  });
  const citizenAggregateQuery = useQuery({
    queryKey: ["citizen-report-aggregates", viewportBbox],
    queryFn: () => fetchCitizenReportAggregates({ bbox: viewportBbox }),
    enabled: !bboxTooBroad,
  });
  const [preview, setPreview] = useState<SimulationPreview | null>(null);
  // The pinned OSM extract is the default so simulated paths follow surveyed geometry;
  // the schematic graph stays an explicit choice.
  const [studyArea, setStudyArea] = useState("taipei_osm_songshan");
  const [outputMode, setOutputMode] = useState<"aggregate" | "trajectory">("aggregate");
  const [showSimulatedPaths, setShowSimulatedPaths] = useState(false);
  const [showNetworkReference, setShowNetworkReference] = useState(false);
  const [showBoundaries, setShowBoundaries] = useState(false);
  const [showStormwater, setShowStormwater] = useState(false);
  const [showRodentReports, setShowRodentReports] = useState(false);
  const [showCitizenAggregates, setShowCitizenAggregates] = useState(false);
  const [selectedDistrict, setSelectedDistrict] = useState<AdministrativeDistrictProperties | null>(
    null,
  );
  const [selectedSegment, setSelectedSegment] = useState<StormwaterProperties | null>(null);
  const [selectedReport, setSelectedReport] = useState<RodentReportProperties | null>(null);
  const [selectedTrajectoryId, setSelectedTrajectoryId] = useState<number | null>(null);
  const [duration, setDuration] = useState(12);
  const [seed, setSeed] = useState(42);
  const [walkers, setWalkers] = useState(24);
  const [originNodeId, setOriginNodeId] = useState<string | null>(null);
  const [activeStep, setActiveStep] = useState(0);
  const [isPlaying, setIsPlaying] = useState(false);
  const mutation = useMutation({
    mutationFn: requestPreview,
    onSuccess: (data) => {
      setPreview(data);
      setActiveStep(0);
      setIsPlaying(false);
    },
    onError: () => {
      // Never leave an earlier trajectory visible after a failed origin run.
      setPreview(null);
      setActiveStep(0);
      setIsPlaying(false);
      setSelectedTrajectoryId(null);
    },
  });
  const layers = layersQuery.data ?? DEFAULT_LAYERS;
  const districts = districtsQuery.data ?? null;
  const hasDistricts = (districts?.features.length ?? 0) > 0;
  const boundaryStatus = districtsQuery.isPending
    ? "邊界載入中…"
    : districtsQuery.isError
      ? "邊界服務無法使用"
      : hasDistricts
        ? "行政區參考 · UNVERIFIED（未驗證）"
        : "尚未匯入邊界";
  const stormwater = stormwaterQuery.data ?? null;
  const hasStormwater = stormwater?.data_state === "available";
  const selectedVisibleSegment =
    stormwaterQuery.isError || stormwater?.data_state !== "available"
      ? null
      : (stormwater.features.find(
          (feature) => feature.properties.segment_id === selectedSegment?.segment_id,
        )?.properties ?? null);
  const stormwaterStatus = bboxTooBroad
    ? "請放大以載入管線"
    : stormwaterQuery.isPending
      ? "管線載入中…"
      : stormwaterQuery.isError
        ? "雨水下水道服務無法使用"
        : stormwater?.data_state === "empty"
          ? "尚未匯入管線"
          : (stormwater?.feature_count ?? 0) === 0
            ? "目前視圖範圍內無管線"
            : stormwater?.truncated
              ? "僅顯示部分資料 · 請放大"
              : "基礎設施參考 · UNVERIFIED（未驗證）";
  const stormwaterContext = bboxTooBroad
    ? "雨水下水道請放大載入"
    : stormwaterQuery.isPending
      ? "雨水下水道載入中"
      : hasStormwater
        ? "雨水下水道參考資料"
        : stormwater?.data_state === "empty"
          ? "尚未匯入雨水下水道"
          : "雨水下水道狀態未知";
  const rodentReports = rodentQuery.data ?? null;
  // Drop cached data while the local UTC range is invalid so no stale points,
  // list, selection, or details remain on screen.
  const activeRodentReports = rodentRangeInvalid ? null : rodentReports;
  const hasRodentReports = activeRodentReports?.data_state === "available";
  const selectedVisibleReport =
    rodentQuery.isError || activeRodentReports?.data_state !== "available"
      ? null
      : (activeRodentReports.features.find(
          (feature) => feature.properties.report_id === selectedReport?.report_id,
        )?.properties ?? null);
  const rodentReportButtons = (activeRodentReports?.features ?? []).slice(
    0,
    RODENT_REPORT_LIST_LIMIT,
  );
  const rodentListTruncated =
    (activeRodentReports?.features.length ?? 0) > RODENT_REPORT_LIST_LIMIT;
  const rodentValidationMessage = rodentRangeInvalid
    ? "回報起時間必須早於或等於回報迄時間。"
    : null;
  const citizenAggregates = citizenAggregateQuery.data ?? null;
  const citizenAggregateCells = citizenAggregates?.features ?? [];
  const hasCitizenAggregates =
    citizenAggregates?.data_state === "available" && citizenAggregateCells.length > 0;
  // Cell counts are suppressed aggregates, so summing them is a floor on reported
  // volume, not a report total: every suppressed group is excluded.
  const citizenAggregateReportCount = citizenAggregateCells.reduce(
    (total, feature) => total + feature.properties.count,
    0,
  );
  const citizenAggregateMonths = [
    ...new Set(citizenAggregateCells.map((feature) => feature.properties.month)),
  ].sort();
  // Imported layers and synthetic preview output are separate groups: a
  // generated fixture is not a missing local dataset.
  const catalogLayers = layers.filter(
    (layer) => layer.id !== "stormwater_networks" && layer.id !== "simulated_paths",
  );
  const simulatedPathsLayer = layers.find((layer) => layer.id === "simulated_paths");
  const hasNetworkGeometry = Boolean(preview?.edges.some((edge) => edge.geometry));
  const trajectories = preview?.trajectories ?? [];
  const showingTrajectories = outputMode === "trajectory" && trajectories.length > 0;
  const reachability = preview ? reachabilityFromOrigin(preview) : null;
  // Server counts are authoritative when present; the BFS only supplies the unsampled count (and
  // stands in when an older API build omits `reachability`).
  const reachabilitySummary = preview
    ? {
        total: preview.reachability?.total_nodes ?? reachability?.total ?? 0,
        reachable: preview.reachability?.reachable_nodes ?? reachability?.reachable ?? 0,
        unsampled: reachability?.unsampled ?? 0,
        components: preview.reachability?.component_count ?? null,
      }
    : null;
  const terminatedTrajectories = trajectories.filter((trajectory) => trajectory.terminated_early);
  const terminationReasons = new Set(
    terminatedTrajectories.map((trajectory) => trajectory.termination_reason),
  );
  const sharedTerminationReason =
    terminatedTrajectories.length > 0 && terminationReasons.size === 1
      ? (terminatedTrajectories[0].termination_reason ?? null)
      : null;
  const catalogLayerAvailable = (layer: Layer) =>
    layer.available || (layer.id === "simulated_paths" && preview !== null);
  const availableCatalogLayers = catalogLayers.filter(catalogLayerAvailable);
  const unavailableCatalogLayers = catalogLayers.filter((layer) => !catalogLayerAvailable(layer));
  // The panel renders five built-in map rows (districts, network reference,
  // stormwater, rodent reports, citizen-report aggregates) plus every catalog
  // entry exactly once.
  const BUILT_IN_LAYER_ROW_COUNT = 5;
  const visibleLayerCount =
    BUILT_IN_LAYER_ROW_COUNT + catalogLayers.length + (simulatedPathsLayer ? 1 : 0);
  const unavailableDatasetSummary = unavailableCatalogLayers
    .map((layer) => LAYER_LABEL_OVERRIDES[layer.id] ?? "未命名資料圖層")
    .join("、");
  // Readouts distinguish "not loaded" from "cannot be determined": a failed
  // request is never rendered as a zero count or a zero-area dataset.
  const referenceLayerCount = (hasDistricts ? 1 : 0) + (hasStormwater ? 1 : 0);
  const referenceLayersKnown = ![districtsQuery, stormwaterQuery].some(
    (query) => query.isPending || query.isError,
  );
  const missingCatalogLabel = layersQuery.isError
    ? "無法判定"
    : layersQuery.isPending
      ? "查詢中"
      : String(unavailableCatalogLayers.length);
  // The map reports the loaded viewport bbox; the gauge shows it against the
  // same 0.30° bound the API enforces rather than implying data coverage.
  const viewportSpanDegrees = viewportBbox[2] - viewportBbox[0];
  const viewportGaugePercent = Math.min(100, (viewportSpanDegrees / BBOX_MAX_SPAN_DEGREES) * 100);
  const selectedVisibleTrajectory = trajectories.find(
    (trajectory) => trajectory.walker_id === selectedTrajectoryId,
  );
  // Eligible origins are nodes the last response returned: the analyst picks one of
  // them, never an arbitrary map coordinate.
  const originNodes = useMemo(
    () => (preview?.nodes ?? []).map((node) => ({ id: node.id, coordinates: node.coordinates })),
    [preview],
  );
  const origin = preview?.origin ?? null;
  const playbackTrajectory =
    trajectories.find((trajectory) => trajectory.walker_id === selectedTrajectoryId) ??
    trajectories[0] ??
    null;
  const playbackSteps = playbackTrajectory?.edges.length ?? 0;
  // A chosen node that differs from the last returned origin must read as pending,
  // not as if the previous run used it.
  const originLabel =
    originNodeId && originNodeId !== origin?.node_id
      ? `${originNodeId} · 已選擇，尚未以此外起點執行 · SIMULATED`
      : origin
        ? `${origin.node_id} · ${origin.coordinates[1].toFixed(5)}, ${origin.coordinates[0].toFixed(5)} · ${
            origin.selection === "user" ? "使用者選擇" : "預設固定起點"
          } · SIMULATED`
        : originNodeId
          ? `${originNodeId} · 已選擇，尚未以此外起點執行 · SIMULATED`
          : "尚未指定；執行後由 API 記錄起點";
  useEffect(() => {
    if (!isPlaying) return;
    if (activeStep >= playbackSteps) {
      // Playback is complete; this is a state-machine transition, not data synchronization.
      // eslint-disable-next-line react-hooks/set-state-in-effect
      setIsPlaying(false);
      return;
    }
    // Playback advances through already-returned edges; it is not elapsed time.
    const timer = setTimeout(() => {
      setActiveStep((step) => Math.min(playbackSteps, step + 1));
    }, 700);
    return () => clearTimeout(timer);
  }, [isPlaying, activeStep, playbackSteps]);
  const selectionSummary = selectedVisibleReport
    ? `回報 ${selectedVisibleReport.report_id} · ${selectedVisibleReport.reported_at} · RODENT_REPORT · SIMULATED`
    : selectedVisibleSegment
      ? `管線 ${selectedVisibleSegment.pipe_number || selectedVisibleSegment.segment_id} · UNVERIFIED（未驗證）`
      : selectedVisibleTrajectory
        ? `模擬軌跡 #${selectedVisibleTrajectory.walker_id} · ${selectedVisibleTrajectory.edges.length} 段 · SIMULATED（合成代理，非動物）`
        : selectedDistrict
          ? `${selectedDistrict.district_name} · UNVERIFIED（未驗證）`
          : "尚未選取圖徵。從地圖或右側清單選取後，摘要顯示於此；詳細屬性保留在右側面板。";
  const applyDatePreset = (preset: DatePreset) => {
    const range = presetRange(preset, new Date());
    setRodentFrom(range?.from ?? "");
    setRodentTo(range?.to ?? "");
    setDatePreset(range ? preset : null);
  };

  const renderCatalogLayer = (layer: Layer) => {
    const available = catalogLayerAvailable(layer);
    const simulatedPaths = layer.id === "simulated_paths";
    const label = LAYER_LABEL_OVERRIDES[layer.id] ?? "未命名資料圖層";
    return (
      <label className={`layer-row ${available ? "" : "is-unavailable"}`} key={layer.id}>
        <LayerGlyph layerId={layer.id} />
        <span className="layer-name">
          {label}
          <small>
            {simulatedPaths
              ? `SIMULATED · 合成測試資料${available ? "" : "；請執行預覽以產生"}`
              : available
                ? (CLASSIFICATION_LABELS[layer.classification ?? ""] ?? "可用")
                : (LAYER_UNAVAILABLE_MESSAGES[layer.id] ?? DEFAULT_UNAVAILABLE_MESSAGE)}
          </small>
        </span>
        {simulatedPaths && available ? (
          <input
            type="checkbox"
            aria-label={label}
            checked={showSimulatedPaths}
            onChange={(event) => setShowSimulatedPaths(event.target.checked)}
          />
        ) : (
          // Catalog entries have no map visibility control, so state it instead
          // of offering a permanently dead checkbox.
          <span className="layer-status">{available ? "可用" : "未載入"}</span>
        )}
      </label>
    );
  };

  const rodentStatus = rodentValidationMessage
    ? "時間範圍無效"
    : bboxTooBroad
      ? "請放大以載入回報"
      : rodentQuery.isPending
        ? "回報載入中…"
        : rodentQuery.isError
          ? "鼠類回報服務無法使用"
          : rodentReports?.data_state === "empty"
            ? "尚未匯入回報"
            : (rodentReports?.feature_count ?? 0) === 0
              ? "篩選條件內無回報"
              : rodentReports?.truncated
                ? "回傳資料已截斷"
                : "RODENT_REPORT · SIMULATED（模擬）";

  const citizenAggregateStatus = bboxTooBroad
    ? "請放大以載入彙整"
    : citizenAggregateQuery.isPending
      ? "彙整載入中…"
      : citizenAggregateQuery.isError
        ? "公民通報彙整服務無法使用"
        : citizenAggregates?.data_state === "empty"
          ? "尚未匯入公民通報彙整"
          : "CITIZEN_REPORT_AGGREGATE · UNVERIFIED（未驗證）";

  return (
    <main className="dashboard-shell">
      <header className="topbar">
        <div className="brand-lockup">
          <div className="brand-mark" aria-hidden="true">
            見
          </div>
          <div>
            <h1>見光鼠</h1>
            <p>RatSight · 都市鼠類移動分析</p>
          </div>
        </div>
        <div className="header-status">
          <span className="status-dot" /> 研究工作區 <span className="status-divider">/</span>{" "}
          臺北市
        </div>
      </header>

      <div className="workspace-heading">
        <div>
          <h2>移動分析工作區</h2>
          <p className="form-meta">表號 RS-001 · 版次 1 · 合成預覽</p>
          <p className="workspace-intro">
            目前尚未載入已查證的鼠類觀測資料。可查看圖層狀態或執行合成預覽；模擬結果不代表真實移動、風險或熱區。
          </p>
        </div>
        <span className="notice-chip">尚未載入真實觀測資料</span>
      </div>

      <section className="hud" aria-label="目前狀態讀數">
        <div className="hud-tag">
          <span className="hud-tag-label">狀態讀數</span>
          <span className="hud-live">
            <i aria-hidden="true" />
            版本化 API
          </span>
        </div>
        <div className="hud-stats">
          <div className="hud-cell">
            <span className="hud-label">參考圖層</span>
            <span className="hud-value">
              {referenceLayersKnown ? `${referenceLayerCount} / 2` : "無法判定"}
            </span>
            <span className="hud-meter" aria-hidden="true">
              <i className={referenceLayerCount > 0 ? "is-lit" : undefined} />
              <i className={referenceLayerCount > 1 ? "is-lit" : undefined} />
            </span>
          </div>
          <div className="hud-cell">
            <span className="hud-label">合成輸出</span>
            <span className="hud-value">
              {mutation.isPending ? "執行中" : preview ? "已產生" : "未產生"}
            </span>
            <span className="hud-meter" aria-hidden="true">
              <i className={preview ? "is-lit" : undefined} />
            </span>
          </div>
          <div className="hud-cell">
            <span className="hud-label">目錄未載入</span>
            <span className="hud-value">{missingCatalogLabel}</span>
            <span className="hud-meter is-alert" aria-hidden="true">
              <i
                className={
                  !layersQuery.isError && unavailableCatalogLayers.length > 0 ? "is-lit" : undefined
                }
              />
            </span>
          </div>
        </div>
      </section>

      <div className="workspace-grid">
        <section className="map-column" aria-label="空間工作區">
          <div className="map-toolbar">
            <div>
              <strong>空間脈絡</strong>
              <span>底圖 · 參考邊界 · {stormwaterContext} · 無鼠類觀測資料</span>
            </div>
            <span className="map-coordinate">25.033° N · 121.565° E</span>
          </div>
          <MapView
            preview={preview}
            showSimulatedPaths={showSimulatedPaths}
            showNetworkReference={showNetworkReference}
            outputMode={outputMode}
            boundaries={districts}
            showBoundaries={showBoundaries}
            selectedDistrictId={selectedDistrict?.district_id ?? null}
            onSelectDistrict={setSelectedDistrict}
            stormwater={stormwater}
            showStormwater={showStormwater}
            selectedSegmentId={selectedVisibleSegment?.segment_id ?? null}
            onSelectSegment={setSelectedSegment}
            rodentReports={activeRodentReports}
            showRodentReports={showRodentReports}
            selectedReportId={selectedVisibleReport?.report_id ?? null}
            onSelectReport={setSelectedReport}
            citizenAggregates={citizenAggregates}
            showCitizenAggregates={showCitizenAggregates}
            onSelectTrajectory={setSelectedTrajectoryId}
            activeStep={showingTrajectories ? activeStep : null}
            selectedTrajectoryId={playbackTrajectory?.walker_id ?? null}
            originNodes={originNodes}
            selectedOriginNodeId={originNodeId}
            onSelectOriginNode={setOriginNodeId}
            onBoundsChange={setViewportBbox}
          />
          <div className="map-legend">
            <span className="legend-item">
              <i className="legend-basemap" /> 底圖
            </span>
            <span className="legend-item">
              <i className="legend-administrative" /> 行政區參考
            </span>
            <span className="legend-item">
              <i className="legend-stormwater" /> 雨水下水道（參考）
            </span>
            <span className="legend-item">
              <i className="legend-rodent-reports" /> 鼠類回報（SIMULATED · 模擬）
            </span>
            <span className="legend-item">
              <i className="legend-citizen-aggregate" /> 公民通報彙整（250 公尺網格）
            </span>
            <span className="legend-item">
              <i className="legend-simulated" /> 模擬 · 合成測試資料
            </span>
            <span className="legend-item">
              <i className="legend-schematic" /> 示意網路 · 直線連接（非路網）
            </span>
          </div>
          {preview?.parameters.study_area === "taipei_synthetic_demo" && (
            <p className="map-note">
              示意拓撲：此示範網路以節點間直線（虛線）連接，不是街道或路網幾何；僅供流程示範，不得判讀為可行路徑或實際移動。
            </p>
          )}
          <div className={`view-gauge ${bboxTooBroad ? "is-over" : ""}`}>
            <span className="view-gauge-label">視圖寬度</span>
            <span className="view-gauge-track" aria-hidden="true">
              <i style={{ width: `${viewportGaugePercent}%` }} />
            </span>
            <span className="view-gauge-value">{viewportSpanDegrees.toFixed(3)}°</span>
            <span className="view-gauge-hint">上限 {BBOX_MAX_SPAN_DEGREES.toFixed(2)}°</span>
          </div>
          <div className="map-selection" aria-live="polite">
            <strong>目前選取</strong>
            <span>{selectionSummary}</span>
          </div>
          <div className="data-boundary">
            <strong>資料界線</strong>
            <span>
              地圖中心僅為導覽起點。RODENT_REPORT · SIMULATED 回報與 SIMULATED
              路徑分開呈現；兩者同圖不代表驗證、因果或同一動物。真實/已查證鼠類觀測資料尚未載入。
            </span>
          </div>
        </section>

        <aside className="control-rail" aria-label="分析控制項">
          <nav className="rail-index" aria-label="章節索引">
            <a href="#panel-status">01 狀態</a>
            <a href="#panel-layers">02 圖層</a>
            <a href="#panel-simulation">03 模擬</a>
            <a href="#panel-reference">04 行政區</a>
            <a href="#panel-stormwater">05 下水道</a>
            <a href="#panel-rodent">06 回報</a>
          </nav>
          <section className="panel orientation-panel" id="panel-status" aria-label="工作區狀態">
            <div className="panel-heading">
              <div>
                <h3>工作區狀態</h3>
              </div>
              <span className="classification-badge">ORIENTATION · 導引</span>
            </div>
            <p className="reference-note">
              此工作區用來說明臺北市鼠類相關資料是否存在、屬於哪一個證據等級，以及可以與不可以回答哪些問題。目前沒有已查證的鼠類觀測資料。
            </p>
            <div className="orientation-grid">
              <div>
                <p className="reference-label">已載入的參考資料</p>
                <ul className="orientation-list">
                  <li>行政區邊界 · UNVERIFIED（未驗證）{hasDistricts ? "" : " · 尚未匯入"}</li>
                  <li>雨水下水道管線 · UNVERIFIED（未驗證）{hasStormwater ? "" : " · 尚未匯入"}</li>
                </ul>
              </div>
              <div>
                <p className="reference-label">合成測試資料</p>
                <ul className="orientation-list">
                  <li>鼠類回報格式測試資料 · RODENT_REPORT · SIMULATED</li>
                  <li>移動模擬輸出 · SIMULATED · 未校準</li>
                </ul>
              </div>
            </div>
            <p className="inline-note">
              {layersQuery.isError
                ? "圖層目錄無法使用：目前無法判定哪些資料集已載入或尚未載入。"
                : unavailableDatasetSummary
                  ? `尚未載入：${unavailableDatasetSummary}。`
                  : "目錄中的資料集皆已載入或已合成產生。"}
            </p>
            <div className="orientation-answers">
              <div>
                <p className="reference-label">目前可回答</p>
                <ul className="orientation-list">
                  <li>哪些圖層已載入、哪些尚未載入</li>
                  <li>行政區與雨水下水道的來源、版本與授權</li>
                  <li>合成模擬在既定參數下的合成造訪次數</li>
                </ul>
              </div>
              <div>
                <p className="reference-label">目前無法回答</p>
                <ul className="orientation-list">
                  <li>臺北市鼠類數量、盛行率、分布或風險</li>
                  <li>真實移動路徑、熱區或介入效果</li>
                  <li>模擬結果的準確度或不確定性</li>
                </ul>
              </div>
            </div>
            <p className="reference-note">
              未載入的資料集由專案負責人依{" "}
              <a
                href={`${INFRASTRUCTURE_GUIDES_URL}/data-sources.md`}
                target="_blank"
                rel="noopener noreferrer"
              >
                資料來源與匯入說明
              </a>{" "}
              整備；瀏覽器不提供匯入操作，未載入也不代表數量為零。
            </p>
          </section>

          <section className="panel layer-panel" id="panel-layers">
            <div className="panel-heading">
              <div>
                <h3>圖層</h3>
              </div>
              <span className="panel-count" aria-label={`已顯示 ${visibleLayerCount} 個圖層列`}>
                {visibleLayerCount}
              </span>
            </div>
            <div className="layer-list">
              <label className={`layer-row ${hasDistricts ? "" : "is-unavailable"}`}>
                <LayerGlyph layerId="administrative_boundaries" />
                <span className="layer-name">
                  行政區
                  <small>{boundaryStatus}</small>
                </span>
                <input
                  type="checkbox"
                  aria-label="行政區"
                  disabled={!hasDistricts}
                  checked={showBoundaries}
                  onChange={(event) => setShowBoundaries(event.target.checked)}
                />
              </label>
              <label className={`layer-row ${hasStormwater ? "" : "is-unavailable"}`}>
                <LayerGlyph layerId="stormwater" />
                <span className="layer-name">
                  雨水下水道管線
                  <small>{stormwaterStatus}</small>
                </span>
                <input
                  type="checkbox"
                  aria-label="雨水下水道管線"
                  disabled={!hasStormwater}
                  checked={showStormwater}
                  onChange={(event) => setShowStormwater(event.target.checked)}
                />
              </label>
              <label className={`layer-row ${hasNetworkGeometry ? "" : "is-unavailable"}`}>
                <LayerGlyph layerId="network-reference" />
                <span className="layer-name">
                  網路／來源參考
                  <small>
                    {hasNetworkGeometry
                      ? "SOURCE NETWORK · 幾何由 API 提供"
                      : "預覽未提供來源網路幾何"}
                  </small>
                </span>
                <input
                  type="checkbox"
                  aria-label="網路／來源參考"
                  disabled={!hasNetworkGeometry}
                  checked={showNetworkReference}
                  onChange={(event) => setShowNetworkReference(event.target.checked)}
                />
              </label>
              <label className={`layer-row ${hasRodentReports ? "" : "is-unavailable"}`}>
                <LayerGlyph layerId="rodent-reports" />
                <span className="layer-name">
                  鼠類回報
                  <small>{rodentStatus}</small>
                </span>
                <input
                  type="checkbox"
                  aria-label="鼠類回報"
                  disabled={!hasRodentReports}
                  checked={showRodentReports}
                  onChange={(event) => setShowRodentReports(event.target.checked)}
                />
              </label>
              <label className={`layer-row ${hasCitizenAggregates ? "" : "is-unavailable"}`}>
                <LayerGlyph layerId="citizen-aggregates" />
                <span className="layer-name">
                  公民通報彙整
                  <small>{citizenAggregateStatus}</small>
                </span>
                <input
                  type="checkbox"
                  aria-label="公民通報彙整"
                  disabled={!hasCitizenAggregates}
                  checked={showCitizenAggregates}
                  onChange={(event) => setShowCitizenAggregates(event.target.checked)}
                />
              </label>
              {availableCatalogLayers.map(renderCatalogLayer)}
            </div>
            {simulatedPathsLayer && (
              <div className="synthetic-layer-group">
                <p className="reference-label">合成模擬</p>
                <div className="layer-list">{renderCatalogLayer(simulatedPathsLayer)}</div>
              </div>
            )}
            {unavailableCatalogLayers.length > 0 && (
              <div className="unavailable-layer-group">
                <p className="reference-label">
                  {layersQuery.isError ? "圖層目錄無法使用" : "此版本尚未載入"}
                </p>
                <p className="inline-note">
                  {layersQuery.isError ? (
                    "圖層目錄無法使用。請在 API 啟動後重試；不得推論任何圖層可用性。"
                  ) : (
                    <>
                      這些規劃中的圖層尚未記錄核准的資料來源或匯入程式。請專案負責人依{" "}
                      <a
                        href={`${INFRASTRUCTURE_GUIDES_URL}/data-sources.md`}
                        target="_blank"
                        rel="noopener noreferrer"
                      >
                        資料來源整備指南
                      </a>{" "}
                      檢視擁有權、存取權、授權條款與可用性。瀏覽器不提供匯入操作。
                    </>
                  )}
                </p>
                <div className="layer-list">{unavailableCatalogLayers.map(renderCatalogLayer)}</div>
              </div>
            )}
          </section>

          <section
            className="panel simulation-panel"
            id="panel-simulation"
            aria-label="合成模擬示範"
          >
            <div className="panel-heading">
              <div>
                <h3>合成模擬示範</h3>
              </div>
              <span className="classification-badge">SIMULATED · 模擬</span>
            </div>
            <p className="reference-note">
              合成預覽 — 僅為模擬測試資料；不含真實觀測或行政調查結果。SIMULATED · schematic/source
              network · 未校準（uncalibrated）。不代表觀察到的動物移動，也不是風險熱圖（not a risk
              heatmap）。
            </p>
            <Button
              className="run-button"
              disabled={mutation.isPending || duration < 1 || walkers < 1 || seed < 0}
              onClick={() =>
                mutation.mutate({
                  study_area: studyArea,
                  duration_steps: duration,
                  walkers,
                  random_seed: seed,
                  movement_model: "weighted_random_walk",
                  intervention_scenario: "baseline",
                  origin_node_id: originNodeId ?? undefined,
                })
              }
            >
              {mutation.isPending ? "模擬執行中…" : "開始模擬"}
            </Button>
            <p className="inline-note">
              預設示範參數：{STUDY_AREA_LABELS[studyArea]} · {duration} 步 · 種子 {seed} · {walkers}{" "}
              個合成代理 · 邊造訪摘要。代理是無單位假設性單元，不是老鼠或任何動物的數量。
            </p>
            {mutation.isError && (
              <p className="error-note" role="alert">
                {mutation.error instanceof Error
                  ? mutation.error.message
                  : "預覽無法使用。請確認 API 正在執行後重試。"}
                {isSourceNetworkUnavailable(mutation.error)
                  ? " 系統未以示意網路替代 OSM 結果；若要使用示意網路，請明確改選「臺北 · 示意合成網路」後重新執行。"
                  : ""}
              </p>
            )}
            {mutation.isSuccess && (
              <p className="success-note" role="status">
                可重現執行完成 · 種子 {preview?.parameters.random_seed}
              </p>
            )}
            {mutation.isSuccess && (
              <span className="stamp is-stamped" aria-hidden="true">
                SIMULATED
              </span>
            )}
            <details className="advanced-settings">
              <summary>
                進階設定 · {STUDY_AREA_LABELS[studyArea]} · {duration} 步 · 種子 {seed} · {walkers}{" "}
                個合成代理
              </summary>
              <div className="form-field">
                <label htmlFor="study-area">研究範圍</label>
                <select
                  id="study-area"
                  value={studyArea}
                  onChange={(event) => {
                    setStudyArea(event.target.value);
                    // Origin node ids belong to one study area; a carried-over id would be rejected.
                    setOriginNodeId(null);
                  }}
                >
                  <option value="taipei_synthetic_demo">臺北 · 示意合成網路</option>
                  <option value="taipei_osm_songshan">臺北松山 · OSM 來源網路</option>
                </select>
                <small>
                  預設使用 bounded OSM surface
                  extract；來源未佈建時明確回報無法使用，不會自動改用示意網路。僅作空間模擬假設，不代表老鼠實際移動。
                </small>
              </div>
              <div className="form-field">
                <label htmlFor="duration">模擬長度 · 步數</label>
                <input
                  id="duration"
                  type="number"
                  min={1}
                  max={100}
                  value={duration}
                  onChange={(event) => setDuration(Number(event.target.value))}
                />
              </div>
              <div className="field-pair">
                <div className="form-field">
                  <label htmlFor="seed">隨機種子</label>
                  <input
                    id="seed"
                    type="number"
                    min={0}
                    value={seed}
                    onChange={(event) => setSeed(Number(event.target.value))}
                  />
                </div>
                <div className="form-field">
                  <label htmlFor="walkers">合成代理數</label>
                  <input
                    id="walkers"
                    type="number"
                    min={1}
                    max={1000}
                    value={walkers}
                    onChange={(event) => setWalkers(Number(event.target.value))}
                  />
                </div>
              </div>
              <div className="form-field">
                <label htmlFor="origin-node">合成起點節點</label>
                <select
                  id="origin-node"
                  value={originNodeId ?? ""}
                  disabled={!originNodes.length}
                  onChange={(event) => setOriginNodeId(event.target.value || null)}
                >
                  <option value="">API 預設固定起點</option>
                  {originNodes.map((node) => (
                    <option key={node.id} value={node.id}>
                      {node.id} · {node.coordinates[1].toFixed(5)}, {node.coordinates[0].toFixed(5)}
                    </option>
                  ))}
                </select>
                <small>
                  {originNodes.length
                    ? "僅能選擇上次結果回傳的網路節點，或直接在地圖上點選節點；座標不會被自動吸附成最近的節點。"
                    : "先執行一次模擬，取得可選的網路節點清單。"}
                </small>
              </div>
              <div className="form-field">
                <label htmlFor="output-mode">輸出模式</label>
                <select
                  id="output-mode"
                  value={outputMode}
                  disabled={!preview?.trajectories?.length}
                  onChange={(event) => {
                    const mode = event.target.value as "aggregate" | "trajectory";
                    setOutputMode(mode);
                    // Trajectories live on the simulated-paths layer; without this the map shows nothing.
                    if (mode === "trajectory") setShowSimulatedPaths(true);
                  }}
                >
                  <option value="aggregate">Aggregate · 邊造訪摘要</option>
                  <option value="trajectory">Trajectory · 個別軌跡</option>
                </select>
                <small>
                  {preview?.trajectory_truncated
                    ? `API 回傳 ${preview.trajectory_count ?? "多個"} 條軌跡；目前僅繪製前 100 條。`
                    : preview?.trajectories?.length
                      ? `API 已提供軌跡；仍標示為 SIMULATED。${
                          terminatedTrajectories.length
                        } 條${terminationLabel(sharedTerminationReason)}；不代表抵達或真實移動。`
                      : "API 未提供軌跡欄位，僅顯示 aggregate。"}
                </small>
              </div>
              <div className="form-field">
                <label htmlFor="model">移動模型</label>
                <select id="model" value="weighted_random_walk" disabled>
                  <option value="weighted_random_walk">加權隨機漫步 · 示範</option>
                </select>
              </div>
              <div className="form-field">
                <label htmlFor="scenario">介入情境</label>
                <select id="scenario" value="baseline" disabled>
                  <option value="baseline">基準情境 · 無介入</option>
                </select>
              </div>
            </details>
            <div className="analysis-row">
              <span>合成起點</span>
              <strong>{originLabel}</strong>
            </div>
            <div className="analysis-row">
              <span>模型網路邊</span>
              <strong>{preview ? `${preview.edges.length} 條模型邊` : "尚未建模"}</strong>
            </div>
            <div className="analysis-row">
              <span>可達節點</span>
              <strong>
                {reachabilitySummary
                  ? `${reachabilitySummary.reachable} / ${reachabilitySummary.total} 個模型節點`
                  : "尚未建模"}
              </strong>
            </div>
            {reachabilitySummary ? (
              <p className="inline-note" aria-live="polite">
                可達性由 API 回傳的模型節點與邊計算（SIMULATED，非觀測或調查）：目前起點下{" "}
                {reachabilitySummary.total - reachabilitySummary.reachable} 個節點不可達、
                未被取樣，{reachabilitySummary.unsampled} 個可達節點也未被取樣。
                {reachabilitySummary.components !== null && reachabilitySummary.components > 1
                  ? ` 模型網路有 ${reachabilitySummary.components} 個互不相連的分量，部分節點在任何單一起點下都不可達。`
                  : ""}
                未取樣或不可達不代表沒有動物、沒有活動，也不代表沒有風險。
              </p>
            ) : null}
            <div className="analysis-row">
              <span>風險估計</span>
              <strong>不提供（本模型不估計風險）</strong>
            </div>
            <div className="analysis-row">
              <span>模型不確定性</span>
              <strong>尚未量化</strong>
            </div>
            <p className="reference-note">
              未估計不確定性；請勿推論盛行率、移動、風險、熱區、完整性或介入效果。
            </p>
            {preview ? (
              <div className="simulation-result" aria-live="polite">
                <div className="result-summary" aria-label="模擬摘要">
                  {showingTrajectories ? (
                    <>
                      <span>{trajectories.length} 條合成軌跡（SIMULATED）</span>
                      <span>·</span>
                      <span>
                        {preview.model_id} v{preview.model_version}
                      </span>
                    </>
                  ) : (
                    <>
                      <span>
                        {preview.nodes.reduce((sum, node) => sum + node.visits, 0)}{" "}
                        次無單位、假設性的節點造訪（非動物數量、非盛行率、非遷移）
                      </span>
                      <span>·</span>
                      <span>
                        {preview.model_id} v{preview.model_version}
                      </span>
                    </>
                  )}
                </div>
                {showingTrajectories && (
                  <div className="playback-block">
                    <div className="playback-row">
                      <label htmlFor="playback-trajectory">合成軌跡</label>
                      <select
                        id="playback-trajectory"
                        value={playbackTrajectory?.walker_id ?? ""}
                        onChange={(event) => {
                          setSelectedTrajectoryId(Number(event.target.value));
                          setActiveStep(0);
                          setIsPlaying(false);
                        }}
                      >
                        {trajectories.map((trajectory) => (
                          <option key={trajectory.walker_id} value={trajectory.walker_id}>
                            #{trajectory.walker_id} · {trajectory.edges.length} 段
                            {trajectory.terminated_early
                              ? ` · ${terminationLabel(trajectory.termination_reason)}`
                              : ""}
                          </option>
                        ))}
                      </select>
                    </div>
                    <div className="playback-row" role="group" aria-label="步驟播放">
                      <button
                        type="button"
                        className="preset-button"
                        onClick={() => {
                          setIsPlaying(false);
                          setActiveStep(0);
                        }}
                        disabled={activeStep === 0 && !isPlaying}
                      >
                        重設
                      </button>
                      <button
                        type="button"
                        className="preset-button"
                        onClick={() => {
                          setIsPlaying(false);
                          setActiveStep((step) => Math.max(0, step - 1));
                        }}
                        disabled={activeStep === 0}
                      >
                        上一步
                      </button>
                      <button
                        type="button"
                        className="preset-button"
                        aria-pressed={isPlaying}
                        onClick={() => {
                          if (!isPlaying && activeStep >= playbackSteps) setActiveStep(0);
                          setIsPlaying(!isPlaying);
                        }}
                        disabled={playbackSteps === 0}
                      >
                        {isPlaying ? "暫停" : "播放"}
                      </button>
                      <button
                        type="button"
                        className="preset-button"
                        onClick={() => {
                          setIsPlaying(false);
                          setActiveStep((step) => Math.min(playbackSteps, step + 1));
                        }}
                        disabled={activeStep >= playbackSteps}
                      >
                        下一步
                      </button>
                      <span className="playback-step" aria-live="polite">
                        步驟 {activeStep} / {playbackSteps}
                      </span>
                    </div>
                    <ol className="playback-steps" aria-label="目前軌跡步驟">
                      {(playbackTrajectory?.edges ?? []).map((edge, index) => {
                        const stepNumber = index + 1;
                        const isCurrent = stepNumber === activeStep;
                        return (
                          <li key={`${edge.edge_id}-${index}`}>
                            <button
                              type="button"
                              className={`playback-step-button${isCurrent ? " is-selected" : ""}`}
                              aria-current={isCurrent ? "step" : undefined}
                              onClick={() => {
                                setIsPlaying(false);
                                setActiveStep(stepNumber);
                              }}
                            >
                              步驟 {stepNumber}
                              {edge.step_index !== undefined
                                ? `（step_index ${edge.step_index}）`
                                : ""}{" "}
                              · {edge.edge_id} · {edge.source} → {edge.target}
                            </button>
                          </li>
                        );
                      })}
                    </ol>
                    <p className="inline-note" aria-live="polite">
                      步驟 0 為起點；只顯示已回傳的合成邊幾何累積到第 {activeStep}{" "}
                      步。這不是經過時間、速度或動物移動；地圖繪製於「模擬移動路徑」圖層，當前步驟以紅色標示。
                      {preview.trajectory_truncated
                        ? ` API 回傳 ${preview.trajectory_count ?? "多個"} 條，僅提供前 ${trajectories.length} 條可播放。`
                        : ""}
                      {playbackTrajectory?.terminated_early
                        ? ` 此合成代理${terminationLabel(
                            playbackTrajectory.termination_reason,
                          )}：那是圖論或模型規則的終止原因，不代表抵達目的地或真實移動，也不代表該處沒有動物。`
                        : ""}
                    </p>
                  </div>
                )}
                <details className="provenance-details">
                  <summary>模擬來源與版本</summary>
                  <div className="provenance-block">
                    {SIMULATION_PROVENANCE_FIELDS.map(([key, label]) => {
                      const value = preview.provenance[key];
                      return (
                        <Fragment key={key}>
                          <span>{label}</span>
                          {key === "source_url" &&
                          typeof value === "string" &&
                          isSafeExternalUrl(value) ? (
                            <a href={value} target="_blank" rel="noopener noreferrer">
                              {value}
                            </a>
                          ) : (
                            <strong>{value || "未提供"}</strong>
                          )}
                        </Fragment>
                      );
                    })}
                    <span>來源說明</span>
                    <strong>{preview.provenance.note}</strong>
                    <small>模擬路徑不是觀察到的動物遷移路線。</small>
                  </div>
                </details>
              </div>
            ) : (
              <p className="inline-note" aria-live="polite">
                尚未執行模擬。結果只會是合成造訪摘要，不含真實觀測。
              </p>
            )}
          </section>
          <section
            className="panel reference-panel"
            id="panel-reference"
            aria-label="行政區參考檢視"
          >
            <div className="panel-heading">
              <div>
                <h3>行政區檢視</h3>
              </div>
              <span className="classification-badge">UNVERIFIED · 未驗證</span>
            </div>
            {hasDistricts && districts ? (
              <>
                <p className="reference-label" id="district-list-label">
                  行政區 · 選取以檢視
                </p>
                <ul className="district-list" aria-labelledby="district-list-label">
                  {districts.features.map((feature) => {
                    const selected =
                      selectedDistrict?.district_id === feature.properties.district_id;
                    return (
                      <li key={feature.properties.district_id}>
                        <button
                          type="button"
                          className={`district-button ${selected ? "is-selected" : ""}`}
                          aria-pressed={selected}
                          onClick={() => setSelectedDistrict(feature.properties)}
                        >
                          {feature.properties.district_name}
                        </button>
                      </li>
                    );
                  })}
                </ul>
                {selectedDistrict ? (
                  <div className="reference-details" aria-live="polite">
                    <div className="analysis-row">
                      <span>行政區</span>
                      <strong>{selectedDistrict.district_name}</strong>
                    </div>
                    <div className="analysis-row">
                      <span>行政區 ID</span>
                      <strong>{selectedDistrict.district_id}</strong>
                    </div>
                    <div className="analysis-row">
                      <span>資料類別</span>
                      <strong>{selectedDistrict.data_class}</strong>
                    </div>
                    <div className="analysis-row">
                      <span>分類</span>
                      <strong>
                        {CLASSIFICATION_LABELS[selectedDistrict.classification] ??
                          selectedDistrict.classification}
                      </strong>
                    </div>
                    <div className="analysis-row">
                      <span>資料集</span>
                      <strong>{selectedDistrict.dataset_id || "未知"}</strong>
                    </div>
                    <div className="analysis-row">
                      <span>資源版本</span>
                      <strong>{selectedDistrict.resource_version || "未知"}</strong>
                    </div>
                  </div>
                ) : (
                  <p className="inline-note" aria-live="polite">
                    從清單或地圖選取行政區，以檢視名稱與來源。
                  </p>
                )}
              </>
            ) : (
              <>
                <p className="inline-note" aria-live="polite">
                  {boundaryStatus}
                </p>
                {boundaryStatus === "尚未匯入邊界" && (
                  <p className="reference-note">
                    僅限維運人員設定 · 授權本地封存檔，不進行即時下載：{" "}
                    <a
                      href={`${INFRASTRUCTURE_GUIDES_URL}/administrative-boundaries-import.md`}
                      target="_blank"
                      rel="noopener noreferrer"
                    >
                      行政區邊界匯入指南
                    </a>
                    .
                  </p>
                )}
              </>
            )}
            <p className="reference-note">
              行政區參考幾何圖形。非鼠類觀測、非推論連結性，亦非模擬移動。
            </p>
            {districts?.provenance && (
              <details className="provenance-details">
                <summary>行政區來源、授權與現勢性</summary>
                <div className="provenance-block" aria-label="行政區來源出處">
                  <span>來源 URL</span>
                  {isSafeExternalUrl(districts.provenance.source_url) ? (
                    <a
                      href={districts.provenance.source_url}
                      target="_blank"
                      rel="noopener noreferrer"
                    >
                      {districts.provenance.source_url}
                    </a>
                  ) : (
                    <strong>{districts.provenance.source_url}</strong>
                  )}
                  <span>姓名標示</span>
                  <strong>{districts.provenance.attribution}</strong>
                  <span>授權條款</span>
                  <strong>{districts.provenance.license}</strong>
                  <span>現勢性</span>
                  <strong>{districts.provenance.uncertainty.currentness}</strong>
                </div>
              </details>
            )}
          </section>

          <section
            className="panel stormwater-panel"
            id="panel-stormwater"
            aria-label="雨水下水道管線檢視"
          >
            <div className="panel-heading">
              <div>
                <h3>雨水下水道管線</h3>
              </div>
              <span className="classification-badge">UNVERIFIED · 未驗證</span>
            </div>
            {hasStormwater ? (
              <>
                <p className="reference-label">{stormwaterStatus}</p>
                <p className="inline-note">
                  目前視窗範圍內回傳 {stormwater?.features.length ?? 0} 條管線。
                  {stormwater?.truncated
                    ? " 已達回傳上限：除這些回傳圖徵外仍有符合條件的管線，且不宣稱精確總數。"
                    : ""}
                </p>
                <p className="reference-label" id="segment-list-label">
                  管線 · 選取以檢視
                </p>
                <ul className="district-list" aria-labelledby="segment-list-label">
                  {stormwater?.features.slice(0, MAX_VISIBLE_PIPELINE_LIST_ITEMS).map((feature) => {
                    const selected =
                      selectedVisibleSegment?.segment_id === feature.properties.segment_id;
                    return (
                      <li key={feature.properties.segment_id}>
                        <button
                          type="button"
                          className={`district-button ${selected ? "is-selected" : ""}`}
                          aria-pressed={selected}
                          aria-label={feature.properties.segment_id}
                          onClick={() => setSelectedSegment(feature.properties)}
                        >
                          {feature.properties.pipe_number || feature.properties.segment_id}
                        </button>
                      </li>
                    );
                  })}
                </ul>
                {(stormwater?.features.length ?? 0) > MAX_VISIBLE_PIPELINE_LIST_ITEMS && (
                  <p className="inline-note">
                    僅顯示前 {MAX_VISIBLE_PIPELINE_LIST_ITEMS} 條管線；其他圖徵請直接在地圖上選取。
                  </p>
                )}
                {selectedVisibleSegment ? (
                  <div className="reference-details" aria-live="polite">
                    {STORMWATER_ATTRIBUTE_LABELS.map(([key, label]) => (
                      <div className="analysis-row" key={key}>
                        <span>{label}</span>
                        <strong>{selectedVisibleSegment[key] || "無資料"}</strong>
                      </div>
                    ))}
                    <div className="analysis-row">
                      <span>資料類別</span>
                      <strong>{selectedVisibleSegment.data_class}</strong>
                    </div>
                    <div className="analysis-row">
                      <span>分類</span>
                      <strong>
                        {CLASSIFICATION_LABELS[selectedVisibleSegment.classification] ??
                          selectedVisibleSegment.classification}
                      </strong>
                    </div>
                  </div>
                ) : (
                  <p className="inline-note" aria-live="polite">
                    從清單或地圖選取管線，以檢視來源屬性。
                  </p>
                )}
                <p className="reference-note">
                  未驗證實際連通性。起點／終點節點值僅為發布機關屬性。
                </p>
              </>
            ) : (
              <>
                <p className="inline-note" aria-live="polite">
                  {stormwaterStatus === "尚未匯入管線"
                    ? "尚未匯入雨水下水道管線。"
                    : bboxTooBroad
                      ? "請放大以載入管線。目前視圖超過載入上限，因此清單暫不顯示，並不代表沒有資料。"
                      : stormwaterStatus}
                </p>
                {stormwaterStatus === "尚未匯入管線" && (
                  <p className="reference-note">
                    僅限維運人員設定 · 使用本地來源檔案，不進行即時下載：{" "}
                    <a
                      href={`${INFRASTRUCTURE_GUIDES_URL}/stormwater-pipelines-import.md`}
                      target="_blank"
                      rel="noopener noreferrer"
                    >
                      雨水下水道匯入指南
                    </a>
                    .
                  </p>
                )}
              </>
            )}
            {stormwater?.provenance && (
              <details className="provenance-details">
                <summary>雨水下水道來源、授權與現勢性</summary>
                <div className="provenance-block" aria-label="雨水下水道來源出處">
                  <span>來源 URL</span>
                  {isSafeExternalUrl(stormwater.provenance.source_url) ? (
                    <a
                      href={stormwater.provenance.source_url}
                      target="_blank"
                      rel="noopener noreferrer"
                    >
                      {stormwater.provenance.source_url}
                    </a>
                  ) : (
                    <strong>{stormwater.provenance.source_url}</strong>
                  )}
                  <span>下載 URL</span>
                  {isSafeExternalUrl(stormwater.provenance.download_url) ? (
                    <a
                      href={stormwater.provenance.download_url}
                      target="_blank"
                      rel="noopener noreferrer"
                    >
                      {stormwater.provenance.download_url}
                    </a>
                  ) : (
                    <strong>{stormwater.provenance.download_url}</strong>
                  )}
                  <span>姓名標示</span>
                  <strong>{stormwater.provenance.attribution}</strong>
                  <span>授權條款</span>
                  <strong>{stormwater.provenance.license}</strong>
                  <span>資源版本</span>
                  <strong>{stormwater.provenance.resource_version}</strong>
                  <span>現勢性</span>
                  <strong>{stormwater.provenance.uncertainty.currentness}</strong>
                  <span>垂直坐標</span>
                  <strong>{zHandlingText(stormwater.provenance.z_handling)}</strong>
                  <span>來源品質</span>
                  <strong>{stormwaterQualitySummary(stormwater.provenance.source_quality)}</strong>
                  {stormwater.provenance.source_quality.reference_only && (
                    <small>
                      發布機關僅供參考警示：請僅作參考；如需精確資料，請向權責公用事業機關取得。
                    </small>
                  )}
                </div>
              </details>
            )}
          </section>

          <section className="panel rodent-panel" id="panel-rodent" aria-label="鼠類回報檢視">
            <div className="panel-heading">
              <div>
                <h3>鼠類回報</h3>
              </div>
              <span className="classification-badge">SIMULATED · 模擬</span>
            </div>
            <div className="field-pair">
              <div className="form-field">
                <label htmlFor="rodent-from">回報起時間（Asia/Taipei，含端點）</label>
                <input
                  id="rodent-from"
                  type="datetime-local"
                  step={60}
                  value={rodentFrom}
                  onChange={(event) => {
                    setRodentFrom(event.target.value);
                    setDatePreset(null);
                  }}
                />
              </div>
              <div className="form-field">
                <label htmlFor="rodent-to">回報迄時間（Asia/Taipei，含端點）</label>
                <input
                  id="rodent-to"
                  type="datetime-local"
                  step={60}
                  value={rodentTo}
                  onChange={(event) => {
                    setRodentTo(event.target.value);
                    setDatePreset(null);
                  }}
                />
              </div>
            </div>
            <p className="inline-note">
              時間為 Asia/Taipei（UTC+8，無日光節約時間）牆鐘時間；起迄端點皆含在內。請求改用對應的
              UTC 邊界，例如 2026-10-01 08:30 → 2026-10-01T00:30:00Z。
            </p>
            <div className="preset-row" role="group" aria-label="回報時間預設範圍">
              {DATE_PRESETS.map(([value, label]) => (
                <button
                  key={value}
                  type="button"
                  className={`preset-button ${datePreset === value ? "is-selected" : ""}`}
                  aria-pressed={datePreset === value}
                  onClick={() => applyDatePreset(value)}
                >
                  {label}
                </button>
              ))}
            </div>
            <p className="inline-note filter-summary" aria-live="polite">
              目前篩選：
              {datePreset
                ? (DATE_PRESETS.find(([value]) => value === datePreset)?.[1] ?? "自訂")
                : "自訂或未設定"}
              （{rodentFrom || "未設定"} ～ {rodentTo || "未設定"} · Asia/Taipei，起迄皆含）
            </p>
            {rodentValidationMessage ? (
              <p className="error-note" role="alert">
                {rodentValidationMessage}
              </p>
            ) : hasRodentReports && (activeRodentReports?.features.length ?? 0) === 0 ? (
              <>
                <p className="reference-label">{rodentStatus}</p>
                <p className="inline-note" aria-live="polite">
                  在選定的 Asia/Taipei 時間範圍與目前視窗內沒有回傳的 SIMULATED
                  合成報告形資料。這不是事件計數；除實際回傳者外，不推論還有其他回報。
                </p>
              </>
            ) : hasRodentReports ? (
              <>
                <p className="reference-label">{rodentStatus}</p>
                <p className="inline-note">
                  目前視窗與 Asia/Taipei 時間範圍（起迄皆含，請求以 UTC 邊界送出）內回傳{" "}
                  {activeRodentReports?.features.length ?? 0} 筆 SIMULATED
                  合成報告形資料；這些是格式測試資料，不是觀測回報。
                  {activeRodentReports?.truncated
                    ? " 已達回傳上限：除這些回傳圖徵外仍有符合條件的紀錄，且不宣稱精確總數。"
                    : ""}
                </p>
                <p className="reference-label" id="report-list-label">
                  回報 · 選取以檢視
                </p>
                <ul className="district-list" aria-labelledby="report-list-label">
                  {rodentReportButtons.map((feature) => {
                    const selected =
                      selectedVisibleReport?.report_id === feature.properties.report_id;
                    return (
                      <li key={feature.properties.report_id}>
                        <button
                          type="button"
                          className={`district-button ${selected ? "is-selected" : ""}`}
                          aria-pressed={selected}
                          aria-label={feature.properties.report_id}
                          onClick={() => setSelectedReport(feature.properties)}
                        >
                          {feature.properties.reported_at}
                        </button>
                      </li>
                    );
                  })}
                </ul>
                {rodentListTruncated && (
                  <p className="inline-note">
                    僅顯示前 {RODENT_REPORT_LIST_LIMIT} 筆，共回傳{" "}
                    {activeRodentReports?.features.length} 筆。請在地圖上選取其他回傳的回報。
                  </p>
                )}
                {selectedVisibleReport ? (
                  <div className="reference-details" aria-live="polite">
                    {RODENT_REPORT_DETAIL_LABELS.map(([key, label]) => (
                      <div className="analysis-row" key={key}>
                        <span>{label}</span>
                        <strong>{selectedVisibleReport[key] || "無資料"}</strong>
                      </div>
                    ))}
                  </div>
                ) : (
                  <p className="inline-note" aria-live="polite">
                    從清單或地圖選取回報，以檢視詳細資料。
                  </p>
                )}
              </>
            ) : (
              <>
                <p className="inline-note" aria-live="polite">
                  {rodentStatus === "尚未匯入回報"
                    ? "尚未匯入合成鼠類回報。"
                    : bboxTooBroad
                      ? "請放大以載入回報。目前視圖超過載入上限，因此清單暫不顯示，並不代表沒有回報。"
                      : rodentStatus}
                </p>
                {rodentStatus === "尚未匯入回報" && (
                  <p className="reference-note">
                    僅限維運人員的測試資料設定，非真實回報：{" "}
                    <a
                      href={`${INFRASTRUCTURE_GUIDES_URL}/rodent-reports-import.md`}
                      target="_blank"
                      rel="noopener noreferrer"
                    >
                      合成回報測試資料匯入指南
                    </a>
                    .
                  </p>
                )}
              </>
            )}
            <p className="reference-note">{RODENT_REPORT_DISCLAIMER}</p>
            {!rodentValidationMessage && activeRodentReports?.provenance && (
              <details className="provenance-details">
                <summary>鼠類回報來源、授權與現勢性</summary>
                <div className="provenance-block" aria-label="鼠類回報來源出處">
                  <span>出處結構版本</span>
                  <strong>{activeRodentReports.provenance.schema_version}</strong>
                  <span>來源類型</span>
                  <strong>{activeRodentReports.provenance.source_kind}</strong>
                  <span>資料集</span>
                  <strong>{activeRodentReports.provenance.dataset_id}</strong>
                  <span>資源版本</span>
                  <strong>{activeRodentReports.provenance.resource_version}</strong>
                  <span>內容 SHA-256</span>
                  <strong>{activeRodentReports.provenance.content_sha256}</strong>
                  <span>授權條款</span>
                  <strong>{activeRodentReports.provenance.license}</strong>
                  <span>姓名標示</span>
                  <strong>{activeRodentReports.provenance.attribution}</strong>
                  <span>現勢性</span>
                  <strong>{activeRodentReports.provenance.uncertainty.currentness}</strong>
                </div>
              </details>
            )}
          </section>

          <section
            className="panel citizen-aggregate-panel"
            id="panel-citizen-aggregates"
            aria-label="公民通報彙整檢視"
          >
            <div className="panel-heading">
              <div>
                <h3>公民通報彙整</h3>
              </div>
              <span className="classification-badge">UNVERIFIED · 未驗證</span>
            </div>
            {hasCitizenAggregates ? (
              <>
                <p className="reference-label">{citizenAggregateStatus}</p>
                <p className="inline-note" aria-live="polite">
                  目前視圖回傳 {citizenAggregateCells.length} 個{" "}
                  {citizenAggregates?.provenance?.aggregation.cell_size_meters ?? 250} 公尺網格、
                  {citizenAggregateReportCount} 筆已發布的通報計數
                  {citizenAggregateMonths.length > 0
                    ? `，涵蓋 ${citizenAggregateMonths.join("、")}`
                    : ""}
                  。每格每月每類型至少{" "}
                  {citizenAggregates?.provenance?.aggregation.suppression_minimum ?? 3}{" "}
                  筆才發布；未達門檻的網格與類型不顯示，因此計數是下限而非通報總數。
                  {citizenAggregates?.truncated
                    ? " 已達回傳上限：除這些網格外仍有符合條件的資料，且不宣稱精確總數。"
                    : ""}
                </p>
                <p className="reference-note">
                  公民自願通報的彙整計數，未經平台或市政驗證。不是鼠類觀測、盛行率、族群、移動或風險估計，也不作為模擬輸入。
                </p>
                {citizenAggregates?.provenance && (
                  <details className="provenance-details">
                    <summary>來源、授權、精度與抑制</summary>
                    <div className="provenance-block" aria-label="公民通報彙整來源出處">
                      <span>來源 URL</span>
                      {isSafeExternalUrl(citizenAggregates.provenance.source_url) ? (
                        <a
                          href={citizenAggregates.provenance.source_url}
                          target="_blank"
                          rel="noopener noreferrer"
                        >
                          {citizenAggregates.provenance.source_url}
                        </a>
                      ) : (
                        <strong>{citizenAggregates.provenance.source_url}</strong>
                      )}
                      <span>姓名標示</span>
                      <strong>{citizenAggregates.provenance.attribution}</strong>
                      <span>授權／再利用</span>
                      <strong>{citizenAggregates.provenance.license}</strong>
                      <span>資料集版本</span>
                      <strong>{citizenAggregates.provenance.resource_version}</strong>
                      <span>內容 SHA-256</span>
                      <strong>{citizenAggregates.provenance.content_sha256}</strong>
                      <span>網格大小</span>
                      <strong>
                        {citizenAggregates.provenance.aggregation.cell_size_meters} 公尺
                      </strong>
                      <span>抑制門檻</span>
                      <strong>
                        每格每月每類型至少{" "}
                        {citizenAggregates.provenance.aggregation.suppression_minimum} 筆
                      </strong>
                      <span>未匯入欄位</span>
                      <strong>
                        {citizenAggregates.provenance.aggregation.dropped_fields.join("、")}
                      </strong>
                      <span>處理計數</span>
                      <strong>
                        解析 {citizenAggregates.provenance.counts.parsed} 筆 · 採用{" "}
                        {citizenAggregates.provenance.counts.used} 筆 · 抑制{" "}
                        {citizenAggregates.provenance.counts.suppressed_records} 筆 /{" "}
                        {citizenAggregates.provenance.counts.suppressed_cells} 格
                      </strong>
                      <span>月份假設</span>
                      <strong>{citizenAggregates.provenance.aggregation.month_timezone_assumption}</strong>
                      <span>現勢性</span>
                      <strong>{citizenAggregates.provenance.uncertainty.currentness}</strong>
                    </div>
                  </details>
                )}
              </>
            ) : (
              <p className="inline-note" aria-live="polite">
                {citizenAggregateStatus}
                {citizenAggregates?.data_state === "empty"
                  ? "：資料庫尚未匯入公民通報彙整；不以其他資料代替。"
                  : "：未取得彙整資料；不顯示代替資料。"}
              </p>
            )}
          </section>
        </aside>
      </div>
      <footer className="footer-note">
        RatSight 初始化版本 <span>·</span> 無觀測資料 <span>·</span> 模擬輸出皆為合成並明確標示
      </footer>
    </main>
  );
}
