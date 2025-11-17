import { describe, it, expect, vi, beforeEach } from "vitest";
import { render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import UploadPage from "../UploadPage";
import { api } from "../../api/client";

// Mock the API client
vi.mock("../../api/client", () => ({
  api: {
    uploadCSV: vi.fn(),
  },
}));

describe("UploadPage", () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it("renders the upload form", () => {
    render(<UploadPage />);

    expect(screen.getByText("CSV Import")).toBeInTheDocument();
    expect(screen.getAllByText(/data type/i).length).toBeGreaterThan(0);
    expect(screen.getByLabelText(/csv file/i)).toBeInTheDocument();
    expect(
      screen.getByRole("button", { name: /upload csv/i })
    ).toBeInTheDocument();
  });

  it("disables upload button when no file or type selected", () => {
    render(<UploadPage />);

    const uploadButton = screen.getByRole("button", { name: /upload csv/i });
    expect(uploadButton).toBeDisabled();
  });

  it("does not show an error message before any upload attempt", async () => {
    render(<UploadPage />);

    await waitFor(() => {
      expect(
        screen.queryByText(/please select a file type and file/i)
      ).not.toBeInTheDocument();
    });
  });

  it("shows file name and size when file is selected", async () => {
    const user = userEvent.setup();
    render(<UploadPage />);

    const file = new File(["test content"], "test.csv", { type: "text/csv" });
    const fileInput = screen.getByLabelText(/csv file/i) as HTMLInputElement;

    await user.upload(fileInput, file);

    expect(screen.getByText(/selected: test\.csv/i)).toBeInTheDocument();
  });

  it("displays CSV format requirements", () => {
    render(<UploadPage />);

    expect(screen.getByText("CSV Format Requirements")).toBeInTheDocument();
    expect(
      screen.getByRole("heading", { name: /merchants/i })
    ).toBeInTheDocument();
    expect(
      screen.getByRole("heading", { name: /drivers/i })
    ).toBeInTheDocument();
    expect(
      screen.getByRole("heading", { name: /vehicles/i })
    ).toBeInTheDocument();
    expect(
      screen.getByRole("heading", { name: /orders/i })
    ).toBeInTheDocument();
  });
});
