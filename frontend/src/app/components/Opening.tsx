"use client";

import { useEffect, useState } from "react";

interface OpeningProps {
  onExitStart: () => void;
  onComplete: () => void;
}

type OpeningPhase =
  | "scatter"
  | "gather"
  | "reveal"
  | "settle"
  | "exit";

interface InformationItem {
  label: string;
  left: string;
  top: string;
  size: string;
  weight: string;
  duration: number;
  delay: number;
}

const informationItems: InformationItem[] = [
  {
    label: "MARKET NEWS",
    left: "14%",
    top: "17%",
    size: "text-[18px] md:text-[25px]",
    weight: "font-semibold",
    duration: 760,
    delay: 0,
  },
  {
    label: "STOCK DATA",
    left: "76%",
    top: "16%",
    size: "text-[15px] md:text-[21px]",
    weight: "font-medium",
    duration: 930,
    delay: 50,
  },
  {
    label: "MACRO",
    left: "25%",
    top: "36%",
    size: "text-[24px] md:text-[34px]",
    weight: "font-semibold",
    duration: 820,
    delay: 90,
  },
  {
    label: "MOMENTUM",
    left: "81%",
    top: "38%",
    size: "text-[17px] md:text-[23px]",
    weight: "font-medium",
    duration: 1040,
    delay: 20,
  },
  {
    label: "NEWS",
    left: "9%",
    top: "63%",
    size: "text-[28px] md:text-[42px]",
    weight: "font-semibold",
    duration: 720,
    delay: 120,
  },
  {
    label: "SECTOR",
    left: "69%",
    top: "67%",
    size: "text-[23px] md:text-[32px]",
    weight: "font-semibold",
    duration: 890,
    delay: 40,
  },
  {
    label: "AI AGENTS",
    left: "27%",
    top: "82%",
    size: "text-[16px] md:text-[23px]",
    weight: "font-medium",
    duration: 1080,
    delay: 100,
  },
  {
    label: "BRIEFING",
    left: "82%",
    top: "84%",
    size: "text-[21px] md:text-[30px]",
    weight: "font-semibold",
    duration: 960,
    delay: 150,
  },
  {
    label: "INTEREST",
    left: "50%",
    top: "12%",
    size: "text-[14px] md:text-[19px]",
    weight: "font-medium",
    duration: 850,
    delay: 70,
  },
  {
    label: "PRICE FLOW",
    left: "48%",
    top: "90%",
    size: "text-[15px] md:text-[21px]",
    weight: "font-medium",
    duration: 1100,
    delay: 10,
  },
  {
    label: "ECONOMY",
    left: "51%",
    top: "29%",
    size: "text-[18px] md:text-[26px]",
    weight: "font-semibold",
    duration: 780,
    delay: 130,
  },
  {
    label: "ANALYSIS",
    left: "51%",
    top: "71%",
    size: "text-[18px] md:text-[27px]",
    weight: "font-semibold",
    duration: 1010,
    delay: 80,
  },
];

