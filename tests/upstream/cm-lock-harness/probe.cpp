// SPDX-FileCopyrightText: 2026 maninblack
// SPDX-License-Identifier: MIT
#include <atomic>
#include <cerrno>
#include <chrono>
#include <condition_variable>
#include <cstdlib>
#include <cstdio>
#include <iostream>
#include <memory>
#include <mutex>
#include <thread>
#include <Poco/Net/HTTPServer.h>
#include <Poco/Net/HTTPRequestHandler.h>
#include <Poco/Net/HTTPRequestHandlerFactory.h>
#include <Poco/Net/HTTPServerRequest.h>
#include <Poco/Net/HTTPServerResponse.h>
#include <Poco/Net/ServerSocket.h>
#include <cm/communication/communication.hpp>
#include <core/cm/monitoring/monitoring.hpp>
#include <core/cm/alerts/alerts.hpp>
#include <core/common/crypto/cryptohelper.hpp>
#include <core/common/tools/heapallocator.hpp>

using namespace std::chrono_literals;
using aos::cm::communication::Communication;

namespace {
void Check(bool condition, const char* text)
{
    if (!condition) {
        std::cerr << "HARNESS_ERROR " << text << std::endl;
        std::_Exit(2);
    }
}

class Event {
public:
    void Set()
    {
        std::lock_guard lock(mMutex);
        mReady = true;
        mCV.notify_all();
    }
    bool Wait(std::chrono::milliseconds timeout = 3s)
    {
        std::unique_lock lock(mMutex);
        return mCV.wait_for(lock, timeout, [this] { return mReady; });
    }
private:
    std::mutex mMutex;
    std::condition_variable mCV;
    bool mReady = false;
};

// The public UUID dependency is reached AFTER the running-state check and
// BEFORE EnqueueMessage takes Communication::mMutex. This also covers Stop.
class GatedUUID final : public aos::crypto::UUIDItf {
public:
    bool armed = false;
    std::atomic<unsigned> sequence {0};
    Event entered, release;
    aos::RetWithError<aos::uuid::UUID> CreateUUIDv4() override
    {
        if (armed) {
            std::cout << "SEND_PASSED_RUNNING_CHECK" << std::endl;
            entered.Set();
            Check(release.Wait(), "UUID gate release timed out");
            std::cout << "SEND_GATE_RELEASED" << std::endl;
        }
        char value[37];
        std::snprintf(value, sizeof(value), "00000000-0000-4000-8000-%012u", ++sequence);
        return aos::uuid::StringToUUID(value);
    }
    aos::RetWithError<aos::uuid::UUID> CreateUUIDv5(
        const aos::uuid::UUID&, const aos::Array<uint8_t>&) override
    {
        return {{}, aos::ErrorEnum::eNotSupported};
    }
};

// Exercise native fallback to the configured local discovery URL. No real
// credentials/TLS are involved; a cached loopback endpoint avoids HTTP discovery.
class MissingCert final : public aos::iamclient::CertProviderItf {
public:
    bool gated = false;
    mutable Event entered, release;
    aos::Error GetCert(const aos::String&, const aos::Array<uint8_t>&,
        const aos::Array<uint8_t>&, aos::CertInfo&) const override
    {
        if (gated) {
            entered.Set();
            Check(release.Wait(), "certificate fixture gate timed out");
        }
        return aos::ErrorEnum::eNotFound;
    }
    aos::Error SubscribeListener(const aos::String&, aos::iamclient::CertListenerItf&) override
    { return aos::ErrorEnum::eNone; }
    aos::Error UnsubscribeListener(aos::iamclient::CertListenerItf&) override
    { return aos::ErrorEnum::eNone; }
};

struct PeerState {
    Event close, firstClose, firstMessage, secondMessage;
    bool worker = false;
    std::atomic<unsigned> connections {0}, messages {0};
};
class WebSocketPeer final : public Poco::Net::HTTPRequestHandler {
public:
    explicit WebSocketPeer(PeerState& state) : mState(state) {}
    void handleRequest(Poco::Net::HTTPServerRequest& request,
        Poco::Net::HTTPServerResponse& response) override
    {
        try {
            Poco::Net::WebSocket peer(request, response);
            const unsigned ordinal = ++mState.connections;
            if (!mState.worker) {
                Check(mState.close.Wait(30s), "local peer lifetime timed out");
            } else if (ordinal == 1) {
                Check(mState.firstClose.Wait(), "first peer close gate timed out");
                peer.shutdown();
            } else {
                Poco::Buffer<char> frame(0);
                int flags = 0;
                for (;;) {
                    const int size = peer.receiveFrame(frame, flags);
                    if (size == 0 || (flags & Poco::Net::WebSocket::FRAME_OP_BITMASK)
                            == Poco::Net::WebSocket::FRAME_OP_CLOSE) {
                        peer.shutdown();
                        break;
                    }
                    Check((flags & Poco::Net::WebSocket::FRAME_OP_BITMASK)
                        == Poco::Net::WebSocket::FRAME_OP_BINARY, "unexpected worker frame");
                    if (++mState.messages == 1) mState.firstMessage.Set();
                    else mState.secondMessage.Set();
                    frame.resize(0);
                }
            }
        } catch (const std::exception&) {
            Check(false, "local WebSocket peer failed");
        }
    }
private:
    PeerState& mState;
};
class PeerFactory final : public Poco::Net::HTTPRequestHandlerFactory {
public:
    explicit PeerFactory(PeerState& state) : mState(state) {}
    Poco::Net::HTTPRequestHandler* createRequestHandler(
        const Poco::Net::HTTPServerRequest&) override { return new WebSocketPeer(mState); }
private:
    PeerState& mState;
};

// Forward to the real subscriber. The marker adds no held lock when the
// callback reaches Monitoring/Alerts. Listener lifetime covers all test threads.
class Subscriber final : public aos::cloudconnection::ConnectionListenerItf {
public:
    aos::cm::monitoring::Monitoring* monitoring = nullptr;
    aos::cm::alerts::Alerts* alerts = nullptr;
    Communication* communication = nullptr;
    bool reentry = false, holdDisconnect = false;
    std::atomic<unsigned> connects {0}, disconnects {0};
    Event connectedEntered, secondConnected, disconnectedEntered, releaseDisconnect;
    void OnConnect() override
    {
        if (reentry) Reenter(true);
        if (monitoring) monitoring->OnConnect();
        if (alerts) alerts->OnConnect();
        if (++connects == 1) connectedEntered.Set();
        else secondConnected.Set();
    }
    void OnDisconnect() override
    {
        std::cout << "DISCONNECT_CALLBACK_ENTERED" << std::endl;
        disconnectedEntered.Set();
        if (holdDisconnect) Check(releaseDisconnect.Wait(), "callback release timed out");
        if (reentry) Reenter(false);
        if (monitoring) monitoring->OnDisconnect();
        if (alerts) alerts->OnDisconnect();
        ++disconnects;
        std::cout << "DISCONNECT_CALLBACK_RETURNED" << std::endl;
    }
    void Reenter(bool connected)
    {
        Check(communication->IsConnected() == connected, "callback state mismatch");
        Check(communication->SendAlerts(aos::Alerts{}).IsNone(), "callback sender failed");
    }
};

void CheckHeld(aos::Mutex& mutex)
{
    const int result = pthread_mutex_trylock(static_cast<pthread_mutex_t*>(mutex));
    if (result == 0) mutex.Unlock();
    Check(result == EBUSY, "subscriber mutex must be held at rendezvous");
}
}

