import { Icon } from "../../shared/components";

export function ReleaseAuthorityLine({ assetFailure }: { assetFailure: boolean }) {
  return (
    <section className="authority-line" aria-label="OEM Release Authority">
      <Icon name="authority" label="OEM Release Authority" broken={assetFailure} />
      <div>
        <b>OEM Release Authority</b>
        <p>Independent from producer teams; reviews evidence and authorizes the exact Test or Production deployment. AosCloud executes.</p>
      </div>
    </section>
  );
}