export default function Opening({
  onExitStart,
  onComplete,
}: OpeningProps) {
  const [phase, setPhase] = useState<OpeningPhase>("scatter");

  useEffect(() => {
    const gatherTimer = window.setTimeout(() => {
      setPhase("gather");
    }, 1050);

    const revealTimer = window.setTimeout(() => {
      setPhase("reveal");
    }, 2250);

    const settleTimer = window.setTimeout(() => {
      setPhase("settle");
    }, 2700);

    const exitTimer = window.setTimeout(() => {
      setPhase("exit");
      onExitStart();
    }, 3550);

    const completeTimer = window.setTimeout(() => {
      onComplete();
    }, 4350);

    return () => {
      window.clearTimeout(gatherTimer);
      window.clearTimeout(revealTimer);
      window.clearTimeout(settleTimer);
      window.clearTimeout(exitTimer);
      window.clearTimeout(completeTimer);
    };
  }, [onExitStart, onComplete]);

  const isGathering =
    phase === "gather" ||
    phase === "reveal" ||
    phase === "settle" ||
    phase === "exit";

  const isRevealed =
    phase === "reveal" || phase === "settle" || phase === "exit";

  const isSettled = phase === "settle" || phase === "exit";
  const isExiting = phase === "exit";

  return (
    <div
      className={[
        "fixed inset-0 z-[9999] overflow-hidden bg-[#fafafa] text-black",
        "transition-all duration-[850ms]",
        "ease-[cubic-bezier(0.76,0,0.24,1)]",
        isExiting
          ? "pointer-events-none -translate-y-3 opacity-0"
          : "translate-y-0 opacity-100",
      ].join(" ")}
    >
      <div className="absolute inset-0">
        {informationItems.map((item) => (
          <span
            key={item.label}
            className={[
              "absolute whitespace-nowrap tracking-[-0.025em]",
              item.size,
              item.weight,
              "ease-[cubic-bezier(0.76,0,0.24,1)]",
            ].join(" ")}
            style={{
              left: isGathering ? "50%" : item.left,
              top: isGathering ? "50%" : item.top,
              color: "#111111",
              opacity: isRevealed ? 0 : isGathering ? 0.3 : 0.86,
              transform: isGathering
                ? "translate(-50%, -50%) scale(0.48)"
                : "translate(-50%, -50%) scale(1)",
              filter: isRevealed ? "blur(10px)" : "blur(0px)",
              transitionProperty:
                "left, top, opacity, transform, filter",
              transitionDuration: `${item.duration}ms`,
              transitionDelay: isGathering
                ? `${item.delay}ms`
                : "0ms",
            }}
          >
            {item.label}
          </span>
        ))}
      </div>

      <div
        className={[
          "absolute left-1/2 top-1/2 h-px -translate-x-1/2",
          "bg-black transition-all duration-500",
          "ease-[cubic-bezier(0.76,0,0.24,1)]",
          phase === "gather"
            ? "w-24 opacity-100"
            : "w-0 opacity-0",
        ].join(" ")}
      />

      <div className="absolute inset-0 flex items-center justify-center">
        <div
          className={[
            "flex flex-col items-center",
            "transition-all duration-500",
            "ease-[cubic-bezier(0.22,1,0.36,1)]",
            !isRevealed
              ? "translate-y-4 scale-[0.94] opacity-0 blur-sm"
              : "",
            phase === "reveal"
              ? "translate-y-0 scale-[1.035] opacity-100 blur-0"
              : "",
            isSettled && !isExiting
              ? "translate-y-0 scale-100 opacity-100 blur-0"
              : "",
            isExiting
              ? "-translate-y-5 scale-[1.015] opacity-0 blur-0"
              : "",
          ].join(" ")}
        >
          <h1 className="text-[clamp(3.6rem,9vw,7.5rem)] font-semibold tracking-[-0.075em] text-black">
            FinSight
          </h1>

          <div
            className={[
              "mt-6 h-px overflow-hidden bg-black",
              "transition-all delay-150 duration-700",
              isRevealed ? "w-32 md:w-44" : "w-0",
            ].join(" ")}
          />

          <p
            className={[
              "mt-5 text-[10px] font-semibold tracking-[0.3em]",
              "text-black/55 transition-all delay-300 duration-700",
              isRevealed
                ? "translate-y-0 opacity-100"
                : "translate-y-2 opacity-0",
            ].join(" ")}
          >
            AI MARKET BRIEFING
          </p>
        </div>
      </div>

      <div
        className={[
          "absolute bottom-8 left-1/2 -translate-x-1/2",
          "whitespace-nowrap text-[10px] font-semibold",
          "tracking-[0.24em] text-black/50",
          "transition-opacity duration-500",
          phase === "scatter" || phase === "gather"
            ? "opacity-100"
            : "opacity-0",
        ].join(" ")}
      >
        INFORMATION · FILTERING · INSIGHT
      </div>
    </div>
  );
}