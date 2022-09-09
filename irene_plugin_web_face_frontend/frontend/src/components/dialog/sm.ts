import { createMachine } from "xstate";

import { connectionStateMachine } from './sm-connection';


export const dialogStateMachine = createMachine(
    {
        id: 'dialog',
        invoke: [
            {
                id: 'connection',
                src: connectionStateMachine,
                data: (context: any) => ({
                    protocols: context.protocols,
                }),
            },
        ]
    },
);
