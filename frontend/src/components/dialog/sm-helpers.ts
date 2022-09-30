
export const eventNameForMessageType = (messageType: string): string =>
    `WS_RECEIVED(${messageType})`

export const eventNameForProtocolName = (protocolName: string): string =>
    `WS_READY(${protocolName})`
