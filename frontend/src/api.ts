import { useEffect, useState } from "react";

export class ApiError extends Error {
  status: number;
  code?: string;
  fields: Record<string, string>;

  constructor(message: string, status: number, fields: Record<string, string> = {}, code?: string) {
    super(message);
    this.name = "ApiError";
    this.status = status;
    this.fields = fields;
    this.code = code;
  }
}

export async function api<T>(path: string, init?: RequestInit): Promise<T> {
  let response: Response;
  try {
    response = await fetch(`/api${path}`, {
      ...init,
      headers: {
        Accept: "application/json",
        ...(init?.body ? { "Content-Type": "application/json" } : {}),
        ...init?.headers,
      },
    });
  } catch (error) {
    if (error instanceof DOMException && error.name === "AbortError") throw error;
    throw new ApiError("Northstar can't reach the server.", 0);
  }
  if (response.status === 204) return undefined as T;
  const payload = await response.json().catch(() => null);
  if (!response.ok) {
    const error = payload?.error;
    throw new ApiError(error?.message || "Something went wrong.", response.status, error?.fields || {}, error?.code);
  }
  return payload as T;
}

export function useFetch<T>(path: string | null) {
  const [data, setData] = useState<T | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(Boolean(path));
  const [tick, setTick] = useState(0);

  useEffect(() => {
    if (!path) {
      setData(null);
      setError(null);
      setLoading(false);
      return;
    }
    const controller = new AbortController();
    setLoading(true);
    setError(null);
    setData(null);
    api<T>(path, { signal: controller.signal })
      .then((next) => {
        setData(next);
        setLoading(false);
      })
      .catch((caught: unknown) => {
        if (caught instanceof DOMException && caught.name === "AbortError") return;
        setError(caught instanceof Error ? caught.message : "Something went wrong.");
        setLoading(false);
      });
    return () => controller.abort();
  }, [path, tick]);

  return { data, error, loading, reload: () => setTick((value) => value + 1) };
}
