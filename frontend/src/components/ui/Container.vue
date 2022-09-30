<template>
    <main class="container" >
        <slot></slot>
    </main>
</template>

<style>
    .container {
        max-width: 100vw;
        width: 512px;
        padding: 32px 8px 8px;
        box-sizing: border-box;
        margin: auto;
        min-height: 100vh;
        background: var(--background-content);
        box-shadow: 1px 1px 5px #aaa;
    }
</style>
