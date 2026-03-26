import { useEffect } from "react";
import { useWalkthrough } from "../hooks/useWalkthrough";
import { useWalkthroughStore } from "../store/useWalkthroughStore";
import { PopoverLayer } from "./PopoverLayer";
import { SpotlightOverlay } from "./SpotlightOverlay";
import { WalkthroughPlaybackBar } from "./WalkthroughPlaybackBar";
import "./walkthrough.css";

export function WalkthroughProvider({ tabId }: { tabId: string }) {
  const controls = useWalkthrough(tabId);
  const playbackDetached = useWalkthroughStore((s) => s.playbackDetached);

  useEffect(() => {
    useWalkthroughStore.getState().setControls(controls);
    return () => useWalkthroughStore.getState().setControls(null);
  }, [controls]);

  return (
    <>
      <SpotlightOverlay />
      <PopoverLayer />
      {playbackDetached ? (
        <div className="pointer-events-none absolute inset-x-0 bottom-8 z-45 flex justify-center px-4">
          <div className="pointer-events-auto w-full max-w-md min-w-0">
            <WalkthroughPlaybackBar placement="floating" />
          </div>
        </div>
      ) : null}
    </>
  );
}
