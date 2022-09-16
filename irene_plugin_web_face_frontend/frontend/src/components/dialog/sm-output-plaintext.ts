import { createMachine, send } from "xstate";
import { busConnector, EventBus } from "../eventBus";
import { eventNameForMessageType, eventNameForProtocolName } from "./sm-helpers";


export type Context = {
    eventBus: EventBus,
};

export const plaintextOutputMachine = createMachine<Context>(
    {
        id: 'plaintextOutput',
        predictableActionArguments: true,
        initial: 'inactive',
        invoke: {
            id: 'eventBus',
            src: 'eventBus',
        },
        states: {
            inactive: {
                on: {
                    [eventNameForProtocolName('out.text-plain')]: { target: 'active' },
                },
            },
            active: {
                on: {
                    WS_DISCONNECTED: { target: 'inactive' },
                    [eventNameForMessageType('out.text-plain/text')]: {
                        actions: ['saveMessageToHistory'],
                    },
                },
            },
        },
    },
    {
        services: {
            eventBus: busConnector([
                eventNameForProtocolName('out.text-plain'),
                eventNameForMessageType('out.text-plain/text'),
                'WS_DISCONNECTED',
            ]),
        },
        actions: {
            saveMessageToHistory: send(
                (_, event) => ({ type: 'HISTORY_ADD_MESSAGE', data: { direction: 'out', text: event.data.text } }),
                { to: 'eventBus' }
            ),
        },
    }
);
