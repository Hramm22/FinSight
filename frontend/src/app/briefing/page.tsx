"use client";

import { useEffect, useRef, useState } from "react";
import type { Dispatch, RefObject, SetStateAction } from "react";

type MarketDataItem = {
  ticker: string;
  name: string;
  current_price: number;
  month_return: number;
  three_month_return: number;
  year_return: number;
};

type NewsDataItem = {
  source: string;
  title: string;
  link: string;
  market_score?: number;
  matched_keywords?: string[];
  is_market_related?: boolean;
};

type BriefingResponse = {
  id: number;
  created_at: string;
  market_data: MarketDataItem[];
  news_data: NewsDataItem[];
  macro_analysis: string;
  sector_analysis: string;
  interest_analysis: string;
  ai_summary: string;
};

type SectorGroup = {
  title: "강세" | "긍정 관찰" | "주의 관찰" | "약세";
  tone: "positive" | "primary" | "warning" | "negative";
  stocks: string[];
};

const sectorGroupMeta: Array<Pick<SectorGroup, "title" | "tone">> = [
  { title: "강세", tone: "positive" },
  { title: "긍정 관찰", tone: "primary" },
  { title: "주의 관찰", tone: "warning" },
  { title: "약세", tone: "negative" },
];

function classifyMarketItem(
  item: MarketDataItem,
): SectorGroup["title"] | "중립" {
  const momentumScore =
    item.month_return * 0.5 +
    item.three_month_return * 0.3 +
    item.year_return * 0.2;

  if (momentumScore >= 30 && item.month_return >= 0) {
    return "강세";
  }

  if (momentumScore >= 10) {
    return "긍정 관찰";
  }

  if (momentumScore <= -20) {
    return "약세";
  }

  if (item.month_return <= -10 || item.three_month_return <= -10) {
    return "주의 관찰";
  }

  return "중립";
}

function extractSectorDistribution(
  analysis: string,
  marketData: MarketDataItem[],
): SectorGroup[] {
  const normalizedAnalysis = analysis.replace(/\r/g, "");
  const groupedStocks = new Map<SectorGroup["title"], string[]>(
    sectorGroupMeta.map(({ title }) => [title, []]),
  );
  const assignedTickers = new Set<string>();

  const categoryPatterns: Array<{
    title: SectorGroup["title"];
    pattern: RegExp;
  }> = [
    { title: "긍정 관찰", pattern: /긍정\s*관찰/ },
    { title: "주의 관찰", pattern: /주의\s*관찰/ },
    { title: "강세", pattern: /강세/ },
    { title: "약세", pattern: /약세/ },
  ];

  const lines = normalizedAnalysis
    .split("\n")
    .map((line) => line.trim())
    .filter(Boolean);

  let currentCategory: SectorGroup["title"] | null = null;

  for (const line of lines) {
    const matchedCategory = categoryPatterns.find(({ pattern }) =>
      pattern.test(line),
    );

    if (matchedCategory) {
      currentCategory = matchedCategory.title;
    }

    for (const item of marketData) {
      if (assignedTickers.has(item.ticker)) {
        continue;
      }

      const containsStock =
        line.includes(item.name) || line.includes(item.ticker);

      if (!containsStock) {
        continue;
      }

      const inlineCategory = categoryPatterns.find(({ pattern }) =>
        pattern.test(line),
      )?.title;
      const category = inlineCategory ?? currentCategory;

      if (category) {
        groupedStocks.get(category)?.push(item.name);
        assignedTickers.add(item.ticker);
      }
    }
  }

  for (const item of marketData) {
    if (assignedTickers.has(item.ticker)) {
      continue;
    }

    const category = classifyMarketItem(item);

    if (category !== "중립") {
      groupedStocks.get(category)?.push(item.name);
    }
  }

  return sectorGroupMeta.map(({ title, tone }) => ({
    title,
    tone,
    stocks: groupedStocks.get(title) ?? [],
  }));
}

type InterestStock = {
  rank: string;
  name: string;
  ticker: string;
  currentPrice: string;
  change: number;
  changeLabel: string;
  type: string;
  chart: string;
};

const circledRankMap: Record<string, number> = {
  "①": 1,
  "②": 2,
  "③": 3,
  "④": 4,
  "⑤": 5,
  "⑥": 6,
  "⑦": 7,
  "⑧": 8,
  "⑨": 9,
  "⑩": 10,
};

function normalizeStockName(value: string) {
  return value
    .replace(/\([^)]*\)/g, "")
    .replace(/[\[\]{}]/g, "")
    .replace(/\s+/g, "")
    .trim()
    .toLowerCase();
}

function normalizeInterestType(value: string) {
  const normalized = value.trim().replace(/\s+/g, " ");

  if (/뉴스\s*기반/.test(normalized)) {
    return "뉴스 기반 관심";
  }

  if (/단순\s*급등/.test(normalized)) {
    return "단순 급등";
  }

  return normalized.replace(/\s*종목$/, "") || "관심 종목";
}

function formatPrice(value: number | undefined) {
  if (typeof value !== "number" || !Number.isFinite(value)) {
    return "정보 없음";
  }

  return `${Math.round(value).toLocaleString("ko-KR")}원`;
}

function formatReturn(value: number) {
  const sign = value > 0 ? "+" : "";
  return `${sign}${value.toFixed(2)}%`;
}

function createMiniChartPoints(change: number, index: number) {
  const startY = change >= 0 ? 31 : 10;
  const endY = change >= 0 ? 9 : 32;
  const amplitude = Math.min(Math.abs(change) / 5, 7);
  const points: string[] = [];

  for (let step = 0; step < 9; step += 1) {
    const progress = step / 8;
    const baseY = startY + (endY - startY) * progress;
    const wave = Math.sin((step + index) * 1.35) * amplitude;
    const y = Math.max(5, Math.min(35, baseY + wave));
    points.push(`${4 + step * 14},${y.toFixed(1)}`);
  }

  return points.join(" ");
}

