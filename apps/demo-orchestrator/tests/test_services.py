# SPDX-FileCopyrightText: 2026 maninblack
# SPDX-License-Identifier: MIT

import copy
import json
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import Mock, patch
from urllib.parse import parse_qs, urlsplit
from uuid import UUID

from aosedge_demo_orchestrator import service_cloud
from aosedge_demo_orchestrator.services import ServiceCatalog
from aosedge_demo_orchestrator.unit_cloud import Cloud, CloudFailure
from aosedge_demo_orchestrator.cli import build_parser, request_from_arguments
from aosedge_demo_orchestrator.api import execute_operation
from aosedge_demo_orchestrator.application import DemoOrchestrator
from aosedge_demo_orchestrator.environment import EnvironmentError

OWNER = "11111111-1111-4111-8111-111111111111"
SERVICE = "22222222-2222-4222-8222-222222222222"
OTHER = "33333333-3333-4333-8333-333333333333"


def row(identity=SERVICE, owner=OWNER):
    return dict(id=identity, service_provider=owner, title="Brake fixture", codename="brake-fixture",
        service_provider_title="Fixture SP", latest_version="1.0.0", created_at="2026-09-10T00:00:00Z",
        description="private unprojected", environment=dict(token="do-not-export"))


class FixtureCloud:
    def __init__(self, role="service provider"):
        self.user = dict(role=role, ownerId=OWNER, effectivePermissions=list(service_cloud.PERMISSIONS), token="do-not-export")
        self.collections = {"services/": [row()], "service-providers/": [dict(id=OWNER, title="Fixture SP", email="do-not-export")],
            "services/" + SERVICE + "/service-versions/": [dict(id=OTHER, version="1.0.0", container_state="ready")],
            "services/" + SERVICE + "/units/": []}
        self.calls = []
        self.detail = dict(row(), service_provider_id=OWNER, default_quotas=dict(secret="do-not-export"))

    def require(self, *permissions):
        Cloud.require(self, *permissions)

    def call(self, path):
        self.calls.append(path)
        if path == "services/" + SERVICE + "/":
            return copy.deepcopy(self.detail)
        parsed = urlsplit(path)
        self.assert_known(parsed.path)
        query = parse_qs(parsed.query)
        if set(query) != {"limit", "offset"}:
            raise AssertionError("No unsupported filter or hidden fallback")
        values = self.collections[parsed.path]
        offset = int(query["offset"][0])
        return dict(total=len(values), offset=offset, items=copy.deepcopy(values[offset:offset + 100]))

    def assert_known(self, path):
        if path not in self.collections:
            raise AssertionError("Unexpected endpoint: " + path)


