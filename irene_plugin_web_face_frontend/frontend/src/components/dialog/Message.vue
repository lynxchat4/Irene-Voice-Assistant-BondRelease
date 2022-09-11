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
    box-shadow: 0px 0px 5px #aaa;
}

.message.in {
    align-self: flex-start;
    background: var(--in-message-background);
}

.message.out {
    align-self: flex-end;
    background: var(--out-message-background);
}
</style>
