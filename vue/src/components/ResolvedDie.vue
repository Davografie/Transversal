<script setup lang="ts">
	import Die from '@/components/Die.vue'
	import { useEntity } from '@/composables/Entity'
	import { useTraitset } from '@/composables/Traitset'
	import { useTrait } from '@/composables/Trait'
	import type { Die as DieType } from '@/interfaces/Types'

	const props = defineProps<{
		die: DieType,
		entity?: boolean
	}>()

	const { entity, retrieve_small_entity } = useEntity(undefined, props.die.entityId)
	const { traitset, retrieve_traitset } = useTraitset(undefined, props.die.traitsetId, props.die.entityId)
	const { trait, retrieve_trait } = useTrait(undefined, props.die.traitId, props.die.traitsettingId, props.die.entityId)
	retrieve_small_entity()
	retrieve_traitset()
	retrieve_trait()
</script>

<template>
	<div class="resolved-die">
		<div class="meta">
			<div class="entity" v-if="entity && props.entity">
				<RouterLink :to="'/entity/' + entity.key">
					{{ entity.name }}
				</RouterLink>
			</div>
			<div class="traitset" v-if="traitset">
				{{ traitset.name }}
			</div>
			<div class="trait" v-if="trait">
				{{ trait.name }}
			</div>
		</div>
		<Die :die="props.die" in_pool />
	</div>
</template>

<style scoped>
	.resolved-die {
		display: flex;
		align-items: center;
		justify-content: space-evenly;
		gap: 1em;
	}
</style>
