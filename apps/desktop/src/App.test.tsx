import { render, screen } from "@testing-library/react";
import { describe, expect, it } from "vitest";
import App from "./App";

describe("desktop first-run experience", () => {
  it("introduces Job Radar and asks for the user’s own preferences without sample job data", () => {
    render(<App />);

    expect(screen.getByRole("heading", { name: "Your search. Your direction." })).toBeTruthy();
    expect(screen.getByLabelText("Role or kind of work")).toBeTruthy();
    expect(screen.getByLabelText("Where would you like to work?")).toBeTruthy();
    expect(screen.getByRole("button", { name: /continue/i })).toBeTruthy();
    expect(screen.queryByText(/emma wilson|python intern|\$120,000/i)).toBeNull();
  });
});
