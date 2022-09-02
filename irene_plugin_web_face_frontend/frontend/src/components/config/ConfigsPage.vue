<script setup lang="ts">
import { useMachine } from '@xstate/vue';

import { configMachine } from './sm';
import Container from '../ui/Container.vue';
import ConfigEditPanel from './ConfigEditPanel.vue';
import { computed } from '@vue/reactivity';

const sm = useMachine(configMachine, {
    context: {
        error: null,
        configs: [],
    }
});

const editingConfig = computed(() => sm.state.value.context.configs?.[sm.state.value.context.editing]);

</script>

<template>
    <Container>
        <template v-if="sm.state.value.matches('loading')">
            Loading...
        </template>
        <template v-else-if="sm.state.value.matches('loadingError')">
            Error: {{ sm.state.value.context.error }}
        </template>
        <ul v-else>
            <li v-for="(config, index) in sm.state.value.context.configs" class="config-entry">
                <h2 class="config-title">{{ config.scope }}</h2>
                <p class="short-comment">{{ config.comment }}</p>
                <div class="config-actions">
                    <button @click="sm.send('EDIT', { data: index })">Настроить</button>
                </div>
            </li>
        </ul>
        <ConfigEditPanel
            :open="sm.state.value.matches('editing')"
            :config="editingConfig"
            :onCancel="() => sm.send('CANCEL')"
            :onSave="data => sm.send('SAVE', { data })"
        />
    </Container>
</template>

<style scoped>
ul {
    list-style: none;
    padding: 0;
    margin: 0;
}

.config-entry {
    display: grid;
    grid-gap: 4px;
    grid-template-areas: 'title actions''comment comment';
    grid-template-columns: auto 1fr;
    padding: 8px;
    border-radius: 4px;
    transition: box-shadow 500ms;
}

.config-entry:hover {
    box-shadow: 0px 0px 10px #aaa;
    z-index: 10;
}

.config-entry>.config-title {
    margin: 0;
    grid-area: title;
    overflow: hidden;
    text-overflow: ellipsis;
}

.config-entry>.config-actions {
    display: flex;
    flex-direction: row;
    justify-content: flex-end;
}

.config-entry>.short-comment {
    grid-area: comment;
    white-space: nowrap;
    text-overflow: ellipsis;
    max-width: 100%;
    overflow: hidden;
    margin: 0;
}
</style>