function extractInterestStocks(
  analysis: string,
  marketData: MarketDataItem[],
): InterestStock[] {
  const lines = analysis
    .replace(/\r/g, "")
    .split("\n")
    .map((line) => line.trim())
    .filter(Boolean);

  const parsedItems: Array<{
    rank: number;
    header: string;
    type: string;
    change: number | null;
  }> = [];

  let currentItem: (typeof parsedItems)[number] | null = null;

  for (const line of lines) {
    const circledMatch = line.match(/^([①②③④⑤⑥⑦⑧⑨⑩])\s*(.+)$/);
    const numericMatch = line.match(/^(\d{1,2})[.)]\s*(.+)$/);
    const rank = circledMatch
      ? circledRankMap[circledMatch[1]]
      : numericMatch
        ? Number(numericMatch[1])
        : null;
    const header = circledMatch?.[2] ?? numericMatch?.[2];

    if (rank !== null && header && rank >= 1 && rank <= 10) {
      currentItem = {
        rank,
        header: header.trim(),
        type: "관심 종목",
        change: null,
      };
      parsedItems.push(currentItem);
      continue;
    }

    if (!currentItem) {
      continue;
    }

    const typeMatch = line.match(/^구분\s*:\s*(.+)$/);

    if (typeMatch) {
      currentItem.type = normalizeInterestType(typeMatch[1]);
      continue;
    }

    const changeMatch = line.match(/등락률\s*:\s*([+-]?\d+(?:\.\d+)?)\s*%/);

    if (changeMatch) {
      currentItem.change = Number(changeMatch[1]);
    }
  }

  return parsedItems
    .sort((a, b) => a.rank - b.rank)
    .slice(0, 5)
    .map((item, index) => {
      const tickerFromHeader = item.header.match(/\((\d{6})\)/)?.[1];
      const headerName = item.header.replace(/\(\d{6}\)/g, "").trim();
      const normalizedHeaderName = normalizeStockName(headerName);
      const matchedMarketItem = marketData.find(
        (marketItem) =>
          marketItem.ticker === tickerFromHeader ||
          normalizeStockName(marketItem.name) === normalizedHeaderName,
      );
      const change = item.change ?? matchedMarketItem?.month_return ?? 0;

      return {
        rank: String(index + 1).padStart(2, "0"),
        name: matchedMarketItem?.name ?? headerName,
        ticker: matchedMarketItem?.ticker ?? tickerFromHeader ?? "------",
        currentPrice: formatPrice(matchedMarketItem?.current_price),
        change,
        changeLabel: formatReturn(change),
        type: item.type,
        chart: createMiniChartPoints(change, index),
      };
    });
}

const NEWS_BATCH_SIZE = 5;

const agentSteps = [
  {
    number: "01",
    name: "Macro Agent",
    description: "뉴스에서 시장 흐름과 주요 이슈를 추출합니다.",
  },
  {
    number: "02",
    name: "Sector Agent",
    description: "수익률과 모멘텀 점수를 기준으로 종목을 분류합니다.",
  },
  {
    number: "03",
    name: "Interest Agent",
    description: "뉴스 언급과 가격 변동을 바탕으로 관심 종목을 선별합니다.",
  },
  {
    number: "04",
    name: "Summary Agent",
    description: "각 Agent 결과를 하나의 시장 브리핑으로 통합합니다.",
  },
];

const summarySignals = [
  {
    label: "시장 흐름",
    value: "변동성 확대",
    description:
      "코스피와 코스닥의 혼조 흐름이 확인돼 방향성보다 변동성 관리가 중요합니다.",
  },
  {
    label: "주요 테마",
    value: "AI 기업 이슈",
    description:
      "AI 기업의 상장 추진과 금융·산업 분야 AI 도입 뉴스가 집중됐습니다.",
  },
  {
    label: "확인 포인트",
    value: "선별적 관찰",
    description:
      "강세 종목과 단기 급등 종목을 구분하고 추격 매수보다 근거 확인이 필요합니다.",
  },
];

function toneClasses(tone: string) {
  if (tone === "positive") {
    return {
      text: "text-[var(--positive)]",
      dot: "bg-[var(--positive)]",
      background: "bg-[var(--positive-soft)]",
      border: "border-[#cce4da]",
    };
  }

  if (tone === "negative") {
    return {
      text: "text-[var(--negative)]",
      dot: "bg-[var(--negative)]",
      background: "bg-[var(--negative-soft)]",
      border: "border-[#eccbd0]",
    };
  }

  if (tone === "warning") {
    return {
      text: "text-[var(--warning)]",
      dot: "bg-[var(--warning)]",
      background: "bg-[var(--warning-soft)]",
      border: "border-[#e7dcae]",
    };
  }

  return {
    text: "text-[var(--primary)]",
    dot: "bg-[var(--primary)]",
    background: "bg-[var(--primary-soft)]",
    border: "border-[#cad8e2]",
  };
}

function MiniPriceChart({
  points,
  trend,
}: {
  points: string;
  trend: number;
}) {
  return (
    <svg
      viewBox="0 0 120 40"
      role="img"
      aria-label="최근 주가 흐름 미리보기"
      className="h-[38px] w-[110px]"
    >
      <line
        x1="0"
        y1="35"
        x2="120"
        y2="35"
        stroke="currentColor"
        strokeOpacity="0.12"
      />

      <polyline
        points={points}
        fill="none"
        stroke={trend < 0 ? "var(--negative)" : "var(--positive)"}
        strokeWidth="2.2"
        strokeLinecap="round"
        strokeLinejoin="round"
      />
    </svg>
  );
}

function SectionHeading({
  label,
  title,
  description,
}: {
  label: string;
  title: string;
  description?: string;
}) {
  return (
    <div className="flex flex-col justify-between gap-5 md:flex-row md:items-end">
      <div>
        <p className="text-[11px] font-semibold tracking-[0.16em] text-[var(--primary)] uppercase">
          {label}
        </p>

        <h2 className="mt-3 text-[34px] font-semibold tracking-[-0.045em] md:text-[44px]">
          {title}
        </h2>
      </div>

      {description && (
        <p className="max-w-md break-keep text-[14px] leading-7 text-[var(--muted)]">
          {description}
        </p>
      )}
    </div>
  );
}

function extractSectionSummary(text: string, marker: string) {
  const markerIndex = text.indexOf(marker);

  if (markerIndex === -1) {
    return "";
  }

  return text
    .slice(markerIndex + marker.length)
    .split("\n")
    .map((line) => line.trim())
    .filter(Boolean)[0] ?? "";
}

