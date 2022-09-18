<template>
    <header class="header">
        <slot></slot>
    </header>
</template>

<style>
.header {
    position: fixed;
    left: 0;
    right: 0;
    top: 0;
    height: 32px;
    background: var(--background-content);
    box-shadow: 1px 1px 5px #aaa;
    display: flex;
    align-items: center;
    padding: 0 8px;
    z-index: var(--z-index-header);
}
</style>
