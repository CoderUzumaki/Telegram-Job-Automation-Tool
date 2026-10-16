import { render, screen } from "@testing-library/react";
import { describe, expect, it } from "vitest";
import App from "./App";

describe("desktop welcome screen", () => {
  it("shows the product name and setup state without sample user data", () => {
    render(<App />);

    expect(screen.getByRole("heading", { name: "Find the roles worth your attention." })).toBeTruthy();
    expect(screen.getByRole("status").textContent).toContain("Ready for setup");
    expect(screen.queryByText(/company|salary|python intern/i)).toBeNull();
  });
});