function extractMacroFlows(text: string) {
  return Array.from(text.matchAll(/시장 흐름:\s*([^\n]+)/g))
    .map((match) => match[1].trim())
    .slice(0, 2);
}

export default function BriefingPage() {
  const [briefing, setBriefing] = useState<BriefingResponse | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [visibleNewsCount, setVisibleNewsCount] = useState(NEWS_BATCH_SIZE);
  const [isSummaryExpanded, setIsSummaryExpanded] = useState(false);
  const [isMacroExpanded, setIsMacroExpanded] = useState(false);
  const [isSectorExpanded, setIsSectorExpanded] = useState(false);
  const [isInterestExpanded, setIsInterestExpanded] = useState(false);

  const summaryRef = useRef<HTMLDivElement>(null);
  const macroRef = useRef<HTMLElement>(null);
  const sectorRef = useRef<HTMLElement>(null);
  const interestRef = useRef<HTMLDivElement>(null);
  const newsSectionRef = useRef<HTMLElement>(null);
  const newsItemRefs = useRef<Record<number, HTMLAnchorElement | null>>({});

  const summaryDetailRef = useRef<HTMLDivElement>(null);
  const macroDetailRef = useRef<HTMLDivElement>(null);
  const sectorDetailRef = useRef<HTMLDivElement>(null);
  const interestDetailRef = useRef<HTMLDivElement>(null);

  function toggleReport(
    isExpanded: boolean,
    setExpanded: Dispatch<SetStateAction<boolean>>,
    sectionRef: RefObject<HTMLElement | HTMLDivElement | null>,
    detailRef: RefObject<HTMLDivElement | null>,
  ) {
    if (isExpanded) {
      setExpanded(false);

      window.setTimeout(() => {
        sectionRef.current?.scrollIntoView({
          behavior: "smooth",
          block: "start",
        });
      }, 120);

      return;
    }

    setExpanded(true);

    window.setTimeout(() => {
      detailRef.current?.scrollIntoView({
        behavior: "smooth",
        block: "start",
      });
    }, 120);
  }

  useEffect(() => {
    const controller = new AbortController();

    async function fetchBriefing() {
      try {
        setLoading(true);
        setError("");

        const response = await fetch(
          "http://127.0.0.1:8000/api/briefings/latest",
          {
            method: "GET",
            headers: {
              Accept: "application/json",
            },
            cache: "no-store",
            signal: controller.signal,
          },
        );

        if (!response.ok) {
          throw new Error(
            `브리핑 조회에 실패했습니다. 상태 코드: ${response.status}`,
          );
        }

        const data: BriefingResponse = await response.json();

        console.log("===== FinSight API 응답 =====");
        console.log(data);

        setBriefing(data);
        setVisibleNewsCount(NEWS_BATCH_SIZE);
        setIsSummaryExpanded(false);
        setIsMacroExpanded(false);
        setIsSectorExpanded(false);
        setIsInterestExpanded(false);
      } catch (err) {
        if (err instanceof DOMException && err.name === "AbortError") {
          return;
        }

        console.error("FinSight API 호출 오류:", err);
        setError("브리핑을 불러오지 못했습니다.");
      } finally {
        if (!controller.signal.aborted) {
          setLoading(false);
        }
      }
    }

    fetchBriefing();

    return () => {
      controller.abort();
    };
  }, []);

  if (loading) {
    return (
      <main className="flex min-h-screen items-center justify-center bg-white text-[var(--foreground)]">
        <div className="text-center">
          <span className="mx-auto block h-8 w-8 animate-spin rounded-full border-2 border-[#d5dce5] border-t-[var(--primary)]" />

          <p className="mt-5 text-[14px] font-medium text-[var(--muted)]">
            최신 브리핑을 불러오는 중입니다.
          </p>
        </div>
      </main>
    );
  }

  if (error) {
    return (
      <main className="flex min-h-screen items-center justify-center bg-white px-6 text-[var(--foreground)]">
        <div className="max-w-md text-center">
          <p className="text-[22px] font-semibold tracking-[-0.035em]">
            브리핑을 불러오지 못했습니다.
          </p>

          <p className="mt-4 break-keep text-[14px] leading-7 text-[var(--muted)]">
            FastAPI 서버가 실행 중인지 확인한 뒤 페이지를 새로고침해 주세요.
          </p>

          <p className="mt-2 text-[12px] text-[var(--negative)]">{error}</p>

          <button
            type="button"
            onClick={() => window.location.reload()}
            className="mt-7 rounded-[9px] bg-[var(--foreground)] px-5 py-3 text-[13px] font-semibold text-white transition-opacity hover:opacity-85"
          >
            다시 시도
          </button>
        </div>
      </main>
    );
  }

  if (!briefing) {
    return (
      <main className="flex min-h-screen items-center justify-center bg-white text-[var(--foreground)]">
        <p className="text-[14px] text-[var(--muted)]">
          표시할 브리핑 데이터가 없습니다.
        </p>
      </main>
    );
  }

  const createdAt = new Date(briefing.created_at);

  const formattedDate = new Intl.DateTimeFormat("ko-KR", {
    year: "numeric",
    month: "long",
    day: "numeric",
  }).format(createdAt);

  const formattedTime = new Intl.DateTimeFormat("ko-KR", {
    hour: "2-digit",
    minute: "2-digit",
    hour12: false,
  }).format(createdAt);

  const visibleNews = briefing.news_data.slice(0, visibleNewsCount);
  const hasMoreNews = visibleNewsCount < briefing.news_data.length;
  const isNewsExpanded =
    briefing.news_data.length > NEWS_BATCH_SIZE && !hasMoreNews;
  const macroFlows = extractMacroFlows(briefing.macro_analysis);
  const macroOverview =
    extractSectionSummary(briefing.macro_analysis, "[Macro Agent 종합]") ||
    "Macro Agent의 상세 분석에서 오늘 시장의 주요 흐름을 확인할 수 있습니다.";
  const sectorDistribution = extractSectorDistribution(
    briefing.sector_analysis,
    briefing.market_data,
  );
  const interestStocks = extractInterestStocks(
    briefing.interest_analysis,
    briefing.market_data,
  );

  function handleNewsToggle() {
    if (hasMoreNews) {
      const firstNewItemIndex = visibleNewsCount;

      setVisibleNewsCount((currentCount) =>
        Math.min(currentCount + NEWS_BATCH_SIZE, briefing.news_data.length),
      );

      window.setTimeout(() => {
        newsItemRefs.current[firstNewItemIndex]?.scrollIntoView({
          behavior: "smooth",
          block: "start",
        });
      }, 120);

      return;
    }

    setVisibleNewsCount(NEWS_BATCH_SIZE);

    window.setTimeout(() => {
      newsSectionRef.current?.scrollIntoView({
        behavior: "smooth",
        block: "start",
      });
    }, 120);
  }

  return (
    <main className="min-h-screen bg-white text-[var(--foreground)]">
      <header className="sticky top-0 z-50 border-b border-[#d1d8e1] bg-white/95 shadow-[0_1px_12px_rgba(15,23,42,0.035)] backdrop-blur-xl">
        <div className="fin-container flex h-[76px] items-center justify-between">
          <a
            href="/?opening=1"
            className="text-[25px] font-semibold tracking-[-0.055em]"
            aria-label="FinSight 오프닝과 랜딩 페이지로 이동"
          >
            FinSight
          </a>

          <nav className="hidden items-center gap-9 text-[14px] font-medium text-[var(--muted)] md:flex">
            <a
              href="#overview"
              className="text-[var(--foreground)] transition-colors hover:text-[var(--primary)]"
            >
              Overview
            </a>

            <a
              href="#market"
              className="transition-colors hover:text-[var(--foreground)]"
            >
              Market
            </a>

            <a
              href="#focus"
              className="transition-colors hover:text-[var(--foreground)]"
            >
              Focus
            </a>

            <a
              href="#news"
              className="transition-colors hover:text-[var(--foreground)]"
            >
              News
            </a>
          </nav>

          <div className="flex items-center gap-5">
            <span className="hidden items-center gap-2 text-[11px] font-semibold text-[var(--positive)] sm:flex">
              <span className="h-2 w-2 rounded-full bg-[var(--positive)]" />
              ANALYSIS COMPLETE
            </span>

            <a
              href="#summary"
              className="group relative inline-flex items-center gap-2 py-2 text-[13px] font-semibold text-[var(--foreground)] transition-colors hover:text-[var(--primary)]"
            >
              AI Briefing

              <span
                aria-hidden="true"
                className="text-[13px] transition-transform duration-200 group-hover:translate-y-0.5"
              >
                ↓
              </span>

              <span className="absolute right-0 bottom-0 left-0 h-px origin-left scale-x-0 bg-[var(--foreground)] transition-transform duration-200 group-hover:scale-x-100" />
            </a>
          </div>
        </div>
      </header>

      <section
        id="overview"
        className="fin-container pt-14 pb-12 md:pt-20 md:pb-16"
      >
        <div className="grid gap-12 border-b border-[#c9d1db] pb-14 lg:grid-cols-[1.2fr_0.8fr] lg:items-end">
          <div>
            <div className="flex flex-wrap items-center gap-x-4 gap-y-2 text-[12px] font-medium text-[var(--muted)]">
              <span>{formattedDate}</span>

              <span className="hidden h-3 w-px bg-[#c9d1db] sm:block" />

              <span>Morning Briefing</span>

              <span className="hidden h-3 w-px bg-[#c9d1db] sm:block" />

              <span className="text-[var(--positive)]">
                {formattedTime} Update
              </span>
            </div>

            <h1 className="mt-7 max-w-4xl text-[clamp(3rem,6vw,6.2rem)] leading-[0.98] font-semibold tracking-[-0.07em]">
              오늘 시장을
              <br />
              한 번에 읽는
              <br />
              브리핑.
            </h1>

            <p className="mt-8 max-w-2xl break-keep text-[16px] leading-8 text-[var(--muted)]">
              뉴스와 시장 데이터를 분석해 오늘 확인해야 할 흐름, 종목 분류,
              관심 종목과 근거를 하나의 순서로 정리했습니다.
            </p>
          </div>

          <aside className="rounded-[16px] border border-[#cbd3dd] bg-[#f7f9fb] p-6 shadow-[0_10px_32px_rgba(15,23,42,0.05)] sm:p-8">
            <div className="flex items-center justify-between border-b border-[#d5dce5] pb-5">
              <div>
                <p className="text-[11px] font-semibold tracking-[0.13em] text-[var(--muted-light)] uppercase">
                  Current Brief
                </p>

                <p className="mt-2 text-[17px] font-semibold">
                  오전 시장 분석 완료
                </p>
              </div>

              <span className="rounded-full border border-[#cce4da] bg-[var(--positive-soft)] px-3 py-1.5 text-[10px] font-semibold text-[var(--positive)]">
                COMPLETE
              </span>
            </div>

            <dl className="grid grid-cols-2 gap-px overflow-hidden rounded-[10px] bg-[#d8dee6] sm:grid-cols-4 lg:grid-cols-2">
              {[
                ["News", String(briefing.news_data.length).padStart(2, "0")],
                ["Stocks", String(briefing.market_data.length).padStart(2, "0")],
                ["Agents", "04"],
                ["Focus", "05"],
              ].map(([label, value]) => (
                <div key={label} className="bg-white p-5">
                  <dt className="text-[10px] font-semibold tracking-[0.12em] text-[var(--muted-light)] uppercase">
                    {label}
                  </dt>

                  <dd className="fin-tabular mt-3 text-[31px] font-semibold tracking-[-0.04em]">
                    {value}
                  </dd>
                </div>
              ))}
            </dl>
          </aside>
        </div>
      </section>

      <section
        id="summary"
        className="border-y border-[#c8d0da] bg-[#f7f9fb]"
      >
        <div ref={summaryRef} className="fin-container scroll-mt-24 py-16 md:py-24">
          <SectionHeading
            label="Summary Agent"
            title="오늘의 AI 브리핑"
            description="각 Agent의 분석 결과를 바탕으로 오늘 시장에서 먼저 확인해야 할 내용을 정리했습니다."
          />

          <div className="mt-12 overflow-hidden rounded-[18px] border border-[#cbd3dd] bg-white shadow-[0_12px_38px_rgba(15,23,42,0.055)]">
            <div className="grid lg:grid-cols-[0.9fr_1.1fr]">
              <article className="px-7 py-10 sm:px-9 lg:border-r lg:border-[#d1d8e1] lg:px-10 lg:py-12">
                <p className="text-[11px] font-semibold tracking-[0.12em] text-[var(--muted-light)] uppercase">
                  Briefing Overview
                </p>

                <h3 className="mt-5 max-w-xl text-[30px] leading-[1.3] font-semibold tracking-[-0.04em] sm:text-[38px]">
                  방향성보다 변동성 확인이 우선입니다.
                </h3>

                <p className="mt-6 max-w-xl break-keep text-[15px] leading-8 text-[var(--muted)]">
                  시장 변동성이 확대된 가운데 AI 관련 기업 뉴스가
                  증가했습니다. 강세 및 긍정 관찰 종목이 다수 확인됐지만 일부
                  종목은 단기 하락 흐름이 이어지고 있습니다.
                </p>

                <div className="mt-9 border-t border-[#d6dde6] pt-6">
                  <p className="text-[11px] font-semibold tracking-[0.12em] text-[var(--primary)] uppercase">
                    AI View
                  </p>

                  <p className="mt-3 max-w-xl break-keep text-[13px] leading-7 text-[var(--muted)]">
                    단기 급등 종목을 추격하기보다 뉴스 근거와 중장기 수익률을
                    함께 확인하는 접근이 필요합니다.
                  </p>
                </div>
              </article>

              <div className="divide-y divide-[#d7dee7] px-7 sm:px-9 lg:px-10">
                {summarySignals.map((signal, index) => (
                  <article
                    key={signal.label}
                    className="grid gap-5 py-8 sm:grid-cols-[42px_160px_1fr] sm:items-center"
                  >
                    <span className="fin-tabular text-[12px] font-semibold text-[var(--primary)]">
                      {String(index + 1).padStart(2, "0")}
                    </span>

                    <div>
                      <p className="text-[11px] font-semibold tracking-[0.1em] text-[var(--muted-light)] uppercase">
                        {signal.label}
                      </p>

                      <h3 className="mt-2 text-[19px] font-semibold tracking-[-0.025em]">
                        {signal.value}
                      </h3>
                    </div>

                    <p className="break-keep text-[13px] leading-7 text-[var(--muted)]">
                      {signal.description}
                    </p>
                  </article>
                ))}
              </div>
            </div>
          </div>


          {isSummaryExpanded && (
            <div ref={summaryDetailRef} className="scroll-mt-24 mt-8 overflow-hidden rounded-[18px] border border-[#cbd3dd] bg-white shadow-[0_12px_38px_rgba(15,23,42,0.055)]">
              <div className="border-b border-[#d7dee7] bg-[#f7f9fb] px-7 py-5 sm:px-9">
                <p className="text-[11px] font-semibold tracking-[0.12em] text-[var(--muted-light)] uppercase">
                  Detailed Analysis
                </p>
                <h3 className="mt-2 text-[22px] font-semibold tracking-[-0.03em]">
                  Summary Agent Report
                </h3>
              </div>
              <div className="whitespace-pre-line break-keep px-7 py-8 text-[15px] leading-8 text-[var(--foreground)] sm:px-9">
                {briefing.ai_summary}
              </div>
            </div>
          )}

          <div className="mt-7 flex justify-center">
            <button
              type="button"
              onClick={() =>
                toggleReport(
                  isSummaryExpanded,
                  setIsSummaryExpanded,
                  summaryRef,
                  summaryDetailRef,
                )
              }
              aria-label={isSummaryExpanded ? "Summary Report 접기" : "Summary Report 펼치기"}
              aria-expanded={isSummaryExpanded}
              className="group flex h-12 w-12 items-center justify-center rounded-full border border-[#d2d9e3] bg-white shadow-[0_14px_36px_rgba(15,23,42,0.14)] transition-all duration-300 hover:-translate-y-1 hover:shadow-[0_18px_45px_rgba(15,23,42,0.18)]"
            >
              <span
                aria-hidden="true"
                className={`text-[20px] font-bold text-black transition-transform duration-300 ${
                  isSummaryExpanded ? "rotate-180" : ""
                }`}
              >
                ↓
              </span>
            </button>
          </div>

          <p className="mt-3 text-center text-[11px] font-medium text-[var(--muted-light)]">
            {isSummaryExpanded
              ? "전체 Summary Report 표시 중 · 버튼을 누르면 접힙니다"
              : "Summary Report 펼쳐보기"}
          </p>
        </div>
      </section>

      <section className="bg-[#fcfcfd]">
        <div className="fin-container pt-16 pb-16 md:pt-20">
          <div className="grid items-start gap-14 border-b border-[#c9d1db] pb-16 lg:grid-cols-[1.05fr_0.95fr]">
            <article ref={macroRef} className="scroll-mt-24">
              <p className="text-[11px] font-semibold tracking-[0.15em] text-[var(--primary)] uppercase">
                Macro Agent
              </p>

              <h2 className="mt-3 max-w-3xl text-[clamp(2rem,4vw,3.8rem)] leading-[1.08] font-semibold tracking-[-0.055em]">
                오늘 시장에서 확인된
                <br />
                핵심 흐름입니다.
              </h2>

              <div className="mt-10 overflow-hidden rounded-[16px] border border-[#cbd3dd] bg-white shadow-[0_10px_32px_rgba(15,23,42,0.045)]">
                <div className="border-b border-[#d7dee7] bg-[#f7f9fb] px-7 py-5">
                  <p className="text-[11px] font-semibold tracking-[0.12em] text-[var(--muted-light)] uppercase">
                    AI Analysis
                  </p>

                  <h3 className="mt-2 text-[22px] font-semibold tracking-[-0.03em]">
                    Macro Agent Report
                  </h3>
                </div>

                <div className="px-7 py-8">
                  <div className="grid gap-7">
                    <div>
                      <p className="text-[11px] font-semibold tracking-[0.1em] text-[var(--muted-light)] uppercase">
                        핵심 흐름
                      </p>
                      <p className="mt-3 text-[19px] font-semibold tracking-[-0.025em]">
                        {macroFlows[0] ?? "오늘 시장의 주요 흐름을 확인했습니다."}
                      </p>
                    </div>

                    {macroFlows[1] && (
                      <div className="border-t border-[#d7dee7] pt-7">
                        <p className="text-[11px] font-semibold tracking-[0.1em] text-[var(--muted-light)] uppercase">
                          추가 흐름
                        </p>
                        <p className="mt-3 text-[17px] font-semibold tracking-[-0.02em]">
                          {macroFlows[1]}
                        </p>
                      </div>
                    )}

                    <div className="border-t border-[#d7dee7] pt-7">
                      <p className="text-[11px] font-semibold tracking-[0.12em] text-[var(--primary)] uppercase">
                        AI View
                      </p>
                      <p className="mt-3 break-keep text-[14px] leading-7 text-[var(--muted)]">
                        {macroOverview}
                      </p>
                    </div>
                  </div>

                  {isMacroExpanded && (
                    <div ref={macroDetailRef} className="scroll-mt-24 mt-8 border-t border-[#d7dee7] pt-8">
                      <p className="mb-5 text-[11px] font-semibold tracking-[0.12em] text-[var(--muted-light)] uppercase">
                        Detailed Analysis
                      </p>
                      <div className="whitespace-pre-line break-keep text-[15px] leading-8 text-[var(--foreground)]">
                        {briefing.macro_analysis}
                      </div>
                    </div>
                  )}
                </div>
              </div>

              <div className="mt-7 flex justify-center">
                <button
                  type="button"
                  onClick={() =>
                    toggleReport(
                      isMacroExpanded,
                      setIsMacroExpanded,
                      macroRef,
                      macroDetailRef,
                    )
                  }
                  aria-label={isMacroExpanded ? "Macro Report 접기" : "Macro Report 펼치기"}
                  aria-expanded={isMacroExpanded}
                  className="group flex h-12 w-12 items-center justify-center rounded-full border border-[#d2d9e3] bg-white shadow-[0_14px_36px_rgba(15,23,42,0.14)] transition-all duration-300 hover:-translate-y-1 hover:shadow-[0_18px_45px_rgba(15,23,42,0.18)]"
                >
                  <span
                    aria-hidden="true"
                    className={`text-[20px] font-bold text-black transition-transform duration-300 ${
                      isMacroExpanded ? "rotate-180" : ""
                    }`}
                  >
                    ↓
                  </span>
                </button>
              </div>

              <p className="mt-3 text-center text-[11px] font-medium text-[var(--muted-light)]">
                {isMacroExpanded
                  ? "전체 Macro Report 표시 중 · 버튼을 누르면 접힙니다"
                  : "Macro Report 펼쳐보기"}
              </p>
            </article>

            <aside>
              <div className="flex items-start justify-between gap-5">
                <div>
                  <p className="text-[11px] font-semibold tracking-[0.15em] text-[var(--primary)] uppercase">
                    Agent Process
                  </p>

                  <h3 className="mt-3 text-[25px] font-semibold tracking-[-0.04em]">
                    브리핑 생성 과정
                  </h3>
                </div>

                <span className="text-[11px] font-semibold text-[var(--positive)]">
                  4 / 4 완료
                </span>
              </div>

              <p className="mt-4 max-w-md break-keep text-[13px] leading-6 text-[var(--muted)]">
                각 Agent가 역할별 분석을 수행한 뒤 Summary Agent가 결과를 하나의
                브리핑으로 정리합니다.
              </p>

              <ol className="mt-8 overflow-hidden rounded-[16px] border border-[#cbd3dd] bg-white px-6 shadow-[0_10px_32px_rgba(15,23,42,0.045)]">
                {agentSteps.map((agent, index) => (
                  <li
                    key={agent.name}
                    className="grid grid-cols-[44px_1fr] gap-5 border-b border-[#d7dee7] py-7 last:border-b-0 sm:grid-cols-[48px_1fr_auto]"
                  >
                    <span className="fin-tabular pt-0.5 text-[12px] font-semibold text-[var(--primary)]">
                      {agent.number}
                    </span>

                    <div>
                      <h4 className="text-[16px] font-semibold">{agent.name}</h4>

                      <p className="mt-2 break-keep text-[13px] leading-6 text-[var(--muted)]">
                        {agent.description}
                      </p>
                    </div>

                    <span className="col-start-2 flex items-center gap-2 text-[10px] font-semibold text-[var(--positive)] sm:col-start-auto sm:justify-self-end">
                      <span className="h-1.5 w-1.5 rounded-full bg-[var(--positive)]" />
                      COMPLETE
                    </span>

                    {index < agentSteps.length - 1 && (
                      <span className="sr-only">다음 단계로 이동</span>
                    )}
                  </li>
                ))}
              </ol>
            </aside>
          </div>
        </div>
      </section>

      <section
        ref={sectorRef}
        id="market"
        className="fin-container scroll-mt-24 py-16 md:py-24"
      >
        <SectionHeading
          label="Sector Agent"
          title="시장 데이터 분류"
          description="1개월·3개월·1년 수익률을 반영한 모멘텀 점수를 기준으로 종목 흐름을 분류했습니다."
        />

        <div className="mt-10 grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
          {sectorDistribution.map((group) => {
            const tone = toneClasses(group.tone);

            return (
              <article
                key={group.title}
                className="min-h-[255px] rounded-[16px] border border-[#cbd3dd] bg-white p-6 shadow-[0_7px_24px_rgba(15,23,42,0.035)] transition-all duration-300 hover:-translate-y-1 hover:shadow-[0_12px_32px_rgba(15,23,42,0.06)]"
              >
                <div className="flex items-start justify-between">
                  <div>
                    <span
                      className={`block h-2.5 w-2.5 rounded-full ${tone.dot}`}
                    />

                    <h3 className="mt-5 text-[17px] font-semibold">
                      {group.title}
                    </h3>
                  </div>

                  <span
                    className={`fin-tabular text-[42px] font-semibold tracking-[-0.06em] ${tone.text}`}
                  >
                    {String(group.stocks.length).padStart(2, "0")}
                  </span>
                </div>

                <div className="mt-8 flex flex-wrap gap-2">
                  {group.stocks.map((stock) => (
                    <span
                      key={stock}
                      className={`rounded-[7px] border px-3 py-2 text-[12px] font-semibold ${tone.border} ${tone.background} ${tone.text}`}
                    >
                      {stock}
                    </span>
                  ))}
                </div>
              </article>
            );
          })}
        </div>


        {isSectorExpanded && (
          <div ref={sectorDetailRef} className="scroll-mt-24 mt-8 overflow-hidden rounded-[16px] border border-[#cbd3dd] bg-white shadow-[0_10px_32px_rgba(15,23,42,0.045)]">
            <div className="border-b border-[#d7dee7] bg-[#f7f9fb] px-7 py-5">
              <p className="text-[11px] font-semibold tracking-[0.12em] text-[var(--muted-light)] uppercase">
                Detailed Analysis
              </p>
              <h3 className="mt-2 text-[22px] font-semibold tracking-[-0.03em]">
                Sector Agent Report
              </h3>
            </div>
            <div className="whitespace-pre-line break-keep px-7 py-8 text-[15px] leading-8 text-[var(--foreground)]">
              {briefing.sector_analysis}
            </div>
          </div>
        )}

        <div className="mt-7 flex justify-center">
          <button
            type="button"
            onClick={() =>
              toggleReport(
                isSectorExpanded,
                setIsSectorExpanded,
                sectorRef,
                sectorDetailRef,
              )
            }
            aria-label={isSectorExpanded ? "Sector Report 접기" : "Sector Report 펼치기"}
            aria-expanded={isSectorExpanded}
            className="group flex h-12 w-12 items-center justify-center rounded-full border border-[#d2d9e3] bg-white shadow-[0_14px_36px_rgba(15,23,42,0.14)] transition-all duration-300 hover:-translate-y-1 hover:shadow-[0_18px_45px_rgba(15,23,42,0.18)]"
          >
            <span
              aria-hidden="true"
              className={`text-[20px] font-bold text-black transition-transform duration-300 ${
                isSectorExpanded ? "rotate-180" : ""
              }`}
            >
              ↓
            </span>
          </button>
        </div>

        <p className="mt-3 text-center text-[11px] font-medium text-[var(--muted-light)]">
          {isSectorExpanded
            ? "전체 Sector Report 표시 중 · 버튼을 누르면 접힙니다"
            : "Sector Report 펼쳐보기"}
        </p>
      </section>

      <section
        id="focus"
        className="border-y border-[#c8d0da] bg-[#fafbfc]"
      >
        <div
          ref={interestRef}
          className="fin-container scroll-mt-24 py-16 md:py-24"
        >
          <SectionHeading
            label="Interest Agent"
            title="오늘의 관심 종목"
            description="급등률과 뉴스 언급을 기준으로 오늘 우선 확인할 종목을 정리했습니다."
          />

          <div className="mt-10 overflow-hidden rounded-[16px] border border-[#cbd3dd] bg-white shadow-[0_10px_32px_rgba(15,23,42,0.045)]">
            <div className="hidden grid-cols-[70px_1.1fr_0.8fr_0.7fr_0.8fr_120px_30px] gap-5 border-b border-[#cbd3dd] bg-[#f4f6f8] px-6 py-4 text-[11px] font-semibold tracking-[0.08em] text-[var(--muted-light)] uppercase md:grid">
              <span>Rank</span>
              <span>종목</span>
              <span>현재가</span>
              <span>등락률</span>
              <span>유형</span>
              <span>최근 흐름</span>
              <span />
            </div>

            {interestStocks.length === 0 && (
              <div className="px-6 py-12 text-center text-[14px] text-[var(--muted)]">
                Interest Agent 분석에서 표시할 관심 종목을 찾지 못했습니다.
              </div>
            )}

            {interestStocks.map((stock) => (
              <a
                key={`${stock.ticker}-${stock.rank}`}
                href={`/stocks/${stock.ticker}`}
                className="group grid gap-5 border-b border-[#d7dee7] px-6 py-6 transition-colors last:border-b-0 hover:bg-[#f8fafc] md:grid-cols-[70px_1.1fr_0.8fr_0.7fr_0.8fr_120px_30px] md:items-center"
              >
                <span className="fin-tabular text-[13px] font-semibold text-[var(--primary)]">
                  {stock.rank}
                </span>

                <div>
                  <p className="text-[16px] font-semibold">{stock.name}</p>

                  <p className="mt-1 text-[11px] text-[var(--muted)]">
                    {stock.ticker}
                  </p>
                </div>

                <p className="fin-tabular text-[14px] font-semibold">
                  {stock.currentPrice}
                </p>

                <p
                  className={`fin-tabular text-[15px] font-semibold ${
                    stock.change < 0
                      ? "text-[var(--negative)]"
                      : stock.change > 0
                        ? "text-[var(--positive)]"
                        : "text-[var(--muted)]"
                  }`}
                >
                  {stock.changeLabel}
                </p>

                <div>
                  <span className="inline-flex rounded-full border border-[#cce4da] bg-[var(--positive-soft)] px-3 py-1.5 text-[11px] font-semibold text-[var(--positive)]">
                    {stock.type}
                  </span>
                </div>

                <MiniPriceChart points={stock.chart} trend={stock.change} />

                <span className="text-[14px] text-[var(--muted-light)] transition-transform group-hover:translate-x-1">
                  →
                </span>
              </a>
            ))}
          </div>

          <p className="mt-5 max-w-2xl break-keep text-[12px] leading-6 text-[var(--muted)]">
            단기 급등 종목은 뉴스 근거와 거래 흐름을 함께 확인해야 하며,
            등락률만을 근거로 판단하지 않는 것이 중요합니다.
          </p>


          {isInterestExpanded && (
            <div ref={interestDetailRef} className="scroll-mt-24 mt-8 overflow-hidden rounded-[16px] border border-[#cbd3dd] bg-white shadow-[0_10px_32px_rgba(15,23,42,0.045)]">
              <div className="border-b border-[#d7dee7] bg-[#f7f9fb] px-7 py-5">
                <p className="text-[11px] font-semibold tracking-[0.12em] text-[var(--muted-light)] uppercase">
                  Detailed Analysis
                </p>
                <h3 className="mt-2 text-[22px] font-semibold tracking-[-0.03em]">
                  Interest Agent Report
                </h3>
              </div>
              <div className="whitespace-pre-line break-keep px-7 py-8 text-[15px] leading-8 text-[var(--foreground)]">
                {briefing.interest_analysis}
              </div>
            </div>
          )}

          <div className="mt-7 flex justify-center">
            <button
              type="button"
              onClick={() =>
                toggleReport(
                  isInterestExpanded,
                  setIsInterestExpanded,
                  interestRef,
                  interestDetailRef,
                )
              }
              aria-label={isInterestExpanded ? "Interest Report 접기" : "Interest Report 펼치기"}
              aria-expanded={isInterestExpanded}
              className="group flex h-12 w-12 items-center justify-center rounded-full border border-[#d2d9e3] bg-white shadow-[0_14px_36px_rgba(15,23,42,0.14)] transition-all duration-300 hover:-translate-y-1 hover:shadow-[0_18px_45px_rgba(15,23,42,0.18)]"
            >
              <span
                aria-hidden="true"
                className={`text-[20px] font-bold text-black transition-transform duration-300 ${
                  isInterestExpanded ? "rotate-180" : ""
                }`}
              >
                ↓
              </span>
            </button>
          </div>

          <p className="mt-3 text-center text-[11px] font-medium text-[var(--muted-light)]">
            {isInterestExpanded
              ? "전체 Interest Report 표시 중 · 버튼을 누르면 접힙니다"
              : "Interest Report 펼쳐보기"}
          </p>
        </div>
      </section>

      <section
        id="news"
        ref={newsSectionRef}
        className="fin-container scroll-mt-[92px] py-16 md:py-24"
      >
        <div className="grid gap-12 lg:grid-cols-[0.42fr_1fr]">
          <div>
            <p className="text-[11px] font-semibold tracking-[0.16em] text-[var(--primary)] uppercase">
              News Sources
            </p>

            <h2 className="mt-3 text-[34px] font-semibold tracking-[-0.055em] md:text-[44px]">
              분석에 사용된
              <br />
              주요 뉴스
            </h2>

            <p className="mt-6 max-w-sm text-[14px] leading-7 text-[var(--muted)]">
              각 뉴스는 원문으로 바로 이동할 수 있으며 새 탭에서 열립니다.
            </p>

          </div>

          <div>
            <div className="overflow-hidden rounded-[16px] border border-[#cbd3dd] bg-white px-6 shadow-[0_10px_32px_rgba(15,23,42,0.04)]">
              {visibleNews.map((news, index) => {
                const sourceParts = news.source.trim().split(/\s+/);
                const sourceName = sourceParts[0] ?? news.source;
                const category =
                  sourceParts.length > 1
                    ? sourceParts.slice(1).join(" ")
                    : "시장";

                return (
                  <a
                    key={`${news.link}-${index}`}
                    ref={(element) => {
                      newsItemRefs.current[index] = element;
                    }}
                    href={news.link}
                    target="_blank"
                    rel="noopener noreferrer"
                    className="group grid scroll-mt-[92px] gap-4 border-b border-[#d7dee7] py-7 last:border-b-0 sm:grid-cols-[66px_76px_1fr_90px_24px] sm:items-center"
                  >
                    <span className="fin-tabular text-[12px] font-semibold text-[var(--muted-light)]">
                      {String(index + 1).padStart(2, "0")}
                    </span>

                    <span className="text-[11px] font-semibold text-[var(--muted)]">
                      {category}
                    </span>

                    <h3 className="text-[16px] leading-7 font-medium transition-transform duration-200 group-hover:translate-x-1 group-hover:text-[var(--primary)]">
                      {news.title}
                    </h3>

                    <span className="text-[12px] text-[var(--muted)]">
                      {sourceName}
                    </span>

                    <span className="text-[15px] text-[var(--muted-light)] transition-transform group-hover:translate-x-1">
                      ↗
                    </span>
                  </a>
                );
              })}
            </div>

            {briefing.news_data.length > NEWS_BATCH_SIZE && (
              <>
                <div className="mt-7 flex justify-center">
                  <button
                    type="button"
                    onClick={handleNewsToggle}
                    aria-label={
                      hasMoreNews
                        ? "뉴스 더 보기"
                        : "뉴스 목록 처음 상태로 접기"
                    }
                    aria-expanded={isNewsExpanded}
                    className="group flex h-12 w-12 items-center justify-center rounded-full border border-[#d2d9e3] bg-white shadow-[0_14px_36px_rgba(15,23,42,0.14)] transition-all duration-300 hover:-translate-y-1 hover:shadow-[0_18px_45px_rgba(15,23,42,0.18)]"
                  >
                    <span
                      aria-hidden="true"
                      className={`text-[20px] font-bold text-black transition-transform duration-300 ${
                        hasMoreNews ? "" : "rotate-180"
                      }`}
                    >
                      ↓
                    </span>
                  </button>
                </div>

                <p className="mt-3 text-center text-[11px] font-medium text-[var(--muted-light)]">
                  {hasMoreNews
                    ? `${Math.min(
                        visibleNewsCount,
                        briefing.news_data.length,
                      )} / ${briefing.news_data.length}개 표시 중`
                    : "전체 뉴스 표시 중 · 버튼을 누르면 접힙니다"}
                </p>
              </>
            )}
          </div>
        </div>
      </section>

      <footer className="border-t border-[#c8d0da] bg-[#f4f7fa]">
        <div className="fin-container py-11">
          <div className="flex flex-col justify-between gap-8 border-b border-[#d3dae3] pb-10 sm:flex-row sm:items-end">
            <div>
              <p className="text-[23px] font-semibold tracking-[-0.05em]">
                FinSight
              </p>

              <p className="mt-2 text-[13px] text-[var(--muted)]">
                시장을 더 짧고 명확하게.
              </p>
            </div>

            <nav className="flex flex-wrap gap-7 text-[13px] font-medium text-[var(--muted)]">
              <a
                href="#overview"
                className="transition-colors hover:text-[var(--foreground)]"
              >
                Overview
              </a>

              <a
                href="#market"
                className="transition-colors hover:text-[var(--foreground)]"
              >
                Market
              </a>

              <a
                href="#focus"
                className="transition-colors hover:text-[var(--foreground)]"
              >
                Focus
              </a>

              <a
                href="#news"
                className="transition-colors hover:text-[var(--foreground)]"
              >
                News
              </a>
            </nav>
          </div>

          <div className="flex flex-col justify-between gap-3 pt-6 text-[11px] leading-5 text-[var(--muted-light)] sm:flex-row">
            <p>© 2026 FinSight.</p>

            <p>
              본 서비스의 정보는 투자 참고용이며 최종 판단은 사용자에게
              있습니다.
            </p>
          </div>
        </div>
      </footer>
    </main>
  );
}