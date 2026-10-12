// SPDX-FileCopyrightText: 2026 maninblack
// SPDX-License-Identifier: MIT
// Test-only GUI-session client. No Cloud, vehicle RPC, shell or network listener.
import AppKit
import ApplicationServices
import CryptoKit
import Darwin

let nativeActions: Set<String> = ["driving.safe-stop", "driving.autopilot", "driving.brake-maneuver", "driving.tire-maneuver", "driving.return-to-road"]
let fixtureBundle = "org.aosedge.sdv.qualification.control-fixture"
let clientBundle = "org.aosedge.sdv.qualification.native-ui-runner"

struct PilotFailure: Error { let code: String }
func requirePilot(_ condition: Bool, _ code: String) throws {
    if !condition { throw PilotFailure(code: code) }
}
func jsonData(_ value: [String: Any]) throws -> Data {
    try JSONSerialization.data(withJSONObject: value, options: [.sortedKeys])
}
func exclusive(_ path: URL, _ value: [String: Any]) throws {
    let fd = Darwin.open(path.path, O_WRONLY | O_CREAT | O_EXCL | O_NOFOLLOW, 0o600)
    try requirePilot(fd >= 0, "REQUEST_ALREADY_CLAIMED")
    let stream = FileHandle(fileDescriptor: fd, closeOnDealloc: true)
    try stream.write(contentsOf: jsonData(value)); try stream.synchronize(); try stream.close()
}
func privateEntry(_ path: URL, directory: Bool) throws {
    let properties = try FileManager.default.attributesOfItem(atPath: path.path)
    try requirePilot(properties[.type] as? FileAttributeType == (directory ? .typeDirectory : .typeRegular), "PRIVATE_ENTRY_INVALID")
    try requirePilot(properties[.ownerAccountID] as? Int == Int(getuid()), "PRIVATE_ENTRY_OWNER_INVALID")
    try requirePilot(properties[.posixPermissions] as? Int == (directory ? 0o700 : 0o600), "PRIVATE_ENTRY_MODE_INVALID")
}

struct PilotRequest {
    let id: String
    let operation: String
    let pid: pid_t
    let digest: String
    let action: String?
    let frame: [CGFloat]?

    init(_ value: [String: Any], filename: String) throws {
        let common: Set<String> = ["schemaVersion", "requestId", "operation", "pid", "executableSha256"]
        let operation = value["operation"] as? String ?? ""
        let extra: Set<String> = operation == "click" ? ["action"] : operation == "place" ? ["frame"] : []
        let schema = value["schemaVersion"] as? NSNumber
        try requirePilot(Set(value.keys) == common.union(extra) && schema?.intValue == 1
            && schema.map { CFGetTypeID($0) != CFBooleanGetTypeID() } == true, "REQUEST_SCHEMA_INVALID")
        let id = value["requestId"] as? String ?? ""
        try requirePilot(UUID(uuidString: id)?.uuidString.lowercased() == id && filename == id + ".json", "REQUEST_ID_INVALID")
        try requirePilot(["inspect", "click", "place", "quit"].contains(operation), "REQUEST_OPERATION_INVALID")
        let pidNumber = value["pid"] as? NSNumber
        try requirePilot(pidNumber.map { CFGetTypeID($0) != CFBooleanGetTypeID() } == true, "REQUEST_PID_INVALID")
        let pid = value["pid"] as? Int ?? 0
        try requirePilot(pid > 1 && pid <= Int(Int32.max), "REQUEST_PID_INVALID")
        let digest = value["executableSha256"] as? String ?? ""
        try requirePilot(digest.range(of: "^[a-f0-9]{64}$", options: .regularExpression) != nil, "REQUEST_DIGEST_INVALID")
        var frame: [CGFloat]?
        if operation == "place" {
            let numbers = value["frame"] as? [Double] ?? []
            try requirePilot(numbers.count == 4 && numbers.allSatisfy { $0.isFinite && abs($0) < 16000 }
                && numbers[2] >= 360 && numbers[3] >= 390, "REQUEST_FRAME_INVALID")
            frame = numbers.map { CGFloat($0) }
        }
        let action = value["action"] as? String
        if operation == "click" { try requirePilot(nativeActions.contains(action ?? ""), "REQUEST_ACTION_INVALID") }
        self.id = id; self.operation = operation; self.pid = pid_t(pid)
        self.digest = digest; self.action = action; self.frame = frame
    }
}
// End pure request validation.

