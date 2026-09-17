import tempfile
import unittest
from pathlib import Path
from unittest.mock import Mock, patch

from aosedge_demo_orchestrator import source_cache
from aosedge_demo_orchestrator.cli import build_parser, request_from_arguments
from aosedge_demo_orchestrator.environment import EnvironmentError


class SourceCacheTests(unittest.TestCase):
    def test_command_is_explicitly_map_scoped_and_preserves_project(self):
        command = source_cache.command(dict(**{"unreal-editor": Path("/engine"), "project": Path("/project")}), Path("/log"))
        self.assertIn("-Map=/Content/Carla/Maps/Town10HD_Opt", command)
        self.assertIn("-TargetPlatform=Mac", command)
        self.assertNotIn("-game", command)
        self.assertNotIn("-save", command)
        self.assertNotIn("-NoShaderCompile", command)
        request = request_from_arguments(build_parser().parse_args(["simulation", "prepare-cache"]))
        self.assertEqual((request.domain, request.action), ("simulation", "prepare-cache"))

    def test_running_source_cannot_prepare_or_be_stopped_implicitly(self):
        service = Mock(root=Path("/fixture"))
        with patch.object(source_cache, "read_json", return_value=dict(source=dict(state="RUNNING"))):
            with self.assertRaisesRegex(EnvironmentError, "REQUIRES_STOPPED"):
                source_cache.prepare(service)
        service.driver.assets.assert_not_called()
        service.driver.stop.assert_not_called()
        service.vm._free_port.assert_not_called()

    def test_native_failure_is_not_reported_as_ready(self):
        with tempfile.TemporaryDirectory() as root:
            service = Mock(root=Path(root))
            service.environment._directory.side_effect = lambda p: (Path(root) / p).mkdir(parents=True)
            service.driver.assets.return_value = {"unreal-editor": Path("/engine"), "project": Path("/project")}
            process = Mock()
            process.wait.return_value = 1
            process.poll.return_value = 1
            with patch.object(source_cache, "read_json", return_value={}), \
                 patch.object(source_cache.shutil, "disk_usage", return_value=Mock(free=100 * 1024**3)), \
                 patch.object(source_cache.subprocess, "Popen", return_value=process):
                with self.assertRaisesRegex(EnvironmentError, "PREPARATION_FAILED"):
                    source_cache.prepare(service)
            service.vm._save.assert_not_called()

    def test_zero_exit_without_the_requested_map_is_not_success(self):
        for loaded in (False, True):
            with self.subTest(map_loaded=loaded), tempfile.TemporaryDirectory() as root:
                service = Mock(root=Path(root))
                service.environment._directory.side_effect = lambda p: (Path(root) / p).mkdir(parents=True)
                service.driver.assets.return_value = {"unreal-editor": Path("/engine"), "project": Path("/project")}
                process = Mock()
                process.wait.return_value = process.poll.return_value = 0
                def launch(args, **kwargs):
                    log = Path(next(x.removeprefix("-abslog=") for x in args if x.startswith("-abslog=")))
                    log.write_text("LogDerivedDataCacheCommandlet: Display: Loading (1) /project/Content/Carla/Maps/Town10HD_Opt.umap\n"
                                   if loaded else "No packages found to load\n")
                    return process
                with patch.object(source_cache, "read_json", return_value={}), \
                     patch.object(source_cache.shutil, "disk_usage", return_value=Mock(free=100 * 1024**3)), \
                     patch.object(source_cache.subprocess, "Popen", side_effect=launch):
                    if loaded:
                        self.assertEqual("PREPARED", source_cache.prepare(service)["state"])
                    else:
                        with self.assertRaisesRegex(EnvironmentError, "MAP_NOT_PROCESSED"):
                            source_cache.prepare(service)


if __name__ == "__main__":
    unittest.main()
