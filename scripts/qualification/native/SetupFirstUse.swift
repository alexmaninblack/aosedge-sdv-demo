// SPDX-FileCopyrightText: 2026 maninblack
// SPDX-License-Identifier: MIT
// Fixed Setup-only qualification. Secrets enter through an owner-private FIFO,
// are typed into native secure fields and are never written to a report.
import AppKit
import ApplicationServices
import CryptoKit
import Darwin

struct Failure: Error { let code: String }
func check(_ ok: Bool, _ code: String) throws { if !ok { throw Failure(code: code) } }
func attr(_ e: AXUIElement, _ key: String) -> CFTypeRef? {
    var value: CFTypeRef?
    return AXUIElementCopyAttributeValue(e, key as CFString, &value) == .success ? value : nil
}
func text(_ e: AXUIElement, _ key: String) -> String { attr(e, key) as? String ?? "" }
func entries(_ root: AXUIElement) throws -> [AXUIElement] {
    var work = [(root, 0)], result: [AXUIElement] = []
    while let (e, depth) = work.popLast() {
        try check(result.count < 2048 && depth < 32, "UI_TREE_LIMIT")
        result.append(e)
        work += (attr(e, kAXChildrenAttribute) as? [AXUIElement] ?? []).map { ($0, depth + 1) }
    }
    return result
}
func geometry(_ e: AXUIElement) throws -> CGRect {
    guard let p = attr(e, kAXPositionAttribute), let s = attr(e, kAXSizeAttribute),
          CFGetTypeID(p) == AXValueGetTypeID(), CFGetTypeID(s) == AXValueGetTypeID()
    else { throw Failure(code: "UI_GEOMETRY_MISSING") }
    var point = CGPoint.zero, size = CGSize.zero
    try check(AXValueGetValue(p as! AXValue, .cgPoint, &point) && AXValueGetValue(s as! AXValue, .cgSize, &size), "UI_GEOMETRY_INVALID")
    try check(size.width > 1 && size.height > 1, "UI_GEOMETRY_INVALID")
    return CGRect(origin: point, size: size)
}

