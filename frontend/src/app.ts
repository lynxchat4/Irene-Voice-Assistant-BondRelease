import { createApp } from 'vue'
import { createRouter, createWebHashHistory } from 'vue-router';
import { interpret } from 'xstate';
import App from './App.vue'
import ConfigsPageVue from './components/config/ConfigsPage.vue';
import DialogPageVue from './components/dialog/DialogPage.vue';
import AboutPageVue from './components/about/AboutPage.vue';
import HeaderTitleVue from './components/ui/HeaderTitle.vue';
import { connectionStateMachine, type ProtocolRequirements } from './components/dialog/sm-connection';
import { textInputMachine } from './components/dialog/sm-input-text';
import { messageHistoryMachine } from './components/dialog/sm-message-history';
import { audioOutputMachine } from './components/dialog/sm-output-audio';
import { plaintextOutputMachine } from './components/dialog/sm-output-plaintext';
import { EventBus, eventBusKey } from './components/eventBus';
import { localRecognizerStateMachine } from './local-recognizer/sm';
import { inputStreamingStateMachine } from './audio-input-streaming/sm';

import z from 'zod';
import { fetchConfig, FRONTEND_CONFIG_SCOPE } from './components/config/service';
import { streamingSupported } from './audio-input-streaming/streamingService';


const FrontendConfig = z.object({
    preferStreamingInput: z.boolean().default(true),
    audioInputEnabled: z.boolean().default(true),
    audioOutputEnabled: z.boolean().default(true),
    microphoneSampleRate: z.number(),
    hideConfiguration: z.boolean().default(false),
});

const loadConfig: () => Promise<z.TypeOf<typeof FrontendConfig>> = () => new Promise(resolve => {
    const tryLoad = async () => {
        try {
            const { config: rawConfig } = await fetchConfig(FRONTEND_CONFIG_SCOPE);

            resolve(FrontendConfig.parse(rawConfig));
        } catch (error) {
            console.error('Не удалось запросить настройки фронтенда, проверьте, исправен ли сервер:', error);

            setTimeout(tryLoad, 5000);
        }
    }

    tryLoad();
});

/**
 * Выберает, какие протоколы клиент будет запрашивать у сервера.
 */
const getProtocolRequirements = ({
    audioInputEnabled,
    audioOutputEnabled,
    preferStreamingInput,
}: z.TypeOf<typeof FrontendConfig>) => {
    const requirements: ProtocolRequirements = [];

    // Протоколы для текстового ввода команд
    requirements.push(['in.text-direct', 'in.text-indirect']);

    // Протоколы для вывода ответов
    if (audioOutputEnabled) {
        // Воспроизведение аудио-файлов
        requirements.push(['out.audio.link']);

        // Использование воспроизведения аудио-файлов для вывода речи и вывод текста на случай если вывод речи не поддерживается.
        requirements.push(['out.tts.serverside', 'out.text-plain']);
    } else {
        // Вывод только текстовых ответов если вывод аудио отключён.
        requirements.push(['out.text-plain'])
    }

    // Голосовой ввод команд
    if (audioInputEnabled) {
        // Проверяем, поддерживается ли потоковый ввод аудио (текущая реализация может перестать работать на новых браузерах)
        if (streamingSupported) {
            if (preferStreamingInput) {
                requirements.push(
                    ['in.stt.serverside', 'in.stt.clientside', 'in.text-indirect']
                );
            } else {
                requirements.push(
                    ['in.stt.clientside', 'in.text-indirect', 'in.stt.serverside']
                );
            }
        } else {
            requirements.push(['in.stt.clientside', 'in.text-indirect'])
        }

        // Получение от сервера сообщений о том, когда следует выключать микрофон.
        requirements.push(['in.mute']);
    }

    return requirements;
}

export const initApplication = async () => {
    const config = await loadConfig();

    const { microphoneSampleRate, hideConfiguration } = config;

    const app = createApp(App);

    app.provide('frontendConfiguration', config);

    const eventBus = new EventBus();
    app.provide(eventBusKey, eventBus);

    app.provide(
        'connectionStateMachine',
        interpret(
            connectionStateMachine.withConfig(
                {},
                {
                    eventBus,
                    protocols: getProtocolRequirements(config),
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
                    sampleRate: microphoneSampleRate,
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
                    sampleRate: microphoneSampleRate,
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
            ...(hideConfiguration ? [] : [{
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
            }]),
            {
                path: '/about',
                components: {
                    main: AboutPageVue,
                    heading: HeaderTitleVue,
                },
                props: {
                    heading: {
                        text: 'О программе',
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
}
