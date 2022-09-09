import { createMachine, send, sendParent, type AnyEventObject, type InvokeCallback } from "xstate";
import { pure } from "xstate/lib/actions";
import { NegotiationAgreeMessage } from "./messages";
import { eventNameForMessageType, eventNameForProtocolName } from "./sm-helpers";


const websocketService = (): InvokeCallback<any, AnyEventObject> => (callback, onReceived) => {
    const url = new URL(window.location.toString());

    url.protocol = url.protocol === 'https:' ? 'wss:' : 'ws:';
    url.pathname = '/api/face_web/ws';

    console.log('Connecting to ', url);

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
}

export const connectionStateMachine = createMachine(
    {
        id: 'connection',
        initial: 'active',
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
        },
        actions: {
            requestNegotiation: send(
                (context: any) => ({ type: 'WS_SEND', data: { type: 'negotiate/request', protocols: context.protocols } }),
                { to: 'websocket' },
            ),
            forwardWsProtocolEvents: pure(
                (_, event: AnyEventObject) => {
                    const { protocols } = NegotiationAgreeMessage.parse(event.data);

                    return protocols
                        .filter(Boolean)
                        .map(proto => sendParent({ type: eventNameForProtocolName(proto) }))
                }
            ),
            forwardIncommingMessage: sendParent((_, { data }: AnyEventObject) => ({ type: eventNameForMessageType(data.type), data })),
        },
    },
);
