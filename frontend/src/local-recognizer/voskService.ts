import { eventNameForMessageType } from '@/components/dialog/sm-helpers';
import { createModel, type KaldiRecognizer } from 'vosk-browser';
import type { ServerMessagePartialResult, ServerMessageResult } from 'vosk-browser/dist/interfaces';
import type { AnyEventObject, Receiver } from 'xstate';

import worklet from './recognizerWorklet.js?url';

const createMediaStream = ({ sampleRate }: { sampleRate: number }): Promise<MediaStream> => {
    if (!navigator?.mediaDevices?.getUserMedia) {
        throw new Error("Голосовой ввод не поддерживается");
    }

    return navigator.mediaDevices.getUserMedia({
        video: false,
        audio: {
            echoCancellation: true,
            noiseSuppression: true,
            channelCount: 1,
            sampleRate,
        },
    });
};

/**
 * Отключает микрофон в переданном `MediaStream` во время воспроизведения аудио на этом клиенте или где-то в другом месте.
 * 
 * Предотвращает распознание речи голосового ассистента в качестве пользовательского ввода.
 * 
 * Использует сообщения, отправляемые сервером по протоколу `in.mute`.
 */
const processMuteRequests = ({ onReceived, mediaStream }: { onReceived: Receiver<AnyEventObject>, mediaStream: MediaStream }) => {
    onReceived(event => {
        const track =  mediaStream.getTracks()[0];

        if (!track) {
            return;
        }

        switch (event.type) {
            case eventNameForMessageType('in.mute/mute'):
                track.enabled = false;
            case eventNameForMessageType('in.mute/unmute'):
                track.enabled = true;
        }
    });
};

export const run = async ({
    modelUrl = '/api/expose_vosk_model/model.zip',
    sampleRate = 48000,
    onRecognized,
    onPartialRecognized,
    onReceived = () => {},
}: {
    modelUrl?: string,
    sampleRate?: number,
    onPartialRecognized?: (text: string) => void,
    onRecognized: (text: string) => void,
    onReceived: Receiver<AnyEventObject>,
}) => {
    let terminate: (() => Promise<void> | void) | null = null;

    try {
        const mediaStream = await createMediaStream({ sampleRate });

        const terminateStream = () => {
            for (const track of mediaStream.getTracks()) {
                track.stop();
            }
        }

        terminate = terminateStream;

        const audioContext = new AudioContext({
            sampleRate
        });

        const terminateContext = () => audioContext.close();

        terminate = async () => {
            await terminateContext();
            terminateStream();
        }

        const source = audioContext.createMediaStreamSource(mediaStream);

        const model = await createModel(modelUrl);

        terminate = async () => {
            await terminateContext();
            terminateStream();
            model.terminate();
        };

        const recognizer: KaldiRecognizer = new model.KaldiRecognizer(
            sampleRate,
        );

        recognizer.on("result", (message) => {
            const msg = message as ServerMessageResult;
            const text = msg.result.text;

            if (text === '') {
                return;
            }

            onRecognized(text);
        });

        if (onPartialRecognized) {
            recognizer.on("partialresult", (message) => {
                const msg = message as ServerMessagePartialResult;
                const text = msg.result.partial;

                if (text === '') {
                    return;
                }

                onPartialRecognized(text);
            });
        }

        const channel = new MessageChannel();
        model.registerPort(channel.port1);

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

        source.connect(recognizerProcessor);

        processMuteRequests({ onReceived, mediaStream });

        return terminate;
    } catch (e) {
        try {
            await terminate?.();
        } catch (ee) {
            console.error(ee);
        }

        if (
            e instanceof Error &&
            /AudioContext.createMediaStreamSource: Connecting AudioNodes from AudioContexts with different sample-rate is currently not supported\./.test(e.message) &&
            /Firefox/g.test(navigator.userAgent)
        ) {
            // Firefox иногда настолько пытается защитить приватность пользователя, что скрывает битрейт микрофона даже от самого себя
            throw new Error('Не удалось запустить распознавание голоса. Попробуйте отключить флаг privacy.resistFingerprinting в настройках (about:config)');
        }

        throw e;
    }
};
