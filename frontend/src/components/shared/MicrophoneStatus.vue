<script setup lang="ts">
import { useActor } from '@xstate/vue';
import { inject } from 'vue';
import type { ActorRef } from 'xstate';

import MicIcon from '~icons/material-symbols/mic-rounded'
import MicOffIcon from '~icons/material-symbols/mic-off-rounded'
import LoadingIcon from '~icons/line-md/loading-twotone-loop'

const sm = useActor<ActorRef<any, any>>(inject('localRecognizerMachine') as any);

</script>

<template>
    <template v-if="sm.state.value.hasTag('error')">
        <span :title="`Ошибка: ${sm.state.value.context.error.message}`">
            <MicOffIcon style="color: red" />
        </span>
    </template>
    <template v-else-if="sm.state.value.matches('inactive')">
        <span title="Микрофон не включен">
            <MicOffIcon />
        </span>
    </template>
    <template v-else-if="sm.state.value.matches('active')">
        <span v-if="sm.state.value.hasTag('starting')" title="Голосовой ввод запускается">
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
