"use client";

import { useMutation, useQuery } from "@tanstack/react-query";
import { useCallback, useEffect, useMemo, useRef, useState } from "react";

import { LayerGlyph } from "@/components/layer-glyph";
import { MapView } from "@/components/map-view";
import { usePrefersReducedMotion } from "@/lib/use-prefers-reduced-motion";
import { Button } from "@/components/ui/button";
import {
  BBOX_MAX_SPAN_DEGREES,
  citizenReportSourceIdentity,
  fetchAdministrativeDistricts,
  fetchCitizenReportAggregates,
  fetchLayers,
  fetchStormwaterPipelines,
  isBboxTooBroad,
  isSourceNetworkUnavailable,
  requestPreview,
  sameCitizenReportSource,
  type AdministrativeDistrictProperties,
  type Bbox,
  type CitizenReportCellProperties,
  type CitizenReportSourceIdentity,
  type Layer,
  type SimulationPreview,
  type StormwaterProperties,
} from "@/lib/api";

const DEFAULT_LAYERS: Layer[] = [
  ["sewer_networks", "污水下水道"],
  ["surface_corridors", "地表移動廊道"],
  ["human_activity", "人類活動"],
  ["environmental_conditions", "環境條件"],
].map(([id, label]) => ({
  id,
  label,
  available: false,
  classification: null,
  message: "尚未載入資料集。",
}));

// Canonical layer ids map to Chinese labels; unknown ids stay generic so API text cannot leak into UI.
const LAYER_LABEL_OVERRIDES: Record<string, string> = {
  sewer_networks: "污水下水道",
  surface_corridors: "地表移動廊道",
  human_activity: "人類活動",
  environmental_conditions: "環境條件",
};

// Unavailable-row copy is owned by the UI, so API payload language never leaks.
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

const STUDY_AREA_ID = "taipei_osm_songshan";
const SIMULATION_DURATION_STEPS = 12;
const SIMULATION_RANDOM_SEED = 42;
const SIMULATION_WALKERS = 24;

