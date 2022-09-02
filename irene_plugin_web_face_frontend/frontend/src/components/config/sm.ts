import { assign, createMachine } from "xstate";

import { fetchConfigs, updateConfig, type Config } from './service';

export type Context = {
    error: Error | null,
    configs?: Config[],
    editing: number,
}

export const configMachine = createMachine<Context>(
    {
        id: 'config-sm',
        initial: 'loading',
        schema: {
            context: {} as Context,
            events: {} as
            | { type: 'RELOAD' }
            | { type: 'EDIT'; data: number }
            | { type: 'CANCEL' }
            | { type: 'SAVE' }
        },
        states: {
            loading: {
                invoke: {
                    src: 'fetchConfigs',
                    onError: {
                        actions: assign({
                            error: (_, event) => event.data,
                        }),
                        target: 'loadingError',
                    },
                    onDone: {
                        actions: assign({
                            error: (_) => null,
                            configs: (_, event) => event.data,
                        }),
                        target: 'idle',
                    },
                },
            },
            loadingError: {
                tags: ['can_reload'],
                after: {
                    reloadOnError: {
                        target: 'loading',
                    },
                },
                on: {
                    RELOAD: {
                        target: 'loading',
                    }
                }
            },
            idle: {
                tags: ['can_reload'],
                on: {
                    RELOAD: {
                        target: 'loading',
                    },
                    EDIT: {
                        actions: assign({
                            editing: (_, event) => event.data,
                        }),
                        target: 'editing',
                    }
                }
            },
            editing: {
                initial: 'idle',
                states: {
                    idle: {
                        on: {
                            CANCEL: '#config-sm.idle',
                            SAVE: 'saving',
                        },
                    },
                    saving: {
                        invoke: {
                            src: 'updateConfig',
                            onDone: {
                                target: '#config-sm.loading',
                                actions: assign({
                                    error: (_) => null,
                                }),
                            },
                            onError: {
                                target: 'idle',
                                actions: assign({
                                    error: (_, event) => event.data as Error,
                                }),
                            },
                        }
                    }
                }
            },
        },
    },
    {
        delays: {
            reloadOnError: 5000,
        },
        services: {
            fetchConfigs,
            updateConfig: (_, event) => updateConfig(event.data.scope, event.data.config),
        }
    }
)
