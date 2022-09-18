<script setup lang="ts">
import HeaderUI from '../ui/Header.vue';
import ConnectionStatus from './ConnectionStatus.vue';
</script>

<template>
    <HeaderUI>
      <ConnectionStatus />
      <div class="middle">
        <RouterView name="heading" />
      </div>
      <RouterLink to="/config">Настройки</RouterLink>
      <RouterLink to="/">Назад</RouterLink>
    </HeaderUI>
</template>

<style scoped>
a.router-link-active {
    display: none;
}

.middle {
    flex-grow: 1;
    text-align: center;
}
</style>
