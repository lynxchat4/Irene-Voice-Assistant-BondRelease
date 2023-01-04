import type { AnyEventObject, InvokeCallback } from "xstate";

export const audioStreamWebsocketService = (
    {
        path,
        sampleRate,
    }: {
        path: string,
        sampleRate: number,
    }): InvokeCallback<any, AnyEventObject> => (callback, onReceived) => {
    const url = new URL(window.location.toString());

    url.protocol = url.protocol === 'https:' ? 'wss:' : 'ws:';
    url.pathname = path;
    url.search = new URLSearchParams({ sample_rate: sampleRate.toString() }).toString();
    url.hash = ''

    const ws = new WebSocket(url);

    const onOpen = () => {
        callback({ type: 'AUDIO_WS_OPEN', data: ws });
    }
    const onError = (event: Event) => callback({ type: 'AUDIO_WS_ERROR', data: event });
    const onClosed = () => callback('AUDIO_WS_CLOSED');

    ws.addEventListener('open', onOpen);
    ws.addEventListener('error', onError);
    ws.addEventListener('close', onClosed);

    onReceived(e => {
        if (e.type === 'SEND_DATA') {
            ws.send(e.data);
        }
    });

    return () => {
        ws.removeEventListener('open', onOpen);
        ws.removeEventListener('error', onError);
        ws.removeEventListener('close', onClosed);

        ws.close();
    };
};