const CITIZEN_REPORT_TYPE_LABELS: Record<string, string> = {
  sighting: "鼠蹤通報",
  bait_station: "毒餌相關通報",
  other: "其他通報",
};

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
  const citizenAggregateQuery = useQuery({
    queryKey: ["citizen-report-aggregates", viewportBbox],
    queryFn: () => fetchCitizenReportAggregates({ bbox: viewportBbox }),
    enabled: !bboxTooBroad,
  });
  const [preview, setPreview] = useState<SimulationPreview | null>(null);
  const [previewOriginCellId, setPreviewOriginCellId] = useState<string | null>(null);
  const [pendingPreviewOriginCellId, setPendingPreviewOriginCellId] = useState<string | null>(null);
  const [previewError, setPreviewError] = useState<unknown>(null);
  // Snapshot the origin was resolved against; results never belong to a later one.
  const [previewSource, setPreviewSource] = useState<CitizenReportSourceIdentity | null>(null);
  // Snapshot the selected marker was read from, captured at selection time.
  const [selectionSource, setSelectionSource] = useState<CitizenReportSourceIdentity | null>(null);
  const [sourceRefreshNotice, setSourceRefreshNotice] = useState<string | null>(null);
  const [outputMode, setOutputMode] = useState<"aggregate" | "trajectory">("aggregate");
  const [activeStep, setActiveStep] = useState(0);
  const [selectedTrajectoryId, setSelectedTrajectoryId] = useState<number | null>(null);
  const [isPlaying, setIsPlaying] = useState(false);
  const latestSimulationRequestId = useRef(0);
  const [showNetworkReference, setShowNetworkReference] = useState(false);
  const [showBoundaries, setShowBoundaries] = useState(false);
  const [showStormwater, setShowStormwater] = useState(false);
  const [selectedDistrict, setSelectedDistrict] = useState<AdministrativeDistrictProperties | null>(
    null,
  );
  const [selectedSegment, setSelectedSegment] = useState<StormwaterProperties | null>(null);
  const [selectedCitizenCell, setSelectedCitizenCell] =
    useState<CitizenReportCellProperties | null>(null);
  const [originCellId, setOriginCellId] = useState<string | null>(null);
  const invalidatePreviewForSelectionChange = useCallback(() => {
    latestSimulationRequestId.current += 1;
    setPreview(null);
    setPreviewOriginCellId(null);
    setPendingPreviewOriginCellId(null);
    setPreviewError(null);
    setPreviewSource(null);
    setOutputMode("aggregate");
    setActiveStep(0);
    setSelectedTrajectoryId(null);
    setIsPlaying(false);
  }, []);
  const mutation = useMutation({
    mutationFn: async ({
      requestId,
      input,
    }: {
      requestId: number;
      input: Parameters<typeof requestPreview>[0];
    }) => ({
      requestId,
      originCellId: input.origin_cell_id,
      source: "origin_source" in input ? input.origin_source : null,
      preview: await requestPreview(input),
    }),
    onSuccess: ({ requestId, originCellId: resultOriginCellId, source, preview: result }) => {
      if (requestId !== latestSimulationRequestId.current) return;
      setPreview(result);
      setPreviewOriginCellId(resultOriginCellId ?? null);
      setPreviewSource(source);
      setPendingPreviewOriginCellId(null);
      setPreviewError(null);
      setOutputMode("aggregate");
      setActiveStep(0);
      setSelectedTrajectoryId(result.trajectories?.[0]?.walker_id ?? null);
      setIsPlaying(false);
    },
    onError: (error, variables) => {
      if (variables.requestId !== latestSimulationRequestId.current) return;
      setPreview(null);
      setPreviewOriginCellId(null);
      setPreviewSource(null);
      setPendingPreviewOriginCellId(null);
      setPreviewError(error);
      setOutputMode("aggregate");
      setActiveStep(0);
      setSelectedTrajectoryId(null);
      setIsPlaying(false);
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
  const citizenAggregates = citizenAggregateQuery.data ?? null;
  const citizenAggregateCells = useMemo(
    () => citizenAggregates?.features ?? [],
    [citizenAggregates],
  );
  // Published snapshot of the loaded aggregates; null while loading or unversioned.
  const citizenSourceIdentity = useMemo(
    () => citizenReportSourceIdentity(citizenAggregates),
    [citizenAggregates],
  );
  // Feature id is the API's stable cell identity: cell_id:month:report_type.
  const citizenOriginOptions = useMemo(
    () =>
      citizenAggregateCells.map(({ properties }) => ({
        id: `${properties.cell_id}:${properties.month}:${properties.report_type}`,
        label: `${properties.cell_id} · ${properties.month} · ${
          CITIZEN_REPORT_TYPE_LABELS[properties.report_type] ?? properties.report_type
        } · ${
          properties.data_class === "SYNTHETIC_AGGREGATE_FIXTURE"
            ? "SIMULATED 本機測試格"
            : `${properties.count ?? "計數不可用"} 筆`
        }`,
        properties,
      })),
    [citizenAggregateCells],
  );
  const hasCitizenAggregates =
    citizenAggregates?.data_state === "available" && citizenAggregateCells.length > 0;
  useEffect(() => {
    if (!originCellId) return;
    if (!citizenAggregateQuery.isSuccess) return;
    if (citizenOriginOptions.some((option) => option.id === originCellId)) return;
    // A refreshed viewport no longer publishes this cell; never submit a stale origin.
    // eslint-disable-next-line react-hooks/set-state-in-effect
    setOriginCellId(null);
  }, [citizenAggregateQuery.isSuccess, citizenOriginOptions, originCellId]);
  useEffect(() => {
    if (!selectedCitizenCell) return;
    // A new viewport query briefly has no data; do not treat that pending state as
    // evidence that the cell disappeared.
    if (citizenAggregateQuery.isPending) return;
    const remainsInViewport = citizenAggregateCells.some(
      ({ properties }) =>
        properties.cell_id === selectedCitizenCell.cell_id &&
        properties.month === selectedCitizenCell.month &&
        properties.report_type === selectedCitizenCell.report_type,
    );
    if (!remainsInViewport) {
      // Refreshed viewport no longer contains this cell; do not revive stale selection.
      // eslint-disable-next-line react-hooks/set-state-in-effect
      invalidatePreviewForSelectionChange();
      setOriginCellId(null);
      setSelectedCitizenCell(null);
    }
  }, [
    citizenAggregateCells,
    citizenAggregateQuery.isPending,
    selectedCitizenCell,
    invalidatePreviewForSelectionChange,
  ]);
  // Only a real snapshot change invalidates the selection: a pending reload or an
  // unchanged version from a viewport move leaves the reviewed origin usable.
  useEffect(() => {
    if (!selectionSource || !citizenSourceIdentity) return;
    if (sameCitizenReportSource(selectionSource, citizenSourceIdentity)) return;
    // eslint-disable-next-line react-hooks/set-state-in-effect
    invalidatePreviewForSelectionChange();
    setOriginCellId(null);
    setSelectedCitizenCell(null);
    setSelectionSource(null);
    setSourceRefreshNotice("公民通報資料已更新，請重新載入並選擇模擬起點。");
  }, [citizenSourceIdentity, invalidatePreviewForSelectionChange, selectionSource]);
  // Cell counts are suppressed aggregates, so summing them is a floor on reported
  // volume, not a report total: every suppressed group is excluded.
  const citizenAggregateReportCount =
    citizenAggregates?.data_class === "CITIZEN_REPORT_AGGREGATE"
      ? citizenAggregateCells.reduce((total, feature) => total + (feature.properties.count ?? 0), 0)
      : null;
  const citizenAggregateMonths = [
    ...new Set(citizenAggregateCells.map((feature) => feature.properties.month)),
  ].sort();
  const syntheticAggregateProvenance =
    citizenAggregates?.provenance?.source_kind === "synthetic_aggregate_fixture"
      ? citizenAggregates.provenance
      : null;
  const publicAggregateProvenance =
    citizenAggregates?.provenance?.source_kind === "public_citizen_report_export"
      ? citizenAggregates.provenance
      : null;
  // Empty fixture datasets have no provenance record, so the response data class
  // is also required to keep "no rows yet" from reading as a citizen dataset.
  const isSyntheticAggregateDataset =
    citizenAggregates?.data_class === "SYNTHETIC_AGGREGATE_FIXTURE" ||
    syntheticAggregateProvenance !== null;
  // The catalog lists datasets. Citizen-report cells and simulated paths are
  // fixed workflow layers that appear as soon as their data is available.
  const catalogLayers = layers.filter(
    (layer) => layer.id !== "stormwater_networks" && layer.id !== "simulated_paths",
  );
  const hasNetworkGeometry = Boolean(preview?.edges.some((edge) => edge.geometry));
  const availableCatalogLayers = catalogLayers.filter((layer) => layer.available);
  const unavailableCatalogLayers = catalogLayers.filter((layer) => !layer.available);
  // Three switchable built-in rows plus every catalog entry exactly once.
  const BUILT_IN_LAYER_ROW_COUNT = 3;
  const visibleLayerCount = BUILT_IN_LAYER_ROW_COUNT + catalogLayers.length;
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
  const selectedCitizenCellKey = selectedCitizenCell
    ? `${selectedCitizenCell.cell_id}:${selectedCitizenCell.month}:${selectedCitizenCell.report_type}`
    : null;
  // Server-owned policy; the action stays disabled for context-only categories.
  const selectedCellIsEligibleOrigin = selectedCitizenCell?.origin_eligibility?.eligible === true;
  const currentPreview =
    preview &&
    previewOriginCellId === selectedCitizenCellKey &&
    sameCitizenReportSource(previewSource, citizenSourceIdentity) &&
    citizenOriginOptions.some((option) => option.id === previewOriginCellId)
      ? preview
      : null;
  const previewPendingForSelection =
    selectedCitizenCellKey !== null && pendingPreviewOriginCellId === selectedCitizenCellKey;
  const selectedTrajectory =
    currentPreview?.trajectories?.find(
      (trajectory) => trajectory.walker_id === selectedTrajectoryId,
    ) ?? null;
  const playbackStepCount = selectedTrajectory?.edges.length ?? 0;
  const reduceMotion = usePrefersReducedMotion();
  const [playbackSpeed, setPlaybackSpeed] = useState(1);
  // null means "follow the system preference"; a real toggle pins the choice.
  const [animationOverride, setAnimationOverride] = useState<boolean | null>(null);
  const animationEnabled = animationOverride ?? !reduceMotion;
  useEffect(() => {
    if (!isPlaying || playbackStepCount === 0 || activeStep >= playbackStepCount) return;
    const timer = window.setTimeout(
      () => {
        const nextStep = Math.min(activeStep + 1, playbackStepCount);
        setActiveStep(nextStep);
        if (nextStep >= playbackStepCount) setIsPlaying(false);
      },
      Math.round(650 / playbackSpeed),
    );
    return () => window.clearTimeout(timer);
  }, [activeStep, isPlaying, playbackSpeed, playbackStepCount]);
  const selectedCitizenCellIsFixture =
    selectedCitizenCell?.data_class === "SYNTHETIC_AGGREGATE_FIXTURE";
  const selectionSummary = selectedVisibleSegment
    ? `管線 ${selectedVisibleSegment.pipe_number || selectedVisibleSegment.segment_id} · UNVERIFIED（未驗證）`
    : selectedCitizenCell
      ? selectedCitizenCellIsFixture
        ? `${selectedCitizenCell.cell_id} · SIMULATED 本機測試格（非公民通報）`
        : `${selectedCitizenCell.cell_id} · ${selectedCitizenCell.month} · ${CITIZEN_REPORT_TYPE_LABELS[selectedCitizenCell.report_type] ?? selectedCitizenCell.report_type} · 公民通報彙整格焦點 · UNVERIFIED（未驗證）`
      : selectedDistrict
        ? `${selectedDistrict.district_name} · UNVERIFIED（未驗證）`
        : "尚未選取圖徵。從地圖或右側清單選取後，摘要顯示於此；詳細屬性保留在右側面板。";

  const renderCatalogLayer = (layer: Layer) => {
    const available = layer.available;
    const label = LAYER_LABEL_OVERRIDES[layer.id] ?? "未命名資料圖層";
    return (
      <label className={`layer-row ${available ? "" : "is-unavailable"}`} key={layer.id}>
        <LayerGlyph layerId={layer.id} />
        <span className="layer-name">
          {label}
          <small>
            {available
              ? (CLASSIFICATION_LABELS[layer.classification ?? ""] ?? "可用")
              : DEFAULT_UNAVAILABLE_MESSAGE}
          </small>
        </span>
        {/* Catalog entries have no map visibility control, so state it instead
            of offering a permanently dead checkbox. */}
        <span className="layer-status">{available ? "可用" : "未載入"}</span>
      </label>
    );
  };

  const citizenAggregateStatus = bboxTooBroad
    ? "請放大以載入彙整"
    : citizenAggregateQuery.isPending
      ? "彙整載入中…"
      : citizenAggregateQuery.isError
        ? "公民通報彙整服務無法使用"
        : citizenAggregates?.data_state === "empty"
          ? isSyntheticAggregateDataset
            ? "尚無本機合成測試格（SIMULATED；非公民通報）"
            : "尚未匯入公民通報彙整"
          : citizenAggregates?.data_class === "SYNTHETIC_AGGREGATE_FIXTURE"
            ? "SIMULATED · 本機合成測試格（不含公民通報）"
            : "CITIZEN_REPORT_AGGREGATE · UNVERIFIED（未驗證）";

  const handleSelectCitizenCell = (cell: CitizenReportCellProperties) => {
    const cellKey = `${cell.cell_id}:${cell.month}:${cell.report_type}`;
    if (cellKey !== selectedCitizenCellKey) invalidatePreviewForSelectionChange();
    setSelectedCitizenCell(cell);
    setOriginCellId(cellKey);
    setSelectionSource(citizenSourceIdentity);
    setSourceRefreshNotice(null);
  };
  const handleSelectTrajectory = (trajectoryId: number) => {
    setIsPlaying(false);
    setActiveStep(0);
    setSelectedTrajectoryId(trajectoryId);
  };
  const changeOutputMode = (mode: "aggregate" | "trajectory") => {
    setIsPlaying(false);
    setActiveStep(0);
    setOutputMode(mode);
  };
  const runPreviewFromSelectedCell = () => {
    if (!selectedCitizenCellKey) return;
    if (!selectedCellIsEligibleOrigin) {
      setPreviewError(
        new Error(selectedCitizenCell?.origin_eligibility?.message ?? "此類通報無法作為模擬起點。"),
      );
      return;
    }
    if (!selectionSource) {
      setPreviewError(new Error("公民通報資料版本尚未載入，請重新載入公民通報後再選擇起點。"));
      return;
    }
    const requestId = latestSimulationRequestId.current + 1;
    latestSimulationRequestId.current = requestId;
    setPreview(null);
    setPreviewOriginCellId(null);
    setPendingPreviewOriginCellId(selectedCitizenCellKey);
    setPreviewError(null);
    setOutputMode("aggregate");
    setActiveStep(0);
    setSelectedTrajectoryId(null);
    setIsPlaying(false);
    setOriginCellId(selectedCitizenCellKey);
    mutation.mutate({
      requestId,
      input: {
        study_area: STUDY_AREA_ID,
        duration_steps: SIMULATION_DURATION_STEPS,
        walkers: SIMULATION_WALKERS,
        random_seed: SIMULATION_RANDOM_SEED,
        movement_model: "weighted_random_walk",
        intervention_scenario: "baseline",
        origin_cell_id: selectedCitizenCellKey,
        origin_source: selectionSource,
      },
    });
  };

  const citizenCellCard = selectedCitizenCell ? (
    <section
      className="map-cell-card"
      aria-label={
        selectedCitizenCellIsFixture ? "本機合成測試格詳細資料" : "公民通報彙整格詳細資料"
      }
    >
      <div className="map-cell-card-heading">
        <span className="reference-label">
          {selectedCitizenCellIsFixture ? "本機合成測試格" : "公民通報彙整格"}
        </span>
        <button
          type="button"
          className="map-cell-card-close"
          aria-label={
            selectedCitizenCellIsFixture
              ? "關閉本機合成測試格詳細資料"
              : "關閉公民通報彙整格詳細資料"
          }
          onClick={() => {
            invalidatePreviewForSelectionChange();
            setOriginCellId(null);
            setSelectedCitizenCell(null);
            setSelectionSource(null);
          }}
        >
          ×
        </button>
      </div>
      <div className="map-cell-card-body">
        <span className="map-cell-card-badge">
          {selectedCitizenCellIsFixture ? "SIMULATED · 本機測試" : "UNVERIFIED · 未驗證"}
        </span>
        <h3>{selectedCitizenCell.cell_id}</h3>
        <dl className="map-cell-card-facts">
          <div>
            <dt>{selectedCitizenCellIsFixture ? "測試類別" : "通報類型"}</dt>
            <dd>
              {selectedCitizenCellIsFixture
                ? "本機合成資料"
                : (CITIZEN_REPORT_TYPE_LABELS[selectedCitizenCell.report_type] ??
                  selectedCitizenCell.report_type)}
            </dd>
          </div>
          <div>
            <dt>{selectedCitizenCellIsFixture ? "測試批次" : "月份"}</dt>
            <dd>{selectedCitizenCell.month}</dd>
          </div>
          {!selectedCitizenCellIsFixture && (
            <div>
              <dt>發布通報計數</dt>
              <dd>
                {selectedCitizenCell.count === null ? "不可用" : `${selectedCitizenCell.count} 筆`}
              </dd>
            </div>
          )}
          <div>
            <dt>空間單元</dt>
            <dd>250 公尺格網 · 標記在格網中心</dd>
          </div>
        </dl>
        <p className="map-cell-card-caution">
          {selectedCitizenCellIsFixture
            ? "僅供隔離本機測試的 SIMULATED 網格；不含公民通報、通報計數或動物觀測。"
            : "不是個別通報點位。通報計數不是鼠類觀測、族群或風險估計，也不會成為代理數或移動權重。"}
        </p>
        <p className="map-cell-card-attribution">{selectedCitizenCell.attribution}</p>
        {selectionSource && (
          <details className="map-cell-card-details">
            <summary>資料來源與版本</summary>
            <dl className="map-cell-card-facts">
              <div>
                <dt>資料集</dt>
                <dd>{selectionSource.dataset_id}</dd>
              </div>
              <div>
                <dt>來源版本</dt>
                <dd>{selectionSource.resource_version}</dd>
              </div>
              <div>
                <dt>內容雜湊</dt>
                <dd className="mono-value">{selectionSource.content_sha256}</dd>
              </div>
              {!selectedCitizenCellIsFixture && (
                <div>
                  <dt>通報類別政策</dt>
                  <dd>{selectedCitizenCell.origin_eligibility.policy_version}</dd>
                </div>
              )}
            </dl>
            <p className="map-cell-card-caution">
              模擬結果只屬於此來源版本；來源更新後必須重新選擇起點。輸入維持 UNVERIFIED，輸出維持
              SIMULATED。
            </p>
          </details>
        )}
      </div>
      {!selectedCellIsEligibleOrigin && selectedCitizenCell.origin_eligibility && (
        <p className="map-cell-card-note is-warning" role="note">
          <strong>
            {selectedCitizenCellIsFixture
              ? "本機測試格"
              : (CITIZEN_REPORT_TYPE_LABELS[selectedCitizenCell.report_type] ??
                selectedCitizenCell.report_type)}
          </strong>
          {" · "}
          {selectedCitizenCell.origin_eligibility.message}
        </p>
      )}
      <Button
        className="map-cell-card-action"
        size="small"
        disabled={
          previewPendingForSelection || !hasCitizenAggregates || !selectedCellIsEligibleOrigin
        }
        onClick={runPreviewFromSelectedCell}
      >
        {!selectedCellIsEligibleOrigin
          ? "此類通報無法作為模擬起點"
          : previewPendingForSelection
            ? "模擬執行中…"
            : "以此格網起點執行模擬"}
      </Button>
      {previewError !== null && (
        <p className="map-cell-card-note is-error" role="alert">
          {previewError instanceof Error
            ? previewError.message
            : "預覽無法使用。請確認 API 正在執行後重試。"}
          {isSourceNetworkUnavailable(previewError) ? " 系統未以示意網路替代 OSM 結果。" : ""}
        </p>
      )}
      {currentPreview && (
        <p className="map-cell-card-note is-success" role="status">
          SIMULATED · 起點 {previewOriginCellId} · 可重現執行完成 · 種子{" "}
          {currentPreview.parameters.random_seed} · 模擬路徑已顯示
        </p>
      )}
    </section>
  ) : null;

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
              {previewPendingForSelection ? "執行中" : currentPreview ? "已產生" : "未產生"}
            </span>
            <span className="hud-meter" aria-hidden="true">
              <i className={currentPreview ? "is-lit" : undefined} />
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
          <div className="map-stage">
            <MapView
              preview={currentPreview}
              showNetworkReference={showNetworkReference}
              outputMode={currentPreview ? outputMode : "aggregate"}
              activeStep={currentPreview && outputMode === "trajectory" ? activeStep : null}
              selectedTrajectoryId={selectedTrajectoryId}
              onSelectTrajectory={handleSelectTrajectory}
              boundaries={districts}
              showBoundaries={showBoundaries}
              selectedDistrictId={selectedDistrict?.district_id ?? null}
              onSelectDistrict={setSelectedDistrict}
              stormwater={stormwater}
              showStormwater={showStormwater}
              selectedSegmentId={selectedVisibleSegment?.segment_id ?? null}
              onSelectSegment={setSelectedSegment}
              citizenAggregates={citizenAggregates}
              selectedCitizenCellKey={selectedCitizenCellKey}
              onSelectCitizenCell={handleSelectCitizenCell}
              playbackSpeed={playbackSpeed}
              animationEnabled={animationEnabled}
              onBoundsChange={setViewportBbox}
            />
          </div>
          {currentPreview && (
            <section className="simulation-playback" aria-label="模擬軌跡播放控制">
              <div className="simulation-playback-heading">
                <p className="simulation-playback-origin">SIMULATED · 起點 {previewOriginCellId}</p>
                <div className="simulation-playback-modes" role="group" aria-label="路徑顯示模式">
                  <button
                    type="button"
                    aria-pressed={outputMode === "aggregate"}
                    onClick={() => changeOutputMode("aggregate")}
                  >
                    彙整路線
                  </button>
                  <button
                    type="button"
                    aria-pressed={outputMode === "trajectory"}
                    disabled={!currentPreview.trajectories?.length}
                    onClick={() => changeOutputMode("trajectory")}
                  >
                    個別路徑
                  </button>
                </div>
              </div>
              <div className="simulation-playback-settings">
                <label className="simulation-playback-speed">
                  播放速度
                  <select
                    aria-label="播放速度"
                    value={playbackSpeed}
                    onChange={(event) => setPlaybackSpeed(Number(event.target.value))}
                  >
                    <option value={0.5}>0.5×</option>
                    <option value={1}>1×</option>
                    <option value={2}>2×</option>
                  </select>
                </label>
                <label className="simulation-playback-toggle">
                  <input
                    type="checkbox"
                    checked={animationEnabled}
                    onChange={(event) => {
                      setAnimationOverride(event.target.checked);
                    }}
                  />
                  動畫效果
                </label>
                <p className="simulation-playback-note simulation-playback-speed-note">
                  模擬播放速度，非實際鼠類移動速度
                </p>
              </div>
              {outputMode === "trajectory" && (
                <div className="simulation-playback-controls">
                  <label className="simulation-playback-walker">
                    行走者
                    <select
                      aria-label="選擇行走者"
                      value={selectedTrajectoryId === null ? "" : String(selectedTrajectoryId)}
                      disabled={!currentPreview.trajectories?.length}
                      onChange={(event) => handleSelectTrajectory(Number(event.target.value))}
                    >
                      {currentPreview.trajectories?.map((trajectory) => (
                        <option key={trajectory.walker_id} value={trajectory.walker_id}>
                          {trajectory.walker_id}
                        </option>
                      ))}
                    </select>
                  </label>
                  <div className="simulation-playback-actions" role="group" aria-label="播放控制">
                    <button
                      type="button"
                      disabled={playbackStepCount === 0 || activeStep === 0}
                      onClick={() => {
                        setIsPlaying(false);
                        setActiveStep((step) => Math.max(0, step - 1));
                      }}
                    >
                      上一步
                    </button>
                    <button
                      type="button"
                      disabled={
                        playbackStepCount === 0 || (!isPlaying && activeStep >= playbackStepCount)
                      }
                      onClick={() => setIsPlaying((playing) => !playing)}
                    >
                      {isPlaying ? "暫停" : "播放"}
                    </button>
                    <button
                      type="button"
                      disabled={playbackStepCount === 0 || activeStep >= playbackStepCount}
                      onClick={() => {
                        setIsPlaying(false);
                        setActiveStep((step) => Math.min(playbackStepCount, step + 1));
                      }}
                    >
                      下一步
                    </button>
                    <button
                      type="button"
                      disabled={playbackStepCount === 0 || activeStep === 0}
                      onClick={() => {
                        setIsPlaying(false);
                        setActiveStep(0);
                      }}
                    >
                      重設
                    </button>
                  </div>
                  <p className="simulation-playback-step" aria-live="polite">
                    步驟 {activeStep} / {playbackStepCount} · 非實際時間
                  </p>
                  {playbackStepCount === 0 && (
                    <p className="simulation-playback-empty" role="status">
                      此路徑沒有可播放的移動步驟。
                    </p>
                  )}
                  <p className="simulation-playback-note">
                    這是模擬序列步驟，不代表實際經過的分鐘、時數或日期；切換行走者會重設至步驟 0。
                  </p>
                </div>
              )}
            </section>
          )}
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
              地圖中心僅為導覽起點。公民通報彙整為 UNVERIFIED，移動路徑為
              SIMULATED；兩者同圖不代表驗證、因果或同一動物。
            </span>
          </div>
        </section>

        <aside className="control-rail" aria-label="分析控制項">
          <nav className="rail-index" aria-label="章節索引">
            <a href="#panel-status">01 狀態</a>
            <a href="#panel-layers">02 圖層</a>
            <a href="#panel-reference">03 行政區</a>
            <a href="#panel-stormwater">04 下水道</a>
            <a href="#panel-citizen-aggregates">05 公民通報</a>
          </nav>
          {citizenCellCard && (
            <div className="citizen-inspector" data-compact={currentPreview ? "true" : undefined}>
              {citizenCellCard}
            </div>
          )}
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
              {availableCatalogLayers.map(renderCatalogLayer)}
            </div>
            <p className="inline-note layer-flow-note">
              公民通報彙整與模擬移動路徑會在資料載入或預覽完成後自動顯示。
            </p>
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
                          aria-label={`${feature.properties.pipe_number || feature.properties.segment_id}（管段 ${feature.properties.segment_id}）`}
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

          <section
            className="panel citizen-aggregate-panel"
            id="panel-citizen-aggregates"
            aria-label={isSyntheticAggregateDataset ? "本機合成測試格檢視" : "公民通報彙整檢視"}
          >
            <div className="panel-heading">
              <div>
                <h3>{isSyntheticAggregateDataset ? "本機合成測試格" : "公民通報彙整"}</h3>
              </div>
              <span className="classification-badge">
                {isSyntheticAggregateDataset ? "SIMULATED · 合成測試" : "UNVERIFIED · 未驗證"}
              </span>
            </div>
            {hasCitizenAggregates ? (
              <>
                <p className="reference-label">{citizenAggregateStatus}</p>
                {sourceRefreshNotice && (
                  <p className="inline-note source-refresh-notice" role="status">
                    {sourceRefreshNotice}
                  </p>
                )}
                <div className="form-field citizen-cell-picker">
                  <label htmlFor="citizen-origin-cell">模擬起點格網</label>
                  <select
                    id="citizen-origin-cell"
                    aria-label={
                      isSyntheticAggregateDataset ? "選擇本機合成測試格" : "選擇公民通報彙整格"
                    }
                    value={selectedCitizenCellKey ?? ""}
                    onChange={(event) => {
                      const option = citizenOriginOptions.find(
                        (candidate) => candidate.id === event.target.value,
                      );
                      if (option) handleSelectCitizenCell(option.properties);
                    }}
                  >
                    <option value="">請選擇一個格網</option>
                    {citizenOriginOptions.map((option) => (
                      <option key={option.id} value={option.id}>
                        {option.label}
                      </option>
                    ))}
                  </select>
                  <small>
                    只會設定起點；變更選擇會清除上一個模擬結果，執行仍需按下詳細資料卡按鈕。
                  </small>
                </div>
                {syntheticAggregateProvenance ? (
                  <>
                    <p className="inline-note" aria-live="polite">
                      目前視圖回傳 {citizenAggregateCells.length} 個 250 公尺 SIMULATED
                      本機測試格；不含公民通報、通報計數或動物觀測。
                    </p>
                    <p className="reference-note">
                      此隔離測試夾具只用於驗證已發布格網至模擬的軟體流程；它不是 Rat Radar
                      資料，不得解讀為真實事件。
                    </p>
                    <details className="provenance-details">
                      <summary>測試夾具與 OSM 參考來源</summary>
                      <div className="provenance-block" aria-label="本機合成測試格來源出處">
                        <span>資料集</span>
                        <strong>{syntheticAggregateProvenance.dataset_id}</strong>
                        <span>版本</span>
                        <strong>{syntheticAggregateProvenance.resource_version}</strong>
                        <span>內容 SHA-256</span>
                        <strong>{syntheticAggregateProvenance.content_sha256}</strong>
                        <span>OSM 參考識別</span>
                        <strong>{syntheticAggregateProvenance.reference_source_id}</strong>
                        <span>OSM 來源 SHA-256</span>
                        <strong>{syntheticAggregateProvenance.reference_source_sha256}</strong>
                        <span>測試範圍</span>
                        <strong>{syntheticAggregateProvenance.test_scope}</strong>
                        <span>說明</span>
                        <strong>{syntheticAggregateProvenance.note}</strong>
                      </div>
                    </details>
                  </>
                ) : (
                  <>
                    <p className="inline-note" aria-live="polite">
                      目前視圖回傳 {citizenAggregateCells.length} 個{" "}
                      {publicAggregateProvenance?.aggregation.cell_size_meters ?? 250} 公尺網格、
                      {citizenAggregateReportCount ?? "計數不可用"} 筆已發布的通報計數
                      {citizenAggregateMonths.length > 0
                        ? `，涵蓋 ${citizenAggregateMonths.join("、")}`
                        : ""}
                      。每格每月每類型至少{" "}
                      {publicAggregateProvenance?.aggregation.suppression_minimum ?? 3}{" "}
                      筆才發布；未達門檻的網格與類型不顯示，因此計數是下限而非通報總數。
                      {citizenAggregates?.truncated
                        ? " 已達回傳上限：除這些網格外仍有符合條件的資料，且不宣稱精確總數。"
                        : ""}
                    </p>
                    <p className="reference-note">
                      公民自願通報的彙整計數，未經平台或市政驗證。不是鼠類觀測、盛行率、族群、移動或風險估計；已發布彙整格可明確選為模擬起點，但僅決定起點節點，計數不會成為代理數或移動權重，也不代表通報地點就是老鼠實際出現位置。資料來源：見鼠雷達
                      Rat Radar — https://ratdar.taipei/
                    </p>
                    {publicAggregateProvenance && (
                      <details className="provenance-details">
                        <summary>來源、授權、精度與抑制</summary>
                        <div className="provenance-block" aria-label="公民通報彙整來源出處">
                          <span>來源 URL</span>
                          {isSafeExternalUrl(publicAggregateProvenance.source_url) ? (
                            <a
                              href={publicAggregateProvenance.source_url}
                              target="_blank"
                              rel="noopener noreferrer"
                            >
                              {publicAggregateProvenance.source_url}
                            </a>
                          ) : (
                            <strong>{publicAggregateProvenance.source_url}</strong>
                          )}
                          <span>姓名標示</span>
                          <strong>{publicAggregateProvenance.attribution}</strong>
                          <span>授權／再利用</span>
                          <strong>{publicAggregateProvenance.license}</strong>
                          <span>資料集版本</span>
                          <strong>{publicAggregateProvenance.resource_version}</strong>
                          <span>內容 SHA-256</span>
                          <strong>{publicAggregateProvenance.content_sha256}</strong>
                          <span>網格大小</span>
                          <strong>
                            {publicAggregateProvenance.aggregation.cell_size_meters} 公尺
                          </strong>
                          <span>抑制門檻</span>
                          <strong>
                            每格每月每類型至少{" "}
                            {publicAggregateProvenance.aggregation.suppression_minimum} 筆
                          </strong>
                          <span>未匯入欄位</span>
                          <strong>
                            {publicAggregateProvenance.aggregation.dropped_fields.join("、")}
                          </strong>
                          <span>處理計數</span>
                          <strong>
                            解析 {publicAggregateProvenance.counts.parsed} 筆 · 採用{" "}
                            {publicAggregateProvenance.counts.used} 筆 · 抑制{" "}
                            {publicAggregateProvenance.counts.suppressed_records} 筆 /{" "}
                            {publicAggregateProvenance.counts.suppressed_cells} 格
                          </strong>
                          <span>月份假設</span>
                          <strong>
                            {publicAggregateProvenance.aggregation.month_timezone_assumption}
                          </strong>
                          <span>現勢性</span>
                          <strong>{publicAggregateProvenance.uncertainty.currentness}</strong>
                        </div>
                      </details>
                    )}
                  </>
                )}
              </>
            ) : (
              <p className="inline-note" aria-live="polite">
                {citizenAggregateStatus}
                {citizenAggregates?.data_state === "empty"
                  ? isSyntheticAggregateDataset
                    ? "：資料庫尚未匯入本機測試夾具；不以其他資料代替。"
                    : "：資料庫尚未匯入公民通報彙整；不以其他資料代替。"
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