func attribute(_ element: AXUIElement, _ name: String) -> CFTypeRef? {
    var value: CFTypeRef?
    return AXUIElementCopyAttributeValue(element, name as CFString, &value) == .success ? value : nil
}
func stringAttribute(_ element: AXUIElement, _ name: String) -> String? { attribute(element, name) as? String }
func boolAttribute(_ element: AXUIElement, _ name: String) -> Bool? { attribute(element, name) as? Bool }
func matches(_ root: AXUIElement, identifier: String) throws -> [AXUIElement] {
    var stack: [(AXUIElement, Int)] = [(root, 0)], answer: [AXUIElement] = [], visited = 0
    while let (element, depth) = stack.popLast() {
        visited += 1
        try requirePilot(visited <= 2048 && depth <= 32, "UI_TREE_LIMIT")
        if stringAttribute(element, kAXIdentifierAttribute) == identifier { answer.append(element) }
        let children = attribute(element, kAXChildrenAttribute) as? [AXUIElement] ?? []
        stack += children.map { ($0, depth + 1) }
    }
    return answer
}
func unique(_ root: AXUIElement, _ identifier: String) throws -> AXUIElement {
    let found = try matches(root, identifier: identifier)
    try requirePilot(!found.isEmpty, "UI_ELEMENT_MISSING")
    try requirePilot(found.count == 1, "UI_ELEMENT_AMBIGUOUS")
    return found[0]
}
func pointAndSize(_ element: AXUIElement) throws -> CGRect {
    guard let p = attribute(element, kAXPositionAttribute), let s = attribute(element, kAXSizeAttribute),
          CFGetTypeID(p) == AXValueGetTypeID(), CFGetTypeID(s) == AXValueGetTypeID() else {
        throw PilotFailure(code: "UI_GEOMETRY_UNAVAILABLE")
    }
    var point = CGPoint.zero, size = CGSize.zero
    try requirePilot(AXValueGetValue(p as! AXValue, .cgPoint, &point)
        && AXValueGetValue(s as! AXValue, .cgSize, &size), "UI_GEOMETRY_UNAVAILABLE")
    let rect = CGRect(origin: point, size: size)
    try requirePilot([rect.minX, rect.minY, rect.width, rect.height].allSatisfy { $0.isFinite }
        && rect.width > 1 && rect.height > 1, "UI_GEOMETRY_INVALID")
    return rect
}

final class NativeClient: NSObject, NSApplicationDelegate {
    let root: URL
    let requests: URL
    var timer: Timer?
    var lastTrust: Bool?

