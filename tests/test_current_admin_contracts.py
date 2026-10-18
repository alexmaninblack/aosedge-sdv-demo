# SPDX-FileCopyrightText: 2026 maninblack
# SPDX-License-Identifier: MIT

"""Current-admin conformance, separate from immutable legacy compatibility tests."""
import copy
import json
from pathlib import Path
import subprocess
import shutil
import runpy
import unittest

ROOT = Path(__file__).resolve().parents[1]
API = runpy.run_path(str(ROOT / "scripts/admin_contract_check.py"))
ContractError, check, document, schema_keywords, validate = (
    API[name] for name in ("ContractError", "check", "document", "schema_keywords", "validate"))


class CurrentAdminContracts(unittest.TestCase):
    def data(self, team):
        folder = ROOT / "contracts" / (team + "-cloud-api")
        return document(folder / "current-admin.schema.json"), document(folder / "fixtures/current-admin.valid.json")

    def test_current_profiles_and_backend_declarations(self):
        self.assertEqual(check(ROOT, workspace=True), [])

    def test_closed_messages_and_boundaries(self):
        for team in ("brake", "tire"):
            schema, fixtures = self.data(team)
            for name, original in fixtures.items():
                if name == "$comment":
                    continue
                ref = {"$ref": "#/$defs/" + name}
                with self.subTest(team=team, message=name):
                    validate(original, ref, schema)
                    for mutate in (lambda v: v.update(extra=True), lambda v: v.pop("schemaVersion"),
                                   lambda v: v.update(schemaVersion=True)):
                        value = copy.deepcopy(original); mutate(value)
                        with self.assertRaises(ContractError):
                            validate(value, ref, schema)
            for name in ("previewRequest", "executeRequest", "preview", "result"):
                for uids in ([], ["a-test", "a-test"], ["a", "b", "c"], ["bad uid"]):
                    value = copy.deepcopy(fixtures[name]); value["systemUids"] = uids
                    with self.assertRaises(ContractError):
                        validate(value, {"$ref": "#/$defs/" + name}, schema)
            for bad in (-1, True, 1.2, "0"):
                value = copy.deepcopy(fixtures["preview"]); value["recordCounts"]["messages"] = bad
                with self.assertRaises(ContractError):
                    validate(value, {"$ref": "#/$defs/preview"}, schema)

    def test_old_six_counter_previews_cannot_pass_as_current(self):
        for team in ("brake", "tire"):
            schema, _ = self.data(team)
            legacy = document(ROOT / "contracts" / (team + "-cloud-api") / "fixtures/cleanup-preview.valid.json")
            with self.assertRaises(ContractError):
                validate(legacy, {"$ref": "#/$defs/preview"}, schema)

    def test_zero_postcondition_and_empty_proof_are_not_cosmetic_labels(self):
        for team in ("brake", "tire"):
            schema, fixtures = self.data(team)
            value = copy.deepcopy(fixtures["result"])
            field = "remainingMatchingRecordCounts" if team == "brake" else "remainingRecordCounts"
            value[field]["resetCommands"] = 1
            with self.assertRaises(ContractError):
                validate(value, {"$ref": "#/$defs/result"}, schema)
            value = copy.deepcopy(fixtures["proof"]); value["recordCounts"]["messages"] = 1
            with self.assertRaises(ContractError):
                validate(value, {"$ref": "#/$defs/proof"}, schema)
            value["state"] = "NONEMPTY"; validate(value, {"$ref": "#/$defs/proof"}, schema)
            value["recordCounts"]["messages"] = 0
            with self.assertRaises(ContractError):
                validate(value, {"$ref": "#/$defs/proof"}, schema)

    def test_protocols_are_not_normalized_into_one_shape(self):
        brake, b = self.data("brake"); tire, t = self.data("tire")
        for value, schema in ((b["preview"], tire), (t["preview"], brake)):
            with self.assertRaises(ContractError):
                validate(value, {"$ref": "#/$defs/preview"}, schema)
        for team, invalid, stale in (("brake", "PREVIEW_TOKEN_EXPIRED", "PREVIEW_STALE"),
                                     ("tire", "INVALID_PREVIEW", "STALE_PREVIEW")):
            profile = document(ROOT / "contracts" / (team + "-cloud-api") / "current-admin-profile.v1.json")
            self.assertEqual((profile["token"]["invalidCode"], profile["token"]["staleCode"]), (invalid, stale))

    def test_unknown_keywords_in_unselected_branch_fail(self):
        schema, _ = self.data("tire")
        schema["$defs"]["proof"]["allOf"][0]["else"]["unsupported"] = True
        with self.assertRaises(ContractError):
            schema_keywords(schema)

    def test_bundle_requires_endpoint_selection_not_an_open_root_validator(self):
        for team in ("brake", "tire"):
            schema, fixtures = self.data(team)
            with self.assertRaises(ContractError):
                validate(fixtures["preview"], schema)
            bad = copy.deepcopy(fixtures["error"]); bad["errorCode"] = "MADE_UP_SUCCESS"
            with self.assertRaises(ContractError):
                validate(bad, {"$ref": "#/$defs/error"}, schema)

    def test_tire_actual_store_messages_conform_without_server_or_build(self):
        # In-memory owner unit: no HTTP listener, filesystem database, Docker or Cloud.
        owner = ROOT.parent / "tire-health-cloud/src/store.mjs"
        if not owner.is_file():
            self.skipTest("optional component checkout unavailable")
        if not shutil.which("node") or subprocess.check_output(["node", "--version"], text=True).strip() != "v26.0.0":
            self.skipTest("pinned Node 26.0.0 unavailable; schema/source checks still run")
        code = '''
import assert from "node:assert/strict";
import {readFileSync} from "node:fs";
import {openStore, TireStore} from OWNER;
const db=openStore(":memory:");
const binding={systemUids:["a-test","z-peer"],testSystemUid:"a-test",productionSystemUid:"z-peer"};
try {
 const store=new TireStore(db,()=>binding,()=>new Date("2026-10-18T12:00:00.000Z"));
 const message=JSON.parse(readFileSync(FIXTURE,"utf8")); delete message.$comment;
 for(const [uid,role] of [["a-test","VALIDATION"],["z-peer","PRODUCTION"]]) {
  store.ingest(JSON.stringify({...message,unitSystemUid:uid,unitRole:role}));
 }
 for(const bad of [[],["a-test","a-test"],["foreign"],["z-peer"]])
  assert.throws(()=>store.preview(bad),/INVALID_SELECTOR/);
 const proof=store.emptyProof(), preview=store.preview(["a-test"]);
 assert.equal(Date.parse(preview.expiresAt)-Date.parse("2026-10-18T12:00:00.000Z"),60000);
 const result=store.execute(["a-test"],preview.confirmationToken);
 assert.deepEqual(result.nonmatchingRecordCounts,preview.nonmatchingRecordCounts);
 assert.equal(result.nonmatchingRecordSetSha256,preview.nonmatchingRecordSetSha256);
 assert.throws(()=>store.execute(["a-test"],preview.confirmationToken),/INVALID_PREVIEW/);
 console.log(JSON.stringify({proof,preview,result}));
} finally {db.close();}
'''.replace("OWNER", json.dumps(owner.as_uri())).replace("FIXTURE", json.dumps(str(
            owner.parents[1] / "test/fixtures/tire-health-assessment.valid.json")))
        result = subprocess.run(["node", "--input-type=module", "-e", code], capture_output=True,
                                text=True, timeout=15, check=True)
        schema, _ = self.data("tire")
        for name, value in json.loads(result.stdout).items():
            validate(value, {"$ref": "#/$defs/" + name}, schema)


if __name__ == "__main__":
    unittest.main()
