import { eventNameForMessageType, eventNameForProtocolName } from "@/components/dialog/sm-helpers";
import { assign, createMachine, send, type AnyEventObject } from "xstate";
import { busConnector, EventBus } from "@/components/eventBus";
import { createModel, type KaldiRecognizer, type Model } from "vosk-browser";
import type { ServerMessageResult } from "vosk-browser/dist/interfaces";

import worklet from './recognizerWorklet.js?url';


const MODEL_URL = '/vosk/models/vosk-model-small-ru-0.22.zip';

const loadModel = async () => {
    return await createModel(MODEL_URL);
};

const openMediaStream = async (ctx: Context) => {
    return await navigator.mediaDevices.getUserMedia({
        video: false,
        audio: {
            echoCancellation: true,
            noiseSuppression: true,
            channelCount: 1,
            sampleRate: ctx.sampleRate,
        },
    });
};

const runRecognizer = (ctx: Context) => {
    const recognizer: KaldiRecognizer = new ctx.model!!.KaldiRecognizer(
        ctx.sampleRate,
    );

    recognizer.on("result", (message) => {
        const msg = message as ServerMessageResult;
        const text = msg.result.text;

        if (text === '') {
            return;
        }

        // TODO: Send recognized message
        console.log(`Result: ${text}`, msg.result.result);
    });

    const channel = new MessageChannel();
    ctx.model!!.registerPort(channel.port1);

    const audioContext = new AudioContext({ sampleRate: ctx.sampleRate });
    await audioContext.audioWorklet.addModule(worklet);
    const recognizerProcessor = new AudioWorkletNode(
        audioContext,
        'recognizer-processor',
        { channelCount: 1, numberOfInputs: 1, numberOfOutputs: 1 }
    );
    recognizerProcessor.port.postMessage(
        { action: 'init', recognizerId: recognizer.id },
        [channel.port2]
    );
    recognizerProcessor.connect(audioContext.destination);

    const source = audioContext.createMediaStreamSource(ctx.mediaStream!!);
    source.connect(recognizerProcessor);
}

export type Context = {
    eventBus: EventBus,
    sampleRate: number,
    model?: Model,
    mediaStream?: MediaStream,
};

export const localRecognizerStateMachine = createMachine<Context>(
    {
        id: 'localRecognizer',
        predictableActionArguments: true,
        invoke: {
            id: 'eventBus',
            src: 'eventBus',
        },
        type: 'parallel',
        states: {
            recognizer: {
                initial: 'inactive',
                states: {
                    inactive: {
                        // on: {
                        //     [eventNameForProtocolName('in.text-indirect')]: { target: 'active' },
                        //     [eventNameForProtocolName('in.stt.clientside')]: { target: 'active' },
                        // },
                    },
                },
            },
            model: {
                initial: 'inactive',
                states: {
                    inactive: {
                        on: {
                            LOAD_MODEL: { target: 'active' },
                        },
                    },
                    active: {
                        invoke: {
                            src: 'loadModel',
                            onError: {
                                target: 'error',
                            },
                            onDone: {
                                actions: [
                                    'storeModel',
                                    'notifyModelLoaded',
                                ],
                                target: 'active.loaded',
                            },
                        },
                        initial: 'loading',
                        states: {
                            loading: {
                                tags: ['loading'],
                            },
                            loaded: {
                                on: {
                                    LOAD_MODEL: {
                                        actions: ['notifyModelLoaded'],
                                    },
                                },
                            },
                        },
                    },
                    error: {
                        tags: ['error'],
                        after: {
                            MODEL_RELOAD_ON_ERROR: { target: 'active' },
                        },
                    },
                },
            },
        },
    },
    {
        services: {
            eventBus: busConnector([
                eventNameForProtocolName('in.text-indirect'),
                eventNameForProtocolName('in.stt.clientside'),
                eventNameForMessageType('in.stt.clientside/recognized'),
            ]),
            loadModel,
            openMediaStream,
        },
        actions: {
            storeModel: assign({
                model: (_, { data }: AnyEventObject) => data,
            }),
            notifyModelLoaded: send('MODEL_LOADED'),
        },
        delays: {
            MODEL_RELOAD_ON_ERROR: 1000,
        },
    },
);