int main(int argc, char** argv)
{
    if (argc != 4) return 2;
    const std::string module = argv[1], action = argv[2], schedule = argv[3];
    Check(module == "monitoring" || module == "alerts", "invalid module");
    Check(action == "disconnect" || action == "stop", "invalid action");
    const bool lifecycle = schedule == "duplicate" || schedule == "close-error" ||
        schedule == "reentry" || schedule == "unsubscribe" || schedule == "parallel-close" ||
        schedule == "connect-stop";
    const bool worker = schedule == "worker";
    Check(schedule == "serial" || schedule == "overlap" || lifecycle || worker, "invalid schedule");
    const bool overlap = schedule == "overlap";

    aos::HeapAllocator allocator;
    auto communication = std::make_unique<Communication>();
    auto monitoring = std::make_unique<aos::cm::monitoring::Monitoring>();
    auto alerts = std::make_unique<aos::cm::alerts::Alerts>();
    GatedUUID uuid;
    MissingCert cert;
    auto crypto = std::make_unique<aos::crypto::CryptoHelper>();
    crypto->mAllocator = &allocator;
    alerts->mAllocator = &allocator;
    aos::cm::config::Config config;
    crypto->mCertProvider = &cert;
    crypto->mServiceDiscoveryURL = "http://127.0.0.1";
    communication->mCryptoHelper = crypto.get();
    communication->mConfig = &config;
    Subscriber subscriber;
    subscriber.communication = communication.get();
    subscriber.reentry = schedule == "reentry";
    communication->mUUIDProvider = &uuid;
    communication->mIsRunning = true;
    monitoring->mSender = communication.get();
    monitoring->mIsRunning = true;
    alerts->mSender = communication.get();
    alerts->mIsRunning = true;
    if (module == "monitoring") subscriber.monitoring = monitoring.get();
    else subscriber.alerts = alerts.get();
    Check(communication->SubscribeListener(subscriber).IsNone(), "subscribe failed");

    PeerState state;
    state.worker = worker;
    Poco::Net::ServerSocket socket(Poco::Net::SocketAddress("127.0.0.1", 0));
    Poco::Net::HTTPServer server(new PeerFactory(state), socket, new Poco::Net::HTTPServerParams);
    server.start();
    communication->mCloudHttpRequest = Poco::Net::HTTPRequest("GET", "/", "HTTP/1.1");
    communication->mDiscoveryResponse.emplace();
    communication->mDiscoveryResponse->mConnectionInfo.push_back(
        "ws://127.0.0.1:" + std::to_string(socket.address().port()));
    auto connect = [&] {
        Check(communication->ConnectToCloud().IsNone(), "native ConnectToCloud failed");
        Check(communication->IsConnected(), "connected state missing");
    };
    if (!worker) connect();
    auto fill = [&] {
        if (module == "monitoring") {
            auto data = std::make_unique<aos::monitoring::NodeMonitoringData>();
            data->mNodeID = "isolated-node";
            Check(monitoring->OnMonitoringReceived(*data).IsNone(), "monitoring input failed");
        } else {
            auto alert = std::make_unique<aos::SystemAlert>();
            alert->mNodeID = "isolated-node";
            alert->mTimestamp = aos::Time::Now();
            alert->mMessage = "isolated synthetic lock-test event";
            Check(alerts->OnAlertReceived(aos::AlertVariant(*alert)).IsNone(), "alert input failed");
        }
    };
    auto send = [&] {
        auto error = module == "monitoring" ? monitoring->SendMonitoringData() : alerts->SendAlerts();
        Check(error.IsNone(), "native sender returned error");
    };
    auto disconnect = [&] {
        auto error = action == "stop" ? communication->Stop() : communication->Disconnect();
        Check(error.IsNone(), "native disconnect returned error");
    };
    auto finish = [&](bool subscribed = true) {
        state.close.Set();
        Check(communication->Disconnect().IsNone(), "final test disconnect failed");
        server.stopAll();
        if (subscribed) Check(communication->UnsubscribeListener(subscriber).IsNone(), "unsubscribe failed");
        std::cout << "PASS_COMPLETED_AND_RECONNECTED" << std::endl;
    };
    if (lifecycle) {
        if (schedule == "duplicate") {
            communication->NotifyConnectionEstablished();
            Check(subscriber.connects == 1, "duplicate connect callback");
            disconnect();
            disconnect();
            Check(subscriber.disconnects == 1, "duplicate disconnect callback");
            connect();
            Check(subscriber.connects == 2, "reconnect callback missing");
        } else if (schedule == "close-error") {
            communication->mWebSocket->close();
            if (action == "stop") Check(communication->Stop().IsNone(), "stop on closed socket failed");
            else Check(!communication->Disconnect().IsNone(), "shutdown exception not exercised");
            Check(!communication->IsConnected(), "shutdown error retained connected state");
            Check(subscriber.disconnects == 1, "shutdown error lost disconnect callback");
            if (action == "stop") Check(communication->Stop().Is(aos::ErrorEnum::eWrongState),
                "repeated Stop must retain its native wrong-state contract");
            Check(communication->Disconnect().IsNone(), "repeat disconnect after close error failed");
            Check(subscriber.disconnects == 1, "shutdown error duplicated callback");
            communication->mIsRunning = true;
            connect();
        } else if (schedule == "reentry") {
            disconnect();
            connect();
            Check(communication->mSendQueue.size() == 3, "callback enqueues missing");
        } else if (schedule == "unsubscribe") {
            subscriber.holdDisconnect = true;
            std::thread closer(disconnect);
            Check(subscriber.disconnectedEntered.Wait(), "no callback for unsubscribe probe");
            Event started, completed;
            std::thread unsubscriber([&] {
                started.Set();
                Check(communication->UnsubscribeListener(subscriber).IsNone(), "concurrent unsubscribe failed");
                completed.Set();
            });
            Check(started.Wait(), "unsubscribe did not start");
            Check(!completed.Wait(100ms), "unsubscribe returned while callback still active");
            subscriber.releaseDisconnect.Set();
            closer.join();
            unsubscriber.join();
            connect();
            disconnect();
            Check(subscriber.connects == 1 && subscriber.disconnects == 1, "callback after unsubscribe");
            finish(false);
            return 0;
        } else if (schedule == "connect-stop") {
            disconnect();
            cert.gated = true;
            std::thread connector([&] { Check(communication->ConnectToCloud().IsNone(),
                "pending connect failed"); });
            Check(cert.entered.Wait(), "connect did not reach certificate gate");
            Event started, stopped;
            std::thread stopper([&] { started.Set();
                Check(communication->Stop().IsNone(), "stop during connect failed"); stopped.Set(); });
            Check(started.Wait(), "stop during connect did not start");
            Check(!stopped.Wait(100ms), "stop overtook pending connect transition");
            cert.release.Set();
            connector.join();
            stopper.join();
            Check(!communication->IsConnected(), "late connect after stop");
            Check(subscriber.connects == 2 && subscriber.disconnects == 2, "connect/stop event order wrong");
        } else {
            Event go;
            std::thread closer([&] { Check(go.Wait(), "close gate"); disconnect(); });
            std::thread stopper([&] { Check(go.Wait(), "stop gate");
                Check(communication->Stop().IsNone(), "concurrent Stop failed"); });
            go.Set();
            closer.join();
            stopper.join();
            Check(subscriber.disconnects == 1, "parallel close duplicated disconnect");
            Check(!communication->IsConnected(), "parallel close retained connected state");
            Check(!communication->ConnectToCloud().IsNone(), "reconnected after Stop");
        }
        finish();
        return 0;
    }
    if (worker) {
        communication->mThreadPool.emplace_back([&] { communication->HandleConnection(); });
        Check(subscriber.connectedEntered.Wait(), "worker first connection missing");
        fill();
        uuid.armed = true;
        std::thread sender(send);
        Check(uuid.entered.Wait(), "worker send did not reach rendezvous");
        state.firstClose.Set();
        Check(subscriber.disconnectedEntered.Wait(), "worker disconnect callback missing");
        uuid.release.Set();
        sender.join();
        uuid.armed = false;
        Check(subscriber.secondConnected.Wait(), "worker did not reconnect");
        Check(subscriber.connects == 2 && subscriber.disconnects == 1, "worker event ordering wrong");
        communication->mThreadPool.emplace_back([&] { communication->HandleSendQueue(); });
        Check(state.firstMessage.Wait(), "queued packet not delivered after reconnect");
        fill();
        send();
        Check(state.secondMessage.Wait(), "next packet not delivered after reconnect");
        Check(communication->Stop().IsNone(), "worker stop/join failed");
        Check(subscriber.connects == 2 && subscriber.disconnects == 2, "stop notification order wrong");
        Check(state.messages == 2, "worker packet count mismatch");
        finish();
        return 0;
    }
    fill();
    if (overlap) {
        uuid.armed = true;
        Event sent, disconnected;
        std::thread sender([&] { send(); sent.Set(); });
        Check(uuid.entered.Wait(), "sender did not reach UUID rendezvous");
        std::thread closer([&] { disconnect(); disconnected.Set(); });
        Check(subscriber.disconnectedEntered.Wait(), "disconnect callback not reached");
        const bool acquired = communication->mMutex.try_lock();
        if (acquired) communication->mMutex.unlock();
        // Do not require the bad lock scope: a future correction may release it.
        std::cout << "TRANSPORT_MUTEX_HELD=" << (!acquired) << std::endl;
        CheckHeld(module == "monitoring" ? monitoring->mMutex : alerts->mMutex);
        uuid.release.Set();
        std::cout << "RENDEZVOUS_COMPLETE" << std::endl;
        if (!sent.Wait(2s) || !disconnected.Wait(2s)) {
            std::cout << "FAIL_BOUNDED_COMPLETION" << std::endl;
            // Keep only this disposable process available for parent stack
            // capture. The external runner/CTest timeout always terminates it.
            std::this_thread::sleep_for(20s);
            std::_Exit(1);
        }
        sender.join();
        closer.join();
        uuid.armed = false;
    } else {
        send();
        disconnect();
    }
    Check(!communication->IsConnected(), "disconnect state missing");
    Check(communication->mSendQueue.size() == 1, "first packet not queued exactly once");
    communication->mIsRunning = true;
    connect();
    fill();
    send();
    Check(communication->mSendQueue.size() == 2, "post-reconnect packet missing");
    finish();
    return 0;
}