    init(root: URL) { self.root = root; self.requests = root.appendingPathComponent("requests") }
    func applicationDidFinishLaunching(_ notification: Notification) {
        NSApp.setActivationPolicy(.accessory)
        timer = Timer.scheduledTimer(withTimeInterval: 0.05, repeats: true) { [weak self] _ in self?.poll() }
        poll()
    }
    func publishStatus(_ trusted: Bool) {
        guard lastTrust != trusted else { return }
        lastTrust = trusted
        let value: [String: Any] = ["schemaVersion": 1, "pid": getpid(), "bundleId": clientBundle,
            "status": trusted ? "READY" : "ACCESSIBILITY_PERMISSION_REQUIRED"]
        try? jsonData(value).write(to: root.appendingPathComponent("runner-status.json"), options: .atomic)
    }
    func target(_ request: PilotRequest) throws -> (NSRunningApplication, AXUIElement, AXUIElement) {
        let expected = root.appendingPathComponent("DrivingControlPilot.app/Contents/MacOS/ControlFixture")
        guard let app = NSRunningApplication(processIdentifier: request.pid) else { throw PilotFailure(code: "TARGET_PROCESS_MISSING") }
        try requirePilot(!app.isTerminated && app.bundleIdentifier == fixtureBundle
            && app.executableURL?.standardizedFileURL == expected.standardizedFileURL, "TARGET_PROCESS_MISMATCH")
        let digest = SHA256.hash(data: try Data(contentsOf: expected)).map { String(format: "%02x", $0) }.joined()
        try requirePilot(digest == request.digest, "TARGET_DIGEST_MISMATCH")
        let ax = AXUIElementCreateApplication(request.pid)
        AXUIElementSetMessagingTimeout(ax, 2)
        let window = try unique(ax, "driving.window")
        try requirePilot(boolAttribute(window, kAXMinimizedAttribute) == false, "TARGET_WINDOW_MINIMIZED")
        return (app, ax, window)
    }
    func poll() {
        let trusted = AXIsProcessTrustedWithOptions(nil)
        publishStatus(trusted)
        guard let entries = try? FileManager.default.contentsOfDirectory(at: requests, includingPropertiesForKeys: nil) else { return }
        for path in entries.sorted(by: { $0.lastPathComponent < $1.lastPathComponent }) where path.pathExtension == "json" {
            let receipt = path.deletingPathExtension().appendingPathExtension("receipt")
            let intent = path.deletingPathExtension().appendingPathExtension("intent")
            if FileManager.default.fileExists(atPath: receipt.path) || FileManager.default.fileExists(atPath: intent.path) { continue }
            let began = ProcessInfo.processInfo.systemUptime
            var sent = false, layoutAttempted = false, id = path.deletingPathExtension().lastPathComponent
            var output: [String: Any] = [:]
            do {
                try privateEntry(path, directory: false)
                let data = try Data(contentsOf: path)
                try requirePilot(data.count <= 4096, "REQUEST_TOO_LARGE")
                guard let value = try JSONSerialization.jsonObject(with: data) as? [String: Any] else { throw PilotFailure(code: "REQUEST_SCHEMA_INVALID") }
                let request = try PilotRequest(value, filename: path.lastPathComponent); id = request.id
                try requirePilot(trusted || request.operation == "quit", "ACCESSIBILITY_PERMISSION_REQUIRED")
                if request.operation == "quit" {
                    try exclusive(receipt, ["requestId": id, "outcome": "PASS", "code": "RUNNER_CLOSED", "inputDispatched": false])
                    timer?.invalidate(); NSApp.terminate(nil); return
                }
                let (app, _, window) = try target(request)
                let resolved = ProcessInfo.processInfo.systemUptime
                if request.operation == "inspect" {
                    var buttons: [[String: Any]] = []
                    for action in nativeActions.sorted() {
                        let element = try unique(window, action), rect = try pointAndSize(element)
                        try requirePilot(stringAttribute(element, kAXRoleAttribute) == kAXButtonRole, "UI_ROLE_MISMATCH")
                        buttons.append(["id": action, "enabled": boolAttribute(element, kAXEnabledAttribute) ?? false,
                            "frame": [rect.minX, rect.minY, rect.width, rect.height]])
                    }
                    output = ["outcome": "PASS", "code": "UI_CONTRACT_OBSERVED", "buttons": buttons]
                } else if request.operation == "place", let frame = request.frame {
                    var point = CGPoint(x: frame[0], y: frame[1]), size = CGSize(width: frame[2], height: frame[3])
                    guard let p = AXValueCreate(.cgPoint, &point), let s = AXValueCreate(.cgSize, &size) else { throw PilotFailure(code: "LAYOUT_VALUE_INVALID") }
                    try exclusive(intent, ["requestId": id, "state": "LAYOUT_INTENT", "pid": request.pid])
                    layoutAttempted = true
                    try requirePilot(AXUIElementSetAttributeValue(window, kAXPositionAttribute as CFString, p) == .success
                        && AXUIElementSetAttributeValue(window, kAXSizeAttribute as CFString, s) == .success, "LAYOUT_CHANGE_UNCONFIRMED")
                    output = ["outcome": "PASS", "code": "LAYOUT_REQUESTED"]
                } else if request.operation == "click", let action = request.action {
                    try requirePilot(app.activate(options: []), "TARGET_ACTIVATION_REFUSED")
                    let deadline = ProcessInfo.processInfo.systemUptime + 1
                    while !app.isActive && ProcessInfo.processInfo.systemUptime < deadline { RunLoop.current.run(until: Date(timeIntervalSinceNow: 0.02)) }
                    try requirePilot(app.isActive, "TARGET_NOT_FOREGROUND")
                    let element = try unique(window, action)
                    try requirePilot(stringAttribute(element, kAXRoleAttribute) == kAXButtonRole, "UI_ROLE_MISMATCH")
                    try requirePilot(boolAttribute(element, kAXEnabledAttribute) == true, "UI_ELEMENT_DISABLED")
                    let frame = try pointAndSize(element), location = CGPoint(x: frame.midX, y: frame.midY)
                    var hit: AXUIElement?
                    try requirePilot(AXUIElementCopyElementAtPosition(AXUIElementCreateSystemWide(), Float(location.x), Float(location.y), &hit) == .success,
                                     "UI_HIT_TEST_UNAVAILABLE")
                    try requirePilot(hit.map { CFEqual($0, element) } == true, "UI_ELEMENT_OBSTRUCTED")
                    let (_, _, freshWindow) = try target(request), fresh = try unique(freshWindow, action)
                    let freshFrame = try pointAndSize(fresh)
                    try requirePilot(CFEqual(fresh, element) && freshFrame == frame
                        && boolAttribute(fresh, kAXEnabledAttribute) == true && app.isActive, "UI_TARGET_CHANGED")
                    guard let down = CGEvent(mouseEventSource: nil, mouseType: .leftMouseDown, mouseCursorPosition: location, mouseButton: .left),
                          let up = CGEvent(mouseEventSource: nil, mouseType: .leftMouseUp, mouseCursorPosition: location, mouseButton: .left) else {
                        throw PilotFailure(code: "UI_INPUT_UNAVAILABLE")
                    }
                    try exclusive(intent, ["requestId": id, "state": "MOUSE_INPUT_INTENT", "pid": request.pid, "action": action])
                    sent = true
                    down.post(tap: .cghidEventTap); up.post(tap: .cghidEventTap)
                    output = ["outcome": "INPUT_DISPATCHED", "code": "MOUSE_DOWN_UP_POSTED", "action": action,
                        "resolvedFrame": [frame.minX, frame.minY, frame.width, frame.height]]
                }
                output["resolveSeconds"] = resolved - began
            } catch let error as PilotFailure {
                output = ["outcome": sent || layoutAttempted ? "UNCERTAIN" : "BLOCKED", "code": error.code]
            } catch {
                output = ["outcome": sent || layoutAttempted ? "UNCERTAIN" : "BLOCKED", "code": "PILOT_REQUEST_UNAVAILABLE"]
            }
            output["requestId"] = id; output["inputDispatched"] = sent
            output["runnerSeconds"] = ProcessInfo.processInfo.systemUptime - began
            try? exclusive(receipt, output)
        }
    }
}

