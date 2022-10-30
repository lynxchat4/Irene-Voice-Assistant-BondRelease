<script setup lang="ts">
import { useMachine } from '@xstate/vue';

import { configMachine } from './sm';
import ConfigEditPanel from './ConfigEditPanel.vue';
import { computed } from '@vue/reactivity';

import LoadingIcon from '~icons/line-md/loading-twotone-loop'
import ErrorIcon from '~icons/material-symbols/error-outline'

const sm = useMachine(configMachine, {
    context: {
        error: null,
        configs: [],
    }
});

const editingConfig = computed(() => sm.state.value.context.configs?.[sm.state.value.context.editing]);

</script>

<template>
    <h1>
        Настройки плагинов Ирины
    </h1>
    <p>
        Для применения некоторых изменений может понадобиться перезапуск сервера.
    </p>
    <div v-if="sm.state.value.matches('loading')" class="loading">
        <LoadingIcon style="font-size: 64px" />
    </div>
    <div v-else-if="sm.state.value.matches('loadingError')" class="error">
        <ErrorIcon style="font-size: 64px" />
        <h2>Ошибка при загрузке настроек:</h2>
        <p>{{ sm.state.value.context.error }}</p>
    </div>
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
</template>

<style scoped>
.error {
    color: var(--color-error);
}

.loading, .error {
    margin-top: 20vh;
    display: flex;
    flex-direction: column;
    justify-content: space-around;
    text-align: center;
    align-items: center;
}

ul {
    list-style: none;
    padding: 0;
    margin: 0;
    display: grid;
    grid-auto-flow: row;
    grid-gap: 8px;
}

.config-entry {
    display: grid;
    grid-gap: 4px;
    grid-template-areas: 'title actions''comment comment';
    grid-template-columns: auto 1fr;
    padding: 8px;
    border-radius: 4px;
    transition: box-shadow 500ms;
    background: var(--background-card);
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
