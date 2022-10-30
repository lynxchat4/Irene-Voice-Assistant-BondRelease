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
    padding: 0 8px;
    z-index: var(--z-index-header);
}

.header>div {
    position: absolute;
    top: 0;
    bottom: 0;
    display: flex;
    align-items: center;
}

.header>div.left>* {
    margin-right: 8px;
}

.header>div.right>* {
    margin-left: 8px;
}

.header>.left {
    left: 8px;
}

.header>.middle {
    left: 0;
    right: 0;
    justify-content: center;
}

.header>.right {
    right: 8px;
}
</style>
