<script setup lang="ts">
import { useActor } from '@xstate/vue';
import { inject } from 'vue';
import type { ActorRef } from 'xstate';

const sm = useActor<ActorRef<any, any>>(inject('localRecognizerMachine') as any);

</script>

<template>
    <template v-if="sm.state.value.hasTag('error')">
        <span :title="`Ошибка: ${sm.state.value.context.error}`">‼</span>
    </template>
    <template v-else-if="sm.state.value.matches('inactive')">
        <span title="Микрофон не включен">⏸</span>
    </template>
    <template v-else-if="sm.state.value.matches('active')">
        <span title="Микрофон включен">🎤</span>
    </template>
</template>

<style scoped>
span {
    cursor: default;
}
</style>
