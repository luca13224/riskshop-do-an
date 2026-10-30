import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query"

import { apiFetch } from "./client"

export interface LabScenario {
  code: string
  title: string
  scene: string
  description: string
  expected: string
}

export interface LabStep {
  actor: string
  action: string
  result: string
  expected: string | null
  ok: boolean | null
}

export interface LabRun {
  id: number
  scenario: string
  status: "queued" | "running" | "done" | "failed"
  run_tag: string
  steps: LabStep[]
  summary: string | null
  passed: boolean | null
  created_at: string
  finished_at: string | null
}

export function useLabScenarios() {
  return useQuery({
    queryKey: ["console", "lab", "scenarios"],
    queryFn: () => apiFetch<LabScenario[]>("/api/console/lab/scenarios"),
    retry: false,
  })
}

export function useLabRuns() {
  return useQuery({
    queryKey: ["console", "lab", "runs"],
    queryFn: () => apiFetch<LabRun[]>("/api/console/lab/runs"),
    // Đang có kịch bản chạy thì hỏi lại mỗi giây để thấy từng bước hiện ra
    refetchInterval: (query) =>
      query.state.data?.some(
        (r) => r.status === "queued" || r.status === "running"
      )
        ? 1000
        : 5000,
  })
}

export function useStartLabRun() {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: (scenario: string) =>
      apiFetch<LabRun>("/api/console/lab/runs", {
        method: "POST",
        body: JSON.stringify({ scenario }),
      }),
    onSuccess: () =>
      queryClient.invalidateQueries({ queryKey: ["console", "lab", "runs"] }),
  })
}
