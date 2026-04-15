<script setup lang="ts">
    import { usePlayerStore } from '@/stores/PlayerStore'
    import { ButtonTypes, useButtonTypes } from '@/composables/Button';
    import ButtonMinimal from '@/components/UI/ButtonMinimal.vue';

    const player = usePlayerStore()
    defineProps<{
        amount?: number
    }>()

    // 🪙☯
</script>

<template>
    <div class="pp" :class="player.small_buttons ? 'small' : 'verbose'" title="plot point">
        <div class="pp-wrapper button-mnml">
            <span v-if="amount" class="amount label">
                {{ amount }}
            </span>
            <!-- <span class="icon">☯</span> -->
			<!-- <img src="/img/icons/plot_point.png" class="icon" /> -->
            <ButtonMinimal :function="ButtonTypes.PP" />
        </div>
        <!-- <span class="label" v-if="!player.small_buttons"> plot point{{ ((amount ?? 0) > 1 ? 's' : '') }}</span> -->
    </div>
</template>

<style scoped>
    .pp {
        /* display: inline-block; */
        /* font-size: .6em; */
        border-radius: 20px;
        padding: 0 .5em;
        /* border: 1px solid var(--color-border); */
        /* background-color: var(--color-background-mute); */
        color: var(--color-text);
        display: inline-flex;
        flex-direction: column;
        justify-content: center;
        .amount {
            padding-right: .2em;
        }
        .icon {
            font-size: 1em;
            /* max-width: 1.4em; */
            /* max-height: 1.4em; */
        }
        .label {
            font-size: .8em;
        }
    }
    .pp.small {
        border: none;
        /* background-color: transparent; */
        text-shadow: 0 0 2px var(--color-background), 0 0 2px var(--color-background);
    }
</style>
