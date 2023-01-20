<script setup lang="ts">
import { useActor } from '@xstate/vue';
import { inject } from 'vue';
import type { ActorRef } from 'xstate';

import MicIcon from '~icons/material-symbols/mic-rounded'
import MicOffIcon from '~icons/material-symbols/mic-off-rounded'
import LoadingIcon from '~icons/line-md/loading-twotone-loop'

const clientSTTMachine = useActor<ActorRef<any, any>>(inject('localRecognizerMachine') as any);
const serverSTTMachine = useActor<ActorRef<any, any>>(inject('inputStreamerMachine') as any);

</script>

<template>
    <template v-if="clientSTTMachine.state.value.hasTag('error') || serverSTTMachine.state.value.hasTag('error')">
        <span :title="`Ошибка: ${clientSTTMachine.state.value.context.error?.message ?? serverSTTMachine.state.value.context.error?.message}`">
            <MicOffIcon style="color: red" />
        </span>
    </template>
    <template v-else-if="clientSTTMachine.state.value.matches('inactive') && !serverSTTMachine.state.value.hasTag('enabled')">
        <span title="Микрофон не включен">
            <MicOffIcon />
        </span>
    </template>
    <template v-else-if="serverSTTMachine.state.value.hasTag('enabled')">
        <span v-if="serverSTTMachine.state.value.hasTag('active')" title="Микрофон включен (потоковый режим)">
            <MicIcon />
        </span>
        <span v-else title="Голосовой ввод запускается (потоковый режим)">
            <MicIcon />
            <LoadingIcon class="loading-icon" />
        </span>
    </template>
    <template v-else-if="clientSTTMachine.state.value.matches('active')">
        <span v-if="clientSTTMachine.state.value.hasTag('starting')" title="Голосовой ввод запускается">
            <MicIcon />
            <LoadingIcon class="loading-icon" />
        </span>
        <span v-else title="Микрофон включен">
            <MicIcon />
        </span>
    </template>
</template>

<style scoped>
span {
    cursor: default;
    display: flex;
}

span>.loading-icon {
    position: absolute;
}
</style>
