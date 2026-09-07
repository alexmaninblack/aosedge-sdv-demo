import { useEffect, useRef } from "react";
import type { PresentationAction, PresentationState, PresenterSnapshot, TeamId } from "../domain";
import { BrakeEvidence, BrakeHeading, BrakeReleaseStory, BrakeSummaries } from "../features/brake-team";
import { PlatformEvidence, PlatformHeading, PlatformReleaseStory, PlatformSummaries } from "../features/platform-team";
import { ReleaseAuthorityLine } from "../features/release-authority";
import { TireEvidence, TireHeading, TireReleaseStory, TireSummaries } from "../features/tire-team";
import { ProducerWorkspaceLayout } from "../shared/layout";
import { vehicleLabel } from "./SharedHeader";
import { LocalPlatformControls } from "../features/platform-team/LocalPlatformControls";
import { usePlatformObservation } from "./state/PresenterReadModelProvider";
import { projectCloudPlatform } from "../domain";

export function ProducerWorkspace({ teamId, snapshot, presentation, dispatch }: {
  teamId: TeamId;
  snapshot: PresenterSnapshot;
  presentation: PresentationState;
  dispatch: React.Dispatch<PresentationAction>;
}) {
  const releaseRef = useRef<HTMLDivElement>(null);
  const restoredTeam = useRef<TeamId | null>(null);
  const cloud = usePlatformObservation();
  const localPlatform = Boolean(snapshot.localDemo && teamId === "platform");
  const team = localPlatform ? projectCloudPlatform(snapshot.teams[teamId], cloud.observation) : snapshot.teams[teamId];

  useEffect(() => {
    if (localPlatform && window.location.hash !== "#native-header") cloud.refresh();
  }, [localPlatform, cloud.refresh]);

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

  if (snapshot.localDemo && teamId !== "platform") return <div className="global-page">
    <header className="page-head"><div><h1>{team.name}</h1><p>This integration follows the Test Vehicle Platform pass.</p></div></header>
    <section className="lifecycle-block"><h2>Not connected</h2><p>Navigation remains available. Service publication, deployment and backend evidence are outside this increment; no successful result is simulated.</p></section>
  </div>;

  let heading;
  let summaries;
  let evidence;
  let releases;
  if (teamId === "platform") {
    heading = <PlatformHeading team={team} />;
    summaries = <PlatformSummaries team={team} vehicleLabel={label} />;
    evidence = <PlatformEvidence team={team} assetFailure={snapshot.assetFailure} onLogs={onLogs} cloud={localPlatform ? cloud : undefined} />;
    releases = <>{snapshot.localDemo && <LocalPlatformControls />}<PlatformReleaseStory team={team} assetFailure={snapshot.assetFailure} onDetails={onDetails} onAction={onAction} /></>;
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
