<script setup lang="ts">
	import { watch } from 'vue'
	import PoolTraitset from './PoolTraitset.vue'
	import { useEntity } from '@/composables/Entity'
	import { useRelation } from '@/composables/Relation'
	import type { Die } from '@/interfaces/Types'
	import { RouterLink } from 'vue-router'
	const props = defineProps<{
		entity_id: string
		dice: Die[]
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
	<div class="pool-entity-wrapper pool-wrapper">
		<RouterLink class="entity_name" :to="'/entity/' + entity.key" v-if="props.dice.some((d) => d.traitsetId != 'Traitsets/1')">
			{{ entity.name }}
		</RouterLink>
		<div class="entity_name complication-entity" v-else>
			{{ entity.name }}
		</div>
		<div class="divider" />
		<div class="traitsets">
			<template v-for="traitset in new Set(dice.map(d => d.traitsetId)).values()" :key="traitset">
				<PoolTraitset :traitset_id="traitset" :dice="dice.filter(d => d.traitsetId == traitset)"
					@longpress_die="(die: Die) => emit('longpress_die', die)" />
				<div class="traitset-divider" />
			</template>
		</div>
	</div>
</template>

<style scoped>
	.pool-entity-wrapper {
		max-width: 24rem;
	}
	.pool-wrapper {
		/* padding-left: 1em; */
		text-align: left;
		.divider {
			border-bottom: 1px solid var(--color-highlight);
		}
		.complication-entity {
			background-color: var(--color-hitch);
			color: var(--color-hitch-text);
			display: inline-block;
			padding: 3px 1em;
		}
		.traitsets {
			box-shadow: inset 0 0 10px var(--color-highlight-mute);
		}
		.traitset-divider {
			border-bottom: 1px solid var(--color-highlight-mute);
		}
	}
</style>
