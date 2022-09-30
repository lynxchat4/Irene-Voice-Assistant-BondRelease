<script setup lang="ts">
import { useActor } from '@xstate/vue';
import { computed, inject } from 'vue';
import type { ActorRef } from 'xstate';

const conn = useActor<ActorRef<any, any>>(inject('connectionStateMachine') as any);

const title = computed(() => {
    if (conn.state.value.matches('active.connecting')) {
        return 'Подключаюсь к серверу...'
    }

    if (conn.state.value.matches('disconnected')) {
        return 'Не удалось подключиться к серверу'
    }

    if (conn.state.value.matches('active.connected')) {
        return 'Подключение к серверу установлено'
    }

    return 'Не понятно, что с подключением к серверу'
});
</script>

<template>
    <div
     class="connection-status"
     :class="{
        connecting: conn.state.value.matches('active.connecting'),
        disconnected: conn.state.value.matches('disconnected'),
        connected: conn.state.value.matches('active.connected'),
     }"
      :title="title"
       />
</template>

<style>
.connection-status {
    width: 16px;
    height: 16px;
    border-radius: 8px;
    background: #555;
    transition: background 1s, box-shadow 1s;
    box-shadow: 0 0 10px #555;
}

.connection-status.connecting {
    background: #ff1;
    box-shadow: 0 0 10px #ff1;
}

.connection-status.disconnected {
    background: #f55;
    box-shadow: 0 0 10px #f55;
}

.connection-status.connected {
    background: #5f5;
    box-shadow: 0 0 10px #5f5;
}
</style>
