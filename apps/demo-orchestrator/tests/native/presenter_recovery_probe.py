# SPDX-FileCopyrightText: 2026 maninblack
# SPDX-License-Identifier: MIT
"""Disposable, synthetic WebKit fixture; never opens the real Presenter page."""
import hashlib
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
import json
import os
from pathlib import Path
import socket
import subprocess
import sys
import threading
import time

ROOT = Path(sys.argv[1]).resolve(strict=True)
SOURCE = Path(__file__).resolve().parents[2] / 'src/aosedge_demo_orchestrator/native/PresenterWorkspace.swift'
source = SOURCE.read_text()
source_sha = hashlib.sha256(source.encode()).hexdigest()
mode = 'candidate'
with socket.socket() as reservation:
    reservation.bind(('127.0.0.1', 0))
    port = reservation.getsockname()[1]
source = source[:source.index('\nif CommandLine.arguments.count == 2')]
source = source.replace('http://127.0.0.1:18080', f'http://127.0.0.1:{port}').replace('url?.port == 18080', f'url?.port == {port}')
# Test-only entry: hidden synthetic views, no product state/layout/Cloud/VM.
harness = r'''
let app = NSApplication.shared
app.setActivationPolicy(.prohibited)
let presenter = Presenter("/nonexistent-synthetic-layout")
for name in ["header", "browser"] {
    let view = WKWebView(frame: NSRect(x: 0, y: 0, width: 600, height: 300))
    view.navigationDelegate = presenter
    presenter.views[name] = view
    view.load(URLRequest(url: URL(string: "FIXTURE/#native-" + name)!))
}
func emit(_ value: [String: Any]) {
    let data = try! JSONSerialization.data(withJSONObject: value, options: [.sortedKeys])
    FileHandle.standardOutput.write(data + Data([10]))
}
func after(_ seconds: Double, _ operation: @escaping () -> Void) {
    DispatchQueue.main.asyncAfter(deadline: .now() + seconds, execute: operation)
}
func snapshot(_ label: String) {
    let group = DispatchGroup()
    var values: [String: String] = [:]
    for (name, view) in presenter.views {
        group.enter()
        view.evaluateJavaScript("document.body ? document.body.getAttribute('data-marker') : null") { value, error in
            values[name] = error == nil ? (value as? String ?? "EMPTY") : "JS_ERROR"
            group.leave()
        }
    }
    group.notify(queue: .main) { emit(["label": label, "views": values]) }
}
func dom(_ script: String) {
    for view in presenter.views.values { view.evaluateJavaScript(script, completionHandler: nil) }
}
let timer = Timer.scheduledTimer(withTimeInterval: 5, repeats: true) { _ in presenter.checkClient() }
after(13) { snapshot("late_server") }
if CommandLine.arguments.last == "baseline" {
    after(14) { exit(0) }
} else {
    after(14) { dom("document.body.insertAdjacentHTML('beforeend','<div id=guard role=dialog></div>')") }
    after(18) { snapshot("dialog_guard") }
    after(19) { dom("document.getElementById('guard').remove(); document.body.setAttribute('data-submission-pending','true')") }
    after(22) { snapshot("submission_guard") }
    after(23) { dom("document.body.removeAttribute('data-submission-pending')") }
    after(28) { snapshot("unblocked_refresh") }
    after(33) { snapshot("same_identity_no_reload") }
    after(38) { snapshot("server_busy_guard") }
    after(43) { snapshot("server_idle_refresh") }
    after(58) { snapshot("failed_refresh_retry") }
    after(62) { exit(0) }
}
app.run()
'''.replace('FIXTURE', f'http://127.0.0.1:{port}')
swift = ROOT / f'{mode}-fixture.swift'
swift.write_text(source + harness)
binary = ROOT / f'{mode}-fixture'
compile_result = subprocess.run(['/usr/bin/xcrun', 'swiftc', '-O', '-module-cache-path', os.environ.get('NATIVE_PRESENTER_SWIFT_CACHE', str(ROOT / 'swift-cache')), str(swift), '-o', str(binary), '-framework', 'AppKit', '-framework', 'WebKit'], capture_output=True, timeout=60)
(ROOT / f'{mode}-compile.log').write_bytes(compile_result.stdout + compile_result.stderr)
assert compile_result.returncode == 0, 'See scoped compile log'
start = time.monotonic()
requests = []
def stage():
    elapsed = time.monotonic() - start
    marker = 'A' if elapsed < 14 else 'B' if elapsed < 34 else 'C' if elapsed < 44 else 'D'
    return elapsed, marker
class Handler(BaseHTTPRequestHandler):
    def log_message(self, *_):
        pass
    def do_GET(self):
        elapsed, marker = stage()
        if self.path == '/api/presenter/client-state':
            body = json.dumps(dict(buildId=marker*64, sessionId='synthetic-only', canReload=not 34 <= elapsed < 39)).encode()
            content_type = 'application/json'
        elif self.path == '/':
            requests.append(dict(at=round(elapsed, 2), marker=marker, failed=44 <= elapsed < 48))
            if 44 <= elapsed < 48:
                self.connection.shutdown(socket.SHUT_RDWR)
                self.connection.close()
                return
            body = f'<!doctype html><html><body data-marker="{marker}"><h1>Synthetic Presenter fixture {marker}</h1></body></html>'.encode()
            content_type = 'text/html'
        else:
            self.send_error(404)
            return
        self.send_response(200)
        self.send_header('Content-Type', content_type)
        self.send_header('Content-Length', str(len(body)))
        self.send_header('Cache-Control', 'no-store')
        self.end_headers()
        self.wfile.write(body)
child = subprocess.Popen([str(binary), mode], stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
server = None
try:
    time.sleep(3)  # The first navigation genuinely has no listening server.
    server = ThreadingHTTPServer(('127.0.0.1', port), Handler)
    threading.Thread(target=server.serve_forever, daemon=True).start()
    stdout, stderr = child.communicate(timeout=68)
    (ROOT / f'{mode}-webkit.log').write_text(stderr)
    observations = [json.loads(line) for line in stdout.splitlines() if line.startswith('{')]
    expected = {'late_server': 'A', 'dialog_guard': 'A', 'submission_guard': 'A', 'unblocked_refresh': 'B', 'same_identity_no_reload': 'B', 'server_busy_guard': 'B', 'server_idle_refresh': 'C', 'failed_refresh_retry': 'D'}
    checks = {row['label']: set(row['views']) == {'header', 'browser'} and
              all(value == expected[row['label']] for value in row['views'].values()) for row in observations}
    (ROOT / f'{mode}-observations.json').write_text(json.dumps(dict(observations=observations, requests=requests, checks=checks), indent=2))
    if mode == 'candidate':
        assert len(checks) == 8 and all(checks.values()), checks
        assert not any(28 < row['at'] < 39 for row in requests), 'unexpected reload while unchanged or busy'
    else:
        assert len(checks) == 1 and not checks['late_server'], 'baseline unexpectedly recovered'
    result = dict(result='PASS', scope='SYNTHETIC_WEBKIT_ONLY', mode=mode, sourceSha256=source_sha, observations=observations, requests=requests, checks=checks, processExitCode=child.returncode)
    (ROOT / f'{mode}-result.json').write_text(json.dumps(result, indent=2))
    print(json.dumps(result))
finally:
    if child.poll() is None:
        child.terminate()
        child.wait(timeout=5)
    if server is not None:
        server.shutdown()
        server.server_close()
