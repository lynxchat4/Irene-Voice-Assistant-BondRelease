<template>
    <div class="container" >
        <slot></slot>
    </div>
</template>

<style>
    .container {
        max-width: 100vw;
        width: 512px;
        padding: 32px 8px 8px;
        box-sizing: border-box;
        margin: auto;
        min-height: 100vh;
        background: var(--content-background);
        box-shadow: 1px 1px 5px #aaa;
    }
</style>
