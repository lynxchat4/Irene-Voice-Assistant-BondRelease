import { createMachine, send } from "xstate";
import { busConnector, EventBus } from "../eventBus";
import { eventNameForProtocolName } from "./sm-helpers";

export type Context = {
    eventBus: EventBus,
};

export const textInputMachine = createMachine<Context>(
    {
        id: 'textInput',
        predictableActionArguments: true,
        initial: 'inactive',
        invoke: {
            id: 'eventBus',
            src: 'eventBus',
        },
        on: {
            WS_DISCONNECTED: { target: 'inactive' },
            [eventNameForProtocolName('in.text-indirect')]: { target: 'indirect_protocol' },
            [eventNameForProtocolName('in.text-direct')]: { target: 'direct_protocol' },
        },
        states: {
            inactive: {
            },
            indirect_protocol: {
                on: {
                    IN_TEXT_COMMAND: {
                        actions: [
                            'sendIndirectMessage',
                            'sendMessageToHistory',
                        ],
                    },
                },
            },
            direct_protocol: {
                on: {
                    [eventNameForProtocolName('in.text-indirect')]: undefined,
                    IN_TEXT_COMMAND: {
                        actions: [
                            'sendDirectMessage',
                            'sendMessageToHistory',
                        ],
                    },
                },
            },
        },
    },
    {
        services: {
            eventBus: busConnector([
                eventNameForProtocolName('in.text-direct'),
                eventNameForProtocolName('in.text-indirect'),
                'IN_TEXT_COMMAND',
                'WS_DISCONNECTED',
            ]),
        },
        actions: {
            sendIndirectMessage: send(
                (_, event) => ({ type: 'WS_SEND', data: { type: 'in.text-indirect/text', text: event.data } }),
                { to: 'eventBus' }
            ),
            sendDirectMessage: send(
                (_, event) => ({ type: 'WS_SEND', data: { type: 'in.text-direct/text', text: event.data } }),
                { to: 'eventBus' }
            ),
            sendMessageToHistory: send(
                (_, event) => ({ type: 'HISTORY_ADD_MESSAGE', data: { direction: 'in', text: event.data } }),
                { to: 'eventBus' }
            )
        },
    },
);
