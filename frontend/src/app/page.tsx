"use client";

import { useCallback, useState } from "react";
import Opening from "./components/Opening";

const agents = [
  {
    name: "Macro Agent",
    role: "시장 전체의 흐름",
    description:
      "경제·산업·증권 뉴스에서 오늘 시장을 설명하는 주요 흐름을 찾습니다.",
  },
  {
    name: "Sector Agent",
    role: "종목의 강약 분류",
    description:
      "기간별 수익률과 모멘텀을 기준으로 종목의 현재 흐름을 구분합니다.",
  },
  {
    name: "Interest Agent",
    role: "관심 종목 선별",
    description:
      "뉴스 언급과 가격 움직임을 함께 보고 오늘 확인할 종목을 찾습니다.",
  },
  {
    name: "Summary Agent",
    role: "최종 브리핑 정리",
    description:
      "각 Agent의 결과를 연결해 하나의 짧고 구조적인 브리핑으로 만듭니다.",
  },
];

export default function Home() {
  const [openingComplete, setOpeningComplete] = useState(false);

  const handleExitStart = useCallback(() => {
    // 랜딩 페이지는 항상 표시 상태로 유지합니다.
    // Opening 컴포넌트가 위에서 덮고 있으므로 별도 상태 변경이 필요하지 않습니다.
  }, []);

  const handleOpeningComplete = useCallback(() => {
    setOpeningComplete(true);
  }, []);

  return (
    <>
      {!openingComplete && (
        <Opening
          onExitStart={handleExitStart}
          onComplete={handleOpeningComplete}
        />
      )}

      <main
        id="top"
        className="min-h-screen translate-y-0 bg-[#f5f7fa] text-[var(--foreground)] opacity-100"
      >
        <header className="sticky top-0 z-40 border-b border-[#d8dee6] bg-white/95 shadow-[0_1px_14px_rgba(15,23,42,0.04)] backdrop-blur-xl">
          <div className="fin-container flex h-[72px] items-center justify-between">
            <a
              href="#top"
              className="text-[21px] font-semibold tracking-[-0.045em]"
              aria-label="랜딩 페이지 상단으로 이동"
            >
              FinSight
            </a>

            <nav className="flex items-center gap-7 text-[13px] font-medium text-[var(--muted)]">
              <a
                href="#agents"
                className="transition-colors hover:text-[var(--foreground)]"
              >
                Agents
              </a>

              <a
                href="/briefing"
                className="transition-colors hover:text-[var(--foreground)]"
              >
                Briefing
              </a>
            </nav>
          </div>
        </header>

        <section className="bg-white">
          <div className="fin-container py-10 md:py-16">
            <article className="relative overflow-hidden rounded-[18px] border border-[#d8dee6] bg-[linear-gradient(135deg,#ffffff_0%,#f8fafc_55%,#f0f5fb_100%)] shadow-[0_20px_70px_rgba(15,23,42,0.06)]">
              <div
                aria-hidden="true"
                className="pointer-events-none absolute right-[-180px] top-[-220px] h-[520px] w-[520px] rounded-full bg-[radial-gradient(circle,rgba(59,130,246,0.13)_0%,rgba(59,130,246,0.04)_42%,transparent_72%)]"
              />

              <div
                aria-hidden="true"
                className="pointer-events-none absolute bottom-[-240px] left-[-190px] h-[460px] w-[460px] rounded-full bg-[radial-gradient(circle,rgba(148,163,184,0.12)_0%,rgba(148,163,184,0.035)_40%,transparent_72%)]"
              />

              <div className="relative px-7 sm:px-10 md:px-14">
                <div className="flex items-center justify-between border-b border-[#dce2e9] py-5">
                  <p className="text-[12px] font-semibold text-[var(--muted)]">
                    AI 기반 시장 브리핑
                  </p>

                  <p className="text-[10px] font-semibold tracking-[0.22em] text-[var(--primary)] sm:text-[11px]">
                    NEWS · DATA · AGENTS
                  </p>
                </div>

                <div className="grid gap-12 py-16 md:grid-cols-[1.15fr_0.85fr] md:items-end md:py-24">
                  <div>
                    <p className="mb-7 text-[11px] font-semibold tracking-[0.18em] text-[var(--muted-light)]">
                      MARKET INTELLIGENCE
                    </p>

                    <h1 className="max-w-3xl text-[clamp(2.6rem,5.2vw,5rem)] font-semibold leading-[1.04] tracking-[-0.06em]">
                      흩어진 시장 정보를
                      <br />
                      하나의 흐름으로.
                    </h1>
                  </div>

                  <div className="md:pb-2">
                    <div className="mb-6 h-[2px] w-12 bg-[var(--primary)]" />

                    <p className="max-w-md break-keep text-[15px] leading-7 text-[var(--muted)] md:text-[16px] md:leading-8">
                      FinSight는 경제 뉴스와 시장 데이터를 수집하고, 역할별
                      AI Agent가 분석한 결과를 하나의 구조적인 브리핑으로
                      정리합니다.
                    </p>
                  </div>
                </div>

                <div className="flex flex-col justify-between gap-5 border-t border-[#dce2e9] py-5 sm:flex-row sm:items-center">
                  <div className="flex items-center gap-3">
                    <span className="h-1.5 w-1.5 rounded-full bg-[var(--primary)]" />

                    <p className="text-[11px] font-semibold tracking-[0.08em] text-[var(--muted)]">
                      POWERED BY MULTI-AGENT AI WORKFLOW
                    </p>
                  </div>

                  <a
                    href="#agents"
                    className="group inline-flex items-center gap-3 text-[13px] font-semibold transition-colors hover:text-[var(--primary)]"
                  >
                    분석 과정 보기

                    <span
                      aria-hidden="true"
                      className="transition-transform duration-300 group-hover:translate-y-1"
                    >
                      ↓
                    </span>
                  </a>
                </div>
              </div>
            </article>
          </div>
        </section>

        <section
          id="agents"
          className="border-y border-[#d8dee6] bg-[#eef2f6]"
        >
          <div className="fin-container py-20 md:py-28">
            <div className="mb-10 flex flex-col justify-between gap-5 sm:flex-row sm:items-end">
              <div>
                <p className="text-[12px] font-semibold text-[var(--muted)]">
                  FinSight Agents
                </p>

                <h2 className="mt-3 text-[30px] font-semibold tracking-[-0.045em] md:text-[40px]">
                  각 Agent가 맡은 역할
                </h2>
              </div>

              <p className="max-w-sm break-keep text-[13px] leading-6 text-[var(--muted)]">
                하나의 AI가 모든 분석을 처리하지 않고, 역할별 Agent가 분석한
                결과를 하나의 흐름으로 연결합니다.
              </p>
            </div>

            <div className="grid overflow-hidden rounded-[16px] border border-[#ccd5df] bg-[#ccd5df] shadow-[0_18px_55px_rgba(15,23,42,0.06)] sm:grid-cols-2">
              {agents.map((agent, index) => (
                <article
                  key={agent.name}
                  className={[
                    "group min-h-[270px] bg-white p-7 transition-colors duration-300 sm:p-9",
                    "hover:bg-[#f8fafc]",
                    index % 2 === 1
                      ? "sm:border-l sm:border-[#ccd5df]"
                      : "",
                    index >= 2 ? "border-t border-[#ccd5df]" : "",
                  ].join(" ")}
                >
                  <div className="flex items-start justify-between gap-5">
                    <p className="fin-tabular text-[12px] font-semibold text-[#8793a1]">
                      0{index + 1}
                    </p>

                    <span className="rounded-full border border-[#cbd9e4] bg-[#edf4f8] px-3 py-1.5 text-[11px] font-semibold text-[var(--primary)]">
                      {agent.role}
                    </span>
                  </div>

                  <div className="mt-14">
                    <div className="mb-5 h-[2px] w-8 bg-[var(--primary)] transition-all duration-300 group-hover:w-12" />

                    <h3 className="text-[25px] font-semibold tracking-[-0.04em]">
                      {agent.name}
                    </h3>

                    <p className="mt-4 max-w-md break-keep text-[14px] leading-7 text-[var(--muted)]">
                      {agent.description}
                    </p>
                  </div>
                </article>
              ))}
            </div>
          </div>
        </section>

        <section className="bg-white">
          <div className="fin-container py-20 md:py-28">
            <article className="relative overflow-hidden rounded-[18px] border border-[#d5dce4] bg-white px-7 py-10 shadow-[0_18px_55px_rgba(15,23,42,0.05)] sm:px-10 md:px-14 md:py-14">
              <div
                aria-hidden="true"
                className="pointer-events-none absolute right-[-120px] top-[-150px] h-[320px] w-[320px] rounded-full bg-[radial-gradient(circle,rgba(59,130,246,0.09)_0%,transparent_70%)]"
              />

              <div className="relative grid gap-10 md:grid-cols-[1fr_auto] md:items-center">
                <div>
                  <div className="flex items-center gap-3">
                    <span className="h-2 w-2 rounded-full bg-[var(--primary)]" />

                    <p className="text-[12px] font-semibold text-[var(--muted)]">
                      Daily Briefing
                    </p>
                  </div>

                  <h2 className="mt-5 text-[30px] font-semibold tracking-[-0.045em] md:text-[40px]">
                    분석 결과는 브리핑에서 확인합니다.
                  </h2>

                  <p className="mt-5 max-w-xl break-keep text-[14px] leading-7 text-[var(--muted)]">
                    시장 흐름, 종목 분류, 관심 종목과 분석 근거를 하나의
                    페이지에서 빠르게 확인할 수 있습니다.
                  </p>
                </div>

                <a
                  href="/briefing"
                  className="group relative inline-flex items-center gap-3 py-3 text-[15px] font-semibold text-[var(--foreground)] transition-colors duration-300 hover:text-[var(--primary)]"
                >
                  Briefing

                  <span
                    aria-hidden="true"
                    className="transition-transform duration-300 group-hover:translate-x-1"
                  >
                    →
                  </span>

                  <span
                    aria-hidden="true"
                    className="absolute right-0 bottom-1 left-0 h-px origin-left scale-x-0 bg-[var(--primary)] transition-transform duration-300 group-hover:scale-x-100"
                  />
                </a>
              </div>
            </article>
          </div>
        </section>

        <footer className="border-t border-[#d7dde5] bg-[#eef2f6]">
          <div className="fin-container py-10">
            <div className="flex flex-col justify-between gap-8 border-b border-[#d5dce4] pb-9 sm:flex-row sm:items-end">
              <div>
                <p className="text-[23px] font-semibold tracking-[-0.05em]">
                  FinSight
                </p>

                <p className="mt-2 text-[13px] text-[var(--muted)]">
                  시장을 더 짧고 명확하게.
                </p>
              </div>

              <nav className="flex items-center gap-7 text-[13px] font-medium text-[var(--muted)]">
                <a
                  href="#agents"
                  className="transition-colors hover:text-[var(--foreground)]"
                >
                  Agents
                </a>

                <a
                  href="/briefing"
                  className="transition-colors hover:text-[var(--foreground)]"
                >
                  Briefing
                </a>
              </nav>
            </div>

            <div className="flex flex-col justify-between gap-3 pt-6 text-[11px] leading-5 text-[var(--muted-light)] sm:flex-row">
              <p>© 2026 FinSight.</p>

              <p className="break-keep">
                본 서비스의 정보는 투자 참고용이며 최종 판단은 사용자에게
                있습니다.
              </p>
            </div>
          </div>
        </footer>
      </main>
    </>
  );
}