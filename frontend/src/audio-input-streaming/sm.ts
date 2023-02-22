import { eventNameForMessageType, eventNameForProtocolName } from "@/components/dialog/sm-helpers";
import { assign, createMachine, send, type AnyEventObject, type InvokeCallback } from "xstate";
import { busConnector, type EventBus } from "@/components/eventBus";

import { audioStreamWebsocketService } from './audioStreamWsService';
import { run as startStreaming } from './streamingService';

export type Context = {
    eventBus: EventBus,
    sampleRate: number,
    error?: Error,
};

export const inputStreamingStateMachine = createMachine<Context>(
    {
        id: 'inputStreamer',
        predictableActionArguments: true,
        invoke: {
            id: 'eventBus',
            src: 'eventBus',
        },
        initial: 'inactive',
        on: {
            WS_DISCONNECTED: { target: 'inactive' },
        },
        states: {
            inactive: {
                on: {
                    [eventNameForProtocolName('in.stt.serverside')]: { target: 'waiting' }
                }
            },
            waiting: {
                tags: ['enabled'],
                on: {
                    [eventNameForMessageType('in.stt.serverside/ready')]: { target: 'streaming' }
                }
            },
            streaming: {
                tags: ['enabled'],
                on: {
                    [eventNameForMessageType('in.stt.serverside/processed')]: {
                        actions: ['forwardProcessedToHistory'],
                    },
                    AUDIO_WS_CLOSED: {
                        target: 'streaming.disconnected',
                    },
                    AUDIO_WS_ERROR: {
                        target: 'error',
                        actions: ['storeError'],
                    },
                },
                invoke: {
                    id: 'stream_socket',
                    src: 'streamSocket',
                },
                initial: 'connecting',
                states: {
                    connecting: {
                        on: {
                            AUDIO_WS_OPEN: { target: 'active' },
                        }
                    },
                    active: {
                        tags: ['active'],
                        invoke: {
                            src: 'streamer',
                            id: 'streamer',
                        },
                        on: {
                            STREAM_CHUNK: {
                                actions: ['forwardToSocket'],
                            },
                            [eventNameForMessageType('in.mute/mute')]: { actions: ['forwardToStreamer'] },
                            [eventNameForMessageType('in.mute/unmute')]: { actions: ['forwardToStreamer'] },
                        }
                    },
                    disconnected: {
                        after: {
                            RECONNECT_DELAY: { target: 'connecting' },
                        }
                    },
                },
            },
            error: {
                tags: ['error'],
            }
        }
    },
    {
        services: {
            eventBus: busConnector([
                eventNameForProtocolName('in.stt.serverside'),
                'WS_DISCONNECTED',
                eventNameForMessageType('in.stt.serverside/ready'),
                eventNameForMessageType('in.stt.serverside/processed'),
                eventNameForMessageType('in.mute/mute'),
                eventNameForMessageType('in.mute/unmute'),
            ]),
            streamSocket: (context, event) => audioStreamWebsocketService({
                sampleRate: context.sampleRate,
                path: event.data.path,
            }),
            streamer: (context) => (callback, onReceived) => {
                const p = startStreaming({
                    sampleRate: context.sampleRate,
                    onReceived,
                    sendChunk: chunk => callback({ type: 'STREAM_CHUNK', data: chunk }),
                });

                return async () => {
                    (await p)();
                };
            },
        },
        actions: {
            forwardProcessedToHistory: send(
                (_, evt) => ({ type: 'HISTORY_ADD_MESSAGE', data: { direction: 'in', text: evt.data.text } }),
                { to: 'eventBus' },
            ),
            forwardToSocket: send(
                (_, evt) => ({ type: 'SEND_DATA', data: evt.data }),
                { to: 'stream_socket' },
            ),
            forwardToStreamer: send(
                (_, evt) => evt,
                { to: 'streamer' },
            ),
            storeError: assign({
                error: (_, event) => event.data,
            }),
        },
        delays: {
            RECONNECT_DELAY: 10000,
        },
    },
);
