<script setup lang="ts">
import { useMachine, useActor } from '@xstate/vue';
import { computed } from 'vue';

import { dialogStateMachine } from './sm';

const sm = useMachine(
    dialogStateMachine,
    {
        context: {
            protocols: [['in.text-direct', 'in.text-indirect'], ['out.text-plain']],
        },
    },
);

const conn = useActor(computed(() => sm.state.value.children.connection));

</script>

<template>
    <div v-if="conn.state.value.matches('active.connecting')" >
        Connecting..
    </div>
    <div v-if="conn.state.value.matches('active.connected')" >
        Connected
    </div>
    <div v-if="conn.state.value.matches('disconnected')" >
        Disconnected
    </div>
</template>
