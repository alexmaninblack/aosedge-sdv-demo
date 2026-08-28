import { StrictMode } from "react";
import { createRoot } from "react-dom/client";
import { PresenterApp } from "./app/PresenterApp";
import { createPresenterDependencies } from "./app/composition/createPresenterDependencies";
import { PresenterReadModelProvider } from "./app/state/PresenterReadModelProvider";
import "./shared/design-tokens/global.css";

const root = document.getElementById("root");
if (!root) throw new Error("Presenter UI root element is missing");
const dependencies = createPresenterDependencies(window.location);

createRoot(root).render(
  <StrictMode>
    <PresenterReadModelProvider dependencies={dependencies}>
      <PresenterApp />
    </PresenterReadModelProvider>
  </StrictMode>,
);
