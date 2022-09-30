<script setup lang="ts">
import Header from './components/shared/Header.vue';
import Container from './components/ui/Container.vue';
</script>

<template>
  <Header />
  <Container>
    <RouterView name="main" />
  </Container>
</template>
