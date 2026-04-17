<script setup lang="ts">
    import { ref } from 'vue'
    import { useDicepoolStore } from '@/stores/DicepoolStore'
    import Die from '@/components/Die.vue'
    import PoolEntity from '@/components/PoolEntity.vue'
    import Resolution from '@/components/Resolution.vue'
    import type { Dicepool } from '@/interfaces/Types'
    const props = defineProps<{
        dicepool: Dicepool,
    }>()

    const dicepoolStore = useDicepoolStore()
    const verbose_dice = ref(false)
</script>

<template>
    <div class="pool-player" @click.stop="verbose_dice = !verbose_dice">
        <div class="player">
            <!-- <div>
                {{ verbose_dice ?
                    player.small_buttons ? '👁' : '👁 detail view' :
                    player.small_buttons ? '🔘' : '🔘 simple view' }}
            </div> -->
            <div class="name header">
                {{ dicepool.player.name }}
            </div>
        </div>
        <div class="active-pool" v-if="dicepool.player.phase != dicepoolStore.phases.RESOLVE">
            <div class="dice" v-if="!verbose_dice">
                <Die v-for="d in dicepool.dice" :key="d.id" :die="d" in_pool />
            </div>
            <div class="verbose-dice" v-if="verbose_dice">
                <PoolEntity
                    v-for="entity in new Set(props.dicepool.dice.map(d => d.entityId)).values()" :key="entity"
                    :entity_id="entity ?? ''"
                    :dice="props.dicepool.dice.filter(d => d.entityId == entity)" />
                <!-- <PoolEntity
                    v-for="entity in new Set(dicepool.dice.map((d) => d.entityId))"
                    :key="entity"
                    :dice="dicepool.dice.filter((d) => d.entityId == entity)"
                    :entity_id="entity" /> -->
            </div>
        </div>
        <div class="resolved-pool" v-if="dicepool.player.phase == dicepoolStore.phases.RESOLVE">
            <Resolution :resolution="dicepool" :winner="dicepool.winner ?? false" :heroic="dicepool.heroic" :verbose="verbose_dice" />
        </div>
    </div>
</template>

<style scoped>
.pool-player {
    padding: .4em 1em;
    border: 1px solid var(--color-border);
    border-radius: 1em;
    background-color: var(--color-background);
}
</style>
