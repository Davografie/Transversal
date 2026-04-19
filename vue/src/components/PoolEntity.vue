<script setup lang="ts">
	import { watch } from 'vue'
	import PoolTraitset from './PoolTraitset.vue'
	import { useEntity } from '@/composables/Entity'
	import { useRelation } from '@/composables/Relation'
	import type { Die } from '@/interfaces/Types'
	import { RouterLink } from 'vue-router'
	import { die_shapes } from '@/composables/Die'
	const props = defineProps<{
		entity_id: string
		dice: Die[]
		result_limit?: number
		effect_limit?: number
	}>()
	const emit = defineEmits(['longpress_die'])
	const { entity, retrieve_entity, set_entity_id } = useEntity(undefined, props.entity_id)
	retrieve_entity()
	const { relation } = useRelation(undefined, props.entity_id)
	watch(relation, (newRelation) => {
		if(!entity.value.id && newRelation.fromEntity.id) {
			set_entity_id(newRelation.toEntity.id)
			retrieve_entity()
		}
	})
	console.log('entity value: ', entity.value.id)
	// if(!entity.value.id && relation.value.entity.id) {
	// 	console.log('no entity found, trying relation path for ', relation.value.entity.id)
	// 	set_entity_id(relation.value.entity.id)
	// 	retrieve_entity()
	// }
</script>

<template>
	<div class="pool-entity pool-wrapper">
		<div>
			<span class="entity-name">
				{{ entity.name }}
			</span>
		</div>
		<div class="traitsets">
			<template v-for="traitset_id in new Set(dice.map(d => d.traitsetId)).values()" :key="traitset_id">
				<PoolTraitset :traitset_id="traitset_id" :dice="dice.filter(d => d.traitsetId == traitset_id)"
					@longpress_die="(die: Die) => emit('longpress_die', die)" />
			</template>
		</div>
	</div>
</template>

<style scoped>
	.pool-entity.pool-wrapper {
		border-left: 1px solid var(--color-text);
		.entity-name {
			background-color: var(--color-text);
			color: var(--color-background);
			padding: .4em;
		}
		.traitsets {
		}
	}
</style>

<style>
.dark {
	.pool-entity-wrapper.pool-wrapper {
		.result-limit {
			color: var(--color-result-light);
		}
	}
}
.light {
	.pool-entity-wrapper.pool-wrapper {
		.result-limit {
			color: var(--color-result);
		}
	}
}
</style>
