import { assign, createMachine } from "xstate";
import { z } from "zod";
import { busConnector, EventBus } from "../eventBus";

export const Message = z.object({
    direction: z.enum(['in', 'out']),
    text: z.string(),
});

export type Message = z.infer<typeof Message>;

export type Context = {
    eventBus: EventBus,
    messages: Message[],
};

export const messageHistoryMachine = createMachine<Context>(
    {
        id: 'messageHistory',
        predictableActionArguments: true,
        initial: 'active',
        invoke: {
            id: 'eventBus',
            src: 'eventBus',
        },
        states: {
            active: {
                on: {
                    HISTORY_ADD_MESSAGE: {
                        actions: ['storeMessage'],
                    },
                },
            },
        },
    },
    {
        services: {
            eventBus: busConnector([
                'HISTORY_ADD_MESSAGE',
            ]),
        },
        actions: {
            storeMessage: assign({
                messages: ({ messages }, { data }) => [...messages, Message.parse(data)],
            }),
        },
    }
);
