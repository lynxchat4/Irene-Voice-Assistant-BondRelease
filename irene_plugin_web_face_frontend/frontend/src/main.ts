import { createApp } from 'vue'
import { interpret } from 'xstate';
import App from './App.vue'
import { connectionStateMachine } from './components/dialog/sm-connection';
import { textInputMachine } from './components/dialog/sm-input-text';
import { messageHistoryMachine } from './components/dialog/sm-message-history';
import { plaintextOutputMachine } from './components/dialog/sm-output-plaintext';
import { EventBus, eventBusKey } from './components/eventBus';
import './main.css'

const app = createApp(App);

const eventBus = new EventBus();
app.provide(eventBusKey, eventBus);

app.provide(
    'connectionStateMachine',
    interpret(
        connectionStateMachine.withConfig(
            {},
            {
                eventBus,
                protocols: [['in.text-direct', 'in.text-indirect'], ['out.text-plain']],
            },
        )
    ).start()
);

app.provide(
    'textInputMachine',
    interpret(
        textInputMachine.withConfig(
            {},
            {
                eventBus,
            },
        )
    ).start()
);

app.provide(
    'messageHistoryMachine',
    interpret(
        messageHistoryMachine.withConfig(
            {},
            {
                eventBus,
                messages: [],
            },
        ),
    ).start()
);

app.provide(
    'plaintextOutputMachine',
    interpret(
        plaintextOutputMachine.withConfig(
            {},
            {
                eventBus,
            },
        ),
    ).start()
);

app.mount('#app')
