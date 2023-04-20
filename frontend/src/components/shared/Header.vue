<script setup lang="ts">
import HeaderUI from '../ui/Header.vue';
import ConnectionStatus from './ConnectionStatus.vue';
import MicrophoneStatus from './MicrophoneStatus.vue';

import SettingsIcon from '~icons/material-symbols/settings'
import BackIcon from '~icons/material-symbols/arrow-back'
import AboutIcon from '~icons/material-symbols/help-outline-rounded'
import { inject } from 'vue';

const hideConfiguration = (inject('frontendConfiguration') as any).hideConfiguration;
</script>

<template>
    <HeaderUI>
      <div class="middle">
        <RouterView name="heading" />
      </div>
      <div class="left">
        <ConnectionStatus />
        <MicrophoneStatus />
      </div>
      <div class="right">
        <RouterLink to="/config" title="Настройки" class="icon-button settings" v-if="!hideConfiguration">
          <SettingsIcon />
        </RouterLink>
        <RouterLink to="/about" title="О программе" class="icon-button about">
          <AboutIcon />
        </RouterLink>
        <RouterLink to="/" title="Назад" class="icon-button back">
          <BackIcon />
        </RouterLink>
      </div>
    </HeaderUI>
</template>

<style scoped>
a {
  display: flex;
}

a.router-link-active {
    display: none;
}

a {
  transition: transform 500ms;
}

a.settings:hover {
  transform: rotate(180deg);
}

a.back:hover {
  transform: scaleX(-1);
}
</style>
