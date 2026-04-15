import { beforeEach, describe, expect, it, vi } from "vitest";

const mockGet = vi.fn();
const mockPost = vi.fn();
const mockPatch = vi.fn();

vi.mock("axios", () => {
  return {
    default: {
      create: () => ({
        get: mockGet,
        post: mockPost,
        patch: mockPatch,
        interceptors: {
          request: { use: vi.fn() },
          response: { use: vi.fn() },
        },
      }),
    },
  };
});

describe("api service critical paths", () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it("usa alias de rota para analise de rota", async () => {
    mockPost.mockResolvedValueOnce({ data: { id: "route-1" } });
    const { routesApi } = await import("@/app/services/api");

    const result = await routesApi.analyzeRoute("ABC1D23");

    expect(mockPost).toHaveBeenCalledWith("/intelligence/routes/analyze", {
      plate_number: "ABC1D23",
    });
    expect(result).toEqual({ id: "route-1" });
  });

  it("consulta fila analitica no endpoint esperado", async () => {
    mockGet.mockResolvedValueOnce({ data: [] });
    const { intelligenceApi } = await import("@/app/services/api");

    const result = await intelligenceApi.getQueue({ plate_number: "ABC1D23" });

    expect(mockGet).toHaveBeenCalledWith("/intelligence/queue", {
      params: { plate_number: "ABC1D23" },
    });
    expect(result).toEqual([]);
  });
});
