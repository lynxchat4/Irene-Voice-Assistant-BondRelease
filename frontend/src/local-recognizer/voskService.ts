import { createModel, type KaldiRecognizer } from 'vosk-browser';
import type { ServerMessagePartialResult, ServerMessageResult } from 'vosk-browser/dist/interfaces';

import worklet from './recognizerWorklet.js?url';

export const run = async ({
    // TODO: Использовать отдельный плагин для загрузки/хранения моделей вместо хранения в папке со статикой
    modelUrl = '/vosk/models/vosk-model-small-ru-0.22.zip',
    sampleRate = 48000,
    onRecognized,
    onPartialRecognized,
}: {
    modelUrl?: string,
    sampleRate?: number,
    onPartialRecognized?: (text: string) => void,
    onRecognized: (text: string) => void,
}) => {
    const model = await createModel(modelUrl);
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

    const mediaStream = await navigator.mediaDevices.getUserMedia({
        video: false,
        audio: {
            echoCancellation: true,
            noiseSuppression: true,
            channelCount: 1,
            sampleRate,
        },
    });

    const channel = new MessageChannel();
    model.registerPort(channel.port1);

    const audioContext = new AudioContext({
        sampleRate
    });
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

    const source = audioContext.createMediaStreamSource(mediaStream);
    source.connect(recognizerProcessor);

    return async () => {
        await audioContext.close();
        model.terminate();
    };
};
