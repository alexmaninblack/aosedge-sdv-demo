import { useEffect, useRef } from "react";
import type { PresentationAction, PresentationState, PresenterSnapshot, TeamId } from "../domain";
import { BrakeEvidence, BrakeHeading, BrakeReleaseStory, BrakeSummaries } from "../features/brake-team";
import { PlatformEvidence, PlatformHeading, PlatformReleaseStory, PlatformSummaries } from "../features/platform-team";
import { ReleaseAuthorityLine } from "../features/release-authority";
import { TireEvidence, TireHeading, TireReleaseStory, TireSummaries } from "../features/tire-team";
import { ProducerWorkspaceLayout } from "../shared/layout";
import { vehicleLabel } from "./SharedHeader";

export function ProducerWorkspace({ teamId, snapshot, presentation, dispatch }: {
  teamId: TeamId;
  snapshot: PresenterSnapshot;
  presentation: PresentationState;
  dispatch: React.Dispatch<PresentationAction>;
}) {
  const releaseRef = useRef<HTMLDivElement>(null);
  const restoredTeam = useRef<TeamId | null>(null);
  const team = snapshot.teams[teamId];

  useEffect(() => {
    if (restoredTeam.current === teamId) return;
    restoredTeam.current = teamId;
    const scroller = releaseRef.current;
    if (!scroller) return;
    scroller.scrollTop = presentation.scrollByTeam[teamId];
    const focusId = presentation.focusByTeam[teamId];
    if (focusId) requestAnimationFrame(() => scroller.querySelector<HTMLElement>(`[data-focus-id="${focusId}"]`)?.focus());
  }, [teamId, presentation.focusByTeam, presentation.scrollByTeam]);

  const onDetails = (releaseId: string) => dispatch({ type: "open-details", team: teamId, releaseId });
  const onAction = (releaseId: string, action: string) => dispatch({ type: "open-action", team: teamId, releaseId, action });
  const onLogs = () => dispatch({ type: "open-logs", team: teamId });
  const label = vehicleLabel(snapshot.vehicle.value);

  let heading;
  let summaries;
  let evidence;
  let releases;
  if (teamId === "platform") {
    heading = <PlatformHeading team={team} />;
    summaries = <PlatformSummaries team={team} vehicleLabel={label} />;
    evidence = <PlatformEvidence team={team} assetFailure={snapshot.assetFailure} onLogs={onLogs} />;
    releases = <PlatformReleaseStory team={team} assetFailure={snapshot.assetFailure} onDetails={onDetails} onAction={onAction} />;
  } else if (teamId === "brake") {
    heading = <BrakeHeading team={team} />;
    summaries = <BrakeSummaries team={team} vehicleLabel={label} />;
    evidence = <BrakeEvidence team={team} assetFailure={snapshot.assetFailure} onLogs={onLogs} />;
    releases = <BrakeReleaseStory team={team} assetFailure={snapshot.assetFailure} onDetails={onDetails} onAction={onAction} />;
  } else {
    heading = <TireHeading team={team} />;
    summaries = <TireSummaries team={team} vehicleLabel={label} />;
    evidence = <TireEvidence team={team} assetFailure={snapshot.assetFailure} onLogs={onLogs} onAction={(action) => dispatch({ type: "open-action", team: teamId, action })} />;
    releases = <TireReleaseStory team={team} assetFailure={snapshot.assetFailure} onDetails={onDetails} onAction={onAction} />;
  }

  return (
    <ProducerWorkspaceLayout
      heading={heading}
      authority={<ReleaseAuthorityLine assetFailure={snapshot.assetFailure} />}
      summaries={summaries}
      evidence={evidence}
      releases={releases}
      releaseRef={releaseRef}
      onReleaseScroll={() => dispatch({ type: "remember-team", team: teamId, scroll: releaseRef.current?.scrollTop ?? 0, focus: presentation.focusByTeam[teamId] })}
      onFocusCapture={(focus) => dispatch({ type: "remember-team", team: teamId, scroll: releaseRef.current?.scrollTop ?? 0, focus })}
    />
  );
}
