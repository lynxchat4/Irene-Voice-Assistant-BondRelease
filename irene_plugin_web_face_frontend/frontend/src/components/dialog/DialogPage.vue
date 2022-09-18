<script setup lang="ts">
import { inject, ref } from 'vue';

import Message from './Message.vue';
import { eventBusKey } from '../eventBus';
import { useActor } from '@xstate/vue';
import type { ActorRef } from 'xstate';

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

const historySm = useActor<ActorRef<any, any>>(inject('messageHistoryMachine') as any);
</script>

<template>
    <div class="messages-wrapper">
        <div id="messages-feed">
            <template v-for="message in historySm.state.value.context.messages">
                <Message :message="message" />
            </template>
            <div v-if="historySm.state.value.context.messages.length === 0" class="empty-feed">
                <p>💬</p>
                <p>Пока ничего нет...</p>
            </div>
        </div>
        <div class="command-input-wrapper">
            <input class="command-input" v-model="inputValue" @keydown.enter="sendCommand"
                placeholder="Введи сообщение" />
            <button @click="sendCommand">&gt;</button>
        </div>
    </div>
</template>

<style scoped>
.messages-wrapper {
    display: grid;
}

.empty-feed {
    text-align: center;
    margin-bottom: auto;
    margin-top: auto;
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
    background: var(--background-content);
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
