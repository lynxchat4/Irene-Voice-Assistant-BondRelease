import type { InjectionKey } from "vue";
import type { AnyEventObject, InvokeCallback } from "xstate";


export class EventBus extends EventTarget {
    send(type: string, data: any) {
        this.dispatchEvent(new BusEvent(type, data));
    }

    dispatchEvent(event: Event): boolean {
        if (import.meta.env.VITE_EVENT_BUS_LOGS) {
            console.log(event);
        }

        return super.dispatchEvent(event);
    }
}

export const eventBusKey: InjectionKey<EventBus> = Symbol('eventBus');

export class BusEvent extends Event {
    data: any;

    constructor(type: string, data: any) {
        super(type);

        this.data = data;
    }
}

export const busConnector =
    (events: string[]) =>
        ({ eventBus }: { eventBus: EventBus }): InvokeCallback<AnyEventObject, AnyEventObject> =>
            (callback, onReceive) => {
                for (const type of events) {
                    eventBus.addEventListener(type, callback);
                }

                onReceive((event) => eventBus.dispatchEvent(new BusEvent(event.type, event.data)));

                return () => {
                    for (const type of events) {
                        eventBus.removeEventListener(type, callback);
                    }
                }
            }
