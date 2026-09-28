// SPDX-FileCopyrightText: 2026 maninblack
// SPDX-License-Identifier: MIT

import AppKit
import Foundation

struct SetupReply: Decodable {
    let status: String
    let volumeUUID: String?
    let revision: Int64?
    let logicalBytes: UInt64?
    let reserveBytes: UInt64?
    let payloadDigestsVerified: Bool?
    let runtimeChanged: Bool?
    let cloudAccessed: Bool?
    let demoReady: Bool?
    let dockerApplicationPresent: Bool?
    let dockerEngineChecked: Bool?
    let domain: String?
    let selectionToken: String?
    let rolesChecked: Bool?
    let oemValidUntil: String?
    let spValidUntil: String?
    let cloudStage: String?
    let checks: [CloudCheck]?
}

struct CloudCheck: Decodable { let label: String; let state: String }

struct SetupEvent: Decodable {
    let kind: String
    let stage: String?
    let bytes: UInt64?
    let totalBytes: UInt64?
    let files: UInt64?
    let totalFiles: UInt64?
    let result: SetupReply?
    let code: String?

    var fraction: Double? {
        guard stage == "COPY_VERIFIED", let bytes, let totalBytes, totalBytes > 0,
              bytes <= totalBytes, let files, let totalFiles, totalFiles > 0,
              files <= totalFiles else { return nil }
        return min(0.99, Double(bytes) / Double(totalBytes))
    }
}

enum SetupFault: Error { case protocolFailure }

let cloudStages = ["CLOUD_LOCAL_STATE": "Checking the private installed instance…",
                   "CLOUD_PACKAGE_LEASE": "Checking the selected package and acquiring its usage locks…",
                   "CLOUD_CONFIGURATION_LOCK": "Acquiring the private Demo Control configuration lock…",
                   "CLOUD_PAIR_CHECK": "Verifying the installed SDK and inspecting both certificates locally…",
                   "CLOUD_REFERENCE_WRITE": "Revalidating and saving the two file references…",
                   "CLOUD_ACCESS_CHECK": "Reading Cloud identities, association and prerequisites…"]

final class CloudDeadline {
    private let lock = NSLock()
    private var expired = false
    private let timer = DispatchSource.makeTimerSource(queue: .global())
    init(_ process: Process, seconds: Double = 120) {
        timer.schedule(deadline: .now() + seconds)
        timer.setEventHandler { [weak self] in
            guard let self, process.isRunning else { return }
            self.lock.lock(); self.expired = true; self.lock.unlock()
            let pid = process.processIdentifier
            if getpgid(pid) == pid { kill(-pid, SIGTERM) }
            else { process.terminate() }
        }
        timer.resume()
    }
    func finish() -> Bool {
        timer.cancel(); lock.lock(); defer { lock.unlock() }; return expired
    }
}

