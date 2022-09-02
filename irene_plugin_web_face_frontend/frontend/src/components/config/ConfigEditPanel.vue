<script setup lang="ts">
import { ref, watch } from 'vue';
import { Vue3JsonEditor } from 'vue3-json-editor';
import Markdown from 'vue3-markdown-it';
import type { Config } from './service';

const props = defineProps<{
    open: boolean,
    config?: Config,
    onCancel: () => void,
    onSave: (cfg: Config) => void,
}>()

const value = ref();

watch(
    () => props.open ? props.config : null,
    (currentConfig) => {
        value.value = currentConfig?.config;
    }
);

const handleChange = (v: object) => {
    value.value = v;
}

const save = () => {
    if (props.config) {
        const updated = { ...props.config, config: value.value };
        props.onSave(updated);
    }
}
</script>

<template>
    <div class="edit-panel" :class="{ open }" tabindex="-1" @keyup.esc="onCancel">
        <template v-if="open && config">
            <div class="edit-container">
                <Markdown :source="config.comment" :linkify="true" />
                <Vue3JsonEditor v-model="value" @json-change="handleChange" mode="tree" :show-btns="false" :expanded-on-start="true"/>
            </div>
            <div class="buttons-container">
                <button @click="save()">Сохранить</button>
                <button @click="() => onCancel()">Отмена</button>
            </div>
        </template>
    </div>
</template>

<style scoped>
.edit-panel {
    display: grid;
    background: white;
    position: fixed;
    right: -512px;
    top: 0;
    bottom: 0;
    width: 512px;
    max-width: 100vw;
    transition: right 500ms, box-shadow 500ms;
    padding: 16px;
    box-sizing: border-box;
    grid-template-rows: 1fr min-content;
}

.edit-panel.open {
    right: 0;
    box-shadow: 0px 0px 100px black;
}

.buttons-container {
    display: grid;
    grid-auto-flow: column;
    grid-template-rows: 54px;
    gap: 8px;
    grid-template-columns: repeat(2, 1fr);
}

.edit-container {
    overflow-y: auto;
}

</style>

<style>
@media (max-width: 450px) {

    .edit-panel .jsoneditor-mode-tree .jsoneditor-search,
    .edit-panel .jsoneditor-mode-form .jsoneditor-search,
    .edit-panel .jsoneditor-mode-view .jsoneditor-search {
        margin-top: 36px;
        z-index: 1;
        border: 1px solid #3883fa;
        background: white;
    }

    .edit-panel .jsoneditor-mode-tree .jsoneditor-menu,
    .edit-panel .jsoneditor-mode-form .jsoneditor-menu,
    .edit-panel .jsoneditor-mode-view .jsoneditor-menu {
        margin-bottom: 36px;
    }
}
</style>