final class Scenario: NSObject, NSApplicationDelegate {
    let root: URL
    var app: NSRunningApplication!
    var tree: AXUIElement!
    var stages: [[String: Any]] = []
    let began = ProcessInfo.processInfo.systemUptime
    init(_ root: URL) { self.root = root }
    func record(_ stage: String) throws {
        stages.append(["stage": stage, "seconds": ProcessInfo.processInfo.systemUptime - began])
        try JSONSerialization.data(withJSONObject: ["stage": stage, "pid": getpid(), "stages": stages], options: .sortedKeys)
            .write(to: root.appendingPathComponent("progress.json"), options: .atomic)
    }
    func find(_ label: String, role: String? = nil, seconds: Double = 12) throws -> AXUIElement {
        let end = ProcessInfo.processInfo.systemUptime + seconds
        repeat {
            try check(!app.isTerminated, "SETUP_EXITED")
            if label == "Connected to Production" {
                let nodes = try entries(tree)
                if nodes.contains(where: { text($0, kAXRoleAttribute) == kAXStaticTextRole &&
                    text($0, kAXValueAttribute) == "Cloud step needs attention — local installation preserved" }) {
                    try button("Back to certificate pair")
                    try button("Close")
                    try button("Details…")
                    let messages = try entries(tree).filter { text($0, kAXRoleAttribute) == kAXStaticTextRole }
                        .map { text($0, kAXValueAttribute) }.filter { $0.hasPrefix("Diagnostic: ") }
                    let code = messages.first.map { String($0.dropFirst("Diagnostic: ".count)) } ?? "SETUP_ERROR_NOT_EXPOSED"
                    try check(code.range(of: "^[A-Z][A-Z0-9_]{2,100}$", options: .regularExpression) != nil, "DIAGNOSTIC_FORMAT_INVALID")
                    throw Failure(code: code)
                }
            }
            let found = try entries(tree).filter { element in
                (role == nil || text(element, kAXRoleAttribute) == role!) &&
                [kAXTitleAttribute, kAXDescriptionAttribute, kAXValueAttribute].contains { key in
                    // Never inspect a secure field's value.
                    key != kAXValueAttribute || text(element, kAXSubroleAttribute) != kAXSecureTextFieldSubrole
                    ? text(element, key) == label : false
                }
            }
            try check(found.count <= 1, "UI_LABEL_AMBIGUOUS")
            if let e = found.first, role == nil || (attr(e, kAXEnabledAttribute) as? Bool == true) { return e }
            Thread.sleep(forTimeInterval: 0.15)
        } while ProcessInfo.processInfo.systemUptime < end
        throw Failure(code: "UI_WAIT_" + label.uppercased().filter { $0.isASCII && ($0.isLetter || $0.isNumber) }.prefix(65))
    }
    func click(_ e: AXUIElement) throws {
        DispatchQueue.main.sync { _ = app.activate(options: []) }
        let end = ProcessInfo.processInfo.systemUptime + 2
        while !app.isActive && ProcessInfo.processInfo.systemUptime < end { Thread.sleep(forTimeInterval: 0.05) }
        try check(app.isActive, "SETUP_NOT_FOREGROUND")
        let r = try geometry(e), p = CGPoint(x: r.midX, y: r.midY)
        var hit: AXUIElement?
        try check(AXUIElementCopyElementAtPosition(AXUIElementCreateSystemWide(), Float(p.x), Float(p.y), &hit) == .success
                  && hit.map { CFEqual($0, e) } == true, "UI_ELEMENT_OBSTRUCTED")
        for type in [CGEventType.leftMouseDown, .leftMouseUp] {
            guard let event = CGEvent(mouseEventSource: nil, mouseType: type, mouseCursorPosition: p, mouseButton: .left)
            else { throw Failure(code: "UI_INPUT_UNAVAILABLE") }
            event.post(tap: .cghidEventTap)
        }
        Thread.sleep(forTimeInterval: 0.2)
    }
    func button(_ label: String, seconds: Double = 12) throws { try click(find(label, role: kAXButtonRole, seconds: seconds)) }
    func key(_ code: CGKeyCode) throws {
        for down in [true, false] {
            guard let e = CGEvent(keyboardEventSource: nil, virtualKey: code, keyDown: down) else { throw Failure(code: "UI_INPUT_UNAVAILABLE") }
            e.post(tap: .cghidEventTap)
        }
        Thread.sleep(forTimeInterval: 0.1)
    }
    func typeSecret(_ label: String, _ value: String) throws {
        let e = try find(label, role: kAXTextFieldRole)
        try check(text(e, kAXSubroleAttribute) == kAXSecureTextFieldSubrole, "SECURE_INPUT_REQUIRED")
        try click(e)
        let chars = Array(value.utf16)
        for start in stride(from: 0, to: chars.count, by: 16) {
            let chunk = Array(chars[start..<min(start + 16, chars.count)])
            for down in [true, false] {
                guard let event = CGEvent(keyboardEventSource: nil, virtualKey: 0, keyDown: down) else { throw Failure(code: "UI_INPUT_UNAVAILABLE") }
                event.keyboardSetUnicodeString(stringLength: chunk.count, unicodeString: chunk)
                event.post(tap: .cghidEventTap)
            }
        }
        Thread.sleep(forTimeInterval: 0.2)
    }
    func tokens() throws -> [String: String] {
        let path = root.appendingPathComponent("tokens.fifo").path
        var info = stat()
        try check(lstat(path, &info) == 0 && info.st_uid == getuid() && (info.st_mode & S_IFMT) == S_IFIFO
                  && (info.st_mode & 0o777) == 0o600, "PRIVATE_FIFO_REQUIRED")
        let fd = Darwin.open(path, O_RDONLY | O_NONBLOCK | O_NOFOLLOW)
        try check(fd >= 0, "PRIVATE_FIFO_UNAVAILABLE")
        defer { Darwin.close(fd) }
        try record("TOKENS_REQUIRED")
        var data = Data(), buf = [UInt8](repeating: 0, count: 2048)
        let end = ProcessInfo.processInfo.systemUptime + 180
        while ProcessInfo.processInfo.systemUptime < end {
            let count = Darwin.read(fd, &buf, buf.count)
            if count > 0 { data.append(contentsOf: buf.prefix(count)) }
            try check(data.count < 16384, "TOKEN_INPUT_LIMIT")
            if data.last == 10 { break }
            Thread.sleep(forTimeInterval: 0.05)
        }
        guard let pair = try JSONSerialization.jsonObject(with: data) as? [String: String] else { throw Failure(code: "TOKEN_INPUT_INVALID") }
        try check(Set(pair.keys) == ["oem", "sp"] && pair.values.allSatisfy { !$0.isEmpty && $0.utf8.count < 8192
            && $0.unicodeScalars.allSatisfy { $0.value >= 33 && $0.value <= 126 } }, "TOKEN_INPUT_INVALID")
        return pair
    }
    func run() throws {
        try check(AXIsProcessTrusted(), "ACCESSIBILITY_PERMISSION_REQUIRED")
        let config = try JSONSerialization.jsonObject(with: Data(contentsOf: root.appendingPathComponent("profile.json"))) as! [String: Any]
        let pid = pid_t(config["pid"] as! Int), exe = URL(fileURLWithPath: config["executable"] as! String)
        app = NSRunningApplication(processIdentifier: pid) ?? NSWorkspace.shared.runningApplications.first { $0.processIdentifier == pid }
        try check(app != nil && app.bundleIdentifier == "org.aosedge.sdvlab.setup.preview"
                  && app.executableURL?.standardizedFileURL == exe.standardizedFileURL, "SETUP_IDENTITY_MISMATCH")
        let hash = SHA256.hash(data: try Data(contentsOf: exe)).map { String(format: "%02x", $0) }.joined()
        try check(hash == config["sha256"] as? String, "SETUP_DIGEST_MISMATCH")
        tree = AXUIElementCreateApplication(pid); AXUIElementSetMessagingTimeout(tree, 2)
        if config["installedUnenrolled"] as? Bool == true {
            try record("INSTALLED_UNENROLLED_CONTINUATION")
        } else {
            try record("EMPTY_SETUP_OBSERVED")
            try button("1. Install SDV Lab", seconds: 30)
            try record("INSTALL_INPUT_DISPATCHED")
        }
        try button("2. Connect to Aos Cloud…", seconds: 900)
        try record("INSTALL_COMPLETED")
        let oem = try find("OEM certificate", role: kAXTextFieldRole)
        let sp = try find("Service Provider certificate", role: kAXTextFieldRole)
        try check(text(oem, kAXValueAttribute).isEmpty && text(sp, kAXValueAttribute).isEmpty, "PREEXISTING_CERTIFICATES")
        try button("Get new certificates…")
        let environment = try find("Cloud environment", role: kAXPopUpButtonRole)
        try click(environment)
        try click(find("Production", role: kAXMenuItemRole))
        let selectedUntil = ProcessInfo.processInfo.systemUptime + 3
        while ![text(environment, kAXValueAttribute), text(environment, kAXTitleAttribute)].contains("Production")
            && ProcessInfo.processInfo.systemUptime < selectedUntil { Thread.sleep(forTimeInterval: 0.1) }
        try check([text(environment, kAXValueAttribute), text(environment, kAXTitleAttribute)].contains("Production"),
                  "PRODUCTION_SELECTION_UNCONFIRMED")
        var pair = try tokens()
        try typeSecret("OEM issuance token", pair["oem"]!)
        try typeSecret("Service Provider issuance token", pair["sp"]!)
        pair.removeAll()
        try record("PAIR_ISSUANCE_INPUT_INTENT")
        try button("Get certificates")
        _ = try find("Connected to Production", seconds: 160)
        try record("NEW_CERTIFICATES_CONNECTED")
        try button("Close")
        try button("3. Open SDV Lab")
        _ = try find("Presenter opened", seconds: 160)
        try record("PASS")
    }
    func applicationDidFinishLaunching(_ notification: Notification) {
        NSApp.setActivationPolicy(.accessory)
        DispatchQueue.global().async {
            do { try self.run() }
            catch { try? self.record((error as? Failure)?.code ?? "FIRST_USE_FAILED") }
            DispatchQueue.main.async { NSApp.terminate(nil) }
        }
    }
}
if CommandLine.arguments == [CommandLine.arguments[0], "--self-test"] { exit(0) }
guard CommandLine.arguments.count == 2 else { exit(2) }
let root = URL(fileURLWithPath: CommandLine.arguments[1])
var info = stat()
guard lstat(root.path, &info) == 0 && info.st_uid == getuid() && (info.st_mode & S_IFMT) == S_IFDIR
    && (info.st_mode & 0o777) == 0o700 else { exit(2) }
let app = NSApplication.shared, owner = Scenario(root)
app.delegate = owner; app.run()
