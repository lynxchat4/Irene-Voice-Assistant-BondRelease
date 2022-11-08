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
 * Отключает микрофон в переданном `MediaStream` во время воспроизведения аудио.
 * 
 * Предотвращает распознание речи голосового ассистента в качестве пользовательского ввода.
 * 
 * Теоретически, параметр `echoCancellation: true`, передаваемый при создании `MediaStream`, должен предотвращать попадание
 * воспроизводимого звука во входящий звуковой поток.
 * Однако, на практике этого не наблюдается.
 */
const trackPlaybacks = ({ onReceived, mediaStream }: { onReceived: Receiver<AnyEventObject>, mediaStream: MediaStream }) => {
    let runningPlaybacks = 0;

    onReceived(event => {
        switch (event.type) {
            case 'PLAYBACK_STARTED':
                ++runningPlaybacks;
                break;
            case 'PLAYBACK_ENDED':
                --runningPlaybacks;
                break;
        }

        if (runningPlaybacks < 0) {
            console.debug("Что-то пошло не так: счётчик активных воспроизведений опустился ниже нуля.");
            runningPlaybacks = 0;
        }

        mediaStream.getTracks()[0].enabled = (runningPlaybacks === 0);
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

        trackPlaybacks({ onReceived, mediaStream });

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
