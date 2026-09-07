// SPDX-FileCopyrightText: 2026 maninblack
// SPDX-License-Identifier: MIT
import AppKit
import WebKit
import CoreGraphics

func builtinScreen() -> NSScreen? {
    NSScreen.screens.first {
        guard let id = $0.deviceDescription[NSDeviceDescriptionKey("NSScreenNumber")] as? NSNumber else { return false }
        return CGDisplayIsBuiltin(id.uint32Value) != 0
    }
}
func screenInfo() -> [String: Any]? {
    guard let screen = builtinScreen(), let primary = NSScreen.screens.first else { return nil }
    let r = screen.visibleFrame
    return ["x": Int(r.minX), "y": Int(primary.frame.maxY - r.maxY),
            "width": Int(r.width), "height": Int(r.height), "scale": screen.backingScaleFactor]
}

final class PresenterWindow: NSWindow {
    override var canBecomeKey: Bool { true }
    override var canBecomeMain: Bool { true }
}
final class BackdropWindow: NSPanel {
    override var canBecomeKey: Bool { false }
    override var canBecomeMain: Bool { false }
}
final class Presenter: NSObject, NSApplicationDelegate, WKScriptMessageHandler, WKNavigationDelegate, NSWindowDelegate {
    let layoutPath: String
    var windows: [String: NSWindow] = [:]
    var views: [String: WKWebView] = [:]
    var signals: [DispatchSourceSignal] = []
    var backdrop: BackdropWindow?
    var foregroundPids = Set<Int>()
    var terminalWindows = Set<Int>()
    init(_ path: String) { layoutPath = path }
    func applicationDidFinishLaunching(_ notification: Notification) {
        NSApp.setActivationPolicy(.regular)
        let background = BackdropWindow(contentRect: .zero,
            styleMask: [.borderless, .nonactivatingPanel], backing: .buffered, defer: false)
        background.title = "Demo Presenter — Background"
        background.backgroundColor = .black
        background.isOpaque = true
        background.hasShadow = false
        background.isFloatingPanel = false
        background.level = .normal
        background.hidesOnDeactivate = false
        background.collectionBehavior = [.stationary, .ignoresCycle]
        background.isReleasedWhenClosed = false
        backdrop = background
        for name in ["header", "browser"] {
            let config = WKWebViewConfiguration()
            config.userContentController.add(self, name: "navigation")
            let view = WKWebView(frame: .zero, configuration: config)
            view.navigationDelegate = self
            let window = PresenterWindow(contentRect: .zero, styleMask: [.borderless], backing: .buffered, defer: false)
            window.title = name == "header" ? "Demo Presenter — Header" : "Demo Presenter — Platform"
            window.contentView = view
            window.delegate = self
            window.isReleasedWhenClosed = false
            windows[name] = window
            views[name] = view
            view.load(URLRequest(url: URL(string: "http://127.0.0.1:18080/#native-" + name)!))
        }
        restore()
        for number in [SIGUSR1, SIGTERM, SIGINT] {
            signal(number, SIG_IGN)
            let source = DispatchSource.makeSignalSource(signal: number, queue: .main)
            source.setEventHandler { [weak self] in
                if number == SIGUSR1 { self?.restore() } else { NSApp.terminate(nil) }
            }
            source.resume()
            signals.append(source)
        }
        let menu = NSMenu()
        let root = NSMenuItem()
        menu.addItem(root)
        let appMenu = NSMenu()
        appMenu.addItem(withTitle: "Close Presenter (keep demo running)", action: #selector(NSApplication.terminate(_:)), keyEquivalent: "q")
        root.submenu = appMenu
        NSApp.mainMenu = menu
        NSApp.activate(ignoringOtherApps: true)
    }
    func restore() {
        guard let data = try? Data(contentsOf: URL(fileURLWithPath: layoutPath)),
              let layout = try? JSONSerialization.jsonObject(with: data) as? [String: [Int]],
              let primary = NSScreen.screens.first else { return }
        foregroundPids = Set(layout["_foregroundPids"] ?? [])
        terminalWindows = Set(layout["_terminalWindows"] ?? [])
        if let r = layout["backdrop"], r.count == 4 {
            backdrop?.setFrame(NSRect(x: r[0], y: Int(primary.frame.maxY) - r[1] - r[3],
                                     width: r[2], height: r[3]), display: true)
        }
        for (name, window) in windows {
            guard let r = layout[name], r.count == 4 else { continue }
            window.setFrame(NSRect(x: r[0], y: Int(primary.frame.maxY) - r[1] - r[3], width: r[2], height: r[3]), display: true)
            window.orderFront(nil)
        }
        placeBackdrop()
    }
    func applicationDidBecomeActive(_ notification: Notification) { placeBackdrop() }
    func placeBackdrop() {
        guard let backdrop = backdrop else { return }
        // Window numbers/PIDs only: no screenshots or titles from unrelated apps.
        let ownWindows = Set(windows.values.map { $0.windowNumber })
        let entries = CGWindowListCopyWindowInfo([.optionOnScreenOnly, .excludeDesktopElements],
                                               kCGNullWindowID) as? [[String: Any]] ?? []
        let anchors = entries.compactMap { entry -> Int? in
            guard let number = entry[kCGWindowNumber as String] as? Int,
                  let owner = entry[kCGWindowOwnerPID as String] as? Int,
                  let layer = entry[kCGWindowLayer as String] as? Int, layer == 0,
                  ownWindows.contains(number) || foregroundPids.contains(owner) || terminalWindows.contains(number)
            else { return nil }
            return number
        }
        // Entries are front-to-back. Stay immediately behind the demo group,
        // above the older windows, without changing anyone else's window level.
        if let backmost = anchors.last {
            backdrop.order(.below, relativeTo: backmost)
        } else {
            backdrop.orderBack(nil)
        }
    }
    func userContentController(_ controller: WKUserContentController, didReceive message: WKScriptMessage) {
        guard message.frameInfo.isMainFrame, message.frameInfo.securityOrigin.host == "127.0.0.1",
              let target = message.body as? String, ["global", "platform", "brake", "tire"].contains(target) else { return }
        // A closed navigation enum only; never command or lifecycle dispatch.
        for view in views.values {
            view.evaluateJavaScript("window.dispatchEvent(new CustomEvent('presenter-navigation',{detail:'" + target + "'}))", completionHandler: nil)
        }
    }
    func webView(_ webView: WKWebView, decidePolicyFor navigationAction: WKNavigationAction,
                 decisionHandler: @escaping (WKNavigationActionPolicy) -> Void) {
        let url = navigationAction.request.url
        decisionHandler(url?.scheme == "http" && url?.host == "127.0.0.1" && url?.port == 18080 ? .allow : .cancel)
    }
    func windowShouldClose(_ sender: NSWindow) -> Bool { NSApp.terminate(nil); return false }
}

if CommandLine.arguments.count == 2 && CommandLine.arguments[1] == "screen" {
    guard let value = screenInfo(), let data = try? JSONSerialization.data(withJSONObject: value) else { exit(2) }
    print(String(decoding: data, as: UTF8.self))
} else if CommandLine.arguments.count == 3 && CommandLine.arguments[1] == "present" {
    let app = NSApplication.shared
    let presenter = Presenter(CommandLine.arguments[2])
    app.delegate = presenter
    app.run()
} else { exit(2) }
