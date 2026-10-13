// SPDX-FileCopyrightText: 2026 maninblack
// SPDX-License-Identifier: MIT
// Compiled with the exact production ControlView prefix, not a replica UI.
import AppKit
import Darwin

final class Fixture: NSObject, NSApplicationDelegate, NSWindowDelegate {
    let root: URL
    var window: NSWindow!
    var control: ControlView!
    var overlay: NSPanel?
    var duplicate: NSButton?
    var timer: Timer?
    var lastCommand = ""

    init(root: URL) { self.root = root }
    func event(_ action: String) {
        let value: [String: Any] = ["action": action, "fixture": true, "inputPath": "production-control-dispatch",
            "mouseDownObserved": NSApp.currentEvent?.type == .leftMouseDown,
            "uptime": ProcessInfo.processInfo.systemUptime]
        if let data = try? JSONSerialization.data(withJSONObject: value, options: [.sortedKeys]) {
            let path = root.appendingPathComponent("fixture-events.jsonl")
            let fd = Darwin.open(path.path, O_WRONLY | O_CREAT | O_APPEND | O_NOFOLLOW, 0o600)
            guard fd >= 0 else { return }
            let handle = FileHandle(fileDescriptor: fd, closeOnDealloc: true)
            try? handle.write(contentsOf: data + Data([10])); try? handle.synchronize(); try? handle.close()
        }
    }
    func applicationDidFinishLaunching(_ notification: Notification) {
        NSApp.setActivationPolicy(.regular)
        control = ControlView(frame: NSRect(x: 0, y: 0, width: 520, height: 600))
        control.connected = true
        control.onMode = { [weak self] mode in
            self?.event(mode == "safe_stop" ? "driving.safe-stop" : "driving.autopilot")
            self?.control.setMode(mode)
        }
        control.onScene = { [weak self] kind in
            self?.event(kind == "brake" ? "driving.brake-maneuver" : kind == "tire" ? "driving.tire-maneuver" : "driving.return-to-road")
        }
        window = NSWindow(contentRect: control.frame, styleMask: [.titled, .closable, .miniaturizable, .resizable], backing: .buffered, defer: false)
        window.title = "Driving Control — UI runner pilot (no vehicle connected)"
        window.setAccessibilityIdentifier("driving.window")
        let container = NSView(frame: control.frame)
        container.addSubview(control)
        window.contentView = container; window.delegate = self
        control.autoresizingMask = [.width, .height]
        window.contentMinSize = NSSize(width: 360, height: 390)
        window.setFrameOrigin(NSPoint(x: 40, y: 160))
        window.makeKeyAndOrderFront(nil); NSApp.activate(ignoringOtherApps: true)
        let state: [String: Any] = ["pid": getpid(), "fixture": true, "bundleId": Bundle.main.bundleIdentifier ?? ""]
        if let data = try? JSONSerialization.data(withJSONObject: state) { try? data.write(to: root.appendingPathComponent("fixture-status.json"), options: .atomic) }
        timer = Timer.scheduledTimer(withTimeInterval: 0.05, repeats: true) { [weak self] _ in self?.poll() }
    }
    func poll() {
        let path = root.appendingPathComponent("fixture-command.json")
        guard let data = try? Data(contentsOf: path), data.count < 2048,
              let value = try? JSONSerialization.jsonObject(with: data) as? [String: Any],
              Set(value.keys) == ["requestId", "mode"], let id = value["requestId"] as? String,
              UUID(uuidString: id) != nil, id != lastCommand, let mode = value["mode"] as? String,
              ["normal", "busy", "missing", "duplicate", "obstructed", "minimized", "quit"].contains(mode) else { return }
        lastCommand = id
        if mode == "quit" { timer?.invalidate(); NSApp.terminate(nil); return }
        duplicate?.removeFromSuperview(); duplicate = nil
        overlay?.close(); overlay = nil
        if window.isMiniaturized { window.deminiaturize(nil) }
        control.sceneBusy = mode == "busy"; control.needsDisplay = true
        control.onScene = mode == "missing" ? nil : { [weak self] kind in
            self?.event(kind == "brake" ? "driving.brake-maneuver" : kind == "tire" ? "driving.tire-maneuver" : "driving.return-to-road")
        }
        if mode == "duplicate" {
            let button = NSButton(title: "Duplicate ID negative fixture", target: nil, action: nil)
            button.setAccessibilityIdentifier("driving.tire-maneuver")
            button.frame = NSRect(x: 10, y: 330, width: 300, height: 30)
            window.contentView?.addSubview(button); duplicate = button
        }
        window.makeKeyAndOrderFront(nil); NSApp.activate(ignoringOtherApps: true)
        if mode == "obstructed" {
            let frame = NSAccessibility.screenRect(fromView: control, rect: control.buttonRect(.tire))
            let panel = NSPanel(contentRect: frame.insetBy(dx: -12, dy: -12), styleMask: [.titled], backing: .buffered, defer: false)
            panel.title = "Pilot obstruction — no click allowed"
            panel.level = .floating
            panel.orderFront(nil); overlay = panel
        }
        if mode == "minimized" { window.miniaturize(nil) }
        let receipt: [String: Any] = ["requestId": id, "mode": mode, "fixture": true]
        if let data = try? JSONSerialization.data(withJSONObject: receipt) { try? data.write(to: root.appendingPathComponent("fixture-command-receipt.json"), options: .atomic) }
    }
    func applicationShouldTerminateAfterLastWindowClosed(_ sender: NSApplication) -> Bool { true }
}
umask(0o077)
guard CommandLine.arguments.count == 2 else { exit(2) }
let root = URL(fileURLWithPath: CommandLine.arguments[1], isDirectory: true).standardizedFileURL
guard root.deletingLastPathComponent() == FileManager.default.homeDirectoryForCurrentUser.appendingPathComponent("SDV-Qualification", isDirectory: true) else { exit(2) }
let app = NSApplication.shared
let fixture = Fixture(root: root)
app.delegate = fixture
app.run()
