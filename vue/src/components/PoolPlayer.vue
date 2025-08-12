<script setup lang="ts">
    import { ref } from 'vue'
    import { usePlayer } from '@/stores/Player'
    import { useDicepoolStore } from '@/stores/DicepoolStore'
    import Die from '@/components/Die.vue'
    import PoolEntity from '@/components/PoolEntity.vue'
    import Resolution from '@/components/Resolution.vue'
    import type { Resolution as ResolutionType } from '@/interfaces/Types'
    const props = defineProps<{
        resolution: ResolutionType
    }>()

    const player = usePlayer()
    const dicepoolStore = useDicepoolStore()
    const verbose_dice = ref(false)
</script>

<template>
    <div @click.stop="verbose_dice = !verbose_dice">
        <div class="player">
            <!-- <div>
                {{ verbose_dice ?
                    player.small_buttons ? '👁' : '👁 detail view' :
                    player.small_buttons ? '🔘' : '🔘 simple view' }}
            </div> -->
            <div class="name header">
                {{ resolution.player.player_name }}
            </div>
        </div>
        <div class="active-pool" v-if="resolution.player.phase != dicepoolStore.phases.RESOLVE">
            <div class="dice" v-if="!verbose_dice">
                <Die v-for="d in resolution.dice" :key="d.id" :die="d" in_pool />
            </div>
            <div class="verbose-dice" v-if="verbose_dice">
                <PoolEntity
                    v-for="entity in new Set(resolution.dice.map((d) => d.entityId))"
                    :key="entity"
                    :dice="resolution.dice.filter((d) => d.entityId == entity)"
                    :entity_id="entity" />
            </div>
        </div>
        <div class="resolved-pool" v-if="resolution.player.phase == dicepoolStore.phases.RESOLVE">
            <Resolution :resolution="resolution" :winner="resolution.winner ?? false" :heroic="resolution.heroic" :verbose="verbose_dice" />
        </div>
    </div>
</template>

<style scoped></style>