umask(0o077)
if CommandLine.arguments.contains("--self-test") {
    let id = "01234567-89ab-cdef-0123-456789abcdef"
    let valid: [String: Any] = ["schemaVersion": 1, "requestId": id, "operation": "click", "pid": 12345,
        "executableSha256": String(repeating: "a", count: 64), "action": "driving.safe-stop"]
    do {
        _ = try PilotRequest(valid, filename: id + ".json")
        for change in [["action": "driving.delete-test"], ["operation": "shell"], ["requestId": "bad"], ["pid": 1], ["pid": true], ["schemaVersion": true], ["unexpected": true]] as [[String: Any]] {
            var broken = valid; for (key, value) in change { broken[key] = value }
            if (try? PilotRequest(broken, filename: id + ".json")) != nil { exit(2) }
        }
        print("PASS native UI request guards"); exit(0)
    } catch { exit(2) }
}
guard CommandLine.arguments.count == 2 else { exit(2) }
let root = URL(fileURLWithPath: CommandLine.arguments[1], isDirectory: true).standardizedFileURL
let parent = FileManager.default.homeDirectoryForCurrentUser.appendingPathComponent("SDV-Qualification", isDirectory: true)
guard root.deletingLastPathComponent() == parent,
      root.lastPathComponent.range(of: "^native-ui-pilot-[0-9]{8}(-[a-z0-9]+)?$", options: .regularExpression) != nil else { exit(2) }
do { try privateEntry(root, directory: true); try privateEntry(root.appendingPathComponent("requests"), directory: true) } catch { exit(2) }
let application = NSApplication.shared
let client = NativeClient(root: root)
application.delegate = client
application.run()
