import { describe, it, expect, vi, beforeEach, beforeAll } from "vitest";
import { render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import OrdersPage from "../OrdersPage";
import type { Order } from "../../types";
import { api, getAuth } from "../../api/client";

// Mock the API client module
vi.mock("../../api/client", () => ({
  api: {
    getOrders: vi.fn(),
    getMerchants: vi.fn(),
    createOrder: vi.fn(),
    updateOrder: vi.fn(),
    cancelOrder: vi.fn(),
  },
  getAuth: vi.fn(),
}));

beforeAll(() => {
  if (!globalThis.ResizeObserver) {
    vi.stubGlobal(
      "ResizeObserver",
      class {
        observe() {}
        unobserve() {}
        disconnect() {}
      }
    );
  }

  if (!window.matchMedia) {
    Object.defineProperty(window, "matchMedia", {
      writable: true,
      value: vi.fn().mockImplementation((query: string) => ({
        matches: false,
        media: query,
        onchange: null,
        addListener: vi.fn(),
        removeListener: vi.fn(),
        addEventListener: vi.fn(),
        removeEventListener: vi.fn(),
        dispatchEvent: vi.fn(),
      })),
    });
  }
});

describe("OrdersPage", () => {
  beforeEach(() => {
    vi.clearAllMocks();

    vi.mocked(getAuth).mockReturnValue({
      accessToken: "test-token",
      merchant: { id: 1, name: "Test Merchant", email: "test@example.com" },
    });
  });

  it("renders the orders page", async () => {
    vi.mocked(api.getOrders).mockResolvedValue({
      orders: [],
      total: 0,
      page: 1,
      per_page: 20,
      total_pages: 0,
    });

    render(<OrdersPage />);

    await waitFor(() => {
      expect(screen.getByText("Orders")).toBeInTheDocument();
      expect(screen.getByText("Test Merchant")).toBeInTheDocument();
    });
  });

  it("loads and displays orders", async () => {
    const mockOrders: Order[] = [
      {
        order_id: 1,
        merchant_id: 1,
        status: "pending",
        description: "Test Order",
        pickup_time: "2025-01-20T10:00:00",
        dropoff_time: "2025-01-20T12:00:00",
        weight: 50.5,
      },
    ];

    vi.mocked(api.getOrders).mockResolvedValue({
      orders: mockOrders,
      total: 1,
      page: 1,
      per_page: 20,
      total_pages: 1,
    });

    render(<OrdersPage />);

    await waitFor(() => {
      expect(screen.getByText("Test Order")).toBeInTheDocument();
      expect(screen.getByText("pending")).toBeInTheDocument();
    });
  });

  it("opens create order dialog", async () => {
    const user = userEvent.setup();

    vi.mocked(api.getOrders).mockResolvedValue({
      orders: [],
      total: 0,
      page: 1,
      per_page: 20,
      total_pages: 0,
    });

    render(<OrdersPage />);

    await waitFor(() => {
      expect(screen.getByText("Create Order")).toBeInTheDocument();
    });

    const createButton = screen.getByRole("button", { name: /create order/i });
    await user.click(createButton);

    await waitFor(() => {
      expect(screen.getByText("Create Order")).toBeInTheDocument();
      expect(screen.getByText(/fill in the details/i)).toBeInTheDocument();
    });
  });
});
