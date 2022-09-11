<script setup lang="ts">
import { inject, ref } from 'vue';

import Container from '../ui/Container.vue';
import Header from '../ui/Header.vue';
import Message from './Message.vue';
import ConnectionStatus from './ConnectionStatus.vue';
import { eventBusKey } from '../eventBus';

const inputValue = ref('');

const eventBus = inject(eventBusKey);

const sendCommand = () => {
    const command = inputValue.value;
    inputValue.value = '';

    if (command.trim() == '') {
        return;
    }

    eventBus?.send('IN_TEXT_COMMAND', command);
}

</script>

<template>
    <Header>
        <ConnectionStatus />
    </Header>
    <Container>
        <div class="messages-wrapper">
            <div id="messages-feed">
                <Message :message="{text: 'asdasd', direction: 'out'}" />
                <Message :message="{text: 'asdasd sdas dasd sda sd sada sda sda asd', direction: 'in'}" />
                <Message :message="{text: 'asdasd ad dsk v mxcvc kvxcmv kxmvx cmvx', direction: 'out'}" />
                <Message :message="{text: 'asdasd sd c adcasdc sdcd', direction: 'in'}" />
                <Message :message="{text: 'asdasd ds sdiu8csj 8vj cvx8cvj jkn', direction: 'out'}" />
            </div>
            <div class="command-input-wrapper">
                <input class="command-input" v-model="inputValue" @keydown.enter="sendCommand"
                    placeholder="Введи сообщение" />
                <button @click="sendCommand">&gt;</button>
            </div>
        </div>
    </Container>
</template>

<style scoped>
.messages-wrapper {
    display: grid;
}

.command-input-wrapper {
    position: fixed;
    bottom: 0;
    width: 512px;
    margin-left: -8px;
    max-width: 100vw;
    height: 64px;
    display: flex;
    justify-content: space-between;
    box-shadow: 0px -2px 5px #aaa;
    transition: box-shadow 500ms;
}

.command-input-wrapper:focus-within {
    box-shadow: 0px -2px 10px #999;
}

input.command-input {
    box-sizing: border-box;
    font-size: 24px;
    padding: 16px;
    border: none;
    flex-grow: 1;
    min-width: 240px;
}

.command-input-wrapper>button {
    border: none;
    background: var(--content-background);
    padding: 16px;
}

input.command-input:focus {
    outline: none;
}

#messages-feed {
    width: 100%;
    box-sizing: border-box;
    padding-bottom: 72px;
    min-height: calc(100vh - 40px);
    box-sizing: border-box;
    display: flex;
    flex-direction: column;
    justify-content: flex-end;
}
</style>
