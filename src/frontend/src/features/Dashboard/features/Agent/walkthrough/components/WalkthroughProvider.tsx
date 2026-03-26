import { useEffect } from "react";
import { useWalkthrough } from "../hooks/useWalkthrough";
import { useWalkthroughStore } from "../store/useWalkthroughStore";
import { PopoverLayer } from "./PopoverLayer";
import { SpotlightOverlay } from "./SpotlightOverlay";
import "./walkthrough.css";

export function WalkthroughProvider({ tabId }: { tabId: string }) {
  const controls = useWalkthrough(tabId);

  useEffect(() => {
    useWalkthroughStore.getState().setControls(controls);
    return () => useWalkthroughStore.getState().setControls(null);
  }, [controls]);

  return (
    <>
      <SpotlightOverlay />
      <PopoverLayer />
    </>
  );
}
