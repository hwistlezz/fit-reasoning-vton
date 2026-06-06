"use client";

import { useEffect, useMemo, useState } from "react";
import { useSearchParams } from "next/navigation";
import ComparePageTemplate from "./ComparePageTemplate";
import { fetchDemoSamples, fetchModelCompare } from "@/lib/api";
import { getMockModelCompare, mockSamples } from "@/lib/mockData";
import type { DemoCompareResponse, DemoSample } from "@/lib/types";

export default function ComparePageClient() {
  const searchParams = useSearchParams();
  const selectedPairId = searchParams.get("pairId") ?? mockSamples[0].pair_id;
  const activeKey = `model:${selectedPairId}`;
  const initialData = useMemo(
    () => getMockModelCompare(selectedPairId),
    [selectedPairId],
  );
  const [loaded, setLoaded] = useState<{
    key: string;
    samples: DemoSample[];
    data: DemoCompareResponse;
  }>({
    key: activeKey,
    samples: mockSamples,
    data: initialData,
  });

  useEffect(() => {
    let ignore = false;

    async function loadData() {
      const [nextSamples, nextData] = await Promise.all([
        fetchDemoSamples(),
        fetchModelCompare(selectedPairId),
      ]);

      if (!ignore) {
        setLoaded({
          key: activeKey,
          samples: nextSamples,
          data: nextData,
        });
      }
    }

    void loadData();

    return () => {
      ignore = true;
    };
  }, [activeKey, selectedPairId]);

  const renderedData = loaded.key === activeKey ? loaded.data : initialData;
  const renderedSamples =
    loaded.key === activeKey ? loaded.samples : mockSamples;

  return <ComparePageTemplate data={renderedData} samples={renderedSamples} />;
}
