<script setup lang="ts">
    import { computed } from 'vue'
    import Die from '@/components/Die.vue'
    import { useTrait } from '@/composables/Trait'
    import { useEntity } from '@/composables/Entity'
    import type { Die as DieType } from '@/interfaces/Types'
    import { useDicepool } from '@/composables/Dicepool'

    const props = defineProps<{
        complication: DieType[]
    }>()

    const emit = defineEmits([
        'click_complication',
        'click_die'
    ])

    const dicepool = useDicepool()

    const { trait, retrieve_trait } = useTrait(
        undefined,
        props.complication[0].traitId,
        props.complication[0].traitsettingId,
        props.complication[0].entityId
    )
    retrieve_trait()

    const { entity, retrieve_small_entity } = useEntity(
        undefined,
        props.complication[0].entityId
    )
    retrieve_small_entity()

    const empty = computed(() => {
        return props.complication.every(d => dicepool.check_die(d.id ?? ''))
    })
</script>

<template>
    <div class="suggested-complication-wrapper" @click="emit('click_complication')" v-if="!empty">
        <div class="name">{{ entity?.name }}</div>
        <div class="trait-name">{{ trait?.name }}</div>
        <div class="statement" v-if="trait?.statement">{{ trait.statement }}</div>
        <div class="rating">
            <template v-for="die in props.complication" :key="die.id">
                <Die :die="die"
                    :in_pool="die.pool"
                    @click.stop="emit('click_die', die)"
                    v-if="!dicepool.check_die(die.id ?? '')" />
            </template>
        </div>
    </div>
</template>

<style scoped>
    .suggested-complication-wrapper {
        border: 1px solid var(--color-border);
        margin: 0.5em;
        padding: 0.5em;
        cursor: pointer;
        .name {
            font-weight: bold;
            text-align: center;
        }
        .rating {
            display: flex;
            justify-content: center;
        }
    }
    .suggested-complication-wrapper:hover {
        background-color: var(--color-highlight);
        color: var(--color-highlight-text);
    }
</style>

<style>
    .dark {
        .suggested-complication-wrapper {
            border-radius: 5px 5px 20px 20px;
            text-shadow: none;
        }
    }
    .light {
    }
</style>
