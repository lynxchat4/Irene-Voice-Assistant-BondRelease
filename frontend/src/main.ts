import { createApp } from 'vue'
import { createRouter, createWebHashHistory } from 'vue-router';
import { interpret } from 'xstate';
import App from './App.vue'
import ConfigsPageVue from './components/config/ConfigsPage.vue';
import DialogPageVue from './components/dialog/DialogPage.vue';
import HeaderTitleVue from './components/ui/HeaderTitle.vue';
import { connectionStateMachine } from './components/dialog/sm-connection';
import { textInputMachine } from './components/dialog/sm-input-text';
import { messageHistoryMachine } from './components/dialog/sm-message-history';
import { audioOutputMachine } from './components/dialog/sm-output-audio';
import { plaintextOutputMachine } from './components/dialog/sm-output-plaintext';
import { EventBus, eventBusKey } from './components/eventBus';
import './main.css';
import { localRecognizerStateMachine } from './local-recognizer/sm';
import { inputStreamingStateMachine } from './audio-input-streaming/sm';

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
                protocols: [
                    ['out.audio.link'],
                    ['in.text-direct', 'in.text-indirect'],
                    ['out.tts.serverside', 'out.text-plain'],
                    ['in.stt.serverside', 'in.stt.clientside', 'in.text-indirect'],
                    ['in.mute'],
                ],
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

app.provide(
    'audioOutputMachine',
    interpret(
        audioOutputMachine.withConfig(
            {},
            {
                eventBus,
            },
        ),
    ).start()
);

app.provide(
    'localRecognizerMachine',
    interpret(
        localRecognizerStateMachine.withConfig(
            {},
            {
                eventBus,
                // TODO: Настраивать в настройках плагина (?)
                sampleRate: 48000,
            },
        ),
    ).start()
);

app.provide(
    'inputStreamerMachine',
    interpret(
        inputStreamingStateMachine.withConfig(
            {},
            {
                eventBus,
                // TODO: Настраивать в настройках плагина (?)
                sampleRate: 48000,
            },
        ),
    ).start()
);

const router = createRouter({
    history: createWebHashHistory(),
    routes: [
        {
            path: '/',
            components: {
                main: DialogPageVue,
                heading: HeaderTitleVue,
            },
            props: {
                heading: {
                    text: 'Ирина',
                },
            },
        },
        {
            path: '/config',
            components: {
                main: ConfigsPageVue,
                heading: HeaderTitleVue,
            },
            props: {
                heading: {
                    text: 'Настройки',
                },
            },
        },
        {
            path: '/:path(.*)*',
            redirect: '/',
        }
    ],
});

app.use(router);

app.mount('#app')
