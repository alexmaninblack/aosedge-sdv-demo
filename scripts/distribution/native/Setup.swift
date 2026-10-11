// SPDX-FileCopyrightText: 2026 maninblack
// SPDX-License-Identifier: MIT

import AppKit
import ApplicationServices
import Foundation

// This is only a convenience path. The trusted helper still authenticates the
// complete inventory against its independent release pin before installation.
func bundledKitURL(app: URL, exists: (URL) -> Bool) -> URL? {
    let candidate = app.deletingLastPathComponent().appendingPathComponent("Runtime Kit", isDirectory: true)
    return exists(candidate.appendingPathComponent("application-manifest.json")) ? candidate : nil
}

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
    let imagesVerified: Int?
    let importAttempted: Bool?
    let domain: String?
    let selectionToken: String?
    let rolesChecked: Bool?
    let oemValidUntil: String?
    let spValidUntil: String?
    let cloudStage: String?
    let checks: [CloudCheck]?
    let presenterObserved: Bool?
    let layoutComplete: Bool?
    let serverStarted: Bool?
    let enrollmentStage: String?
    let role: String?
    let attemptId: String?
    let credentialPath: String?
    let subjects: [CloudSubjectRow]?
    let localInstalled: Bool?
    let backendsObserved: Bool?
    let launcherObserved: Bool?
    let storePath: String?
    let oemPath: String?
    let spPath: String?
    let prerequisite: String?
}

struct CloudCheck: Decodable { let label: String; let state: String }
struct CloudSubjectRow: Decodable { let team: String; let id: String; let state: String; let reason: String; let reference: [String: String]? }

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

enum CloudFeedbackTarget { case pair, enrollment, subjects }

func cloudFeedbackTarget(_ action: String) -> CloudFeedbackTarget? {
    if action.hasPrefix("cloud-enrollment-") { return .enrollment }
    if action.hasPrefix("cloud-subjects-") { return .subjects }
    return action.hasPrefix("cloud-") ? .pair : nil
}

func launchPermissionFailure(accessibilityTrusted: Bool) -> String? {
    accessibilityTrusted ? nil : "SETUP_LAUNCH_ACCESSIBILITY_REQUIRED"
}

let storageAccessHint = "Checking access to the selected package storage… If macOS asks for removable-disk access, review its system prompt. File verification waits for your response."
let cloudStages = ["CLOUD_LOCAL_STATE": "Checking the private installed instance…",
                   "CLOUD_PREREQUISITES": "Preparing only the missing demo model and Test verification set…",
                   "CLOUD_ENROLLMENT_STATE": "Checking the preserved enrollment attempt. A submission sends at most one request; no automatic retry…",
                   "CLOUD_SUBJECTS_CHECK": "Reading exact OEM/SP, Subject, service and recipient identities. No Cloud object is changed…",
                   "CLOUD_PACKAGE_LEASE": storageAccessHint,
                   "CLOUD_CONFIGURATION_LOCK": "Acquiring the private Demo Control configuration lock…",
                   "CLOUD_PAIR_CHECK": "Verifying the installed SDK and inspecting both certificates locally…",
                   "CLOUD_REFERENCE_WRITE": "Revalidating and saving the two file references…",
                   "CLOUD_ACCESS_CHECK": "Reading Cloud identities, association and prerequisites…"]

let launchStages = ["LAUNCH_VERIFYING_SELECTION": "Verifying the selected private instance…",
                    "LAUNCH_PACKAGE_ACCESS": storageAccessHint,
                    "LAUNCH_VERIFYING_PROGRAM": "Package storage is accessible. Verifying the selected program files…",
                    "LAUNCH_STARTING_PRESENTER": "Starting the selected Presenter — vehicle unchanged…",
                    "LAUNCH_OPENING_WINDOWS": "Opening the existing workspace and checking its windows…"]

let backendStages = ["BACKENDS_VERIFYING_SELECTION": "Verifying the selected installed instance…",
                     "BACKENDS_VERIFYING_ARCHIVE": "Verifying the packaged Brake and Tire images…",
                     "BACKENDS_CHECKING_ENGINE": "Checking the running local Docker Desktop engine and exact image IDs…",
                     "BACKENDS_IMPORTING": "Loading the verified images from your installed package — no download…",
                     "BACKENDS_RECONCILING": "Confirming both immutable images in the same Docker engine…"]

