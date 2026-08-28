import { useReducer } from "react";
import { initialPresentationState, presentationReducer } from "../../domain";

export function usePresentationState() {
  return useReducer(presentationReducer, initialPresentationState);
}
