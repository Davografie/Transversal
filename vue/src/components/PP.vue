<script setup lang="ts">
    import { usePlayer } from '@/stores/Player'

    const player = usePlayer()
    defineProps<{
        amount?: number
    }>()

    // 🪙
</script>

<template>
    <button class="pp" :class="player.small_buttons ? 'small' : 'verbose'" title="plot point">
        <div class="pp-wrapper">
            <span v-if="amount" class="amount">
                {{ amount }}
            </span>
            <span class="icon">☯</span>
        </div>
        <span class="label" v-if="!player.small_buttons"> plot point{{ ((amount ?? 0) > 1 ? 's' : '') }}</span>
    </button>
</template>

<style scoped>
    .pp {
        /* display: inline-block; */
        /* font-size: .6em; */
        border-radius: 20px;
        padding: 0 .5em;
        border: 1px solid var(--color-border);
        background-color: var(--color-background-mute);
        color: var(--color-text);
        display: inline-flex;
        flex-direction: column;
        justify-content: center;
        .amount {
            padding-right: .2em;
        }
        .icon {
            font-size: 1.8em;
        }
        .label {
            font-size: .8em;
        }
    }
    .pp.small {
        border: none;
        background-color: transparent;
        text-shadow: 0 0 2px var(--color-background), 0 0 2px var(--color-background);
    }
</style>