// The same scoped explanation is used in the main window and its Cloud sheet.
// A certificate domain mismatch is not evidence of a damaged installation.
func setupFailureHint(action: String, code: String) -> String {
    if code == "SETUP_FILE_ACCESS_DENIED" { return "Access to a selected file or folder was denied. Review folder permissions and any macOS removable-disk prompt. Setup does not change permissions or retry automatically." }
    if code == "SETUP_BACKENDS_DOCKER_MISSING" { return "Install Docker Desktop for Apple silicon using the Docker instructions, complete its first-run prompts, then choose Install SDV Lab again. No demo files were copied." }
    if code == "SETUP_BACKENDS_ENGINE_UNAVAILABLE" { return "Start the existing Docker Engine and wait until it is ready, then continue installation. Setup will reuse it without restarting it or opening Dashboard." }
    if code == "SETUP_LAUNCHER_FOREIGN_APPLICATION" || code == "SETUP_LAUNCHER_IDENTITY_INVALID" { return "The existing Applications entry is not an authorized SDV Lab launcher. It was preserved; resolve the application-name conflict before continuing." }
    if code == "SETUP_LAUNCHER_RECONCILIATION_REQUIRED" { return "A launcher replacement was interrupted or has an unknown predecessor. Existing applications are preserved. Review the signed launcher transaction before continuing." }
    if code == "CLOUD_REPAIR_SAME_OEM_REQUIRED" || code == "CLOUD_REPAIR_OWNER_CHANGED" { return "This retained Test belongs to its original OEM and Cloud environment. Keep the same OEM certificate and choose its associated SP. Setup will not repoint or delete the Test." }
    if code == "CLOUD_REPAIR_SP_ALREADY_CONFIGURED" { return "This Test already has an SP certificate. This repair only adds missing access; it does not replace an established Service Provider." }
    if code == "CLOUD_PAIR_AUTHENTICATION_REQUIRED" { return "Both accounts, their OEM/SP association and delivery permissions must be confirmed. Check that these are the intended OEM and associated Service Provider certificates; local file validity alone is insufficient." }
    if action == "prepare-backends" {
        if code.contains("DOCKER_MISSING") || code.contains("ENGINE_UNAVAILABLE") { return "Open Docker Desktop and wait until its engine is running, then choose Prepare backends. Setup does not install or start Docker." }
        if code.contains("LOCAL_CONTEXT") || code.contains("PLATFORM") { return "Use Docker Desktop's local desktop-linux context on this Apple silicon Mac. A remote or incompatible engine cannot be used; no Docker settings were changed." }
        if code.contains("UNCONFIRMED") || code.contains("DEADLINE") || code.contains("ENGINE_CHANGED") { return "The import outcome needs reconciliation. Existing images and the saved attempt are preserved. Prepare backends will inspect the same engine first and will not repeat an unresolved import." }
        if code.contains("PREPARATION_REQUIRED") || code.contains("INSTANCE_NOT_FOUND") { return "Choose the existing private-data folder prepared for this installer's version. Nothing was installed or selected automatically." }
        if code.contains("RETAINED") || code.contains("BUSY") { return "This first-use action cannot change a retained or busy demo. Existing vehicle state was preserved." }
        return "Backend preparation was not confirmed. Check the installed package and preserved attempt record. No containers, vehicle or Cloud operations were started; no automatic retry."
    }
    if action == "launch" {
        if code == "SETUP_LAUNCH_ACCESSIBILITY_REQUIRED" { return "macOS has not authorized this signed Setup app to place and inspect demo windows. In System Settings → Privacy & Security → Accessibility, authorize this version of AosEdge SDV Lab Setup. An enabled entry for an older preview may not apply. Then choose Open demo again. No launch operation was started; existing demo processes and data are unchanged. Full Disk Access and screen recording are not required." }
        if code == "SETUP_INSTANCE_NOT_FOUND" { return "No prepared instance was found in that private-data folder. Choose the existing demo data, or use Prepare local data for a new installation. Nothing was created or started." }
        if code.contains("PREPARATION_REQUIRED") { return "Choose the private-data folder already prepared for this installer's version. No version was switched." }
        if code.contains("BUSY") { return "Demo Control is busy or needs reconciliation. Finish that operation in the existing Presenter; nothing was stopped." }
        if code.contains("PORT") || code.contains("OWNER") { return "The local ports belong to another or unconfirmed instance. Its processes were preserved; no second Presenter was started." }
        if code.contains("VOLUME") { return "Reconnect the original package disk. Setup will not use another location." }
        if code.contains("DEADLINE") { return "Opening exceeded its two-minute limit. Review any pending macOS removable-disk prompt, then inspect existing Presenter windows before another explicit attempt. Any started Presenter is preserved; no action was replayed." }
        if code.contains("UNCONFIRMED") { return "Opening could not be confirmed. Any started Presenter is preserved. Inspect its windows before another explicit attempt; no action was replayed." }
        return "Opening was not confirmed. Review the selected instance and OS permissions. Existing demo data and processes were preserved."
    }
    if action.hasPrefix("cloud-") {
        if code == "CLOUD_PACKAGE_SIGNING_RSA_KEY_REQUIRED" { return "This certificate cannot sign demo packages. The installed Aos signer requires an RSA key for RS256. Choose an authorized RSA certificate pair; no key or certificate was replaced. Successful Cloud authentication alone does not prove package-signing compatibility." }
        if action.hasPrefix("cloud-enrollment-") { return "Enrollment was not confirmed. Inspect the saved attempt before any new submission. A request may already have reached Cloud; the retained key and attempt must not be deleted. Reconcile issuance in the official Cloud portal before requesting a replacement token. No automatic retry." }
        if code.contains("DOMAIN_MISMATCH") { return "OEM and SP certificates belong to different Cloud domains. Choose a matching pair." }
        if code.contains("CHANGED") { return "A file, configuration or package selection changed. Inspect again before using this pair." }
        if code.contains("RETAINED") { return "This instance already has a retained demo run. Use its normal Demo Control flow, or a fresh setup instance." }
        if code.contains("PREPARATION_REQUIRED") || code.contains("PACKAGE_REQUIRED") { return "Prepare local data and select this installer's version before setting up Cloud access." }
        if code.contains("PRIVATE") || code.contains("CREDENTIAL") || code.contains("CERTIFICATE") { return "Choose two distinct owner-private, valid, unencrypted PKCS#12 files. Setup does not change file permissions or decrypt certificates." }
        if code.contains("DEADLINE") { return "The Cloud step exceeded its two-minute limit. Review any pending macOS removable-disk prompt and the connection before another explicit inspection. Its helper was stopped; completed local saves are preserved. No automatic retry." }
        return "Check the selected files and inspect again. Completed local saves are preserved; no automatic retry."
    }
    if code.contains("SPACE") { return "Free more space on the selected package disk." }
    if code.contains("VOLUME") { return "Reconnect the original disk and enable ownership. Private data must remain on the internal disk." }
    if code.contains("SOCKET_PATH") { return "Choose a shorter internal private-data path, for example ~/SDV-Lab-Data." }
    if code.contains("RETAINED") || code.contains("IN_USE") || code.contains("BUSY") { return "This instance has a retained run or an active owner. Do not delete it to proceed; use a separate fresh data folder." }
    if code.contains("REVISION") { return "The selected version changed. Check again before selecting a version." }
    if code.contains("MANIFEST") || code.contains("DIGEST") || code.contains("MISMATCH") { return "Choose the intact package supplied with this installer. Setup will not accept altered files." }
    if code.contains("PLATFORM") { return "This preview requires Apple silicon and macOS 26 or later." }
    return "Review the folders and package. Existing files and any completed transaction are preserved."
}

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
            guard (["COPY_VERIFIED", "VERIFYING_AND_INSTALLING", "VERIFYING_LOCAL_SELECTION", "CHECKING_DOCKER", "INSTALLING_LAUNCHER"].contains(event.stage ?? "") || cloudStages[event.stage ?? ""] != nil || launchStages[event.stage ?? ""] != nil || backendStages[event.stage ?? ""] != nil),
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
              reply.runtimeChanged == (action == "launch"), reply.cloudAccessed != nil,
              ["cloud-enrollment-submit", "cloud-enrollment-pair"].contains(action) || reply.cloudAccessed == (["cloud-check", "cloud-connect", "cloud-observe", "cloud-subjects-inspect", "cloud-subjects-save"].contains(action)) else { throw SetupFault.protocolFailure }
        switch action {
        case "cloud-enrollment-pair":
            guard reply.status == "PAIR_ENROLLMENT_OBSERVED", reply.demoReady == false, reply.rolesChecked == false,
                  ["aws-stage.epmp-aos.projects.epam.com", "aoscloud.io"].contains(reply.domain ?? ""),
                  ["NOT_STARTED", "PREPARED", "RECEIVED", "RECONCILIATION_REQUIRED", "LOCAL_RECOVERY_AVAILABLE"].contains(reply.enrollmentStage ?? "") else { throw SetupFault.protocolFailure }
            for (role, path) in [("oem", reply.oemPath), ("sp", reply.spPath)] {
                if let path {
                    guard path.hasPrefix("/"), path.count <= 1024, !path.contains("/../"),
                          !path.unicodeScalars.contains(where: { $0.value < 32 }),
                          path.hasSuffix("/credentials/enrollment/\(role)/client.p12") else { throw SetupFault.protocolFailure }
                }
            }
            if reply.enrollmentStage == "RECEIVED" {
                guard reply.oemPath != nil, reply.spPath != nil else { throw SetupFault.protocolFailure }
            } else { guard ["oem", "sp"].contains(reply.role ?? "") else { throw SetupFault.protocolFailure } }
        case "setup-status":
            guard ["SETUP_NOT_INSTALLED", "SETUP_INSTALLED_OBSERVED"].contains(reply.status),
                  reply.localInstalled == (reply.status == "SETUP_INSTALLED_OBSERVED"),
                  reply.backendsObserved != nil, reply.launcherObserved != nil,
                  reply.localInstalled == true || (reply.backendsObserved == false && reply.launcherObserved == false),
                  reply.demoReady == false else { throw SetupFault.protocolFailure }
        case "setup-install":
            guard reply.status == "SETUP_LOCAL_INSTALLED", reply.localInstalled == true,
                  reply.backendsObserved == true, reply.launcherObserved == true,
                  reply.demoReady == false else { throw SetupFault.protocolFailure }
        case "install-launcher":
            guard reply.status == "SETUP_LAUNCHER_INSTALLED", reply.demoReady == false else { throw SetupFault.protocolFailure }
        case "cloud-connect", "cloud-observe":
            guard reply.status == "CLOUD_CONNECTED_OBSERVED", reply.demoReady == false,
                  reply.rolesChecked != nil, ["READY", "MISSING", "BLOCKED"].contains(reply.cloudStage ?? ""),
                  let domain = reply.domain, domain.count <= 253,
                  domain.range(of: "^[a-z0-9.-]+$", options: .regularExpression) != nil,
                  let checks = reply.checks, checks.count <= 20,
                  checks.allSatisfy({ $0.label.count <= 80 && ["READY", "MISSING", "BLOCKED", "CONFLICT", "AFTER_PROVISION"].contains($0.state) }) else { throw SetupFault.protocolFailure }
        case "prepare-backends":
            guard reply.status == "BACKEND_IMAGES_AVAILABLE", reply.demoReady == false,
                  reply.dockerEngineChecked == true, reply.imagesVerified == 2,
                  reply.importAttempted != nil else { throw SetupFault.protocolFailure }
        case "cloud-enrollment-status", "cloud-enrollment-recover", "cloud-enrollment-submit":
            guard reply.status == "CLOUD_ENROLLMENT_OBSERVED", reply.demoReady == false, reply.rolesChecked == false,
                  ["oem", "sp"].contains(reply.role ?? ""), let domain = reply.domain, domain.count <= 253,
                  domain.range(of: "^[a-z0-9.-]+$", options: .regularExpression) != nil,
                  ["NOT_STARTED", "PREPARED", "RECEIVED", "RECONCILIATION_REQUIRED", "LOCAL_RECOVERY_AVAILABLE"].contains(reply.enrollmentStage ?? ""),
                  reply.enrollmentStage == "NOT_STARTED" || UUID(uuidString: reply.attemptId ?? "") != nil else { throw SetupFault.protocolFailure }
            if reply.enrollmentStage == "RECEIVED" {
                guard let path = reply.credentialPath, path.hasPrefix("/"), path.count <= 1024,
                      path.hasSuffix("/credentials/enrollment/\(reply.role!)/client.p12"),
                      !path.contains("/../"), !path.unicodeScalars.contains(where: { $0.value < 32 }) else { throw SetupFault.protocolFailure }
            }
        case "launch":
            guard ["PRESENTER_OPENED", "PRESENTER_NEEDS_ATTENTION"].contains(reply.status),
                  reply.demoReady == false, reply.serverStarted != nil, reply.layoutComplete != nil,
                  reply.presenterObserved == (reply.status == "PRESENTER_OPENED"),
                  reply.layoutComplete != true || reply.presenterObserved == true else { throw SetupFault.protocolFailure }
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
        case "cloud-inspect", "cloud-save", "cloud-check", "cloud-subjects-inspect", "cloud-subjects-save":
            let expected = ["cloud-inspect": "CERTIFICATE_PAIR_INSPECTED", "cloud-save": "CLOUD_REFERENCES_SAVED", "cloud-check": "CLOUD_ACCESS_OBSERVED", "cloud-subjects-inspect": "CLOUD_SUBJECTS_OBSERVED", "cloud-subjects-save": "CLOUD_SUBJECT_REFERENCE_SAVED"]
            guard reply.status == expected[action], reply.demoReady == false,
                  (action == "cloud-check" ? reply.rolesChecked != nil : reply.rolesChecked == false), let domain = reply.domain, domain.count <= 253,
                  domain.range(of: "^[a-z0-9.-]+$", options: .regularExpression) != nil,
                  let token = reply.selectionToken,
                  token.range(of: "^[a-f0-9]{64}$", options: .regularExpression) != nil,
                  reply.oemValidUntil != nil, reply.spValidUntil != nil else { throw SetupFault.protocolFailure }
            if action == "cloud-subjects-inspect" {
                guard let rows = reply.subjects, rows.count <= 16 else { throw SetupFault.protocolFailure }
                for row in rows {
                    guard ["brake", "tire"].contains(row.team), UUID(uuidString: row.id) != nil,
                          ["ELIGIBLE", "BLOCKED"].contains(row.state), row.reason.count <= 100 else { throw SetupFault.protocolFailure }
                    if row.state == "ELIGIBLE" {
                        guard let ref = row.reference, Set(ref.keys) == Set(["team", "id", "serviceId", "ownerId", "serviceProviderId", "createdBy"]),
                              ref["team"] == row.team, ref["id"] == row.id,
                              ref.filter({ $0.key != "team" }).allSatisfy({ UUID(uuidString: $0.value) != nil }) else { throw SetupFault.protocolFailure }
                    } else if row.reference != nil { throw SetupFault.protocolFailure }
                }
            }
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
    private let install = NSButton(title: "1. Install SDV Lab", target: nil, action: nil)
    private let prepare = NSButton(title: "Prepare local data", target: nil, action: nil)
    private let backends = NSButton(title: "Prepare backends", target: nil, action: nil)
    private let cloud = NSButton(title: "2. Connect to Aos Cloud…", target: nil, action: nil)
    private let launch = NSButton(title: "3. Open SDV Lab", target: nil, action: nil)
    private var cloudWindow: NSWindow?
    private let oem = NSTextField(string: "")
    private let sp = NSTextField(string: "")
    private let inspectPair = NSButton(title: "Connect", target: nil, action: nil)
    private let savePair = NSButton(title: "2. Use this pair", target: nil, action: nil)
    private let checkCloud = NSButton(title: "3. Check Cloud access", target: nil, action: nil)
    private let closeCloud = NSButton(title: "Close", target: nil, action: nil)
    private let cloudStatus = NSTextField(wrappingLabelWithString: "")
    private let cloudDetail = NSTextField(wrappingLabelWithString: "")
    private let cloudDiagnostics = NSStackView()
    private let enrollmentDiagnostics = NSStackView()
    private let diagnostic = NSTextField(wrappingLabelWithString: "")
    private var cloudPickers: [NSButton] = []
    private var pairToken: String?
    private var pairSaved = false
    private var enrollmentWindow: NSWindow?
    private let enrollmentEnvironment = NSPopUpButton()
    private let enrollmentSPToken = NSSecureTextField(string: "")
    private let enrollmentDomain = NSTextField(string: "")
    private let enrollmentRole = NSPopUpButton()
    private let enrollmentToken = NSSecureTextField(string: "")
    private let enrollmentInspect = NSButton(title: "Inspect saved attempt", target: nil, action: nil)
    private let enrollmentSubmit = NSButton(title: "Get certificates", target: nil, action: nil)
    private let enrollmentRecover = NSButton(title: "Recover saved certificate", target: nil, action: nil)
    private let enrollmentReconciled = NSButton(checkboxWithTitle: "I reconciled this exact attempt in Cloud and obtained a replacement token", target: nil, action: nil)
    private let enrollmentClose = NSButton(title: "Back to certificate pair", target: nil, action: nil)
    private let enrollmentDetail = NSTextField(wrappingLabelWithString: "Choose the Cloud domain and role, then inspect saved state before submitting a token.")
    private var enrollmentObservation: SetupReply?
    private var subjectsWindow: NSWindow?
    private let subjectsOpen = NSButton(title: "Review existing Brake / Tire assignments…", target: nil, action: nil)
    private let subjectsInspect = NSButton(title: "Read existing objects", target: nil, action: nil)
    private let subjectsChoose = NSPopUpButton()
    private let subjectsSave = NSButton(title: "Use selected exact reference", target: nil, action: nil)
    private let subjectsClose = NSButton(title: "Back to Cloud access", target: nil, action: nil)
    private let subjectsDetail = NSTextField(wrappingLabelWithString: "")
    private var subjectRows: [CloudSubjectRow] = []
    private let status = NSTextField(wrappingLabelWithString: "Choose the complete offline kit to begin.")
    private let detail = NSTextField(wrappingLabelWithString: "Installation is offline. Cloud access is a separate, explicit step; your running demo stays unchanged.")
    private let next = NSTextField(wrappingLabelWithString: "After local setup\nOpen Docker Desktop, then Prepare backends. Set up Cloud access and Open demo.\nReturning? Choose your existing private-data folder and Open demo.")
    private let progress = NSProgressIndicator()
    private var pickers: [NSButton] = []
    private var checked: SetupReply?
    private var installed = false
    private var localInstalled = false
    private var backendsObserved = false
    private var launcherObserved = false
    private var cloudObserved = false
    private var pendingLaunch = false
    private let advancedRow = NSStackView()
    private var busy = false
    private var generation = UUID()

    func applicationDidFinishLaunching(_ notification: Notification) {
        if let kit = bundledKitURL(app: Bundle.main.bundleURL, exists: { FileManager.default.fileExists(atPath: $0.path) }) {
            source.stringValue = kit.path
            status.stringValue = "The complete SDV Lab package is included."
            detail.stringValue = "Choose Check installation to verify this Mac and your installation location. Nothing has been installed or started yet."
        }
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
        window = NSWindow(contentRect: NSRect(x: 0, y: 0, width: 780, height: 660),
                          styleMask: [.titled, .closable, .miniaturizable], backing: .buffered, defer: false)
        window.title = "AosEdge Platform — SDV Lab Setup"
        window.delegate = self
        window.isReleasedWhenClosed = false
        window.backgroundColor = .windowBackgroundColor
        let column = NSStackView()
        column.orientation = .vertical
        column.alignment = .leading
        column.spacing = 12
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
        let subtitle = label("Install SDV Lab  →  Connect to Aos Cloud  →  Open your lab", 15, .medium)
        subtitle.textColor = .systemBlue
        column.addArrangedSubview(subtitle)
        column.addArrangedSubview(label("Local engineering preview · Apple silicon · macOS 26 or later", 12))
        column.addArrangedSubview(label("A simulated vehicle and controller, powered by the real AosEdge platform. The complete package is included; Docker Desktop is a separate prerequisite.", 15))
        column.addArrangedSubview(NSButton(title: "Advanced installation location…", target: self, action: #selector(toggleAdvanced)))
        store.delegate = self; store.setAccessibilityLabel("Program installation location")
        let choose = NSButton(title: "Choose…", target: self, action: #selector(pick(_:))); choose.tag = 1
        pickers.append(choose)
        advancedRow.addArrangedSubview(store); advancedRow.addArrangedSubview(choose); advancedRow.spacing = 10
        advancedRow.isHidden = true; column.addArrangedSubview(advancedRow)
        advancedRow.widthAnchor.constraint(equalTo: column.widthAnchor).isActive = true
        check.target = self; check.action = #selector(doCheck)
        install.target = self; install.action = #selector(doInstall)
        prepare.target = self; prepare.action = #selector(doPrepare)
        backends.target = self; backends.action = #selector(doBackends)
        cloud.target = self; cloud.action = #selector(openCloud)
        launch.target = self; launch.action = #selector(doLaunch)
        check.bezelStyle = .rounded; install.bezelStyle = .rounded; prepare.bezelStyle = .rounded
        column.addArrangedSubview(NSStackView(views: [install, cloud, launch]))
        column.addArrangedSubview(NSButton(title: "Docker installation instructions…", target: self, action: #selector(openDockerHelp)))
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
        diagnostic.font = .systemFont(ofSize: 11); diagnostic.textColor = .secondaryLabelColor
        diagnostic.isHidden = true
        column.addArrangedSubview(NSButton(title: "Details…", target: self, action: #selector(toggleDetails)))
        column.addArrangedSubview(diagnostic)
        refresh()
        window.center(); window.makeKeyAndOrderFront(nil)
        NSApp.activate(ignoringOtherApps: true)
        run("setup-status")
    }

    @objc private func toggleAdvanced() { guard !busy else { return }; advancedRow.isHidden.toggle() }
    @objc private func toggleDetails() { diagnostic.isHidden.toggle() }
    @objc private func toggleCloudDetails() { cloudDiagnostics.isHidden.toggle() }
    @objc private func toggleEnrollmentDetails() { enrollmentDiagnostics.isHidden.toggle() }
    @objc private func openDockerHelp() {
        NSWorkspace.shared.open(URL(string: "https://docs.docker.com/desktop/setup/install/mac-install/")!)
    }

    private func refresh() {
        // Completed-step advice (including permission to close) is not current
        // while an operation owns the window. Restore it after the result.
        next.isHidden = busy
        check.isEnabled = !busy && !source.stringValue.isEmpty
        install.isEnabled = !busy && (!source.stringValue.isEmpty || localInstalled)
        prepare.isEnabled = !busy && installed && checked != nil
        cloud.isEnabled = !busy && localInstalled
        backends.isEnabled = !busy && !state.stringValue.isEmpty
        launch.isEnabled = !busy && localInstalled && backendsObserved && launcherObserved && cloudObserved
        for field in [source, state] { field.isEnabled = !busy }
        store.isEnabled = !busy && !localInstalled
        for button in pickers { button.isEnabled = !busy && !localInstalled }
        for field in [oem, sp] { field.isEnabled = !busy }
        for button in cloudPickers { button.isEnabled = !busy }
        inspectPair.isEnabled = !busy && !oem.stringValue.isEmpty && !sp.stringValue.isEmpty
        savePair.isEnabled = !busy && pairToken != nil && !pairSaved
        checkCloud.isEnabled = !busy && pairToken != nil && pairSaved
        closeCloud.isEnabled = !busy
        for field in [enrollmentDomain, enrollmentToken, enrollmentSPToken] { field.isEnabled = !busy }
        enrollmentEnvironment.isEnabled = !busy
        enrollmentRole.isEnabled = !busy; enrollmentClose.isEnabled = !busy
        enrollmentInspect.isEnabled = !busy && !enrollmentDomain.stringValue.isEmpty
        let enrollmentStage = enrollmentObservation?.enrollmentStage
        enrollmentReconciled.isEnabled = !busy && enrollmentStage == "RECONCILIATION_REQUIRED"
        enrollmentSubmit.isEnabled = !busy && (!enrollmentToken.stringValue.isEmpty || !enrollmentSPToken.stringValue.isEmpty)
        enrollmentRecover.isEnabled = !busy && enrollmentStage == "LOCAL_RECOVERY_AVAILABLE"
        subjectsOpen.isEnabled = !busy && pairToken != nil && pairSaved
        subjectsInspect.isEnabled = subjectsOpen.isEnabled
        subjectsChoose.isEnabled = !busy && !subjectRows.isEmpty
        let subjectIndex = subjectsChoose.indexOfSelectedItem - 1
        subjectsSave.isEnabled = !busy && pairToken != nil && pairSaved && subjectRows.indices.contains(subjectIndex) && subjectRows[subjectIndex].state == "ELIGIBLE"
        subjectsClose.isEnabled = !busy
    }

    private func invalidate() {
        guard !busy else { return }
        generation = UUID(); checked = nil; installed = false; cloudObserved = false
        enrollmentObservation = nil; enrollmentToken.stringValue = ""; enrollmentSPToken.stringValue = ""; enrollmentReconciled.state = .off
        enrollmentDomain.stringValue = enrollmentEnvironment.indexOfSelectedItem == 1 ? "aoscloud.io" : "aws-stage.epmp-aos.projects.epam.com"
        progress.doubleValue = 0
        status.stringValue = "Check your selected folders before installing."
        status.textColor = .labelColor
        detail.stringValue = "Changing any folder requires a new check. No running demo will be switched."
        next.stringValue = "After local setup\nOpen Docker Desktop, then Prepare backends. Set up Cloud access and Open demo.\nAlready installed? Only the existing private-data folder is needed."
        refresh()
    }

    func controlTextDidChange(_ obj: Notification) {
        if let field = obj.object as? NSTextField, field === enrollmentToken || field === enrollmentSPToken { refresh(); return }
        if let field = obj.object as? NSTextField, field === enrollmentDomain { resetEnrollment(); return }
        if let field = obj.object as? NSTextField, field === oem || field === sp { invalidatePair() }
        else { invalidate() }
    }

    private func invalidatePair() {
        guard !busy else { return }
        pairToken = nil; pairSaved = false
        cloudObserved = false
        subjectRows = []; subjectsChoose.removeAllItems(); subjectsChoose.addItem(withTitle: "Choose an exact object after inspection…")
        cloudStatus.stringValue = "Choose your existing OEM and SP certificate files."
        cloudStatus.textColor = .labelColor
        cloudDetail.stringValue = "Connect checks both accounts and their association, then saves file references. It can prepare the missing demo model and Test set. Keys stay in their current locations; no vehicle or package is created."
        refresh()
    }

    @objc private func openCloud() {
        guard !busy else { return }
        if cloudWindow == nil {
            let sheet = NSWindow(contentRect: NSRect(x: 0, y: 0, width: 790, height: 720),
                                 styleMask: [.titled], backing: .buffered, defer: false)
            sheet.title = "Cloud access — existing certificates"
            sheet.isReleasedWhenClosed = false
            let column = NSStackView(); column.orientation = .vertical
            column.alignment = .leading; column.spacing = 10
            column.translatesAutoresizingMaskIntoConstraints = false
            sheet.contentView!.addSubview(column)
            NSLayoutConstraint.activate([
                column.leadingAnchor.constraint(equalTo: sheet.contentView!.leadingAnchor, constant: 24),
                column.trailingAnchor.constraint(equalTo: sheet.contentView!.trailingAnchor, constant: -24),
                column.topAnchor.constraint(equalTo: sheet.contentView!.topAnchor, constant: 24)
            ])
            let title = NSTextField(labelWithString: "Connect your own Cloud access")
            title.font = .systemFont(ofSize: 24, weight: .bold); column.addArrangedSubview(title)
            let intro = NSTextField(wrappingLabelWithString: "Use existing certificates, or get new ones below. One OEM and one associated Service Provider for both services. The environment is determined by your certificates.")
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
            column.addArrangedSubview(inspectPair)
            column.addArrangedSubview(NSButton(title: "Get new certificates…", target: self, action: #selector(openEnrollment)))
            column.addArrangedSubview(NSButton(title: "Details and existing references…", target: self, action: #selector(toggleCloudDetails)))
            cloudDiagnostics.orientation = .vertical; cloudDiagnostics.alignment = .leading
            cloudDiagnostics.isHidden = true
            let inspect = NSButton(title: "Inspect pair only", target: self, action: #selector(inspectOnly))
            savePair.target = self; savePair.action = #selector(doSavePair)
            checkCloud.target = self; checkCloud.action = #selector(doCheckCloud)
            cloudDiagnostics.addArrangedSubview(NSStackView(views: [inspect, savePair, checkCloud]))
            subjectsOpen.target = self; subjectsOpen.action = #selector(openSubjects)
            cloudDiagnostics.addArrangedSubview(subjectsOpen)
            column.addArrangedSubview(cloudDiagnostics)
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

    @objc private func doInspectPair() { run("cloud-connect") }
    @objc private func inspectOnly() { run("cloud-inspect") }
    @objc private func doSavePair() { run("cloud-save") }
    @objc private func doCheckCloud() { run("cloud-check") }

    @objc private func inspectSubjects() { run("cloud-subjects-inspect") }
    @objc private func saveSubject() { run("cloud-subjects-save") }
    @objc private func chooseSubject() {
        let index = subjectsChoose.indexOfSelectedItem - 1
        if subjectRows.indices.contains(index) {
            let row = subjectRows[index]
            subjectsDetail.stringValue = "\(row.team.capitalized) Subject: \(row.id)\n" + (row.reference.map { "Service: \($0["serviceId"]!)\nOEM: \($0["ownerId"]!)\nSP: \($0["serviceProviderId"]!)\nCreator: \($0["createdBy"]!)\nEligible when last read. Save performs a fresh check." } ?? "Blocked: exact ownership, service binding or zero recipients could not be confirmed. No object will be adopted.")
        }
        refresh()
    }
    @objc private func closeSubjects() {
        guard !busy, let sheet = subjectsWindow else { return }
        window.endSheet(sheet); sheet.orderOut(nil); window.beginSheet(cloudWindow!); refresh()
    }
    @objc private func openSubjects() {
        guard !busy, pairSaved else { return }
        if subjectsWindow == nil {
            let sheet = NSWindow(contentRect: NSRect(x: 0, y: 0, width: 790, height: 440), styleMask: [.titled], backing: .buffered, defer: false)
            sheet.title = "Existing demo references"; sheet.isReleasedWhenClosed = false
            let column = NSStackView(); column.orientation = .vertical; column.alignment = .leading; column.spacing = 16
            column.translatesAutoresizingMaskIntoConstraints = false; sheet.contentView!.addSubview(column)
            NSLayoutConstraint.activate([column.leadingAnchor.constraint(equalTo: sheet.contentView!.leadingAnchor, constant: 24), column.trailingAnchor.constraint(equalTo: sheet.contentView!.trailingAnchor, constant: -24), column.topAnchor.constraint(equalTo: sheet.contentView!.topAnchor, constant: 24)])
            column.addArrangedSubview(NSTextField(wrappingLabelWithString: "Optional: explicitly reuse an existing unbound Brake or Tire Subject. A matching name is not enough. Nothing is selected automatically; inspecting or saving does not change Cloud assignments."))
            subjectsInspect.target = self; subjectsInspect.action = #selector(inspectSubjects); column.addArrangedSubview(subjectsInspect)
            subjectsChoose.target = self; subjectsChoose.action = #selector(chooseSubject); column.addArrangedSubview(subjectsChoose)
            subjectsChoose.widthAnchor.constraint(equalTo: column.widthAnchor).isActive = true
            subjectsDetail.font = .systemFont(ofSize: 13); column.addArrangedSubview(subjectsDetail); subjectsDetail.widthAnchor.constraint(equalTo: column.widthAnchor).isActive = true
            subjectsSave.target = self; subjectsSave.action = #selector(saveSubject)
            subjectsClose.target = self; subjectsClose.action = #selector(closeSubjects)
            column.addArrangedSubview(NSStackView(views: [subjectsSave, subjectsClose])); subjectsWindow = sheet
        }
        subjectRows = []; subjectsChoose.removeAllItems(); subjectsChoose.addItem(withTitle: "Choose an exact object after inspection…")
        subjectsDetail.stringValue = "Read the authenticated inventory first. Objects with existing desired or reported vehicle recipients are blocked."
        window.endSheet(cloudWindow!); cloudWindow!.orderOut(nil); window.beginSheet(subjectsWindow!); refresh()
    }

    @objc private func resetEnrollment() {
        enrollmentObservation = nil; enrollmentToken.stringValue = ""; enrollmentReconciled.state = .off
        enrollmentDetail.stringValue = "Inspect the saved state for this role and domain. A token is never stored or retried automatically."
        refresh()
    }
    @objc private func enrollmentCheckboxChanged() { refresh() }
    @objc private func inspectEnrollment() { run("cloud-enrollment-status") }
    @objc private func submitEnrollment() { run("cloud-enrollment-pair") }
    @objc private func submitSingleEnrollment() { run("cloud-enrollment-submit") }
    @objc private func openRegistration() {
        NSWorkspace.shared.open(URL(string: "https://" + enrollmentDomain.stringValue + "/")!)
    }
    @objc private func recoverEnrollment() { run("cloud-enrollment-recover") }
    @objc private func closeEnrollment() {
        guard !busy, let sheet = enrollmentWindow else { return }
        enrollmentToken.stringValue = ""; enrollmentSPToken.stringValue = ""; window.endSheet(sheet); sheet.orderOut(nil)
        window.beginSheet(cloudWindow!); refresh()
    }
    @objc private func openEnrollment() {
        guard !busy else { return }
        if enrollmentWindow == nil {
            let sheet = NSWindow(contentRect: NSRect(x: 0, y: 0, width: 790, height: 600), styleMask: [.titled], backing: .buffered, defer: false)
            sheet.title = "Cloud certificate enrollment"; sheet.isReleasedWhenClosed = false
            let column = NSStackView(); column.orientation = .vertical; column.alignment = .leading; column.spacing = 14
            column.translatesAutoresizingMaskIntoConstraints = false; sheet.contentView!.addSubview(column)
            NSLayoutConstraint.activate([column.leadingAnchor.constraint(equalTo: sheet.contentView!.leadingAnchor, constant: 24), column.trailingAnchor.constraint(equalTo: sheet.contentView!.trailingAnchor, constant: -24), column.topAnchor.constraint(equalTo: sheet.contentView!.topAnchor, constant: 24)])
            let title = NSTextField(labelWithString: "Get OEM and Service Provider certificates"); title.font = .systemFont(ofSize: 24, weight: .bold)
            column.addArrangedSubview(title)
            column.addArrangedSubview(NSTextField(wrappingLabelWithString: "Choose your Cloud environment. Register or sign in through the official portal, then paste the OEM and associated SP issuance tokens below. Account confirmation and Cloud terms remain yours to review. No terminal commands are needed."))
            enrollmentEnvironment.addItems(withTitles: ["Staging", "Production"])
            enrollmentEnvironment.target = self; enrollmentEnvironment.action = #selector(resetEnrollment)
            enrollmentEnvironment.setAccessibilityLabel("Cloud environment")
            column.addArrangedSubview(enrollmentEnvironment)
            column.addArrangedSubview(NSButton(title: "Open official Cloud registration…", target: self, action: #selector(openRegistration)))
            enrollmentRole.addItems(withTitles: ["OEM", "Service Provider"]); enrollmentRole.target = self; enrollmentRole.action = #selector(resetEnrollment)
            enrollmentToken.placeholderString = "OEM issuance token"; enrollmentToken.delegate = self
            enrollmentToken.setAccessibilityLabel("OEM issuance token"); column.addArrangedSubview(enrollmentToken)
            enrollmentToken.widthAnchor.constraint(equalTo: column.widthAnchor).isActive = true
            enrollmentSPToken.placeholderString = "Service Provider issuance token"; enrollmentSPToken.delegate = self
            enrollmentSPToken.setAccessibilityLabel("Service Provider issuance token"); column.addArrangedSubview(enrollmentSPToken)
            enrollmentSPToken.widthAnchor.constraint(equalTo: column.widthAnchor).isActive = true
            enrollmentSubmit.target = self; enrollmentSubmit.action = #selector(submitEnrollment)
            enrollmentRecover.target = self; enrollmentRecover.action = #selector(recoverEnrollment)
            column.addArrangedSubview(enrollmentSubmit)
            column.addArrangedSubview(NSTextField(wrappingLabelWithString: "If issuance is uncertain, the saved attempt is preserved and will not be retried. Reconcile it in Cloud before requesting a replacement token."))
            column.addArrangedSubview(NSButton(title: "Details and enrollment recovery…", target: self, action: #selector(toggleEnrollmentDetails)))
            enrollmentDiagnostics.orientation = .vertical; enrollmentDiagnostics.alignment = .leading
            enrollmentDiagnostics.isHidden = true
            enrollmentInspect.target = self; enrollmentInspect.action = #selector(inspectEnrollment)
            enrollmentReconciled.target = self; enrollmentReconciled.action = #selector(enrollmentCheckboxChanged)
            enrollmentDiagnostics.addArrangedSubview(NSStackView(views: [enrollmentRole, enrollmentInspect, enrollmentRecover]))
            enrollmentDiagnostics.addArrangedSubview(enrollmentReconciled)
            enrollmentDiagnostics.addArrangedSubview(NSButton(title: "Submit reconciled role token", target: self, action: #selector(submitSingleEnrollment)))
            column.addArrangedSubview(enrollmentDiagnostics)
            enrollmentDetail.font = .systemFont(ofSize: 13); column.addArrangedSubview(enrollmentDetail)
            enrollmentDetail.widthAnchor.constraint(equalTo: column.widthAnchor).isActive = true
            enrollmentClose.target = self; enrollmentClose.action = #selector(closeEnrollment); column.addArrangedSubview(enrollmentClose)
            enrollmentWindow = sheet
        }
        window.endSheet(cloudWindow!); cloudWindow!.orderOut(nil); resetEnrollment(); window.beginSheet(enrollmentWindow!)
    }

    @objc private func pick(_ sender: NSButton) {
        guard !busy, !localInstalled else { return }
        let panel = NSOpenPanel()
        panel.canChooseDirectories = true; panel.canChooseFiles = false
        panel.canCreateDirectories = false; panel.allowsMultipleSelection = false
        panel.prompt = "Choose folder"
        panel.message = sender.tag == 0 ? "Select the complete kit supplied with this installer." :
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
    @objc private func doInstall() {
        if localInstalled { run(backendsObserved ? "install-launcher" : "prepare-backends") }
        else { run("setup-install") }
    }
    @objc private func doPrepare() { run("prepare") }
    @objc private func doLaunch() {
        guard !busy else { return }
        // Read current trust only. No OS prompt, grant, settings change or
        // subprocess may precede this first-use gate.
        if let code = launchPermissionFailure(accessibilityTrusted: AXIsProcessTrusted()) {
            status.stringValue = "Accessibility permission needed"
            status.textColor = .systemOrange
            detail.stringValue = setupFailureHint(action: "launch", code: code)
            progress.doubleValue = 0
            return
        }
        pendingLaunch = true
        run("setup-status")
    }

    @objc private func doBackends() { run("prepare-backends") }

    private func run(_ action: String) {
        let cloudAction = action.hasPrefix("cloud-")
        let backendAction = action == "prepare-backends"
        let launchAction = action == "launch"
        let enrollmentAction = action.hasPrefix("cloud-enrollment-")
        let subjectsAction = action.hasPrefix("cloud-subjects-")
        let workflowAction = ["setup-status", "setup-install", "install-launcher"].contains(action)
        guard !busy, cloudAction || launchAction || backendAction || workflowAction || action == "preflight" || checked != nil else { return }
        var request: [String: Any] = ["action": action, "source": source.stringValue,
                                      "store": store.stringValue, "state": state.stringValue]
        if launchAction || backendAction || action == "setup-status" || action == "install-launcher" {
            request = ["action": action, "state": state.stringValue]
        } else if action == "cloud-enrollment-pair" {
            request = ["action": action, "state": state.stringValue, "domain": enrollmentDomain.stringValue,
                       "oemToken": enrollmentToken.stringValue, "spToken": enrollmentSPToken.stringValue]
        } else if enrollmentAction {
            request = ["action": action, "state": state.stringValue, "domain": enrollmentDomain.stringValue, "role": enrollmentRole.indexOfSelectedItem == 0 ? "oem" : "sp"]
        if action == "cloud-enrollment-submit" {
                guard enrollmentSubmit.isEnabled else { return }
                request["token"] = enrollmentRole.indexOfSelectedItem == 0 ? enrollmentToken.stringValue : enrollmentSPToken.stringValue
                request["reconcileAttempt"] = enrollmentReconciled.state == .on ? (enrollmentObservation?.attemptId as Any? ?? NSNull()) : NSNull()
            }
        } else if cloudAction {
            request = ["action": action, "state": state.stringValue, "oem": oem.stringValue, "sp": sp.stringValue]
            if !["cloud-inspect", "cloud-connect", "cloud-observe"].contains(action) {
                guard let pairToken else { return }; request["selectionToken"] = pairToken
            }
            if action == "cloud-subjects-save" {
                let index = subjectsChoose.indexOfSelectedItem - 1
                guard subjectsSave.isEnabled, subjectRows.indices.contains(index), let ref = subjectRows[index].reference else { return }
                request["reference"] = ref
            }
        } else if action != "preflight" && action != "setup-install" {
            request["volumeUUID"] = checked!.volumeUUID!
            request["revision"] = checked!.revision!
        } else { checked = nil; installed = false }
        guard let raw = try? JSONSerialization.data(withJSONObject: request),
              let resources = Bundle.main.resourceURL else { return }
        busy = true; generation = UUID(); let token = generation
        if cloudAction { cloudObserved = false }
        if enrollmentAction {
            enrollmentToken.stringValue = ""; enrollmentSPToken.stringValue = ""
            request.removeValue(forKey: "token"); request.removeValue(forKey: "oemToken"); request.removeValue(forKey: "spToken")
            enrollmentObservation = nil; enrollmentReconciled.state = .off
            enrollmentDetail.stringValue = "Checking preserved state and the verified private Cloud runtime…"
        }
        if subjectsAction { subjectsDetail.stringValue = "Rechecking exact identities and recipients — no Cloud mutation…" }
        status.textColor = .labelColor
        status.stringValue = action == "preflight" ? "Checking folders, release and available space…" :
            action == "install" ? "Verifying and installing the complete package…" : "Verifying the selected version and preparing local data…"
        detail.stringValue = "This window stays responsive. Large-file verification can take several minutes."
        if backendAction {
            status.stringValue = "Preparing the local backend images…"
            detail.stringValue = "Docker Desktop must already be running. Only the two packaged images are loaded; no container or vehicle is started."
        }
        if workflowAction {
            status.stringValue = action == "setup-install" ? "Installing SDV Lab…" : "Checking your installed lab…"
            detail.stringValue = "Verifying installation, local Docker and the selected package. No vehicle is started."
        }
        if launchAction {
            status.stringValue = "Opening the selected demo…"
            detail.stringValue = "Only Presenter and its windows are opened. No machine, simulator, provisioning or driving action will be started."
        }
        if cloudFeedbackTarget(action) == .pair {
            cloudStatus.textColor = .labelColor
            cloudStatus.stringValue = action == "cloud-connect" ? "Connecting both Cloud accounts…" : "Checking Cloud access…"
            cloudDetail.stringValue = action == "cloud-connect" ? "Authenticating both roles and their association. Only missing demo prerequisites may be prepared; no Unit is created or package published." : "Reading authenticated access and prerequisites without changing Cloud."
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
                if cloudAction || launchAction || backendAction { deadline = CloudDeadline(process, seconds: backendAction || action == "cloud-enrollment-pair" ? 180 : 120) }
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
                                    switch cloudFeedbackTarget(action) {
                                    case .enrollment: self.enrollmentDetail.stringValue = message
                                    case .subjects: self.subjectsDetail.stringValue = message
                                    case .pair: self.cloudDetail.stringValue = message
                                    case nil: break
                                    }
                                }
                                if let stage = event.stage, let message = launchStages[stage] {
                                    self.detail.stringValue = message
                                }
                                if let stage = event.stage, let message = backendStages[stage] {
                                    self.detail.stringValue = message
                                }
                                if event.stage == "CHECKING_DOCKER" { self.detail.stringValue = "Checking your existing local Docker Engine…" }
                                if event.stage == "INSTALLING_LAUNCHER" { self.detail.stringValue = "Installing the signed SDV Lab launcher in Applications…" }
                                if let fraction = event.fraction {
                                    self.progress.stopAnimation(nil); self.progress.isIndeterminate = false
                                    self.progress.doubleValue = fraction
                                    self.detail.stringValue = "Verified \(event.files!) of \(event.totalFiles!) files · \(Int(fraction * 100))%"
                                } else if event.kind == "progress" {
                                    self.progress.isIndeterminate = true; self.progress.startAnimation(nil)
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
                let code = deadline?.finish() == true ? (backendAction ? "SETUP_BACKENDS_DEADLINE" : launchAction ? "SETUP_LAUNCH_DEADLINE" : "SETUP_CLOUD_DEADLINE") : (exchange.terminal?.kind == "error" ? exchange.terminal?.code : nil)
                DispatchQueue.main.async { [weak self] in self?.fail(action, code ?? "SETUP_HELPER_FAILED", token) }
            }
        }
    }

    private func complete(_ action: String, _ reply: SetupReply, _ token: UUID) {
        guard generation == token else { return }
        busy = false; progress.stopAnimation(nil); progress.isIndeterminate = false; progress.doubleValue = 1
        status.textColor = .labelColor
        if action == "cloud-enrollment-pair" {
            if let path = reply.oemPath { oem.stringValue = path }
            if let path = reply.spPath { sp.stringValue = path }
            if reply.enrollmentStage == "RECEIVED" {
                if let sheet = enrollmentWindow { window.endSheet(sheet); sheet.orderOut(nil) }
                window.beginSheet(cloudWindow!)
                refresh(); run("cloud-connect")
            } else {
                enrollmentDetail.stringValue = reply.enrollmentStage == "RECONCILIATION_REQUIRED" ? "\(reply.role == "oem" ? "OEM" : "SP") issuance needs reconciliation. No request was retried. Your key and received certificates are preserved." : "\(reply.role == "oem" ? "OEM" : "SP") still needs an issuance token. Any received certificate is preserved."
                refresh()
            }
            return
        }
        if action == "setup-status" || action == "setup-install" {
            localInstalled = reply.localInstalled == true; backendsObserved = reply.backendsObserved == true
            launcherObserved = reply.launcherObserved == true
            cloudObserved = false
            if let path = reply.storePath { store.stringValue = path }
            if let path = reply.oemPath { oem.stringValue = path }
            if let path = reply.spPath { sp.stringValue = path }
            install.title = localInstalled ? (backendsObserved && launcherObserved ? "Check installation again" : "Continue installation") : "1. Install SDV Lab"
            status.stringValue = localInstalled ? "Installed — connect to Aos Cloud" : "Ready to install SDV Lab"
            detail.stringValue = localInstalled ? (backendsObserved ? "Program and backend images verified. Connect your OEM and Service Provider accounts next." : "Program is installed. Local Docker or its backend images need attention. Continue installation after starting Docker.") : "Everything is included in the DMG. Install prepares the program, backend images and a persistent launcher."
            next.stringValue = "Later, open AosEdge SDV Lab from your user Applications folder. Create Controller and the simulated vehicle journey remain in Presenter."
            refresh()
            if localInstalled && backendsObserved && launcherObserved && !oem.stringValue.isEmpty && !sp.stringValue.isEmpty && FileManager.default.fileExists(atPath: oem.stringValue) && FileManager.default.fileExists(atPath: sp.stringValue) {
                run("cloud-observe")
            } else {
                pendingLaunch = false
                if !localInstalled && source.stringValue.isEmpty {
                    status.stringValue = "Open Setup from the complete SDV Lab DMG"
                    detail.stringValue = "No installed selection or matching media was found. Setup will not search for another kit."
                }
            }
            return
        }
        if action == "install-launcher" {
            launcherObserved = true
            status.stringValue = "SDV Lab launcher installed"
            detail.stringValue = "You can eject the DMG after closing Setup. Later, open AosEdge SDV Lab from your user Applications folder."
            refresh(); run("setup-status"); return
        }
        if action == "cloud-connect" || action == "cloud-observe" {
            cloudObserved = reply.cloudStage == "READY" && reply.rolesChecked == true
            pairSaved = cloudObserved
            let environment = reply.domain == "aws-stage.epmp-aos.projects.epam.com" ? "Staging" : reply.domain == "aoscloud.io" ? "Production" : "Cloud"
            cloudStatus.stringValue = cloudObserved ? "Connected to \(environment)" : "Cloud access needs attention"
            cloudDetail.stringValue = "\(reply.domain!)\n" + (reply.checks ?? []).filter { $0.state != "READY" }.map { "\($0.label): \($0.state.lowercased())" }.joined(separator: "\n")
            status.stringValue = cloudObserved && backendsObserved && launcherObserved ? "Ready to open SDV Lab" : "Continue SDV Lab setup"
            detail.stringValue = cloudObserved ? "\(environment): \(reply.domain!). Open SDV Lab opens Presenter; Create Controller starts the vehicle journey." : "Check the Cloud access window. Your installed program and retained Test are preserved."
            refresh()
            if pendingLaunch {
                pendingLaunch = false
                if cloudObserved && backendsObserved && launcherObserved { run("launch") }
            }
            return
        }
        if action == "prepare-backends" {
            backendsObserved = true; localInstalled = true
            status.stringValue = "Backend images available — demo not started"
            detail.stringValue = reply.importAttempted == true ? "Brake and Tire images were loaded and verified in local Docker Desktop. No containers were started." : "Both exact images are already available and verified. No import was needed."
            next.stringValue = "Continue first use\nSet up or check Cloud access, then Open demo and use Create Controller.\nThis check confirms images only, not a running vehicle or backend."
            refresh(); run("install-launcher"); return
        }
        if action == "launch" {
            status.stringValue = reply.presenterObserved == true ? "Presenter opened" : "Presenter needs attention — inspect the desktop"
            status.textColor = reply.presenterObserved == true ? .labelColor : .systemOrange
            detail.stringValue = reply.presenterObserved == true ?
                (reply.layoutComplete == true ? "Existing workspace layout verified. Vehicle, services and driving state were not changed." : "Presenter windows verified. Simulator and controller are not fully ready; use Demo Control to continue setup.") :
                "Opening was requested, but window placement or ordering could not be confirmed. Check screen lock and Accessibility/Automation permission; no automatic retry."
            next.stringValue = "Continue in Presenter\nOpening a window is not a full readiness check. The existing Demo Control owns all lifecycle actions.\nYou can close this setup window; the Presenter stays open."
            refresh(); return
        }
        if action.hasPrefix("cloud-subjects-") {
            pairToken = reply.selectionToken
            subjectRows = reply.subjects ?? []
            subjectsChoose.removeAllItems(); subjectsChoose.addItem(withTitle: "Choose an exact object — no automatic selection")
            for row in subjectRows { subjectsChoose.addItem(withTitle: "\(row.team.capitalized) · \(row.id) · \(row.state.lowercased())") }
            subjectsChoose.selectItem(at: 0)
            subjectsDetail.stringValue = action == "cloud-subjects-save" ? "Exact reference saved locally. No Cloud binding changed. It will be rechecked when assigning this service to the new Test. Read again to select another reference." : subjectRows.isEmpty ? "No matching Subjects were found in the complete inventory. Normal first service assignment can create its own Subject." : "Select an eligible exact object to inspect its OEM, SP, creator and service identifiers. Blocked objects cannot be reused."
            status.stringValue = "Existing references checked — demo unchanged"
            detail.stringValue = "The reference window shows current eligibility. No Unit or service assignment was changed."
            refresh(); return
        }
        if action.hasPrefix("cloud-enrollment-") {
            enrollmentObservation = reply
            let names = ["NOT_STARTED": "No attempt recorded — ready for an explicit token submission.", "PREPARED": "Key and request preserved; no dispatch was recorded.", "RECEIVED": "Certificate saved privately. Return to the pair, then inspect, save and check Cloud access. Receiving a certificate does not prove account roles.", "LOCAL_RECOVERY_AVAILABLE": "A valid certificate is already saved. Recover it without contacting Cloud.", "RECONCILIATION_REQUIRED": "The request outcome is uncertain. No automatic retry. Reconcile this attempt in the official Cloud portal before obtaining a replacement token."]
            enrollmentDetail.stringValue = names[reply.enrollmentStage!]! + (reply.attemptId.map { "\nAttempt: \($0)" } ?? "")
            if reply.enrollmentStage == "RECEIVED" {
                (reply.role == "oem" ? oem : sp).stringValue = reply.credentialPath!
                invalidatePair()
            }
            status.stringValue = "Enrollment state inspected — demo unchanged"
            detail.stringValue = "See the enrollment window. Existing run data and Cloud assignments were not changed."
            refresh(); return
        }
        if action.hasPrefix("cloud-") {
            cloudStatus.textColor = .labelColor
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
            detail.stringValue = "See the Cloud access window for the observation. Close it and choose Open demo to open Presenter. Docker readiness is checked separately."
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
            next.stringValue = "Next steps — not yet verified\nDocker: \(reply.dockerApplicationPresent == true ? "application found; engine not checked" : "application not found in /Applications").\nOpen Docker Desktop, choose Prepare backends, then set up Cloud access and Open demo."
        }
        refresh()
    }

    private func fail(_ action: String, _ code: String, _ token: UUID) {
        guard generation == token else { return }
        busy = false; checked = nil; installed = false; cloudObserved = false; pendingLaunch = false
        progress.stopAnimation(nil); progress.isIndeterminate = false; progress.doubleValue = 0
        status.textColor = .systemRed
        status.stringValue = "Setup stopped safely — review and check again"
        let hint = setupFailureHint(action: action, code: code)
        detail.stringValue = hint
        diagnostic.stringValue = "Diagnostic: " + code
        if action == "prepare-backends" { status.stringValue = "Backend preparation needs attention — demo preserved" }
        if action == "launch" { status.stringValue = "Presenter opening needs attention — demo preserved" }
        if action.hasPrefix("cloud-") {
            pairToken = nil; pairSaved = false
            if action.hasPrefix("cloud-enrollment-") { enrollmentObservation = nil; enrollmentDetail.stringValue = detail.stringValue }
            if action.hasPrefix("cloud-subjects-") { subjectRows = []; subjectsDetail.stringValue = detail.stringValue }
            status.stringValue = "Cloud step needs attention — local installation preserved"
            cloudStatus.textColor = .systemRed
            cloudStatus.stringValue = "Cloud step stopped — no readiness confirmed"
            cloudDetail.stringValue = detail.stringValue
        }
        refresh()
    }

    private func mayClose() -> Bool {
        guard busy else { return true }
        let alert = NSAlert()
        alert.messageText = "A setup operation is still running"
        alert.informativeText = "Wait for this operation's result before closing. No VM or Cloud lifecycle action is performed by setup."
        alert.addButton(withTitle: "Keep setup open")
        alert.beginSheetModal(for: window)
        return false
    }
    func windowShouldClose(_ sender: NSWindow) -> Bool { mayClose() }
    func applicationShouldTerminate(_ sender: NSApplication) -> NSApplication.TerminateReply { mayClose() ? .terminateNow : .terminateCancel }
    func applicationShouldTerminateAfterLastWindowClosed(_ sender: NSApplication) -> Bool { true }
}

func selfTest() throws {
    let mediaApp = URL(fileURLWithPath: "/Volumes/SDV Lab/AosEdge SDV Lab Setup.app")
    var discoveries: [String] = []
    let kit = bundledKitURL(app: mediaApp, exists: { discoveries.append($0.path); return true })
    precondition(kit?.path == "/Volumes/SDV Lab/Runtime Kit")
    precondition(discoveries == ["/Volumes/SDV Lab/Runtime Kit/application-manifest.json"])
    precondition(bundledKitURL(app: mediaApp, exists: { _ in false }) == nil)
    for action in ["cloud-inspect", "cloud-save", "cloud-check"] {
        precondition(cloudFeedbackTarget(action) == .pair)
    }
    for action in ["cloud-enrollment-status", "cloud-enrollment-recover", "cloud-enrollment-submit"] {
        precondition(cloudFeedbackTarget(action) == .enrollment)
    }
    for action in ["cloud-subjects-inspect", "cloud-subjects-save"] {
        precondition(cloudFeedbackTarget(action) == .subjects)
    }
    precondition(cloudFeedbackTarget("launch") == nil)
    func enrollmentReply(_ stage: String, _ accessed: Bool = false) throws -> SetupExchange {
        let data: [String: Any] = ["kind": "result", "result": ["status": "CLOUD_ENROLLMENT_OBSERVED", "runtimeChanged": false, "cloudAccessed": accessed, "demoReady": false, "rolesChecked": false, "domain": "stage.example.test", "role": "oem", "enrollmentStage": stage, "attemptId": "11111111-1111-4111-8111-111111111111", "credentialPath": "/private/fixture/credentials/enrollment/oem/client.p12"]]
        var exchange = SetupExchange()
        try exchange.receive(JSONDecoder().decode(SetupEvent.self, from: JSONSerialization.data(withJSONObject: data)))
        return exchange
    }
    _ = try enrollmentReply("NOT_STARTED").finish(action: "cloud-enrollment-status", exit: 0)
    _ = try enrollmentReply("RECEIVED", true).finish(action: "cloud-enrollment-submit", exit: 0)
    _ = try enrollmentReply("LOCAL_RECOVERY_AVAILABLE").finish(action: "cloud-enrollment-status", exit: 0)
    _ = try enrollmentReply("RECEIVED").finish(action: "cloud-enrollment-recover", exit: 0)
    _ = try enrollmentReply("RECONCILIATION_REQUIRED", true).finish(action: "cloud-enrollment-submit", exit: 0)
    precondition(launchPermissionFailure(accessibilityTrusted: true) == nil)
    let accessCode = launchPermissionFailure(accessibilityTrusted: false)!
    precondition(accessCode == "SETUP_LAUNCH_ACCESSIBILITY_REQUIRED")
    precondition(setupFailureHint(action: "launch", code: accessCode).contains("No launch operation was started"))
    precondition(setupFailureHint(action: "launch", code: accessCode).contains("older preview"))
    let mismatchHint = setupFailureHint(action: "cloud-inspect", code: "CLOUD_OEM_SP_DOMAIN_MISMATCH")
    precondition(mismatchHint.contains("different Cloud domains") && !mismatchHint.contains("package"))
    precondition(setupFailureHint(action: "install", code: "INPUT_DIGEST_MISMATCH").contains("intact package"))
    precondition(setupFailureHint(action: "cloud-save", code: "CLOUD_CERTIFICATE_CHANGED_SINCE_PREVIEW").contains("Inspect again"))
    precondition(setupFailureHint(action: "cloud-inspect", code: "CLOUD_PACKAGE_SIGNING_RSA_KEY_REQUIRED").contains("no key or certificate was replaced"))
    precondition(setupFailureHint(action: "cloud-check", code: "SETUP_CLOUD_DEADLINE").contains("completed local saves are preserved"))
    precondition(setupFailureHint(action: "cloud-inspect", code: "SETUP_LOCAL_PREPARATION_REQUIRED").contains("this installer's version"))
    precondition(setupFailureHint(action: "launch", code: "SETUP_LAUNCH_FOREIGN_OWNER").contains("preserved"))
    precondition(setupFailureHint(action: "launch", code: "SETUP_LAUNCH_DEADLINE").contains("macOS"))
    precondition(setupFailureHint(action: "launch", code: "SETUP_INSTANCE_NOT_FOUND").contains("Nothing was created"))
    precondition(setupFailureHint(action: "launch", code: "SETUP_FILE_ACCESS_DENIED").contains("does not change permissions"))
    precondition(launchStages["LAUNCH_PACKAGE_ACCESS"] == cloudStages["CLOUD_PACKAGE_LEASE"])
    var accessProgress = SetupExchange()
    try accessProgress.receive(event(#"{"kind":"progress","stage":"LAUNCH_PACKAGE_ACCESS"}"#))
    try accessProgress.receive(event(#"{"kind":"progress","stage":"LAUNCH_VERIFYING_PROGRAM"}"#))
    func event(_ raw: String) throws -> SetupEvent { try JSONDecoder().decode(SetupEvent.self, from: Data(raw.utf8)) }
    func rejects(_ action: () throws -> Void) {
        do { try action(); fatalError("Expected rejection") } catch {}
    }
    for (action, raw) in [
        ("setup-status", #"{"kind":"result","result":{"status":"SETUP_NOT_INSTALLED","runtimeChanged":false,"cloudAccessed":false,"demoReady":false,"localInstalled":false,"backendsObserved":false,"launcherObserved":false}}"#),
        ("setup-install", #"{"kind":"result","result":{"status":"SETUP_LOCAL_INSTALLED","runtimeChanged":false,"cloudAccessed":false,"demoReady":false,"localInstalled":true,"backendsObserved":true,"launcherObserved":true}}"#),
        ("cloud-connect", #"{"kind":"result","result":{"status":"CLOUD_CONNECTED_OBSERVED","runtimeChanged":false,"cloudAccessed":true,"demoReady":false,"rolesChecked":true,"domain":"stage.example.test","cloudStage":"READY","checks":[]}}"#),
        ("cloud-enrollment-pair", #"{"kind":"result","result":{"status":"PAIR_ENROLLMENT_OBSERVED","runtimeChanged":false,"cloudAccessed":false,"demoReady":false,"rolesChecked":false,"domain":"aoscloud.io","enrollmentStage":"RECONCILIATION_REQUIRED","role":"sp"}}"#)
    ] {
        var integrated = SetupExchange(); try integrated.receive(event(raw))
        _ = try integrated.finish(action: action, exit: 0)
        rejects { _ = try integrated.finish(action: action, exit: 1) }
        rejects { _ = try integrated.finish(action: "launch", exit: 0) }
    }
    for raw in [
        #"{"kind":"result","result":{"status":"SETUP_NOT_INSTALLED","runtimeChanged":false,"cloudAccessed":false,"demoReady":false,"localInstalled":true,"backendsObserved":true,"launcherObserved":true}}"#,
        #"{"kind":"result","result":{"status":"SETUP_LOCAL_INSTALLED","runtimeChanged":false,"cloudAccessed":false,"demoReady":false,"localInstalled":true,"backendsObserved":true}}"#
    ] {
        var invalidInstallation = SetupExchange(); try invalidInstallation.receive(event(raw))
        rejects { _ = try invalidInstallation.finish(action: "setup-status", exit: 0) }
        rejects { _ = try invalidInstallation.finish(action: "setup-install", exit: 0) }
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
    let launchRaw = #"{"kind":"result","result":{"status":"PRESENTER_OPENED","runtimeChanged":true,"cloudAccessed":false,"demoReady":false,"presenterObserved":true,"layoutComplete":false,"serverStarted":false}}"#
    var launch = SetupExchange(); try launch.receive(event(launchRaw))
    _ = try launch.finish(action: "launch", exit: 0)
    rejects { _ = try launch.finish(action: "launch", exit: 1) }
    rejects { _ = try launch.finish(action: "prepare", exit: 0) }
    var falseLaunch = SetupExchange()
    try falseLaunch.receive(event(launchRaw.replacingOccurrences(of: "\"demoReady\":false", with: "\"demoReady\":true")))
    rejects { _ = try falseLaunch.finish(action: "launch", exit: 0) }
    let sleeper = Process(); sleeper.executableURL = URL(fileURLWithPath: "/bin/sleep")
    let backendRaw = #"{"kind":"result","result":{"status":"BACKEND_IMAGES_AVAILABLE","runtimeChanged":false,"cloudAccessed":false,"demoReady":false,"dockerEngineChecked":true,"imagesVerified":2,"importAttempted":false}}"#
    var backend = SetupExchange(); try backend.receive(event(backendRaw))
    _ = try backend.finish(action: "prepare-backends", exit: 0)
    rejects { _ = try backend.finish(action: "launch", exit: 0) }
    rejects { _ = try backend.finish(action: "prepare-backends", exit: 1) }
    var incompleteBackend = SetupExchange()
    try incompleteBackend.receive(event(backendRaw.replacingOccurrences(of: "\"imagesVerified\":2", with: "\"imagesVerified\":1")))
    rejects { _ = try incompleteBackend.finish(action: "prepare-backends", exit: 0) }
    precondition(setupFailureHint(action: "prepare-backends", code: "SETUP_BACKENDS_ENGINE_UNAVAILABLE").contains("without restarting"))
    precondition(setupFailureHint(action: "prepare-backends", code: "SETUP_BACKENDS_IMPORT_UNCONFIRMED").contains("will not repeat"))
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
