import { createMachine, send, type AnyEventObject, type InvokeCallback } from "xstate";
import { pure } from "xstate/lib/actions";
import { busConnector, EventBus } from "../eventBus";
import { NegotiationAgreeMessage } from "./messages";
import { eventNameForMessageType, eventNameForProtocolName } from "./sm-helpers";


const websocketService = (): InvokeCallback<any, AnyEventObject> => (callback, onReceived) => {
    const url = new URL(window.location.toString());

    url.protocol = url.protocol === 'https:' ? 'wss:' : 'ws:';
    url.pathname = '/api/face_web/ws';
    url.hash = ''

    const ws = new WebSocket(url);

    const onOpen = () => {
        callback({ type: 'WS_OPEN', data: ws });
    }
    const onError = (event: Event) => callback({ type: 'WS_ERROR', data: event });
    const onClosed = () => callback('WS_CLOSED');
    const onMessage = (event: MessageEvent) => {
        const data = JSON.parse(event.data);

        callback({ type: 'WS_RECEIVED', data });
    };

    ws.addEventListener('open', onOpen);
    ws.addEventListener('error', onError);
    ws.addEventListener('close', onClosed);
    ws.addEventListener('message', onMessage);

    onReceived(e => {
        if (e.type === 'WS_SEND') {
            ws.send(JSON.stringify(e.data));
        }
    });

    return () => {
        ws.removeEventListener('open', onOpen);
        ws.removeEventListener('error', onError);
        ws.removeEventListener('close', onClosed);
        ws.removeEventListener('message', onMessage);

        ws.close();
    };
};

export type Context = {
    eventBus: EventBus,
    protocols: (string | null)[][],
}

export const connectionStateMachine = createMachine<Context>(
    {
        id: 'connection',
        predictableActionArguments: true,
        initial: 'active',
        invoke: {
            id: 'eventBus',
            src: 'eventBus',
        },
        states: {
            active: {
                invoke: {
                    id: 'websocket',
                    src: 'websocket',
                },
                on: {
                    WS_ERROR: {
                        target: 'disconnected',
                    },
                    WS_CLOSED: {
                        target: 'disconnected',
                    },
                },
                initial: 'connecting',
                states: {
                    connecting: {
                        initial: 'opening',
                        states: {
                            opening: {
                                on: {
                                    WS_OPEN: {
                                        actions: ['requestNegotiation'],
                                        target: 'negotiating',
                                    },
                                },
                            },
                            negotiating: {
                                on: {
                                    WS_RECEIVED: {
                                        actions: ['forwardWsProtocolEvents'],
                                        target: '#connection.active.connected',
                                    },
                                },
                            },
                        },
                    },
                    connected: {
                        on: {
                            WS_RECEIVED: {
                                actions: ['forwardIncommingMessage'],
                            },
                            WS_SEND: {
                                actions: ['forwardToWebsocket'],
                            },
                            WS_ERROR: {
                                target: '#connection.disconnected',
                                actions: ['notifyDisconnect'],
                            },
                            WS_CLOSED: {
                                target: '#connection.disconnected',
                                actions: ['notifyDisconnect'],
                            },
                        },
                    },
                },
            },
            disconnected: {
                after: {
                    RECONNECT_DELAY: { target: 'active' },
                },
            },
        },
    },
    {
        delays: {
            RECONNECT_DELAY: 1000,
        },
        services: {
            websocket: websocketService,
            eventBus: busConnector(['WS_SEND']),
        },
        actions: {
            requestNegotiation: send(
                (context) => ({ type: 'WS_SEND', data: { type: 'negotiate/request', protocols: context.protocols } }),
                { to: 'websocket' },
            ),
            forwardWsProtocolEvents: pure(
                (_, event: AnyEventObject) => {
                    const { protocols } = NegotiationAgreeMessage.parse(event.data);

                    return protocols
                        .filter(Boolean)
                        .map(proto => send({ type: eventNameForProtocolName(proto as string) }, { to: 'eventBus' }))
                }
            ),
            forwardIncommingMessage: send(
                (_, { data }: AnyEventObject) => ({ type: eventNameForMessageType(data.type), data }),
                { to: 'eventBus' },
            ),
            forwardToWebsocket: send((_, event) => event, { to: 'websocket' }),
            notifyDisconnect: send({ type: 'WS_DISCONNECTED' }, { to: 'eventBus' }),
        },
    },
);
