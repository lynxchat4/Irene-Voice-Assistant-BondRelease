<script setup lang="ts">
const props = defineProps<{
    message: {
        text: string,
        direction: 'in' | 'out',
    }
}>();
</script>

<template>
    <div class="message" :class="{
        in: props.message.direction === 'in',
        out: props.message.direction === 'out',
    }">
        <div class="text">
            {{ props.message.text }}
        </div>
    </div>
</template>

<style>

.message {
    min-width: 50%;
    max-width: 70%;
    margin-top: 16px;
    padding: 16px;
    border-radius: 16px;
}

.message.in {
    align-self: flex-end;
    background: var(--background-in-message);
    border-bottom-right-radius: 0;
}

.message.out {
    align-self: flex-start;
    background: var(--background-out-message);
    border-top-left-radius: 0;
}
</style>
