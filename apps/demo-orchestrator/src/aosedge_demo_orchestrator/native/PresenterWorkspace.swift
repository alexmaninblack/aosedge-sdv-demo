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
    var clientTimer: Timer?
    var checkingClient = false
    var loadedClient: String?
    var perspective = "global"
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
        clientTimer = Timer.scheduledTimer(withTimeInterval: 5, repeats: true) { [weak self] _ in self?.checkClient() }
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
    func checkClient() {
        guard !checkingClient, !views.values.contains(where: { $0.isLoading }) else { return }
        checkingClient = true
        var request = URLRequest(url: URL(string: "http://127.0.0.1:18080/api/presenter/client-state")!)
        request.cachePolicy = .reloadIgnoringLocalCacheData
        request.timeoutInterval = 3
        URLSession.shared.dataTask(with: request) { [weak self] data, response, _ in
            DispatchQueue.main.async {
                guard let self = self else { return }
                guard (response as? HTTPURLResponse)?.statusCode == 200, let data = data,
                      let state = try? JSONSerialization.jsonObject(with: data) as? [String: Any],
                      let build = state["buildId"] as? String, build.count == 64,
                      let session = state["sessionId"] as? String, state["canReload"] as? Bool == true else {
                    self.checkingClient = false; return
                }
                let identity = build + ":" + session
                guard identity != self.loadedClient else { self.checkingClient = false; return }
                // Keep a protected confirmation or an unresolved client submission
                // intact. Only the paired idle windows adopt the new build/session.
                let group = DispatchGroup()
                var safe = true
                for view in self.views.values {
                    group.enter()
                    view.evaluateJavaScript("!document.querySelector('[role=dialog]') && !document.querySelector('[data-submission-pending=true]')") { value, error in
                        if error != nil || value as? Bool != true { safe = false }
                        group.leave()
                    }
                }
                group.notify(queue: .main) {
                    self.checkingClient = false
                    guard safe else { return }
                    self.loadedClient = identity
                    for view in self.views.values { view.reloadFromOrigin() }
                }
            }
        }.resume()
    }
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
              let target = message.body as? String, ["global", "platform", "brake", "tire", "session"].contains(target) else { return }
        if target == "session" {
            views["browser"]?.evaluateJavaScript("window.dispatchEvent(new Event('presenter-session'))", completionHandler: nil)
            return
        }
        perspective = target
        // A closed navigation enum only; never command or lifecycle dispatch.
        for view in views.values {
            view.evaluateJavaScript("window.dispatchEvent(new CustomEvent('presenter-navigation',{detail:'" + target + "'}))", completionHandler: nil)
        }
    }
    func webView(_ webView: WKWebView, didFinish navigation: WKNavigation!) {
        webView.evaluateJavaScript("window.dispatchEvent(new CustomEvent('presenter-navigation',{detail:'" + perspective + "'}))", completionHandler: nil)
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