class ServiceCloudTests(unittest.TestCase):
    def test_sp_catalog_is_owned_not_team_bound_and_projection_is_safe(self):
        cloud = FixtureCloud()
        result = service_cloud.inspect(cloud, dict(action="list"))
        self.assertEqual("CURRENT", result["services"]["state"])
        self.assertEqual("OWNED_BY_AUTHENTICATED_SP", result["services"]["value"]["items"][0]["authorityRelation"])
        self.assertEqual("NOT_CONFIGURED", result["authority"]["value"]["teamBinding"])
        self.assertEqual("NOT_EVALUATED", result["authority"]["value"]["mutationAuthority"])
        self.assertEqual(["services/?limit=100&offset=0"], cloud.calls)
        self.assertNotIn("do-not-export", json.dumps(result))
        self.assertNotIn("private unprojected", json.dumps(result))

    def test_oem_visibility_is_not_sp_ownership(self):
        cloud = FixtureCloud("oem")
        cloud.collections["services/"][0]["service_provider"] = OTHER
        result = service_cloud.inspect(cloud, dict(action="list", ownerId=OWNER))
        self.assertEqual("VISIBLE_TO_OEM_NOT_OEM_OWNED", result["services"]["value"]["items"][0]["authorityRelation"])
        self.assertEqual("MATCHED", result["authority"]["value"]["ownerBinding"])
        self.assertEqual(1, result["providers"]["value"]["coverage"]["total"])
        self.assertNotIn("do-not-export", json.dumps(result))

    def test_foreign_owner_rejected_in_sp_list_and_detail(self):
        cloud = FixtureCloud()
        cloud.collections["services/"][0]["service_provider"] = OTHER
        result = service_cloud.inspect(cloud, dict(action="list"))
        self.assertEqual("UNKNOWN", result["services"]["state"])
        self.assertIsNone(result["services"]["value"])
        cloud.detail.update(service_provider=OTHER, service_provider_id=OTHER)
        result = service_cloud.inspect(cloud, dict(action="status", serviceId=SERVICE))
        self.assertEqual("SERVICE_SP_OWNERSHIP_MISMATCH", result["service"]["reason"])
        self.assertNotIn("versions", result)

    def test_empty_missing_and_unavailable_are_distinct(self):
        cloud = FixtureCloud()
        cloud.collections["services/"] = []
        result = service_cloud.inspect(cloud, dict(action="list"))["services"]
        self.assertEqual("CURRENT", result["state"])
        self.assertEqual([], result["value"]["items"])
        self.assertTrue(result["value"]["coverage"]["complete"])
        for response in ({"items": None, "total": 0, "offset": 0}, {"items": []}):
            cloud.call = Mock(return_value=response)
            self.assertEqual("UNKNOWN", service_cloud.inspect(cloud, dict(action="list"))["services"]["state"])
        cloud.call = Mock(side_effect=CloudFailure("CLOUD_HTTP_403"))
        failed = service_cloud.inspect(cloud, dict(action="list"))["services"]
        self.assertEqual("FORBIDDEN", failed["transport"])
        self.assertIsNone(failed["value"])

    def test_pagination_duplicates_and_bound_are_truthful(self):
        cloud = FixtureCloud()
        cloud.collections["services/"] = [row(str(UUID(int=index + 1))) for index in range(101)]
        result = service_cloud.inspect(cloud, dict(action="list"))["services"]
        self.assertEqual(101, len(result["value"]["items"]))
        self.assertEqual(2, len(cloud.calls))
        cloud.collections["services/"] = [row(str(UUID(int=index + 1))) for index in range(801)]
        result = service_cloud.inspect(cloud, dict(action="list"))["services"]
        self.assertEqual("INCOMPLETE", result["state"])
        self.assertEqual(800, result["value"]["coverage"]["returned"])
        cloud.collections["services/"] = [row(), row()]
        result = service_cloud.inspect(cloud, dict(action="list"))["services"]
        self.assertEqual("UNKNOWN", result["state"])
        self.assertIsNone(result["value"])

    def test_permission_denial_does_not_contact_endpoint(self):
        cloud = FixtureCloud()
        cloud.user["effectivePermissions"] = []
        result = service_cloud.inspect(cloud, dict(action="list"))
        self.assertEqual("SP_PERMISSION_MISSING:services_list", result["services"]["reason"])
        self.assertEqual("FORBIDDEN", result["services"]["transport"])
        self.assertEqual([], cloud.calls)

    def test_detail_versions_and_assigned_units_are_not_process_health(self):
        cloud = FixtureCloud()
        result = service_cloud.inspect(cloud, dict(action="status", serviceId=SERVICE))
        self.assertEqual("ready", result["versions"]["value"]["items"][0]["container_state"])
        self.assertEqual([], result["units"]["value"]["items"])
        self.assertNotIn("runtime", json.dumps(result).lower())
        self.assertNotIn("do-not-export", json.dumps(result))
        cloud.detail["service_provider_id"] = OTHER
        conflict = service_cloud.inspect(cloud, dict(action="status", serviceId=SERVICE))
        self.assertEqual("SERVICE_OWNER_FIELDS_CONFLICT", conflict["service"]["reason"])

    def test_role_and_owner_mismatch_return_unavailable_not_a_fallback(self):
        with patch.object(service_cloud, "Cloud", side_effect=CloudFailure("SP_AUTHORITY_NOT_PROVEN")) as constructor:
            result = service_cloud.execute(dict(action="list", expectedRole="service provider", ownerId=OWNER))
        constructor.assert_called_once_with(dict(action="list", expectedRole="service provider", ownerId=OWNER), expected_role="service provider")
        self.assertEqual("SP_AUTHORITY_NOT_PROVEN", result["authority"]["reason"])
        self.assertNotIn("services", result)

    def test_error_text_and_config_are_redacted(self):
        cloud = FixtureCloud()
        cloud.detail["title"] = "token=do-not-export"
        result = service_cloud.inspect(cloud, dict(action="status", serviceId=SERVICE))
        self.assertEqual("[REDACTED]", result["service"]["value"]["title"])
        self.assertNotIn("do-not-export", json.dumps(result))


class ServiceAdaptersTests(unittest.TestCase):
    def setUp(self):
        self.environment = SimpleNamespace(root=Path("/unused-test-root"))
        self.catalog = ServiceCatalog(self.environment)

    def test_cli_uses_exact_catalog_id_and_named_profile(self):
        parser = build_parser()
        request = request_from_arguments(parser.parse_args(["service", "status", SERVICE, "--profile", "service-provider"]))
        self.assertEqual(SERVICE, request.service_id)
        self.assertEqual("service-provider", request.profile)
        self.assertIsNone(request.target)

    def test_api_scope_is_read_only_and_partial_is_preserved(self):
        app = DemoOrchestrator(environment_service=self.environment)
        payload = dict(domain="service", action="list", profile="service-provider")
        with patch.object(ServiceCatalog, "execute", return_value=dict(problems=[dict(reason="unavailable")])):
            self.assertEqual("PARTIAL", execute_operation(payload, app)["state"])
        for extra in ({"action": "upload"}, {"credential": "/secret"}, {"ownerId": OWNER}, {"target": "production"}, {"url": "https://example.com"}):
            with self.assertRaises(ValueError):
                execute_operation(dict(payload, **extra), app)

    def test_profiles_are_read_separately_not_adopted_or_merged(self):
        config = dict(cloudProfiles={"oem-delivery": dict(expectedRole="oem"), "service-provider": dict(expectedRole="service provider")})
        response = dict(authority=service_cloud.observed(dict(ownerId=OWNER)))
        with patch("aosedge_demo_orchestrator.services.load_configuration", return_value=config), \
                patch.object(self.catalog, "_read", return_value=response) as reader:
            result = self.catalog.execute("list")
        self.assertEqual({"oem-delivery", "service-provider"}, set(result["profiles"]))
        self.assertEqual(2, reader.call_count)
        with patch("aosedge_demo_orchestrator.services.load_configuration", return_value=config):
            with self.assertRaisesRegex(EnvironmentError, "PROFILE_NOT_CONFIGURED"):
                self.catalog.execute("list", profile="invented-tire-owner")
        with self.assertRaisesRegex(EnvironmentError, "CATALOG_REQUIRED"):
            self.catalog.execute("status", service_id="../../not-a-service")


if __name__ == "__main__":
    unittest.main()