// A terminal message alone is not success: also require a clean process exit.
struct SetupExchange {
    var terminal: SetupEvent?
    mutating func receive(_ event: SetupEvent) throws {
        guard terminal == nil else { throw SetupFault.protocolFailure }
        switch event.kind {
        case "progress":
            guard (["COPY_VERIFIED", "VERIFYING_AND_INSTALLING", "VERIFYING_LOCAL_SELECTION"].contains(event.stage ?? "") || cloudStages[event.stage ?? ""] != nil),
                  event.stage != "COPY_VERIFIED" || event.fraction != nil else { throw SetupFault.protocolFailure }
        case "result":
            guard event.result != nil else { throw SetupFault.protocolFailure }
            terminal = event
        case "error":
            guard let code = event.code,
                  code.range(of: "^[A-Z][A-Z0-9_]{2,100}$", options: .regularExpression) != nil
            else { throw SetupFault.protocolFailure }
            terminal = event
        default: throw SetupFault.protocolFailure
        }
    }
    func finish(action: String, exit: Int32) throws -> SetupReply {
        guard exit == 0, let event = terminal, event.kind == "result", let reply = event.result,
              reply.runtimeChanged == false, reply.cloudAccessed == (action == "cloud-check") else { throw SetupFault.protocolFailure }
        switch action {
        case "preflight":
            guard reply.status == "PREFLIGHT_PASSED", let uuid = reply.volumeUUID, UUID(uuidString: uuid) != nil,
                  let revision = reply.revision, revision >= 0, revision < 9_007_199_254_740_992,
                  reply.logicalBytes != nil, reply.reserveBytes != nil,
                  reply.payloadDigestsVerified == false else { throw SetupFault.protocolFailure }
        case "install":
            guard reply.status == "INSTALLED_NOT_ACTIVATED" else { throw SetupFault.protocolFailure }
        case "prepare":
            guard reply.status == "SELECTED_NOT_STARTED", reply.demoReady == false,
                  reply.dockerEngineChecked == false else { throw SetupFault.protocolFailure }
        case "cloud-inspect", "cloud-save", "cloud-check":
            let expected = ["cloud-inspect": "CERTIFICATE_PAIR_INSPECTED", "cloud-save": "CLOUD_REFERENCES_SAVED", "cloud-check": "CLOUD_ACCESS_OBSERVED"]
            guard reply.status == expected[action], reply.demoReady == false,
                  (action == "cloud-check" ? reply.rolesChecked != nil : reply.rolesChecked == false), let domain = reply.domain, domain.count <= 253,
                  domain.range(of: "^[a-z0-9.-]+$", options: .regularExpression) != nil,
                  let token = reply.selectionToken,
                  token.range(of: "^[a-f0-9]{64}$", options: .regularExpression) != nil,
                  reply.oemValidUntil != nil, reply.spValidUntil != nil else { throw SetupFault.protocolFailure }
            if action == "cloud-check" {
                guard ["READY", "MISSING", "BLOCKED"].contains(reply.cloudStage ?? ""),
                      let checks = reply.checks, !checks.isEmpty, checks.count <= 11,
                      checks.allSatisfy({ $0.label.count <= 80 && ["READY", "MISSING", "BLOCKED", "CONFLICT", "AFTER_PROVISION"].contains($0.state) })
                else { throw SetupFault.protocolFailure }
            }
        default: throw SetupFault.protocolFailure
        }
        return reply
    }
}

final class SetupApp: NSObject, NSApplicationDelegate, NSWindowDelegate, NSTextFieldDelegate {
    private var window: NSWindow!
    private let source = NSTextField(string: "")
    private let store = NSTextField(string: NSHomeDirectory() + "/AosEdge SDV Packages")
    private let state = NSTextField(string: NSHomeDirectory() + "/SDV-Lab-Data")
    private let check = NSButton(title: "Check installation", target: nil, action: nil)
    private let install = NSButton(title: "Install package", target: nil, action: nil)
    private let prepare = NSButton(title: "Prepare local data", target: nil, action: nil)
    private let cloud = NSButton(title: "Set up Cloud access…", target: nil, action: nil)
    private var cloudWindow: NSWindow?
    private let oem = NSTextField(string: "")
    private let sp = NSTextField(string: "")
    private let inspectPair = NSButton(title: "1. Inspect locally", target: nil, action: nil)
    private let savePair = NSButton(title: "2. Use this pair", target: nil, action: nil)
    private let checkCloud = NSButton(title: "3. Check Cloud access", target: nil, action: nil)
    private let closeCloud = NSButton(title: "Close", target: nil, action: nil)
    private let cloudStatus = NSTextField(wrappingLabelWithString: "")
    private let cloudDetail = NSTextField(wrappingLabelWithString: "")
    private var cloudPickers: [NSButton] = []
    private var pairToken: String?
    private var pairSaved = false
    private let status = NSTextField(wrappingLabelWithString: "Choose the complete offline kit to begin.")
    private let detail = NSTextField(wrappingLabelWithString: "Installation is offline. Cloud access is a separate, explicit step; your running demo stays unchanged.")
    private let next = NSTextField(wrappingLabelWithString: "After local setup\nHave OEM and SP certificates? Open Cloud access. A selected, fresh instance is required.\nNew-certificate enrollment and first launch remain separate, upcoming steps.")
    private let progress = NSProgressIndicator()
    private var pickers: [NSButton] = []
    private var checked: SetupReply?
    private var installed = false
    private var busy = false
    private var generation = UUID()

