import type { PresentationAction, PresentationState } from "./model";

export const initialPresentationState: PresentationState = {
  perspective: "platform",
  openOverlay: null,
  scrollByTeam: { platform: 0, brake: 0, tire: 0 },
  focusByTeam: { platform: null, brake: null, tire: null },
  actionNotice: null,
};

export function presentationReducer(state: PresentationState, action: PresentationAction): PresentationState {
  switch (action.type) {
    case "navigate":
      return { ...state, perspective: action.perspective, openOverlay: null, actionNotice: null };
    case "remember-team":
      return {
        ...state,
        scrollByTeam: { ...state.scrollByTeam, [action.team]: action.scroll },
        focusByTeam: { ...state.focusByTeam, [action.team]: action.focus },
      };
    case "open-details":
      return { ...state, openOverlay: { kind: "details", team: action.team, releaseId: action.releaseId } };
    case "open-logs":
      return { ...state, openOverlay: { kind: "logs", team: action.team } };
    case "open-action":
      return {
        ...state,
        openOverlay: { kind: "action", team: action.team, releaseId: action.releaseId, action: action.action },
      };
    case "close-overlay":
      return { ...state, openOverlay: null };
    case "confirm-fixture-action":
      return {
        ...state,
        openOverlay: null,
        actionNotice: `${action.action} · fixture presentation updated only · no external operation submitted`,
      };
  }
}
