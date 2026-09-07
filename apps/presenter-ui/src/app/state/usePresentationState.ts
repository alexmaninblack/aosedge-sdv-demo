import { useReducer } from "react";
import { initialPresentationState, presentationReducer, type Perspective } from "../../domain";

export function usePresentationState(perspective: Perspective = "platform") {
  return useReducer(presentationReducer, { ...initialPresentationState, perspective });
}