    func applicationDidFinishLaunching(_ notification: Notification) {
        let menu = NSMenu()
        let application = NSMenuItem()
        menu.addItem(application)
        application.submenu = NSMenu()
        application.submenu?.addItem(withTitle: "Quit SDV Lab Setup", action: #selector(NSApplication.terminate(_:)), keyEquivalent: "q")
        let edit = NSMenuItem(title: "Edit", action: nil, keyEquivalent: "")
        edit.submenu = NSMenu(title: "Edit")
        for (title, selector, key) in [("Undo", "undo:", "z"), ("Cut", "cut:", "x"),
                                       ("Copy", "copy:", "c"), ("Paste", "paste:", "v"),
                                       ("Select All", "selectAll:", "a")] {
            edit.submenu?.addItem(withTitle: title, action: NSSelectorFromString(selector), keyEquivalent: key)
        }
        menu.addItem(edit)
        NSApp.mainMenu = menu
        window = NSWindow(contentRect: NSRect(x: 0, y: 0, width: 850, height: 760),
                          styleMask: [.titled, .closable, .miniaturizable], backing: .buffered, defer: false)
        window.title = "AosEdge Platform — SDV Lab Setup"
        window.delegate = self
        window.isReleasedWhenClosed = false
        window.backgroundColor = .windowBackgroundColor
        let column = NSStackView()
        column.orientation = .vertical
        column.alignment = .leading
        column.spacing = 15
        column.translatesAutoresizingMaskIntoConstraints = false
        window.contentView!.addSubview(column)
        NSLayoutConstraint.activate([
            column.leadingAnchor.constraint(equalTo: window.contentView!.leadingAnchor, constant: 30),
            column.trailingAnchor.constraint(equalTo: window.contentView!.trailingAnchor, constant: -30),
            column.topAnchor.constraint(equalTo: window.contentView!.topAnchor, constant: 26)
        ])
        func label(_ text: String, _ size: CGFloat, _ weight: NSFont.Weight = .regular) -> NSTextField {
            let view = NSTextField(wrappingLabelWithString: text)
            view.font = .systemFont(ofSize: size, weight: weight)
            return view
        }
        column.addArrangedSubview(label("AosEdge Platform", 14, .semibold))
        column.addArrangedSubview(label("Set up your SDV Lab", 30, .bold))
        let subtitle = label("1  Choose & check     →     2  Install     →     3  Prepare local data", 15, .medium)
        subtitle.textColor = .systemBlue
        column.addArrangedSubview(subtitle)
        column.addArrangedSubview(label("Local engineering preview · Apple silicon · macOS 26 or later", 12))
        for (index, title, field, caption) in [
            (0, "Complete offline kit", source, "Select the Kit 007 folder. This installer verifies its independently pinned release."),
            (1, "Package storage", store, "Large, verified program files. An external disk with ownership enabled is supported."),
            (2, "Private demo data", state, "Keep this short path on the internal disk. Credentials and run data are never copied from a developer setup.")
        ] {
            column.addArrangedSubview(label(title, 15, .semibold))
            field.font = .systemFont(ofSize: 13)
            field.placeholderString = index == 0 ? "Choose a complete kit folder…" : nil
            field.delegate = self
            field.setAccessibilityLabel(title)
            let choose = NSButton(title: "Choose…", target: self, action: #selector(pick(_:)))
            choose.tag = index
            choose.setAccessibilityLabel("Choose " + title.lowercased())
            pickers.append(choose)
            let row = NSStackView(views: [field, choose])
            row.spacing = 10
            column.addArrangedSubview(row)
            row.widthAnchor.constraint(equalTo: column.widthAnchor).isActive = true
            field.setContentHuggingPriority(.defaultLow, for: .horizontal)
            let note = label(caption, 12)
            note.textColor = .secondaryLabelColor
            column.addArrangedSubview(note)
        }
        check.target = self; check.action = #selector(doCheck)
        install.target = self; install.action = #selector(doInstall)
        prepare.target = self; prepare.action = #selector(doPrepare)
        cloud.target = self; cloud.action = #selector(openCloud)
        check.bezelStyle = .rounded; install.bezelStyle = .rounded; prepare.bezelStyle = .rounded
        column.addArrangedSubview(NSStackView(views: [check, install, prepare, cloud]))
        progress.style = .bar; progress.isIndeterminate = false
        progress.minValue = 0; progress.maxValue = 1
        column.addArrangedSubview(progress)
        progress.widthAnchor.constraint(equalTo: column.widthAnchor).isActive = true
        status.font = .systemFont(ofSize: 16, weight: .semibold)
        detail.font = .systemFont(ofSize: 13)
        next.font = .systemFont(ofSize: 13)
        next.textColor = .secondaryLabelColor
        for view in [status, detail, next] {
            column.addArrangedSubview(view)
            view.widthAnchor.constraint(equalTo: column.widthAnchor).isActive = true
        }
        refresh()
        window.center(); window.makeKeyAndOrderFront(nil)
        NSApp.activate(ignoringOtherApps: true)
    }

    private func refresh() {
        check.isEnabled = !busy && !source.stringValue.isEmpty
        install.isEnabled = !busy && checked != nil && !installed
        prepare.isEnabled = !busy && installed && checked != nil
        cloud.isEnabled = !busy && !state.stringValue.isEmpty
        for field in [source, store, state] { field.isEnabled = !busy }
        for button in pickers { button.isEnabled = !busy }
        for field in [oem, sp] { field.isEnabled = !busy }
        for button in cloudPickers { button.isEnabled = !busy }
        inspectPair.isEnabled = !busy && !oem.stringValue.isEmpty && !sp.stringValue.isEmpty
        savePair.isEnabled = !busy && pairToken != nil && !pairSaved
        checkCloud.isEnabled = !busy && pairToken != nil && pairSaved
        closeCloud.isEnabled = !busy
    }

    private func invalidate() {
        guard !busy else { return }
        generation = UUID(); checked = nil; installed = false
        progress.doubleValue = 0
        status.stringValue = "Check your selected folders before installing."
        status.textColor = .labelColor
        detail.stringValue = "Changing any folder requires a new check. No running demo will be switched."
        next.stringValue = "After local setup\nUse Cloud access for existing OEM/SP certificates.\nSecure enrollment and first launch remain separate, upcoming steps."
        refresh()
    }

    func controlTextDidChange(_ obj: Notification) {
        if let field = obj.object as? NSTextField, field === oem || field === sp { invalidatePair() }
        else { invalidate() }
    }

    private func invalidatePair() {
        guard !busy else { return }
        pairToken = nil; pairSaved = false
        cloudStatus.stringValue = "Choose your existing OEM and SP certificate files."
        cloudStatus.textColor = .labelColor
        cloudDetail.stringValue = "Inspection is local only. It checks format, validity and a common domain — not account roles. Files stay in their current locations; only their references will be saved."
        refresh()
    }

    @objc private func openCloud() {
        guard !busy else { return }
        if cloudWindow == nil {
            let sheet = NSWindow(contentRect: NSRect(x: 0, y: 0, width: 790, height: 650),
                                 styleMask: [.titled], backing: .buffered, defer: false)
            sheet.title = "Cloud access — existing certificates"
            sheet.isReleasedWhenClosed = false
            let column = NSStackView(); column.orientation = .vertical
            column.alignment = .leading; column.spacing = 16
            column.translatesAutoresizingMaskIntoConstraints = false
            sheet.contentView!.addSubview(column)
            NSLayoutConstraint.activate([
                column.leadingAnchor.constraint(equalTo: sheet.contentView!.leadingAnchor, constant: 24),
                column.trailingAnchor.constraint(equalTo: sheet.contentView!.trailingAnchor, constant: -24),
                column.topAnchor.constraint(equalTo: sheet.contentView!.topAnchor, constant: 24)
            ])
            let title = NSTextField(labelWithString: "Connect your own Cloud access")
            title.font = .systemFont(ofSize: 24, weight: .bold); column.addArrangedSubview(title)
            let intro = NSTextField(wrappingLabelWithString: "One OEM and one associated Service Provider for Brake and Tire.\nThis step never creates an account, publishes packages, provisions a unit or starts the demo.")
            intro.font = .systemFont(ofSize: 14); column.addArrangedSubview(intro)
            for (index, name, field) in [(0, "OEM certificate", oem), (1, "Service Provider certificate", sp)] {
                column.addArrangedSubview(NSTextField(labelWithString: name))
                field.delegate = self; field.setAccessibilityLabel(name)
                field.placeholderString = "Choose a private, unencrypted .p12 file…"
                let choose = NSButton(title: "Choose…", target: self, action: #selector(pickCertificate(_:)))
                choose.tag = index; choose.setAccessibilityLabel("Choose " + name)
                cloudPickers.append(choose)
                let row = NSStackView(views: [field, choose]); row.spacing = 10
                column.addArrangedSubview(row); row.widthAnchor.constraint(equalTo: column.widthAnchor).isActive = true
                field.setContentHuggingPriority(.defaultLow, for: .horizontal)
            }
            inspectPair.target = self; inspectPair.action = #selector(doInspectPair)
            savePair.target = self; savePair.action = #selector(doSavePair)
            checkCloud.target = self; checkCloud.action = #selector(doCheckCloud)
            column.addArrangedSubview(NSStackView(views: [inspectPair, savePair, checkCloud]))
            cloudStatus.font = .systemFont(ofSize: 16, weight: .semibold)
            cloudDetail.font = .systemFont(ofSize: 13)
            for view in [cloudStatus, cloudDetail] {
                column.addArrangedSubview(view); view.widthAnchor.constraint(equalTo: column.widthAnchor).isActive = true
            }
            closeCloud.target = self; closeCloud.action = #selector(dismissCloud)
            column.addArrangedSubview(closeCloud)
            cloudWindow = sheet
        }
        invalidatePair()
        window.beginSheet(cloudWindow!)
    }

    @objc private func dismissCloud() {
        guard !busy, let sheet = cloudWindow else { return }
        window.endSheet(sheet); sheet.orderOut(nil)
    }

    @objc private func pickCertificate(_ sender: NSButton) {
        guard !busy, let sheet = cloudWindow else { return }
        let panel = NSOpenPanel(); panel.canChooseFiles = true; panel.canChooseDirectories = false
        panel.allowsMultipleSelection = false; panel.prompt = "Use file reference"
        panel.message = "Select your own owner-private PKCS#12 file. Setup does not copy the key."
        panel.beginSheetModal(for: sheet) { [weak self] response in
            guard let self, response == .OK, let url = panel.url else { return }
            [self.oem, self.sp][sender.tag].stringValue = url.path
            self.invalidatePair()
        }
    }

    @objc private func doInspectPair() { run("cloud-inspect") }
    @objc private func doSavePair() { run("cloud-save") }
    @objc private func doCheckCloud() { run("cloud-check") }

    @objc private func pick(_ sender: NSButton) {
        guard !busy else { return }
        let panel = NSOpenPanel()
        panel.canChooseDirectories = true; panel.canChooseFiles = false
        panel.canCreateDirectories = false; panel.allowsMultipleSelection = false
        panel.prompt = "Choose folder"
        panel.message = sender.tag == 0 ? "Select the complete Kit 007 folder." :
            "Select an existing SDV folder, or a parent folder in which setup may create one."
        panel.beginSheetModal(for: window) { [weak self] response in
            guard let self, response == .OK, let url = panel.url else { return }
            var chosen = url.path
            if sender.tag > 0 {
                let marker = sender.tag == 1 ? "store.json" : "instance.json"
                if !FileManager.default.fileExists(atPath: url.appendingPathComponent(marker).path) {
                    chosen = url.appendingPathComponent(sender.tag == 1 ? "AosEdge SDV Packages" : "SDV-Lab-Data").path
                }
            }
            [self.source, self.store, self.state][sender.tag].stringValue = chosen
            self.invalidate()
        }
    }

    @objc private func doCheck() { run("preflight") }
    @objc private func doInstall() { run("install") }
    @objc private func doPrepare() { run("prepare") }

    private func run(_ action: String) {
        let cloudAction = action.hasPrefix("cloud-")
        guard !busy, cloudAction || action == "preflight" || checked != nil else { return }
        var request: [String: Any] = ["action": action, "source": source.stringValue,
                                      "store": store.stringValue, "state": state.stringValue]
        if cloudAction {
            request = ["action": action, "state": state.stringValue, "oem": oem.stringValue, "sp": sp.stringValue]
            if action != "cloud-inspect" {
                guard let pairToken else { return }; request["selectionToken"] = pairToken
            }
        } else if action != "preflight" {
            request["volumeUUID"] = checked!.volumeUUID!
            request["revision"] = checked!.revision!
        } else { checked = nil; installed = false }
        guard let raw = try? JSONSerialization.data(withJSONObject: request),
              let resources = Bundle.main.resourceURL else { return }
        busy = true; generation = UUID(); let token = generation
        status.textColor = .labelColor
        status.stringValue = action == "preflight" ? "Checking folders, release and available space…" :
            action == "install" ? "Verifying and installing the complete package…" : "Verifying the selected version and preparing local data…"
        detail.stringValue = "This window stays responsive. Large-file verification can take several minutes."
        if cloudAction {
            cloudStatus.textColor = .labelColor
            cloudStatus.stringValue = action == "cloud-inspect" ? "Inspecting files locally…" : action == "cloud-save" ? "Rechecking and saving both references…" : "Checking the selected Cloud — read only…"
            cloudDetail.stringValue = action == "cloud-check" ? "Authenticating OEM and SP, checking association and prerequisites. This can take up to 45 seconds after local SDK verification. No Cloud objects will be created." : "Verifying the installed SDK and certificate files. No Cloud request is made."
        }
        progress.isIndeterminate = true; progress.startAnimation(nil)
        refresh()
        DispatchQueue.global(qos: .userInitiated).async { [weak self] in
            let process = Process()
            process.executableURL = resources.appendingPathComponent("python/bin/python3.12")
            process.arguments = ["-I", "-B", resources.appendingPathComponent("tooling/scripts/distribution/setup_bridge.py").path]
            process.environment = ["HOME": NSHomeDirectory(), "PATH": "/usr/bin:/bin:/usr/sbin:/sbin", "LC_ALL": "C"]
            let input = Pipe(), output = Pipe()
            process.standardInput = input; process.standardOutput = output
            process.standardError = FileHandle.nullDevice
            var exchange = SetupExchange()
            var failed = false
            var deadline: CloudDeadline?
            do {
                try process.run()
                if cloudAction { deadline = CloudDeadline(process) }
                try input.fileHandleForWriting.write(contentsOf: raw)
                try input.fileHandleForWriting.close()
                var buffer = Data()
                while true {
                    let chunk = output.fileHandleForReading.availableData
                    if chunk.isEmpty { break }
                    if failed { continue } // Drain without unbounded allocation; never kill a writer.
                    buffer.append(chunk)
                    while let end = buffer.firstIndex(of: 10) {
                        let line = buffer[..<end]
                        guard line.count <= 16384 else { throw SetupFault.protocolFailure }
                        do {
                            let event = try JSONDecoder().decode(SetupEvent.self, from: line)
                            try exchange.receive(event)
                            DispatchQueue.main.async { [weak self] in
                                guard let self, self.generation == token else { return }
                                if let stage = event.stage, let message = cloudStages[stage] {
                                    self.cloudDetail.stringValue = message
                                }
                                if let fraction = event.fraction {
                                    self.progress.stopAnimation(nil); self.progress.isIndeterminate = false
                                    self.progress.doubleValue = fraction
                                    self.detail.stringValue = "Verified \(event.files!) of \(event.totalFiles!) files · \(Int(fraction * 100))%"
                                }
                            }
                        } catch { failed = true }
                        buffer.removeSubrange(...end)
                    }
                    if buffer.count > 16384 { failed = true; buffer.removeAll() }
                }
                if !buffer.isEmpty { failed = true }
                process.waitUntilExit()
                if deadline?.finish() == true { throw SetupFault.protocolFailure }
                if failed { throw SetupFault.protocolFailure }
                let reply = try exchange.finish(action: action, exit: process.terminationStatus)
                DispatchQueue.main.async { [weak self] in self?.complete(action, reply, token) }
            } catch {
                // Launch failures or a malformed protocol never become a success receipt.
                if process.isRunning {
                    try? input.fileHandleForWriting.close()
                    while !output.fileHandleForReading.availableData.isEmpty {}
                    process.waitUntilExit()
                }
                let code = deadline?.finish() == true ? "SETUP_CLOUD_DEADLINE" : (exchange.terminal?.kind == "error" ? exchange.terminal?.code : nil)
                DispatchQueue.main.async { [weak self] in self?.fail(action, code ?? "SETUP_HELPER_FAILED", token) }
            }
        }
    }

    private func complete(_ action: String, _ reply: SetupReply, _ token: UUID) {
        guard generation == token else { return }
        busy = false; progress.stopAnimation(nil); progress.isIndeterminate = false; progress.doubleValue = 1
        status.textColor = .labelColor
        if action.hasPrefix("cloud-") {
            pairToken = reply.selectionToken
            if action == "cloud-inspect" {
                pairSaved = false
                cloudStatus.stringValue = "Local inspection passed — roles not yet checked"
                cloudDetail.stringValue = "Cloud domain: \(reply.domain!)\nOEM valid until: \(reply.oemValidUntil!)\nSP valid until: \(reply.spValidUntil!)\nUse this pair to save both file references. No Cloud connection has been attempted."
            } else if action == "cloud-save" {
                pairSaved = true
                cloudStatus.stringValue = "References saved — Cloud access not yet checked"
                cloudDetail.stringValue = "Cloud domain: \(reply.domain!)\nCheck Cloud access to authenticate the selected pair and inspect prerequisites. No keys were copied and nothing was started."
            } else {
                let headings = ["READY": "Cloud prerequisites observed — demo not started", "MISSING": "Access checked — Cloud preparation is still needed", "BLOCKED": "Cloud check found blockers — demo not started"]
                cloudStatus.stringValue = headings[reply.cloudStage!]!
                let states = ["READY": "Confirmed", "MISSING": "Missing — not created", "BLOCKED": "Blocked", "CONFLICT": "Conflict", "AFTER_PROVISION": "Verify after provisioning"]
                cloudDetail.stringValue = "Cloud domain: \(reply.domain!)\n" + reply.checks!.map { "\($0.label): \(states[$0.state]!)" }.joined(separator: "\n")
            }
            status.stringValue = "Cloud access step completed — demo not started"
            detail.stringValue = "See the Cloud access window for the observation. Docker, secure enrollment and first launch remain separate steps."
            refresh(); return
        }
        if action == "preflight" {
            checked = reply
            status.stringValue = "Checks passed — ready to install files"
            let gib = Double(reply.logicalBytes!) / pow(1024, 3)
            detail.stringValue = String(format: "Package: %.1f GiB logical size. 90 GiB engineering reserve checked. Full content verification happens during installation.", gib)
        } else if action == "install" {
            installed = true
            status.stringValue = "Package installed — demo not started"
            detail.stringValue = "Next, explicitly prepare private local data and select this version. No Cloud access or running installation was changed."
        } else {
            checked = nil
            status.stringValue = "Local setup complete — Cloud setup remains"
            detail.stringValue = "Version selected, not started. Your private data folder is separate from program storage."
            next.stringValue = "Next steps — not yet verified\nDocker: \(reply.dockerApplicationPresent == true ? "application found; engine not checked" : "application not found in /Applications").\nOpen Cloud access if you already have OEM and SP certificates. New-certificate enrollment and first launch remain separate steps."
        }
        refresh()
    }

    private func fail(_ action: String, _ code: String, _ token: UUID) {
        guard generation == token else { return }
        busy = false; checked = nil; installed = false
        progress.stopAnimation(nil); progress.isIndeterminate = false; progress.doubleValue = 0
        status.textColor = .systemRed
        status.stringValue = "Setup stopped safely — review and check again"
        let hint: String
        if code.contains("SPACE") { hint = "Free more space on the selected package disk." }
        else if code.contains("VOLUME") { hint = "Reconnect the original disk and enable ownership. Private data must remain on the internal disk." }
        else if code.contains("SOCKET_PATH") { hint = "Choose a shorter internal private-data path, for example ~/SDV-Lab-Data." }
        else if code.contains("RETAINED") || code.contains("IN_USE") || code.contains("BUSY") { hint = "This instance has a retained run or an active owner. Do not delete it to proceed; use a separate fresh data folder." }
        else if code.contains("REVISION") { hint = "The selected version changed. Check again before selecting a version." }
        else if code.contains("MANIFEST") || code.contains("DIGEST") || code.contains("MISMATCH") { hint = "Choose the intact Kit 007 package. Setup will not accept altered files." }
        else if code.contains("PLATFORM") { hint = "This preview requires Apple silicon and macOS 26 or later." }
        else { hint = "Review the folders and package. Existing files and any completed transaction are preserved." }
        detail.stringValue = hint + "\nDiagnostic: " + code
        if action.hasPrefix("cloud-") {
            pairToken = nil; pairSaved = false
            status.stringValue = "Cloud step needs attention — local installation preserved"
            cloudStatus.textColor = .systemRed
            cloudStatus.stringValue = "Cloud step stopped — no readiness confirmed"
            var explanation = "Check the selected files and inspect again. Completed local saves are preserved; no automatic retry."
            if code.contains("DOMAIN_MISMATCH") { explanation = "OEM and SP certificates belong to different Cloud domains. Choose a matching pair." }
            else if code.contains("CHANGED") { explanation = "A file, configuration or package selection changed. Inspect again before using this pair." }
            else if code.contains("RETAINED") { explanation = "This instance already has a retained demo run. Use its normal Demo Control flow, or a fresh setup instance." }
            else if code.contains("PREPARATION_REQUIRED") || code.contains("PACKAGE_REQUIRED") { explanation = "Prepare local data and select Kit 007 before setting up Cloud access." }
            else if code.contains("PRIVATE") || code.contains("CREDENTIAL") || code.contains("CERTIFICATE") { explanation = "Choose two distinct owner-private, valid, unencrypted PKCS#12 files. Setup does not change file permissions or decrypt certificates." }
            else if code.contains("DEADLINE") { explanation = "The Cloud step exceeded its two-minute limit. Its helper was stopped; any completed local save is preserved. Inspect again explicitly after reviewing the local files or connection." }
            cloudDetail.stringValue = explanation + "\nDiagnostic: " + code
        }
        refresh()
    }

    private func mayClose() -> Bool {
        guard busy else { return true }
        let alert = NSAlert()
        alert.messageText = "A setup operation is still running"
        alert.informativeText = "Wait for its result before closing. The working demo is not being changed."
        alert.addButton(withTitle: "Keep setup open")
        alert.beginSheetModal(for: window)
        return false
    }
    func windowShouldClose(_ sender: NSWindow) -> Bool { mayClose() }
    func applicationShouldTerminate(_ sender: NSApplication) -> NSApplication.TerminateReply { mayClose() ? .terminateNow : .terminateCancel }
    func applicationShouldTerminateAfterLastWindowClosed(_ sender: NSApplication) -> Bool { true }
}

func selfTest() throws {
    func event(_ raw: String) throws -> SetupEvent { try JSONDecoder().decode(SetupEvent.self, from: Data(raw.utf8)) }
    func rejects(_ action: () throws -> Void) {
        do { try action(); fatalError("Expected rejection") } catch {}
    }
    let copy = try event(#"{"kind":"progress","stage":"COPY_VERIFIED","bytes":10,"totalBytes":10,"files":1,"totalFiles":1}"#)
    precondition(copy.fraction == 0.99)
    let invalid = try event(#"{"kind":"progress","stage":"COPY_VERIFIED","bytes":11,"totalBytes":10,"files":1,"totalFiles":1}"#)
    var exchange = SetupExchange()
    rejects { try exchange.receive(invalid) }
    try exchange.receive(copy)
    rejects { _ = try exchange.finish(action: "install", exit: 0) }
    let result = try event(#"{"kind":"result","result":{"status":"INSTALLED_NOT_ACTIVATED","runtimeChanged":false,"cloudAccessed":false}}"#)
    try exchange.receive(result)
    rejects { try exchange.receive(copy) }
    rejects { _ = try exchange.finish(action: "install", exit: 1) }
    _ = try exchange.finish(action: "install", exit: 0)
    rejects { _ = try exchange.finish(action: "prepare", exit: 0) }
    let cloudRaw = #"{"kind":"result","result":{"status":"CLOUD_ACCESS_OBSERVED","runtimeChanged":false,"cloudAccessed":true,"demoReady":false,"domain":"stage.example.test","selectionToken":"aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa","rolesChecked":false,"oemValidUntil":"2030","spValidUntil":"2030","cloudStage":"MISSING","checks":[{"label":"Factory model","state":"MISSING"}]}}"#
    var cloud = SetupExchange(); try cloud.receive(event(cloudRaw))
    _ = try cloud.finish(action: "cloud-check", exit: 0)
    rejects { _ = try cloud.finish(action: "cloud-save", exit: 0) }
    rejects { _ = try cloud.finish(action: "cloud-check", exit: 1) }
    var falseReady = SetupExchange()
    try falseReady.receive(event(cloudRaw.replacingOccurrences(of: "\"demoReady\":false", with: "\"demoReady\":true")))
    rejects { _ = try falseReady.finish(action: "cloud-check", exit: 0) }
    let sleeper = Process(); sleeper.executableURL = URL(fileURLWithPath: "/bin/sleep")
    sleeper.arguments = ["5"]
    try sleeper.run()
    let deadline = CloudDeadline(sleeper, seconds: 0.05)
    sleeper.waitUntilExit()
    precondition(deadline.finish() && sleeper.terminationStatus != 0)
    print("SETUP_NATIVE_PROTOCOL_PASS")
}

if CommandLine.arguments.contains("--self-test") {
    do { try selfTest() } catch { exit(1) }
} else {
    let app = NSApplication.shared
    let delegate = SetupApp()
    app.delegate = delegate
    app.setActivationPolicy(.regular)
    app.run()
}
