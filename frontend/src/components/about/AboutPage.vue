<script setup lang="ts">
import GithubIcon from '~icons/simple-icons/github';
import TelegramIcon from '~icons/simple-icons/telegram';
</script>

<template>
    <div class="wrapper">
        <h1>Голосовой ассистент Ирина</h1>
        <p>
            Разработано <a class="github-account-link" href="https://github.com/AlexeyBond">@AlexeyBond</a>.
        </p>
        <p>
            <a class="link-with-icon" href="https://github.com/AlexeyBond/Irene-Voice-Assistant">
                <GithubIcon />
                репозиторий проекта
            </a>
        </p>
        <div class="original-info">
            <p>
                Основано на
                <a class="link-with-icon" href="https://github.com/janvarev/Irene-Voice-Assistant">
                    <GithubIcon />
                    оригинальном проекте
                </a>
                от
                <a class="github-account-link" href="https://github.com/janvarev">@janvarev</a>.
            </p>
            <p>
                <a class="link-with-icon" href="https://t.me/irene_va">
                    <TelegramIcon />
                    Группа проекта в Telegram
                </a>
            </p>
        </div>
    </div>
</template>

<style scoped>
div.wrapper {
    display: flex;
    flex-direction: column;
    text-align: center;
}

h1 {
    margin: 1em auto;
}

p {
    margin: 1em auto;
}

a.github-account-link {
    color: black;
    text-decoration: underline;
    font-weight: bold;
}

a.link-with-icon {
    display: inline-flex;
    vertical-align: middle;
    color: var(--color-link);
}

a.link-with-icon>svg {
    padding-right: 4px;
}

div.original-info {
    font-size: 0.8em;
    margin-top: 1em;
}

div.original-info p {
    margin-bottom: 0.25em;
    margin-top: 0;
}
</style>
